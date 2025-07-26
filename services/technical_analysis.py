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
from scipy.signal import find_peaks # Added missing import

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignal:
    """技术分析信号数据类 - 支持多种技术指标"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    price: float      # 信号产生时的价格
    message: str      # 清晰、可读的分析报告
    indicator_type: str = 'RSI'  # 指标类型：'RSI', 'FIBONACCI', 'MACD'等
    
    # RSI相关数据 (向后兼容)
    rsi_value: Optional[float] = None
    
    # 斐波那契相关数据
    fib_level: Optional[float] = None       # 斐波那契水平 (如0.618)
    fib_price: Optional[float] = None       # 对应的价格水平
    fib_type: Optional[str] = None          # 'RETRACEMENT' 或 'EXTENSION'
    trend_direction: Optional[str] = None   # 'UP' 或 'DOWN'
    
    # 通用技术数据
    confidence: float = 0.5                 # 信号置信度 (0-1)
    additional_data: Optional[Dict] = None  # 其他技术指标数据


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


class FibonacciAnalyzer:
    """
    基于斐波那契回调和扩展的技术分析器
    
    功能：
    - 识别关键高低点
    - 计算斐波那契回调水平
    - 计算斐波那契扩展水平
    - 生成支撑/阻力位信号
    """
    
    def __init__(self, 
                 lookback_period: int = 20,
                 min_price_change_pct: float = 0.05,
                 proximity_threshold_pct: float = 0.02):
        """
        初始化斐波那契分析器
        
        Args:
            lookback_period: 寻找高低点的回看周期
            min_price_change_pct: 最小价格变化百分比(用于过滤噪音)
            proximity_threshold_pct: 价格接近斐波那契水平的阈值百分比
        """
        self.lookback_period = lookback_period
        self.min_price_change_pct = min_price_change_pct
        self.proximity_threshold_pct = proximity_threshold_pct
        
        # 斐波那契关键水平
        self.FIB_RETRACEMENT_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.FIB_EXTENSION_LEVELS = [1.272, 1.618, 2.618]
    
    def analyze(self, symbol: str, ohlcv_df: pd.DataFrame) -> Optional[List[TechnicalSignal]]:
        """
        对给定的市场数据进行斐波那契分析
        
        Args:
            symbol: 交易对标识
            ohlcv_df: 包含OHLC和成交量的数据
            
        Returns:
            斐波那契信号列表，如果数据不足则返回None
        """
        try:
            # 检查数据是否充足
            if ohlcv_df.empty or len(ohlcv_df) < self.lookback_period * 2:
                logger.warning(f"{symbol}: 数据不足，需要至少{self.lookback_period * 2}条记录")
                return None
            
            current_price = float(ohlcv_df['close'].iloc[-1])
            current_time = ohlcv_df.index[-1]
            
            logger.debug(f"🔍 开始分析 {symbol} 斐波那契水平，当前价格: {current_price:.4f}")
            
            # 处理时间戳
            if hasattr(current_time, 'to_pydatetime'):
                current_time = current_time.to_pydatetime()
            elif not isinstance(current_time, datetime):
                current_time = datetime.now()
            
            # 1. 识别关键高低点
            logger.debug(f"📊 {symbol}: 开始识别关键高低点 (回看周期: {self.lookback_period})")
            swing_points = self._find_swing_points(ohlcv_df)
            
            if len(swing_points) < 2:
                logger.info(f"{symbol}: 未找到足够的摆动点进行分析 (发现{len(swing_points)}个，需要至少2个)")
                return None
            
            logger.info(f"📍 {symbol}: 识别到 {len(swing_points)} 个关键摆动点:")
            for i, point in enumerate(swing_points[-5:]):  # 显示最近的5个点
                time_str = point['time'].strftime('%m-%d %H:%M') if hasattr(point['time'], 'strftime') else str(point['time'])
                logger.info(f"  点{i+1}: {point['type'].upper()} @ {point['price']:.4f} ({time_str})")
            
            # 2. 基于识别出的趋势和关键点，进行斐波那契回调和扩展分析
            logger.debug(f"📈 {symbol}: 开始回调分析...")
            retracement_signals = self._analyze_retracements(symbol, swing_points, current_price, current_time)
            
            extension_signals = []
            if len(swing_points) >= 3:
                logger.debug(f"📈 {symbol}: 开始扩展分析...")
                extension_signals = self._analyze_extensions(symbol, swing_points, current_price, current_time)
            else:
                logger.debug(f"{symbol}: 摆动点不足(需要3个)，跳过扩展分析")

            all_signals = retracement_signals + extension_signals
            
            if all_signals:
                logger.info(f"✅ {symbol}: 斐波那契分析完成，发现 {len(retracement_signals)} 个回调信号, {len(extension_signals)} 个扩展信号")
            else:
                logger.info(f"ℹ️  {symbol}: 斐波那契分析完成，未发现有效信号")
            
            # 按置信度排序
            all_signals.sort(key=lambda s: s.confidence, reverse=True)

            return all_signals if all_signals else None
            
        except Exception as e:
            logger.error(f"{symbol}: 斐波那契分析时出错: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _find_swing_points(self, df: pd.DataFrame) -> List[Dict]:
        """
        使用 find_peaks 识别主要的摆动高点和低点
        
        Args:
            df: OHLCV数据
            
        Returns:
            包含摆动点的字典列表，按时间排序
        """
        # 参数设置
        # prominence: 波峰的突出程度，可以过滤掉小波动
        # width: 波峰的宽度
        price_range = df['high'].max() - df['low'].min()
        prominence = price_range * self.min_price_change_pct
        min_width = self.lookback_period // 2
        
        logger.debug(f"🔍 摆动点识别参数: prominence={prominence:.4f}, min_width={min_width}, 价格区间={price_range:.4f}")
        
        # 寻找高点 (swing highs)
        high_peaks_indices, high_properties = find_peaks(
            df['high'], 
            prominence=prominence, 
            width=min_width
        )
        
        # 寻找低点 (swing lows) - 通过反转序列寻找波峰
        low_peaks_indices, low_properties = find_peaks(
            -df['low'], 
            prominence=prominence, 
            width=min_width
        )

        logger.debug(f"📊 峰值检测结果: {len(high_peaks_indices)} 个高点, {len(low_peaks_indices)} 个低点")

        swing_points = []
        for i in high_peaks_indices:
            swing_points.append({
                'type': 'high',
                'price': df['high'].iloc[i],
                'time': df.index[i]
            })
            
        for i in low_peaks_indices:
            swing_points.append({
                'type': 'low',
                'price': df['low'].iloc[i],
                'time': df.index[i]
            })
        
        if not swing_points:
            # 如果未找到显著高低点，使用全局高低点作为回退方案
            logger.warning(f"⚠️  在指定参数下未找到显著的摆动高低点，使用全局高低点作为回退方案")
            min_price = df['low'].min()
            max_price = df['high'].max()
            min_time = df['low'].idxmin()
            max_time = df['high'].idxmax()

            swing_points.append({'type': 'low', 'price': min_price, 'time': min_time})
            swing_points.append({'type': 'high', 'price': max_price, 'time': max_time})
            
            logger.debug(f"  全局低点: {min_price:.4f}, 全局高点: {max_price:.4f}")

        # 按时间排序并去重
        swing_points.sort(key=lambda x: x['time'])
        
        # 去除连续相同的摆动点 (例如，连续两个高点)
        unique_swing_points = []
        if swing_points:
            unique_swing_points.append(swing_points[0])
            removed_count = 0
            for i in range(1, len(swing_points)):
                if swing_points[i]['type'] != swing_points[i-1]['type']:
                    unique_swing_points.append(swing_points[i])
                else:
                    removed_count += 1
            
            if removed_count > 0:
                logger.debug(f"🧹 去除 {removed_count} 个连续同类型的摆动点")

        logger.debug(f"✅ 最终识别到 {len(unique_swing_points)} 个有效摆动点")

        return unique_swing_points

    def _analyze_retracements(self, symbol: str, swing_points: List[Dict], 
                            current_price: float, current_time: datetime) -> List[TechnicalSignal]:
        """
        分析最新趋势的斐波那契回调水平
        """
        if len(swing_points) < 2:
            return []
        
        signals = []
        # 只分析最新的趋势，即最后两个摆动点
        last_two_points = swing_points[-2:]
        
        start_point = last_two_points[0]
        end_point = last_two_points[1]

        # 确定趋势方向
        trend_direction = "UP" if end_point['price'] > start_point['price'] else "DOWN"
        price_range = abs(end_point['price'] - start_point['price'])
        
        logger.debug(f"📊 {symbol}: 回调分析 - {trend_direction}趋势")
        logger.debug(f"  起点: {start_point['type'].upper()}({start_point['price']:.4f})")
        logger.debug(f"  终点: {end_point['type'].upper()}({end_point['price']:.4f})")
        logger.debug(f"  价格区间: {price_range:.4f} ({price_range/start_point['price']*100:.1f}%)")
        
        found_levels = []  # 记录找到的有效水平

        for level in self.FIB_RETRACEMENT_LEVELS:
            if trend_direction == "UP":
                fib_price = end_point['price'] - price_range * level
            else: # DOWN
                fib_price = end_point['price'] + price_range * level

            proximity = abs(current_price - fib_price) / current_price
            
            logger.debug(f"  {level*100:.1f}%回调位: {fib_price:.4f} (偏差: {proximity*100:.2f}%)")
            
            if proximity <= self.proximity_threshold_pct:
                signal_type = self._determine_retracement_signal(level, trend_direction, current_price, fib_price)
                
                logger.info(f"🎯 {symbol}: 价格({current_price:.4f})接近{level*100:.1f}%回调位({fib_price:.4f})")
                
                if signal_type != 'NEUTRAL':
                    confidence = self._calculate_fib_confidence(proximity, level)
                    message = self._generate_fib_message(
                        'RETRACEMENT', level, fib_price, current_price, trend_direction, signal_type
                    )
                    
                    found_levels.append(f"{level*100:.1f}%@{fib_price:.4f}")
                    
                    signals.append(TechnicalSignal(
                        symbol=symbol,
                        timestamp=current_time,
                        signal_type=signal_type,
                        price=current_price,
                        message=message,
                        indicator_type='FIBONACCI',
                        fib_level=level,
                        fib_price=fib_price,
                        fib_type='RETRACEMENT',
                        trend_direction=trend_direction,
                        confidence=confidence,
                        additional_data={'start_point': start_point, 'end_point': end_point}
                    ))
                    
                    logger.info(f"  ✅ 生成{signal_type}信号，置信度: {confidence:.1%}")
        
        if found_levels:
            logger.info(f"📈 {symbol}: 回调分析发现 {len(found_levels)} 个有效水平: {', '.join(found_levels)}")
        else:
            logger.debug(f"📈 {symbol}: 回调分析未发现接近的斐波那契水平")
        
        return signals

    def _analyze_extensions(self, symbol: str, swing_points: List[Dict],
                          current_price: float, current_time: datetime) -> List[TechnicalSignal]:
        """
        分析斐波那契扩展水平 (基于最新的ABC波浪)
        """
        if len(swing_points) < 3:
            return []
            
        signals = []
        # 分析最近的ABC模式
        point_a = swing_points[-3]
        point_b = swing_points[-2]
        point_c = swing_points[-1]

        # 确保是有效的ABC模式 (不同类型的点)
        if (point_a['type'] == point_b['type'] or point_b['type'] == point_c['type']):
            logger.debug(f"📊 {symbol}: ABC模式无效 - 相邻点类型相同")
            return []
            
        # 确定主趋势方向 (A -> B)
        trend_direction = "UP" if point_b['price'] > point_a['price'] else "DOWN"
        ab_distance = abs(point_b['price'] - point_a['price'])
        
        # C点是回调/反弹的结束点，扩展从C点开始计算
        start_for_extension_price = point_c['price']
        
        logger.debug(f"📊 {symbol}: 扩展分析 - {trend_direction}趋势 ABC波浪")
        logger.debug(f"  A点: {point_a['type'].upper()}({point_a['price']:.4f})")
        logger.debug(f"  B点: {point_b['type'].upper()}({point_b['price']:.4f})")
        logger.debug(f"  C点: {point_c['type'].upper()}({point_c['price']:.4f})")
        logger.debug(f"  AB距离: {ab_distance:.4f}")
        logger.debug(f"  扩展起点(C): {start_for_extension_price:.4f}")

        found_extensions = []  # 记录找到的有效扩展水平

        # 计算斐波那契扩展水平
        for level in self.FIB_EXTENSION_LEVELS:
            if trend_direction == "UP":
                # 主趋势向上，扩展目标在C点上方
                fib_price = start_for_extension_price + ab_distance * level
            else: # DOWN
                # 主趋势向下，扩展目标在C点下方
                fib_price = start_for_extension_price - ab_distance * level
            
            # 检查当前价格是否接近该扩展水平
            proximity = abs(current_price - fib_price) / current_price
            
            logger.debug(f"  {level*100:.1f}%扩展位: {fib_price:.4f} (偏差: {proximity*100:.2f}%)")
            
            if proximity <= self.proximity_threshold_pct:
                signal_type = self._determine_extension_signal(
                    level, trend_direction, current_price, fib_price
                )
                
                logger.info(f"🎯 {symbol}: 价格({current_price:.4f})接近{level*100:.1f}%扩展位({fib_price:.4f})")
                
                if signal_type != 'NEUTRAL':
                    confidence = self._calculate_fib_confidence(proximity, level)
                    
                    message = self._generate_fib_message(
                        'EXTENSION', level, fib_price, current_price,
                        trend_direction, signal_type
                    )
                    
                    found_extensions.append(f"{level*100:.1f}%@{fib_price:.4f}")
                    
                    signals.append(TechnicalSignal(
                        symbol=symbol,
                        timestamp=current_time,
                        signal_type=signal_type,
                        price=current_price,
                        message=message,
                        indicator_type='FIBONACCI',
                        fib_level=level,
                        fib_price=fib_price,
                        fib_type='EXTENSION',
                        trend_direction=trend_direction,
                        confidence=confidence,
                        additional_data={
                            'start_point': point_a,
                            'end_point': point_b,
                            'wave_c_point': point_c,
                        }
                    ))
                    
                    logger.info(f"  ✅ 生成{signal_type}信号，置信度: {confidence:.1%}")
        
        if found_extensions:
            logger.info(f"📈 {symbol}: 扩展分析发现 {len(found_extensions)} 个有效水平: {', '.join(found_extensions)}")
        else:
            logger.debug(f"📈 {symbol}: 扩展分析未发现接近的斐波那契水平")
        
        return signals
    
    def _determine_retracement_signal(self, fib_level: float, trend_direction: str,
                                    current_price: float, fib_price: float) -> str:
        """确定斐波那契回调信号类型"""
        # 关键回调水平通常是反转机会
        key_levels = [0.382, 0.5, 0.618]
        
        if fib_level in key_levels:
            if trend_direction == 'UP':
                # 上升趋势中的回调，在支撑位买入
                return 'BUY'
            else:
                # 下降趋势中的回调，在阻力位卖出
                return 'SELL'
        
        return 'NEUTRAL'
    
    def _determine_extension_signal(self, fib_level: float, trend_direction: str,
                                  current_price: float, fib_price: float) -> str:
        """确定斐波那契扩展信号类型"""
        # 扩展水平通常是获利目标或反转点
        if fib_level >= 1.618:  # 黄金扩展比例
            if trend_direction == 'UP':
                return 'SELL'  # 到达上方目标，考虑卖出
            else:
                return 'BUY'   # 到达下方目标，考虑买入
        
        return 'NEUTRAL'
    
    def _calculate_fib_confidence(self, proximity: float, fib_level: float) -> float:
        """
        计算斐波那契信号的置信度
        
        Args:
            proximity: 价格接近程度 (0-1)
            fib_level: 斐波那契水平
            
        Returns:
            置信度 (0-1)
        """
        # 基础置信度：越接近，置信度越高
        distance_confidence = 1 - (proximity / self.proximity_threshold_pct)
        
        # 水平重要性权重
        if fib_level in [0.382, 0.618, 1.618]:  # 黄金比例
            level_weight = 1.0
        elif fib_level in [0.5, 1.272]:  # 重要水平
            level_weight = 0.8
        else:
            level_weight = 0.6
        
        return min(1.0, distance_confidence * level_weight)
    
    def _generate_fib_message(self, fib_type: str, fib_level: float, fib_price: float,
                            current_price: float, trend_direction: str, signal_type: str) -> str:
        """生成斐波那契分析消息"""
        level_pct = fib_level * 100
        
        if fib_type == 'RETRACEMENT':
            base_msg = f"斐波那契{level_pct:.1f}%回调位({fib_price:.4f})"
            
            if signal_type == 'BUY':
                return f"{base_msg}，{trend_direction.lower()}趋势回调到关键支撑，考虑买入机会"
            elif signal_type == 'SELL':  
                return f"{base_msg}，{trend_direction.lower()}趋势回调到关键阻力，考虑卖出机会"
            else:
                return f"{base_msg}，当前价格{current_price:.4f}接近该水平"
                
        else:  # EXTENSION
            base_msg = f"斐波那契{level_pct:.1f}%扩展位({fib_price:.4f})"
            
            if signal_type == 'SELL':
                return f"{base_msg}，价格到达{trend_direction.lower()}趋势扩展目标，考虑获利了结"
            elif signal_type == 'BUY':
                return f"{base_msg}，价格到达{trend_direction.lower()}趋势扩展目标，可能出现反弹"
            else:
                return f"{base_msg}，当前价格{current_price:.4f}接近该目标位"


class MarketAnalyzer:
    """
    市场分析器 - 管理多种技术分析指标
    
    负责：
    - 批量分析多个交易对
    - 集成RSI和斐波那契分析
    - 生成综合市场概览
    - 提供统一的分析接口
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化市场分析器
        
        Args:
            config: 可选配置，包含各种技术指标参数
        """
        self.config = config or {}
        
        # 从配置中获取RSI参数
        rsi_config = self.config.get('rsi', {})
        self.rsi_analyzer = RsiAnalyzer(
            rsi_period=rsi_config.get('period', 14),
            oversold=rsi_config.get('oversold', 30),
            overbought=rsi_config.get('overbought', 70)
        )
        
        # 从配置中获取斐波那契参数
        fib_config = self.config.get('fibonacci', {})
        self.fibonacci_analyzer = FibonacciAnalyzer(
            lookback_period=fib_config.get('lookback_period', 20),
            min_price_change_pct=fib_config.get('min_price_change_pct', 0.05),
            proximity_threshold_pct=fib_config.get('proximity_threshold_pct', 0.02)
        )
        
        # 启用的分析器设置
        self.enable_rsi = True
        self.enable_fibonacci = True
    
    def analyze_market(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, List[TechnicalSignal]]:
        """
        分析市场中所有交易对的技术信号 (RSI + 斐波那契)
        
        Args:
            market_data: {symbol: DataFrame} 格式的市场数据
            
        Returns:
            {symbol: List[TechnicalSignal]} 格式的信号字典，每个交易对可能有多个信号
        """
        all_signals = {}
        
        for symbol, df in market_data.items():
            symbol_signals = []
            
            # 1. RSI分析
            if self.enable_rsi:
                try:
                    rsi_signal = self.rsi_analyzer.analyze(symbol, df)
                    if rsi_signal:
                        symbol_signals.append(rsi_signal)
                        logger.info(f"{symbol} RSI: {rsi_signal.message}")
                except Exception as e:
                    logger.error(f"{symbol} RSI分析失败: {e}")
            
            # 2. 斐波那契分析
            if self.enable_fibonacci:
                try:
                    fib_signals = self.fibonacci_analyzer.analyze(symbol, df)
                    if fib_signals:
                        symbol_signals.extend(fib_signals)
                        for fib_signal in fib_signals:
                            logger.info(f"{symbol} FIB: {fib_signal.message}")
                except Exception as e:
                    logger.error(f"{symbol} 斐波那契分析失败: {e}")
            
            # 只有有信号的交易对才添加到结果中
            if symbol_signals:
                all_signals[symbol] = symbol_signals
        
        return all_signals
    
    def get_market_summary(self, signals: Dict[str, List[TechnicalSignal]]) -> Dict[str, Any]:
        """
        生成市场摘要统计 (支持多种技术指标)
        
        Args:
            signals: 信号字典，每个交易对可能有多个信号
            
        Returns:
            市场摘要数据
        """
        if not signals:
            return {
                'total_symbols': 0,
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'neutral_signals': 0,
                'rsi_analysis': {'count': 0, 'avg_rsi': 0.0},
                'fibonacci_analysis': {'count': 0, 'retracement_count': 0, 'extension_count': 0},
                'high_confidence_signals': 0,
                'market_sentiment': 'NEUTRAL'
            }
        
        # 展开所有信号
        all_signals = []
        for symbol_signals in signals.values():
            all_signals.extend(symbol_signals)
        
        if not all_signals:
            return {
                'total_symbols': len(signals),
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'neutral_signals': 0,
                'rsi_analysis': {'count': 0, 'avg_rsi': 0.0},
                'fibonacci_analysis': {'count': 0, 'retracement_count': 0, 'extension_count': 0},
                'high_confidence_signals': 0,
                'market_sentiment': 'NEUTRAL'
            }
        
        # 统计各类信号数量
        buy_count = sum(1 for s in all_signals if s.signal_type == 'BUY')
        sell_count = sum(1 for s in all_signals if s.signal_type == 'SELL')
        neutral_count = len(all_signals) - buy_count - sell_count
        
        # RSI分析统计
        rsi_signals = [s for s in all_signals if s.indicator_type == 'RSI' and s.rsi_value is not None]
        avg_rsi = np.mean([s.rsi_value for s in rsi_signals]) if rsi_signals else 0.0
        
        # 斐波那契分析统计
        fib_signals = [s for s in all_signals if s.indicator_type == 'FIBONACCI']
        fib_retracement_count = sum(1 for s in fib_signals if s.fib_type == 'RETRACEMENT')
        fib_extension_count = sum(1 for s in fib_signals if s.fib_type == 'EXTENSION')
        
        # 高置信度信号统计
        high_confidence_count = sum(1 for s in all_signals if s.confidence >= 0.7)
        
        # 判断市场情绪（基于高置信度信号）
        high_conf_buy = sum(1 for s in all_signals if s.signal_type == 'BUY' and s.confidence >= 0.6)
        high_conf_sell = sum(1 for s in all_signals if s.signal_type == 'SELL' and s.confidence >= 0.6)
        
        if high_conf_buy > high_conf_sell * 1.5:
            market_sentiment = 'BULLISH'  # 偏多
        elif high_conf_sell > high_conf_buy * 1.5:
            market_sentiment = 'BEARISH'  # 偏空
        else:
            market_sentiment = 'NEUTRAL'  # 中性
        
        return {
            'total_symbols': len(signals),
            'total_signals': len(all_signals),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'neutral_signals': neutral_count,
            'rsi_analysis': {
                'count': len(rsi_signals),
                'avg_rsi': float(avg_rsi) if not np.isnan(avg_rsi) else 0.0
            },
            'fibonacci_analysis': {
                'count': len(fib_signals),
                'retracement_count': fib_retracement_count,
                'extension_count': fib_extension_count
            },
            'high_confidence_signals': high_confidence_count,
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