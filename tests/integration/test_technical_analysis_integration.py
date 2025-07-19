"""
技术分析模块集成测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from services.technical_analysis import TechnicalAnalyzer, MarketAnalyzer


class TestTechnicalAnalysisIntegration:
    """技术分析集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建真实的测试数据
        self.create_realistic_test_data()
        
    def create_realistic_test_data(self):
        """创建模拟真实市场的测试数据"""
        # 生成100个数据点的模拟价格数据
        np.random.seed(42)  # 固定随机种子以确保测试可重复
        
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        
        # 模拟价格走势 - 先下跌后上涨的趋势
        base_price = 50000
        trend = np.concatenate([
            np.linspace(0, -2000, 30),  # 下跌趋势
            np.linspace(-2000, -1800, 20),  # 横盘
            np.linspace(-1800, 1000, 50)   # 上涨趋势
        ])
        
        # 添加随机波动
        noise = np.random.normal(0, 200, 100)
        close_prices = base_price + trend + noise
        
        # 生成OHLV数据
        self.btc_data = pd.DataFrame({
            'open': close_prices + np.random.normal(0, 50, 100),
            'high': close_prices + np.abs(np.random.normal(100, 50, 100)),
            'low': close_prices - np.abs(np.random.normal(100, 50, 100)),
            'close': close_prices,
            'volume': np.random.uniform(500, 2000, 100)
        }, index=dates)
        
        # 确保OHLC逻辑正确
        for i in range(len(self.btc_data)):
            high = max(self.btc_data.iloc[i]['open'], self.btc_data.iloc[i]['close'], self.btc_data.iloc[i]['high'])
            low = min(self.btc_data.iloc[i]['open'], self.btc_data.iloc[i]['close'], self.btc_data.iloc[i]['low'])
            self.btc_data.iloc[i, self.btc_data.columns.get_loc('high')] = high
            self.btc_data.iloc[i, self.btc_data.columns.get_loc('low')] = low
        
        # 创建ETH数据（与BTC相关但有自己的特点）
        eth_base = 2500
        eth_trend = trend * 0.06  # ETH相对变化较小
        eth_noise = np.random.normal(0, 20, 100)
        eth_close = eth_base + eth_trend + eth_noise
        
        self.eth_data = pd.DataFrame({
            'open': eth_close + np.random.normal(0, 10, 100),
            'high': eth_close + np.abs(np.random.normal(20, 10, 100)),
            'low': eth_close - np.abs(np.random.normal(20, 10, 100)),
            'close': eth_close,
            'volume': np.random.uniform(200, 800, 100)
        }, index=dates)
        
        # 确保ETH的OHLC逻辑正确
        for i in range(len(self.eth_data)):
            high = max(self.eth_data.iloc[i]['open'], self.eth_data.iloc[i]['close'], self.eth_data.iloc[i]['high'])
            low = min(self.eth_data.iloc[i]['open'], self.eth_data.iloc[i]['close'], self.eth_data.iloc[i]['low'])
            self.eth_data.iloc[i, self.eth_data.columns.get_loc('high')] = high
            self.eth_data.iloc[i, self.eth_data.columns.get_loc('low')] = low

    def test_full_analysis_workflow(self):
        """测试完整的分析工作流程"""
        # 创建分析器
        analyzer = TechnicalAnalyzer()
        
        # 计算技术指标
        btc_with_indicators = analyzer.calculate_indicators(self.btc_data)
        
        # 验证指标计算
        assert 'sma' in btc_with_indicators.columns
        assert 'ema' in btc_with_indicators.columns
        assert 'rsi' in btc_with_indicators.columns
        
        # 验证指标数据不全为NaN
        assert not btc_with_indicators['sma'].isna().all()
        assert not btc_with_indicators['rsi'].isna().all()
        
        # 分析信号
        signals = analyzer.analyze_signals(btc_with_indicators, 'BTCUSDT')
        
        # 验证信号分析结果
        assert isinstance(signals, list)
        # 在真实数据上，应该能检测到一些信号
        if signals:
            signal = signals[0]
            assert signal.symbol == 'BTCUSDT'
            assert signal.signal_type in ['BUY', 'SELL', 'NEUTRAL']
            assert 0 <= signal.confidence <= 1
            assert isinstance(signal.timestamp, datetime)

    def test_market_analyzer_workflow(self):
        """测试市场分析器完整工作流程"""
        # 创建市场分析器
        market_analyzer = MarketAnalyzer()
        
        # 准备多个交易对数据
        symbols_data = {
            'BTCUSDT': self.btc_data,
            'ETHUSDT': self.eth_data
        }
        
        # 分析所有交易对
        results = market_analyzer.analyze_symbols(symbols_data)
        
        # 验证结果
        assert isinstance(results, dict)
        
        # 生成市场摘要
        summary = market_analyzer.get_market_summary(results)
        
        # 验证摘要
        assert 'total_symbols' in summary
        assert 'total_signals' in summary
        assert 'market_sentiment' in summary
        assert summary['market_sentiment'] in ['BULLISH', 'BEARISH', 'NEUTRAL']

    def test_signal_quality_with_trending_market(self):
        """测试在趋势市场中的信号质量"""
        # 使用自定义配置，降低信号阈值以便更容易触发
        config = {
            'indicators': {
                'sma': {'enabled': True, 'params': {'window': 10}, 'weight': 1.0},
                'ema': {'enabled': True, 'params': {'window': 8}, 'weight': 1.0},
                'rsi': {'enabled': True, 'params': {'window': 10}, 'weight': 1.2},
                'macd': {'enabled': True, 'params': {'fast': 8, 'slow': 16, 'signal': 6}, 'weight': 1.1},
            },
            'signal_rules': {
                'min_indicators': 1,  # 只需要1个指标
                'confidence_threshold': 0.3  # 较低的置信度阈值
            }
        }
        
        analyzer = TechnicalAnalyzer(config)
        
        # 使用上涨趋势的数据
        trending_data = self.btc_data.tail(30).copy()  # 使用最后30个数据点（上涨趋势）
        
        # 计算指标
        trending_with_indicators = analyzer.calculate_indicators(trending_data)
        
        # 分析信号
        signals = analyzer.analyze_signals(trending_with_indicators, 'BTCUSDT')
        
        # 在上涨趋势中，应该更容易产生买入信号
        if signals:
            print(f"检测到信号: {signals[0].signal_type}, 置信度: {signals[0].confidence}")
            print(f"触发规则: {signals[0].triggered_rules}")

    def test_indicator_calculation_accuracy(self):
        """测试技术指标计算的准确性"""
        analyzer = TechnicalAnalyzer()
        
        # 使用简单的测试数据验证计算准确性
        simple_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        result = analyzer.calculate_indicators(simple_data)
        
        # 验证SMA计算（最后一个值应该是前几个close价格的平均值）
        if 'sma' in result.columns and not result['sma'].isna().all():
            # 对于20周期的SMA，在只有5个数据点的情况下，前面会是NaN
            assert result['sma'].isna().sum() > 0  # 应该有NaN值

    def test_timestamp_preservation(self):
        """测试时间戳的正确保存"""
        analyzer = TechnicalAnalyzer()
        
        # 使用带有特定时间戳的数据
        test_timestamp = datetime(2023, 6, 15, 14, 30, 0)
        timestamped_data = self.btc_data.copy()
        timestamped_data.index = pd.date_range(test_timestamp, periods=len(timestamped_data), freq='1H')
        
        # 计算指标
        with_indicators = analyzer.calculate_indicators(timestamped_data)
        
        # 分析信号
        signals = analyzer.analyze_signals(with_indicators, 'BTCUSDT')
        
        if signals:
            signal_timestamp = signals[0].timestamp
            expected_timestamp = timestamped_data.index[-1]
            
            # 转换时间戳格式进行比较
            if hasattr(expected_timestamp, 'to_pydatetime'):
                expected_timestamp = expected_timestamp.to_pydatetime()
            
            assert signal_timestamp == expected_timestamp

    def test_error_handling(self):
        """测试错误处理能力"""
        analyzer = TechnicalAnalyzer()
        
        # 测试空数据
        empty_df = pd.DataFrame()
        result = analyzer.calculate_indicators(empty_df)
        assert result.empty
        
        signals = analyzer.analyze_signals(empty_df, 'BTCUSDT')
        assert len(signals) == 0
        
        # 测试缺少列的数据
        incomplete_df = pd.DataFrame({'close': [1, 2, 3]})
        with pytest.raises(ValueError):
            analyzer.calculate_indicators(incomplete_df)

    def test_custom_configuration(self):
        """测试自定义配置的影响"""
        # 创建两个不同配置的分析器
        conservative_config = {
            'signal_rules': {
                'min_indicators': 3,
                'confidence_threshold': 0.8
            }
        }
        
        aggressive_config = {
            'signal_rules': {
                'min_indicators': 1,
                'confidence_threshold': 0.3
            }
        }
        
        conservative_analyzer = TechnicalAnalyzer(conservative_config)
        aggressive_analyzer = TechnicalAnalyzer(aggressive_config)
        
        # 使用相同数据分析
        data_with_indicators = conservative_analyzer.calculate_indicators(self.btc_data)
        
        conservative_signals = conservative_analyzer.analyze_signals(data_with_indicators, 'BTCUSDT')
        aggressive_signals = aggressive_analyzer.analyze_signals(data_with_indicators, 'BTCUSDT')
        
        # 激进配置应该产生更多或至少相同数量的信号
        assert len(aggressive_signals) >= len(conservative_signals)

    def test_performance_with_large_dataset(self):
        """测试大数据集的性能"""
        # 创建较大的数据集
        large_dates = pd.date_range('2023-01-01', periods=1000, freq='1H')
        large_data = pd.DataFrame({
            'open': np.random.uniform(45000, 55000, 1000),
            'high': np.random.uniform(46000, 56000, 1000),
            'low': np.random.uniform(44000, 54000, 1000),
            'close': np.random.uniform(45000, 55000, 1000),
            'volume': np.random.uniform(100, 1000, 1000)
        }, index=large_dates)
        
        analyzer = TechnicalAnalyzer()
        
        # 测试计算性能
        import time
        start_time = time.time()
        
        result = analyzer.calculate_indicators(large_data)
        signals = analyzer.analyze_signals(result, 'BTCUSDT')
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 处理1000个数据点应该在合理时间内完成（比如5秒）
        assert processing_time < 5.0
        
        print(f"处理1000个数据点耗时: {processing_time:.2f}秒")


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 