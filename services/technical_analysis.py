"""
RSI技术分析服务模块 (MVP版本)

专注于RSI指标的技术分析，提供清晰、简洁的信号识别功能。
设计理念：简单、高效、易于扩展。
"""

import logging
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignal:
    """技术分析信号数据类 (简化版)"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    price: float      # 信号产生时的价格
    rsi_value: float  # RSI指标值
    message: str      # 清晰、可读的分析报告


class RsiAnalyzer:
    """
    基于RSI指标的技术分析器 (MVP核心组件)
    
    功能：
    - 计算RSI指标
    - 识别超买/超卖信号
    - 生成清晰的分析报告
    """
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        初始化RSI分析器
        
        Args:
            rsi_period: RSI计算周期，默认14
            oversold: 超卖阈值，默认30
            overbought: 超买阈值，默认70
        """
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
    
    def analyze(self, symbol: str, ohlcv_df: pd.DataFrame) -> Optional[TechnicalSignal]:
        """
        对给定的市场数据进行RSI分析
        
        Args:
            symbol: 交易对标识
            ohlcv_df: 包含'close'价格的OHLCV数据
            
        Returns:
            TechnicalSignal: 分析结果，如果数据不足则返回None
        """
        try:
            # 1. 检查数据是否充足
            if ohlcv_df.empty or len(ohlcv_df) < self.rsi_period + 10:
                logger.warning(f"{symbol}: 数据不足，需要至少{self.rsi_period + 10}条记录")
                return None
            
            # 2. 计算RSI指标
            rsi_series = ta.rsi(ohlcv_df['close'], length=self.rsi_period)
            
            if rsi_series.isna().all():
                logger.warning(f"{symbol}: RSI计算失败")
                return None
            
            # 3. 获取最新的RSI值和价格
            latest_rsi = rsi_series.iloc[-1]
            latest_price = ohlcv_df['close'].iloc[-1]
            latest_time = ohlcv_df.index[-1] if hasattr(ohlcv_df.index[-1], 'to_pydatetime') else datetime.now()
            
            # 处理时间戳
            if hasattr(latest_time, 'to_pydatetime'):
                latest_time = latest_time.to_pydatetime()
            elif not isinstance(latest_time, datetime):
                latest_time = datetime.now()
            
            # 4. 判断信号类型和生成消息
            signal_type, message = self._evaluate_rsi_signal(latest_rsi)
            
            return TechnicalSignal(
                symbol=symbol,
                timestamp=latest_time,
                signal_type=signal_type,
                price=float(latest_price),
                rsi_value=float(latest_rsi),
                message=message
            )
            
        except Exception as e:
            logger.error(f"{symbol}: RSI分析时出错: {e}")
            return None
    
    def _evaluate_rsi_signal(self, rsi_value: float) -> tuple[str, str]:
        """
        根据RSI值评估交易信号
        
        Args:
            rsi_value: 当前RSI值
            
        Returns:
            tuple: (信号类型, 描述消息)
        """
        if np.isnan(rsi_value):
            return 'NEUTRAL', "RSI数据无效"
        
        if rsi_value <= self.oversold:
            return 'BUY', f"RSI({self.rsi_period})为{rsi_value:.1f}，进入超卖区域(<={self.oversold})，可能出现反弹机会"
        elif rsi_value >= self.overbought:
            return 'SELL', f"RSI({self.rsi_period})为{rsi_value:.1f}，进入超买区域(>={self.overbought})，可能出现回调风险"
        else:
            # 进一步细分中性区域
            if rsi_value < 40:
                return 'NEUTRAL', f"RSI({self.rsi_period})为{rsi_value:.1f}，偏向弱势，关注是否跌破{self.oversold}"
            elif rsi_value > 60:
                return 'NEUTRAL', f"RSI({self.rsi_period})为{rsi_value:.1f}，偏向强势，关注是否突破{self.overbought}"
            else:
                return 'NEUTRAL', f"RSI({self.rsi_period})为{rsi_value:.1f}，处于中性区域，无明确信号"


