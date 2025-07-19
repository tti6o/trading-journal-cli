"""
技术分析模块单元测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from services.technical_analysis import (
    TechnicalAnalyzer, MarketAnalyzer, TechnicalSignal,
    MovingAverageRule, RSIRule, MACDRule, BollingerBandsRule,
    VolumeRule
)


class TestTechnicalSignal:
    """测试TechnicalSignal数据类"""
    
    def test_signal_creation(self):
        """测试信号创建"""
        signal = TechnicalSignal(
            symbol='BTCUSDT',
            timestamp=datetime.now(),
            signal_type='BUY',
            confidence=0.8,
            indicators={'rsi': 25, 'macd': 0.5},
            triggered_rules=['RSI超卖', 'MACD金叉'],
            price=50000.0,
            message='买入信号'
        )
        
        assert signal.symbol == 'BTCUSDT'
        assert signal.signal_type == 'BUY'
        assert signal.confidence == 0.8
        assert len(signal.triggered_rules) == 2


class TestSignalRules:
    """测试信号规则"""
    
    def setup_method(self):
        """设置测试数据"""
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=50, freq='h')
        np.random.seed(42)
        
        close_prices = 50000 + np.cumsum(np.random.normal(0, 100, 50))
        
        self.test_data = pd.DataFrame({
            'open': close_prices + np.random.normal(0, 50, 50),
            'high': close_prices + np.abs(np.random.normal(100, 50, 50)),
            'low': close_prices - np.abs(np.random.normal(100, 50, 50)),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 50)
        }, index=dates)
        
        # 添加指标（模拟计算结果）
        self.test_data['SMA_10'] = self.test_data['close'].rolling(10).mean()
        self.test_data['SMA_20'] = self.test_data['close'].rolling(20).mean()
        self.test_data['RSI_14'] = np.random.uniform(20, 80, 50)
        self.test_data['MACD_12_26_9'] = np.random.normal(0, 50, 50)
        self.test_data['MACDs_12_26_9'] = np.random.normal(0, 40, 50)
        self.test_data['MACDh_12_26_9'] = self.test_data['MACD_12_26_9'] - self.test_data['MACDs_12_26_9']
        
    def test_moving_average_rule(self):
        """测试移动平均规则"""
        rule = MovingAverageRule(fast_period=10, slow_period=20, weight=1.0)
        
        # 创建金叉条件
        current_data = self.test_data.iloc[-1].copy()
        indicators = {
            'SMA_10': 50100,
            'SMA_20': 50000
        }
        
        # 修改历史数据创建交叉
        historical_data = self.test_data.copy()
        historical_data.loc[historical_data.index[-2], 'SMA_10'] = 49950
        historical_data.loc[historical_data.index[-2], 'SMA_20'] = 50000
        historical_data.loc[historical_data.index[-1], 'SMA_10'] = 50100
        historical_data.loc[historical_data.index[-1], 'SMA_20'] = 50000
        
        signal_type, confidence, message = rule.evaluate(indicators, current_data, historical_data)
        
        assert signal_type == 'BUY'
        assert confidence > 0
        assert '金叉' in message
    
    def test_rsi_rule(self):
        """测试RSI规则"""
        rule = RSIRule(period=14, weight=1.0)
        
        # 创建RSI反弹条件
        current_data = self.test_data.iloc[-1].copy()
        indicators = {'RSI_14': 35}
        
        # 修改历史数据创建反弹
        historical_data = self.test_data.copy()
        historical_data.loc[historical_data.index[-2], 'RSI_14'] = 25
        historical_data.loc[historical_data.index[-1], 'RSI_14'] = 35
        
        signal_type, confidence, message = rule.evaluate(indicators, current_data, historical_data)
        
        assert signal_type == 'BUY'
        assert confidence > 0
        assert 'RSI' in message
    
    def test_macd_rule(self):
        """测试MACD规则"""
        rule = MACDRule(fast=12, slow=26, signal=9, weight=1.0)
        
        # 创建MACD金叉条件
        current_data = self.test_data.iloc[-1].copy()
        indicators = {
            'MACD_12_26_9': 10,
            'MACDs_12_26_9': 8,
            'MACDh_12_26_9': 2
        }
        
        # 修改历史数据创建金叉
        historical_data = self.test_data.copy()
        historical_data.loc[historical_data.index[-2], 'MACDh_12_26_9'] = -1
        historical_data.loc[historical_data.index[-1], 'MACDh_12_26_9'] = 2
        
        signal_type, confidence, message = rule.evaluate(indicators, current_data, historical_data)
        
        assert signal_type == 'BUY'
        assert confidence > 0
        assert 'MACD' in message


class TestTechnicalAnalyzer:
    """测试技术分析器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.analyzer = TechnicalAnalyzer('BTCUSDT')
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=100, freq='h')
        np.random.seed(42)
        
        base_price = 50000
        price_changes = np.cumsum(np.random.normal(0, 100, 100))
        close_prices = base_price + price_changes
        
        self.test_data = pd.DataFrame({
            'open': close_prices + np.random.normal(0, 50, 100),
            'high': close_prices + np.abs(np.random.normal(100, 50, 100)),
            'low': close_prices - np.abs(np.random.normal(100, 50, 100)),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
    
    def test_calculate_indicators(self):
        """测试指标计算"""
        result = self.analyzer.calculate_indicators(self.test_data)
        
        # 检查是否添加了指标列
        expected_indicators = ['SMA_10', 'SMA_20', 'EMA_12', 'RSI_14', 'MACD_12_26_9']
        
        for indicator in expected_indicators:
            assert indicator in result.columns, f"缺少指标: {indicator}"
        
        # 检查指标值不全为NaN
        assert not result['SMA_20'].iloc[-10:].isna().all(), "SMA_20全为NaN"
        assert not result['RSI_14'].iloc[-10:].isna().all(), "RSI_14全为NaN"
    
    def test_analyze_signals_with_insufficient_data(self):
        """测试数据不足时的信号分析"""
        small_data = self.test_data.head(5)
        signal = self.analyzer.analyze_signals(small_data)
        
        assert signal is None or signal.signal_type == 'NEUTRAL'
    
    def test_analyze_signals_with_valid_data(self):
        """测试有效数据的信号分析"""
        # 先计算指标
        data_with_indicators = self.analyzer.calculate_indicators(self.test_data)
        
        # 分析信号
        signal = self.analyzer.analyze_signals(data_with_indicators)
        
        assert signal is not None
        assert signal.symbol == 'BTCUSDT'
        assert signal.signal_type in ['BUY', 'SELL', 'NEUTRAL']
        assert 0 <= signal.confidence <= 1
        assert isinstance(signal.price, float)


class TestMarketAnalyzer:
    """测试市场分析器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.market_analyzer = MarketAnalyzer()
        
        # 创建多个交易对的测试数据
        self.market_data = {}
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        for i, symbol in enumerate(symbols):
            dates = pd.date_range('2023-01-01', periods=100, freq='h')
            np.random.seed(42 + i)
            
            base_price = [50000, 3000][i]
            price_changes = np.cumsum(np.random.normal(0, base_price * 0.002, 100))
            close_prices = base_price + price_changes
            
            self.market_data[symbol] = pd.DataFrame({
                'open': close_prices + np.random.normal(0, base_price * 0.001, 100),
                'high': close_prices + np.abs(np.random.normal(base_price * 0.002, base_price * 0.001, 100)),
                'low': close_prices - np.abs(np.random.normal(base_price * 0.002, base_price * 0.001, 100)),
                'close': close_prices,
                'volume': np.random.uniform(1000, 5000, 100)
            }, index=dates)
    
    def test_add_remove_symbol(self):
        """测试添加和移除交易对"""
        self.market_analyzer.add_symbol('BTCUSDT')
        assert 'BTCUSDT' in self.market_analyzer.analyzers
        
        self.market_analyzer.remove_symbol('BTCUSDT')
        assert 'BTCUSDT' not in self.market_analyzer.analyzers
    
    def test_analyze_market(self):
        """测试市场分析"""
        signals = self.market_analyzer.analyze_market(self.market_data)
        
        assert len(signals) == len(self.market_data)
        
        for symbol in self.market_data.keys():
            assert symbol in signals
            signal = signals[symbol]
            assert isinstance(signal, TechnicalSignal)
            assert signal.symbol == symbol
    
    def test_get_market_summary(self):
        """测试市场摘要"""
        signals = self.market_analyzer.analyze_market(self.market_data)
        summary = self.market_analyzer.get_market_summary(signals)
        
        assert 'total_symbols' in summary
        assert 'buy_signals' in summary
        assert 'sell_signals' in summary
        assert 'neutral_signals' in summary
        assert 'avg_confidence' in summary
        assert 'market_sentiment' in summary
        
        assert summary['total_symbols'] == len(signals)
        assert summary['buy_signals'] + summary['sell_signals'] + summary['neutral_signals'] == len(signals)
        assert summary['market_sentiment'] in ['BULLISH', 'BEARISH', 'NEUTRAL']


class TestConfigurationHandling:
    """测试配置处理"""
    
    def test_default_config(self):
        """测试默认配置"""
        analyzer = TechnicalAnalyzer('BTCUSDT')
        config = analyzer.config
        
        assert 'indicators' in config
        assert 'signal_rules' in config
        
        # 检查默认指标配置
        indicators = config['indicators']
        assert 'SMA_10' in indicators
        assert 'RSI_14' in indicators
        assert 'MACD' in indicators
    
    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = {
            'indicators': {
                'SMA_10': {'enabled': True, 'params': {'length': 10}},
                'RSI_14': {'enabled': False, 'params': {'length': 14}},
            },
            'signal_rules': {
                'ma_cross': {'enabled': True, 'weight': 1.5},
                'rsi_reversal': {'enabled': False, 'weight': 0.0},
            }
        }
        
        analyzer = TechnicalAnalyzer('BTCUSDT', custom_config)
        assert analyzer.config == custom_config


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_dataframe(self):
        """测试空DataFrame"""
        analyzer = TechnicalAnalyzer('BTCUSDT')
        empty_df = pd.DataFrame()
        
        result = analyzer.calculate_indicators(empty_df)
        assert result.empty
        
        signal = analyzer.analyze_signals(empty_df)
        assert signal is None
    
    def test_insufficient_data(self):
        """测试数据不足的情况"""
        analyzer = TechnicalAnalyzer('BTCUSDT')
        
        # 只有5行数据
        small_df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = analyzer.calculate_indicators(small_df)
        # 数据不足时应该返回原数据
        assert len(result) == 5
        
    def test_missing_columns(self):
        """测试缺少必需列的情况"""
        analyzer = TechnicalAnalyzer('BTCUSDT')
        
        # 缺少volume列
        incomplete_df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [102, 103, 104]
        })
        
        result = analyzer.calculate_indicators(incomplete_df)
        # 应该返回原数据（因为缺少必需列）
        assert len(result) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 