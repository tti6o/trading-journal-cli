"""
技术分析服务模块

提供各种技术指标计算和信号识别功能。
支持多种技术指标：MA, EMA, RSI, MACD, 布林带等。
"""

import logging
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignal:
    """技术分析信号数据类"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float  # 0-1 置信度
    indicators: Dict[str, Any]  # 指标数值
    triggered_rules: List[str]  # 触发的规则
    price: float
    message: str


@dataclass
class IndicatorConfig:
    """指标配置数据类"""
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # 权重


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化技术分析器
        
        Args:
            config: 分析器配置
        """
        self.config = config or self._get_default_config()
        self.indicators_config = self.config.get('indicators', {})
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'indicators': {
                'sma': {'enabled': True, 'params': {'window': 20}, 'weight': 1.0},
                'ema': {'enabled': True, 'params': {'window': 12}, 'weight': 1.0},
                'rsi': {'enabled': True, 'params': {'window': 14}, 'weight': 1.2},
                'macd': {'enabled': True, 'params': {'fast': 12, 'slow': 26, 'signal': 9}, 'weight': 1.1},
                'bollinger': {'enabled': True, 'params': {'window': 20, 'std': 2}, 'weight': 1.0},
                'volume_sma': {'enabled': True, 'params': {'window': 20}, 'weight': 0.8},
                'stoch': {'enabled': True, 'params': {'k': 14, 'd': 3}, 'weight': 1.0}
            },
            'signal_rules': {
                'min_indicators': 3,  # 至少满足3个指标
                'confidence_threshold': 0.6  # 置信度阈值
            }
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有启用的技术指标
        
        Args:
            df: K线数据DataFrame，包含 [timestamp, open, high, low, close, volume]
            
        Returns:
            带有技术指标的DataFrame
        """
        if df.empty:
            return df
            
        # 确保数据格式正确
        df = df.copy()
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrame缺少必需的列: {col}")
        
        # 计算各种技术指标
        indicators = {}
        
        # 移动平均线
        if self.indicators_config.get('sma', {}).get('enabled', False):
            window = self.indicators_config['sma']['params']['window']
            indicators['sma'] = ta.sma(df['close'], length=window)
        
        if self.indicators_config.get('ema', {}).get('enabled', False):
            window = self.indicators_config['ema']['params']['window']
            indicators['ema'] = ta.ema(df['close'], length=window)
        
        # RSI
        if self.indicators_config.get('rsi', {}).get('enabled', False):
            window = self.indicators_config['rsi']['params']['window']
            indicators['rsi'] = ta.rsi(df['close'], length=window)
        
        # MACD
        if self.indicators_config.get('macd', {}).get('enabled', False):
            params = self.indicators_config['macd']['params']
            macd_result = ta.macd(df['close'], 
                                fast=params['fast'], 
                                slow=params['slow'], 
                                signal=params['signal'])
            if macd_result is not None:
                indicators['macd'] = macd_result.iloc[:, 0]  # MACD线
                indicators['macd_signal'] = macd_result.iloc[:, 1]  # 信号线
                indicators['macd_histogram'] = macd_result.iloc[:, 2]  # 柱状图
        
        # 布林带
        if self.indicators_config.get('bollinger', {}).get('enabled', False):
            params = self.indicators_config['bollinger']['params']
            bb_result = ta.bbands(df['close'], 
                                length=params['window'], 
                                std=params['std'])
            if bb_result is not None:
                indicators['bb_upper'] = bb_result.iloc[:, 0]  # 上轨
                indicators['bb_middle'] = bb_result.iloc[:, 1]  # 中轨
                indicators['bb_lower'] = bb_result.iloc[:, 2]  # 下轨
        
        # 成交量移动平均
        if self.indicators_config.get('volume_sma', {}).get('enabled', False):
            window = self.indicators_config['volume_sma']['params']['window']
            indicators['volume_sma'] = ta.sma(df['volume'], length=window)
        
        # 随机指标
        if self.indicators_config.get('stoch', {}).get('enabled', False):
            params = self.indicators_config['stoch']['params']
            stoch_result = ta.stoch(df['high'], df['low'], df['close'], 
                                  k=params['k'], d=params['d'])
            if stoch_result is not None:
                indicators['stoch_k'] = stoch_result.iloc[:, 0]  # %K
                indicators['stoch_d'] = stoch_result.iloc[:, 1]  # %D
        
        # 将指标添加到DataFrame
        for name, values in indicators.items():
            df[name] = values
            
        return df
    
    def analyze_signals(self, df: pd.DataFrame, symbol: str) -> List[TechnicalSignal]:
        """
        分析技术信号
        
        Args:
            df: 带有技术指标的DataFrame
            symbol: 交易对符号
            
        Returns:
            技术信号列表
        """
        signals = []
        
        if df.empty or len(df) < 2:
            return signals
        
        # 获取最新和前一个数据点
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # 分析每个时间点的信号
        signal_analysis = self._analyze_current_signals(current, previous, symbol)
        
        if signal_analysis:
            signals.append(signal_analysis)
            
        return signals
    
    def _analyze_current_signals(self, current: pd.Series, previous: pd.Series, symbol: str) -> Optional[TechnicalSignal]:
        """
        分析当前时间点的信号
        
        Args:
            current: 当前数据点
            previous: 前一个数据点
            symbol: 交易对符号
            
        Returns:
            技术信号或None
        """
        buy_signals = []
        sell_signals = []
        indicators_values = {}
        
        # 移动平均线信号
        if 'sma' in current and 'ema' in current:
            if not pd.isna(current['sma']) and not pd.isna(current['ema']):
                indicators_values['sma'] = current['sma']
                indicators_values['ema'] = current['ema']
                
                # 价格突破移动平均线
                if current['close'] > current['sma'] and previous['close'] <= previous['sma']:
                    buy_signals.append('价格突破SMA')
                elif current['close'] < current['sma'] and previous['close'] >= previous['sma']:
                    sell_signals.append('价格跌破SMA')
                
                # EMA与SMA交叉
                if current['ema'] > current['sma'] and previous['ema'] <= previous['sma']:
                    buy_signals.append('EMA上穿SMA')
                elif current['ema'] < current['sma'] and previous['ema'] >= previous['sma']:
                    sell_signals.append('EMA下穿SMA')
        
        # RSI信号
        if 'rsi' in current and not pd.isna(current['rsi']):
            indicators_values['rsi'] = current['rsi']
            
            if current['rsi'] < 30:
                buy_signals.append('RSI超卖')
            elif current['rsi'] > 70:
                sell_signals.append('RSI超买')
        
        # MACD信号
        if 'macd' in current and 'macd_signal' in current:
            if not pd.isna(current['macd']) and not pd.isna(current['macd_signal']):
                indicators_values['macd'] = current['macd']
                indicators_values['macd_signal'] = current['macd_signal']
                
                # MACD金叉死叉
                if current['macd'] > current['macd_signal'] and previous['macd'] <= previous['macd_signal']:
                    buy_signals.append('MACD金叉')
                elif current['macd'] < current['macd_signal'] and previous['macd'] >= previous['macd_signal']:
                    sell_signals.append('MACD死叉')
        
        # 布林带信号
        if 'bb_upper' in current and 'bb_lower' in current:
            if not pd.isna(current['bb_upper']) and not pd.isna(current['bb_lower']):
                indicators_values['bb_upper'] = current['bb_upper']
                indicators_values['bb_lower'] = current['bb_lower']
                
                # 价格触碰布林带
                if current['close'] <= current['bb_lower']:
                    buy_signals.append('价格触及布林带下轨')
                elif current['close'] >= current['bb_upper']:
                    sell_signals.append('价格触及布林带上轨')
        
        # 随机指标信号
        if 'stoch_k' in current and 'stoch_d' in current:
            if not pd.isna(current['stoch_k']) and not pd.isna(current['stoch_d']):
                indicators_values['stoch_k'] = current['stoch_k']
                indicators_values['stoch_d'] = current['stoch_d']
                
                # 随机指标超买超卖
                if current['stoch_k'] < 20 and current['stoch_d'] < 20:
                    buy_signals.append('随机指标超卖')
                elif current['stoch_k'] > 80 and current['stoch_d'] > 80:
                    sell_signals.append('随机指标超买')
        
        # 成交量信号
        if 'volume_sma' in current and not pd.isna(current['volume_sma']):
            indicators_values['volume_sma'] = current['volume_sma']
            
            if current['volume'] > current['volume_sma'] * 1.5:
                if buy_signals:
                    buy_signals.append('成交量放大')
                if sell_signals:
                    sell_signals.append('成交量放大')
        
        # 确定最终信号
        min_indicators = self.config['signal_rules']['min_indicators']
        confidence_threshold = self.config['signal_rules']['confidence_threshold']
        
        signal_type = 'NEUTRAL'
        confidence = 0.0
        triggered_rules = []
        message = ''
        
        if len(buy_signals) >= min_indicators:
            signal_type = 'BUY'
            triggered_rules = buy_signals
            confidence = min(1.0, len(buy_signals) / 5.0)  # 最多5个信号
            message = f'买入信号: {", ".join(buy_signals)}'
        elif len(sell_signals) >= min_indicators:
            signal_type = 'SELL'
            triggered_rules = sell_signals
            confidence = min(1.0, len(sell_signals) / 5.0)
            message = f'卖出信号: {", ".join(sell_signals)}'
        
        # 只返回置信度高于阈值的信号
        if confidence >= confidence_threshold:
            return TechnicalSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal_type=signal_type,
                confidence=confidence,
                indicators=indicators_values,
                triggered_rules=triggered_rules,
                price=current['close'],
                message=message
            )
        
        return None


class MarketAnalyzer:
    """市场分析器 - 管理多个交易对的技术分析"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化市场分析器
        
        Args:
            config: 分析器配置
        """
        self.config = config or {}
        self.analyzer = TechnicalAnalyzer(config)
        
    def analyze_symbols(self, symbols_data: Dict[str, pd.DataFrame]) -> Dict[str, List[TechnicalSignal]]:
        """
        分析多个交易对的技术信号
        
        Args:
            symbols_data: 交易对数据字典 {symbol: DataFrame}
            
        Returns:
            信号字典 {symbol: [signals]}
        """
        results = {}
        
        for symbol, df in symbols_data.items():
            try:
                # 计算技术指标
                df_with_indicators = self.analyzer.calculate_indicators(df)
                
                # 分析信号
                signals = self.analyzer.analyze_signals(df_with_indicators, symbol)
                
                if signals:
                    results[symbol] = signals
                    logger.info(f"分析 {symbol} 完成，发现 {len(signals)} 个信号")
                
            except Exception as e:
                logger.error(f"分析 {symbol} 时发生错误: {e}")
                continue
        
        return results
    
    def get_market_summary(self, signals_data: Dict[str, List[TechnicalSignal]]) -> Dict[str, Any]:
        """
        生成市场分析摘要
        
        Args:
            signals_data: 信号数据字典
            
        Returns:
            市场摘要字典
        """
        total_signals = 0
        buy_signals = 0
        sell_signals = 0
        high_confidence_signals = 0
        
        for symbol, signals in signals_data.items():
            for signal in signals:
                total_signals += 1
                if signal.signal_type == 'BUY':
                    buy_signals += 1
                elif signal.signal_type == 'SELL':
                    sell_signals += 1
                    
                if signal.confidence >= 0.8:
                    high_confidence_signals += 1
        
        return {
            'total_symbols': len(signals_data),
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'high_confidence_signals': high_confidence_signals,
            'market_sentiment': 'BULLISH' if buy_signals > sell_signals else 'BEARISH' if sell_signals > buy_signals else 'NEUTRAL'
        }