class MarketAnalyzer:
    """
    市场分析器 - 管理多个交易对的RSI分析
    
    负责：
    - 批量分析多个交易对
    - 生成市场概览
    - 提供统一的分析接口
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化市场分析器
        
        Args:
            config: 可选配置，包含RSI参数
        """
        self.config = config or {}
        
        # 从配置中获取RSI参数
        rsi_config = self.config.get('rsi', {})
        self.rsi_analyzer = RsiAnalyzer(
            rsi_period=rsi_config.get('period', 14),
            oversold=rsi_config.get('oversold', 30),
            overbought=rsi_config.get('overbought', 70)
        )
    
    def analyze_market(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, TechnicalSignal]:
        """
        分析市场中所有交易对的RSI信号
        
        Args:
            market_data: {symbol: DataFrame} 格式的市场数据
            
        Returns:
            {symbol: TechnicalSignal} 格式的信号字典
        """
        signals = {}
        
        for symbol, df in market_data.items():
            signal = self.rsi_analyzer.analyze(symbol, df)
            if signal:
                signals[symbol] = signal
                logger.info(f"{symbol}: {signal.message}")
        
        return signals
    
    def get_market_summary(self, signals: Dict[str, TechnicalSignal]) -> Dict[str, Any]:
        """
        生成市场摘要统计
        
        Args:
            signals: 信号字典
            
        Returns:
            市场摘要数据
        """
        if not signals:
            return {
                'total_symbols': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'neutral_signals': 0,
                'avg_rsi': 0.0,
                'extreme_signals': [],  # 极端信号列表
                'market_sentiment': 'NEUTRAL'
            }
        
        # 统计各类信号数量
        buy_count = sum(1 for s in signals.values() if s.signal_type == 'BUY')
        sell_count = sum(1 for s in signals.values() if s.signal_type == 'SELL')
        neutral_count = len(signals) - buy_count - sell_count
        
        # 计算平均RSI
        avg_rsi = np.mean([s.rsi_value for s in signals.values()])
        
        # 找出极端信号（RSI < 25 或 RSI > 75）
        extreme_signals = [
            s for s in signals.values() 
            if s.rsi_value <= 25 or s.rsi_value >= 75
        ]
        
        # 判断市场情绪
        if buy_count > sell_count * 1.5:
            market_sentiment = 'BULLISH'  # 偏多
        elif sell_count > buy_count * 1.5:
            market_sentiment = 'BEARISH'  # 偏空
        else:
            market_sentiment = 'NEUTRAL'  # 中性
        
        return {
            'total_symbols': len(signals),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'neutral_signals': neutral_count,
            'avg_rsi': float(avg_rsi),
            'extreme_signals': extreme_signals,
            'market_sentiment': market_sentiment
        }


# 便捷函数 - 对外提供的简单接口
def analyze_symbol_rsi(symbol: str, df: pd.DataFrame, config: Optional[Dict] = None) -> Optional[TechnicalSignal]:
    """
    分析单个交易对的RSI信号 (便捷函数)
    
    Args:
        symbol: 交易对符号
        df: OHLCV数据
        config: 可选配置
        
    Returns:
        技术信号或None
    """
    # 从配置中获取RSI参数
    if config and 'rsi' in config:
        rsi_config = config['rsi']
        analyzer = RsiAnalyzer(
            rsi_period=rsi_config.get('period', 14),
            oversold=rsi_config.get('oversold', 30),
            overbought=rsi_config.get('overbought', 70)
        )
    else:
        analyzer = RsiAnalyzer()  # 使用默认参数
    
    return analyzer.analyze(symbol, df)


def analyze_market_rsi(market_data: Dict[str, pd.DataFrame], config: Optional[Dict] = None) -> Dict[str, TechnicalSignal]:
    """
    分析整个市场的RSI信号 (便捷函数)
    
    Args:
        market_data: {symbol: DataFrame} 格式的市场数据
        config: 可选配置
        
    Returns:
        {symbol: TechnicalSignal} 格式的信号字典
    """
    market_analyzer = MarketAnalyzer(config)
    return market_analyzer.analyze_market(market_data)


# 为了保持向后兼容，保留原有的函数名
def analyze_symbol(symbol: str, df: pd.DataFrame, config: Optional[Dict] = None) -> Optional[TechnicalSignal]:
    """向后兼容的函数名"""
    return analyze_symbol_rsi(symbol, df, config)


def analyze_market(market_data: Dict[str, pd.DataFrame], config: Optional[Dict] = None) -> Dict[str, TechnicalSignal]:
    """向后兼容的函数名"""
    return analyze_market_rsi(market_data, config)