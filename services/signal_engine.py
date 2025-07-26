"""
信号引擎模块

集成技术分析和通知服务，提供完整的信号检测和推送功能。
负责管理监控的交易对、执行分析任务、发送通知等。
"""

import logging
import configparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import pandas as pd

from .technical_analysis import MarketAnalyzer, TechnicalSignal, analyze_market
from .notification import get_notification_service
from exchange_client.factory import ExchangeClientFactory
from core.database import get_historical_symbols

logger = logging.getLogger(__name__)


class SignalEngine:
    """信号引擎 - 技术分析信号检测和通知的核心组件"""
    
    def __init__(self, config_file: str = 'config/config.ini'):
        """
        初始化信号引擎
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = {}
        self.market_analyzer = None
        self.notification_service = None
        self.exchange_client = None
        self.enabled = False
        self.monitored_symbols = set()
        self.notification_recipients = []
        
        # 加载配置
        self._load_config()
        
        # 初始化组件
        if self.enabled:
            self._initialize_components()
    
    def _load_config(self) -> None:
        """从配置文件加载信号引擎设置"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            # 技术分析配置
            if config.has_section('technical_analysis'):
                self.enabled = config.getboolean('technical_analysis', 'enabled', fallback=False)
                
                # 监控的交易对
                symbols_str = config.get('technical_analysis', 'monitored_symbols', fallback='')
                if symbols_str:
                    self.monitored_symbols = set(symbol.strip() for symbol in symbols_str.split(','))
                
                # 通知收件人 - 从email段读取
                recipients_str = ''
                if config.has_section('email'):
                    recipients_str = config.get('email', 'notification_recipients', fallback='')
                if not recipients_str and config.has_option('technical_analysis', 'notification_recipients'):
                    # 向后兼容：如果email段没有，尝试从technical_analysis段读取
                    recipients_str = config.get('technical_analysis', 'notification_recipients', fallback='')
                
                if recipients_str:
                    self.notification_recipients = [email.strip() for email in recipients_str.split(',')]
                
                # 技术分析参数
                self.config = {
                    'kline_interval': config.get('technical_analysis', 'kline_interval', fallback='1h'),
                    'kline_limit': config.getint('technical_analysis', 'kline_limit', fallback=200),
                    'analysis_enabled': config.getboolean('technical_analysis', 'analysis_enabled', fallback=True),
                    'auto_detect_symbols': config.getboolean('technical_analysis', 'auto_detect_symbols', fallback=True),
                    'confidence_threshold': config.getfloat('technical_analysis', 'confidence_threshold', fallback=0.5),
                    'indicators': self._parse_indicators_config(config)
                }
                
                logger.info(f"信号引擎配置已加载: enabled={self.enabled}, "
                           f"monitored_symbols={len(self.monitored_symbols)}, "
                           f"recipients={len(self.notification_recipients)}")
            else:
                logger.warning("配置文件中未找到技术分析配置段")
                
        except Exception as e:
            logger.error(f"加载信号引擎配置失败: {e}")
            self.enabled = False
    
    def _parse_indicators_config(self, config: configparser.ConfigParser) -> Dict[str, Any]:
        """解析技术指标配置，适配新的技术分析模块"""
        # 使用新的技术分析模块配置格式
        indicators_config = {
            'SMA_10': {'enabled': True, 'params': {'length': 10}},
            'SMA_20': {'enabled': True, 'params': {'length': 20}},
            'SMA_50': {'enabled': True, 'params': {'length': 50}},
            'EMA_12': {'enabled': True, 'params': {'length': 12}},
            'EMA_26': {'enabled': True, 'params': {'length': 26}},
            'RSI_14': {'enabled': True, 'params': {'length': 14}},
            'MACD': {'enabled': True, 'params': {'fast': 12, 'slow': 26, 'signal': 9}},
            'BBANDS_20': {'enabled': True, 'params': {'length': 20, 'std': 2.0}},
            'volume_SMA_20': {'enabled': True, 'params': {'length': 20}},
        }
        
        signal_rules_config = {
            'ma_cross': {'enabled': True, 'weight': 1.0},
            'rsi_reversal': {'enabled': True, 'weight': 0.8},
            'macd_cross': {'enabled': True, 'weight': 0.9},
            'bollinger_bands': {'enabled': True, 'weight': 0.7},
            'volume_confirmation': {'enabled': True, 'weight': 0.5},
        }
        
        # 从配置文件读取具体的指标设置
        try:
            if config.has_section('indicators'):
                for indicator in indicators_config:
                    if config.has_option('indicators', f'{indicator}_enabled'):
                        indicators_config[indicator]['enabled'] = config.getboolean('indicators', f'{indicator}_enabled')
                        
            if config.has_section('signal_rules'):
                for rule in signal_rules_config:
                    if config.has_option('signal_rules', f'{rule}_enabled'):
                        signal_rules_config[rule]['enabled'] = config.getboolean('signal_rules', f'{rule}_enabled')
                    if config.has_option('signal_rules', f'{rule}_weight'):
                        signal_rules_config[rule]['weight'] = config.getfloat('signal_rules', f'{rule}_weight')
                        
        except Exception as e:
            logger.warning(f"解析指标配置失败，使用默认配置: {e}")
        
        return {
            'indicators': indicators_config,
            'signal_rules': signal_rules_config
        }
    
    def _initialize_components(self) -> None:
        """初始化各个组件"""
        try:
            # 初始化市场分析器
            self.market_analyzer = MarketAnalyzer(self.config)
            
            # 获取通知服务
            self.notification_service = get_notification_service()
            
            # 获取交易所客户端
            try:
                self.exchange_client = ExchangeClientFactory.create_from_config('config/config.ini')
            except Exception as e:
                logger.warning(f"初始化交易所客户端失败: {e}")
                self.exchange_client = None
            
            # 如果启用自动检测，补充历史交易对
            if self.config.get('auto_detect_symbols', False):
                self._auto_detect_symbols()
            
            logger.info("信号引擎组件初始化完成")
            
        except Exception as e:
            logger.error(f"初始化信号引擎组件失败: {e}")
            self.enabled = False
    
    def _auto_detect_symbols(self) -> None:
        """自动检测需要监控的交易对"""
        try:
            # 从数据库获取历史交易对
            historical_symbols = get_historical_symbols()
            
            # 获取当前活跃的交易对
            if self.exchange_client:
                try:
                    active_symbols = self.exchange_client.get_active_symbols()
                    historical_symbols.extend(active_symbols)
                except Exception as e:
                    logger.warning(f"获取活跃交易对失败: {e}")
            
            # 合并到监控列表
            auto_detected = set(historical_symbols)
            original_count = len(self.monitored_symbols)
            self.monitored_symbols.update(auto_detected)
            
            logger.info(f"自动检测到 {len(auto_detected)} 个交易对，"
                       f"监控列表从 {original_count} 个增加到 {len(self.monitored_symbols)} 个")
            
        except Exception as e:
            logger.error(f"自动检测交易对失败: {e}")
    
    def run_analysis(self, send_notification: bool = True) -> Dict[str, Any]:
        """
        运行完整的技术分析流程 (集成RSI和斐波那契分析)

        Args:
            send_notification: 是否发送邮件通知，默认为 True

        Returns:
            分析结果字典
        """
        logger.info("🚀 开始执行完整技术分析 (RSI + 斐波那契)...")

        if not self.enabled:
            return {'success': False, 'error': '信号引擎未启用'}
        
        if not self.monitored_symbols:
            return {'success': False, 'error': '没有配置监控的交易对'}
        
        try:
            logger.info(f"开始执行技术分析，监控 {len(self.monitored_symbols)} 个交易对")
            
            # 获取K线数据
            symbols_data = self._fetch_klines_data()
            
            if not symbols_data:
                return {'success': False, 'error': '未获取到K线数据'}
            
            logger.info(f"📊 成功获取 {len(symbols_data)} 个交易对的K线数据，开始斐波那契和RSI分析...")
            
            # 执行完整的技术分析 (RSI + 斐波那契)
            signals_result = self.market_analyzer.analyze_market(symbols_data)
            
            # 详细记录斐波那契分析结果
            self._log_fibonacci_analysis_details(signals_result, symbols_data)
            
            # 生成市场摘要
            market_summary = self.market_analyzer.get_market_summary(signals_result)
            
            # 展开所有信号并过滤非中性信号
            all_signals = []
            all_signals_detail = {}
            
            for symbol, symbol_signals in signals_result.items():
                # 过滤非中性信号用于通知
                non_neutral_signals = [s for s in symbol_signals if s.signal_type != 'NEUTRAL']
                
                if non_neutral_signals:
                    all_signals.extend(non_neutral_signals)
                    all_signals_detail[symbol] = non_neutral_signals
            
            # 生成技术分析图表 (如果有信号)
            chart_paths = []
            if all_signals:
                chart_paths = self._generate_analysis_charts(symbols_data, signals_result)
                
            # 发送通知 (如果找到信号且需要发送)
            notification_sent = False
            
            if send_notification and all_signals and self.notification_service.enabled:
                if not self.notification_recipients:
                    logger.warning("未配置收件人邮箱，无法发送通知")
                else:
                    logger.info(f"发现 {len(all_signals)} 个信号，准备发送通知给: {self.notification_recipients}")
                    
                    # 为每个收件人发送邮件
                    for recipient in self.notification_recipients:
                        if recipient:
                            success = self.notification_service.send_signal_notification_with_charts(
                                signals=all_signals,
                                recipient=recipient,
                                chart_paths=chart_paths,
                                market_summary=market_summary
                            )
                            if success:
                                notification_sent = True
            elif not send_notification:
                logger.info("分析完成，但设置为不发送通知")
            elif not all_signals:
                logger.info("分析完成，未发现需要通知的信号 (BUY/SELL)")
            elif not self.notification_service.enabled:
                logger.info("发现信号，但邮件通知服务未启用")

            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'analyzed_symbols': len(symbols_data),
                'signals_found': len(all_signals),
                'total_signals': sum(len(signals) for signals in signals_result.values()),
                'market_summary': market_summary,
                'notification_sent': notification_sent,
                'signals_detail': all_signals_detail,
                'chart_paths': chart_paths
            }
            
            logger.info(f"✅ 技术分析完成: 分析了 {result['analyzed_symbols']} 个交易对，"
                       f"发现 {len(all_signals_detail)} 个有信号的交易对，其中 {result['signals_found']} 个为非中性信号")
            
            return result
            
        except Exception as e:
            logger.error(f"执行技术分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def _log_fibonacci_analysis_details(self, signals_result: Dict[str, List], symbols_data: Dict[str, pd.DataFrame]) -> None:
        """
        详细记录斐波那契分析过程和结果
        
        Args:
            signals_result: 分析信号结果
            symbols_data: K线数据
        """
        logger.info("📈 ===== 斐波那契分析详细报告 =====")
        
        fib_signal_count = 0
        rsi_signal_count = 0
        
        for symbol, symbol_signals in signals_result.items():
            if not symbol_signals:
                continue
                
            # 分离RSI和斐波那契信号
            rsi_signals = [s for s in symbol_signals if s.indicator_type == 'RSI']
            fib_signals = [s for s in symbol_signals if s.indicator_type == 'FIBONACCI']
            
            rsi_signal_count += len(rsi_signals)
            fib_signal_count += len(fib_signals)
            
            if fib_signals or rsi_signals:
                current_price = symbols_data[symbol]['close'].iloc[-1] if symbol in symbols_data else 0
                logger.info(f"🔍 {symbol} (当前价格: {current_price:.4f}) - 发现 {len(fib_signals)} 个斐波那契信号, {len(rsi_signals)} 个RSI信号")
                
                # 详细记录RSI信号
                for rsi_signal in rsi_signals:
                    logger.info(f"  📊 RSI信号: {rsi_signal.signal_type} | RSI值: {rsi_signal.rsi_value:.1f} | {rsi_signal.message}")
                
                # 详细记录斐波那契信号
                for fib_signal in fib_signals:
                    self._log_single_fibonacci_signal(symbol, fib_signal, current_price)
                
                # 如果有斐波那契信号，尝试获取更多分析详情
                if fib_signals and symbol in symbols_data:
                    self._log_fibonacci_analysis_context(symbol, symbols_data[symbol])
        
        # 总结统计
        logger.info(f"📊 斐波那契分析总结: 共发现 {fib_signal_count} 个斐波那契信号, {rsi_signal_count} 个RSI信号")
        if fib_signal_count > 0:
            # 统计信号类型分布
            retracement_count = sum(1 for symbol_signals in signals_result.values() 
                                  for s in symbol_signals 
                                  if s.indicator_type == 'FIBONACCI' and s.fib_type == 'RETRACEMENT')
            extension_count = sum(1 for symbol_signals in signals_result.values() 
                                for s in symbol_signals 
                                if s.indicator_type == 'FIBONACCI' and s.fib_type == 'EXTENSION')
            
            logger.info(f"  📈 回调信号: {retracement_count} 个, 扩展信号: {extension_count} 个")
        
        logger.info("=====================================")
    
    def _log_single_fibonacci_signal(self, symbol: str, fib_signal, current_price: float) -> None:
        """
        记录单个斐波那契信号的详细信息
        
        Args:
            symbol: 交易对符号
            fib_signal: 斐波那契信号对象
            current_price: 当前价格
        """
        fib_level_pct = fib_signal.fib_level * 100 if fib_signal.fib_level else 0
        price_diff = abs(current_price - fib_signal.fib_price) if fib_signal.fib_price else 0
        price_diff_pct = (price_diff / current_price * 100) if current_price > 0 else 0
        
        # 根据信号类型选择合适的图标
        signal_icon = "🟢" if fib_signal.signal_type == "BUY" else "🔴" if fib_signal.signal_type == "SELL" else "⚪"
        
        logger.info(f"  {signal_icon} 斐波那契{fib_signal.fib_type}信号:")
        logger.info(f"    📍 {fib_level_pct:.1f}%水平 @ {fib_signal.fib_price:.4f} ({fib_signal.trend_direction}趋势)")
        logger.info(f"    📏 价格偏差: {price_diff:.4f} ({price_diff_pct:.2f}%)")
        logger.info(f"    🎯 置信度: {fib_signal.confidence:.1%}")
        logger.info(f"    💬 {fib_signal.message}")
        
        # 如果有额外数据，显示关键点位信息
        if fib_signal.additional_data:
            additional_data = fib_signal.additional_data
            if 'start_point' in additional_data and 'end_point' in additional_data:
                start_point = additional_data['start_point']
                end_point = additional_data['end_point']
                logger.info(f"    📊 关键点位: {start_point['type'].upper()}({start_point['price']:.4f}) → {end_point['type'].upper()}({end_point['price']:.4f})")
                
                # 计算价格变动幅度
                price_move = abs(end_point['price'] - start_point['price'])
                price_move_pct = (price_move / start_point['price'] * 100) if start_point['price'] > 0 else 0
                logger.info(f"    📈 趋势幅度: {price_move:.4f} ({price_move_pct:.1f}%)")
            
            # 如果是扩展信号，显示ABC波浪信息
            if 'wave_c_point' in additional_data:
                c_point = additional_data['wave_c_point']
                logger.info(f"    〰️  ABC波浪 C点: {c_point['type'].upper()}({c_point['price']:.4f})")
    
    def _log_fibonacci_analysis_context(self, symbol: str, df: pd.DataFrame) -> None:
        """
        记录斐波那契分析的市场环境信息
        
        Args:
            symbol: 交易对符号  
            df: K线数据
        """
        try:
            # 获取最近的价格信息
            recent_data = df.tail(20)
            current_price = df['close'].iloc[-1]
            highest_20 = recent_data['high'].max()
            lowest_20 = recent_data['low'].min()
            
            # 计算当前价格在区间中的位置
            price_position = ((current_price - lowest_20) / (highest_20 - lowest_20) * 100) if highest_20 != lowest_20 else 50
            
            # 计算近期波动性
            recent_returns = df['close'].pct_change().dropna().tail(20)
            volatility = recent_returns.std() * 100  # 转换为百分比
            
            logger.info(f"  📋 {symbol} 市场环境:")
            logger.info(f"    🏔️  近20期高点: {highest_20:.4f}")
            logger.info(f"    🏔️  近20期低点: {lowest_20:.4f}")
            logger.info(f"    📍 价格位置: {price_position:.1f}% (在20期区间内)")
            logger.info(f"    📊 近期波动率: {volatility:.2f}%")
            
            # 判断趋势方向
            sma_5 = df['close'].rolling(5).mean().iloc[-1]
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            
            if current_price > sma_5 > sma_20:
                trend_desc = "📈 上升趋势"
            elif current_price < sma_5 < sma_20:
                trend_desc = "📉 下降趋势"
            else:
                trend_desc = "➡️  横盘整理"
                
            logger.info(f"    {trend_desc}")
            
        except Exception as e:
            logger.warning(f"记录 {symbol} 市场环境时出错: {e}")
    
    def _fetch_klines_data(self) -> Dict[str, pd.DataFrame]:
        """
        获取K线数据
        
        Returns:
            交易对K线数据字典
        """
        symbols_data = {}
        
        if not self.exchange_client:
            logger.error("交易所客户端未初始化")
            return symbols_data
        
        interval = self.config.get('kline_interval', '1h')
        limit = self.config.get('kline_limit', 200)
        
        for symbol in self.monitored_symbols:
            try:
                # 获取K线数据
                klines = self.exchange_client.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    limit=limit
                )
                
                if klines:
                    # 转换为DataFrame
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume'
                    ])
                    
                    # 数据类型转换
                    df['open'] = pd.to_numeric(df['open'])
                    df['high'] = pd.to_numeric(df['high'])
                    df['low'] = pd.to_numeric(df['low'])
                    df['close'] = pd.to_numeric(df['close'])
                    df['volume'] = pd.to_numeric(df['volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # 设置时间戳为索引
                    df = df.set_index('timestamp')
                    
                    # 按时间排序
                    df = df.sort_index()
                    
                    if len(df) >= 50:  # 至少需要50个数据点进行分析
                        symbols_data[symbol] = df
                        logger.debug(f"获取 {symbol} K线数据成功: {len(df)} 条记录")
                    else:
                        logger.warning(f"{symbol} K线数据不足，跳过分析")
                
            except Exception as e:
                logger.error(f"获取 {symbol} K线数据失败: {e}")
                continue
        
        logger.info(f"成功获取 {len(symbols_data)} 个交易对的K线数据")
        return symbols_data
    
    def _process_signals(self, signals: List[TechnicalSignal]) -> Dict[str, Any]:
        """
        处理信号并发送通知
        
        Args:
            signals: 技术分析信号列表
            
        Returns:
            处理结果字典
        """
        if not signals:
            return {'sent': False, 'reason': '没有信号需要处理'}
        
        # 发送通知
        if self.notification_recipients and self.notification_service:
            try:
                sent_count = 0
                for recipient in self.notification_recipients:
                    success = self.notification_service.send_signal_notification(
                        signals=signals,
                        recipient=recipient
                    )
                    if success:
                        sent_count += 1
                
                return {
                    'sent': sent_count > 0,
                    'sent_count': sent_count,
                    'total_recipients': len(self.notification_recipients),
                    'signals_count': len(signals)
                }
                
            except Exception as e:
                logger.error(f"发送信号通知失败: {e}")
                return {'sent': False, 'error': str(e)}
        else:
            return {'sent': False, 'reason': '没有配置通知收件人或通知服务不可用'}
    
    def add_monitored_symbol(self, symbol: str) -> bool:
        """
        添加监控的交易对
        
        Args:
            symbol: 交易对符号
            
        Returns:
            是否添加成功
        """
        if symbol not in self.monitored_symbols:
            self.monitored_symbols.add(symbol)
            logger.info(f"添加监控交易对: {symbol}")
            return True
        return False
    
    def remove_monitored_symbol(self, symbol: str) -> bool:
        """
        移除监控的交易对
        
        Args:
            symbol: 交易对符号
            
        Returns:
            是否移除成功
        """
        if symbol in self.monitored_symbols:
            self.monitored_symbols.remove(symbol)
            logger.info(f"移除监控交易对: {symbol}")
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取信号引擎状态
        
        Returns:
            状态字典
        """
        return {
            'enabled': self.enabled,
            'monitored_symbols_count': len(self.monitored_symbols),
            'monitored_symbols': list(self.monitored_symbols),
            'notification_recipients_count': len(self.notification_recipients),
            'market_analyzer_ready': self.market_analyzer is not None,
            'notification_service_ready': self.notification_service is not None,
            'exchange_client_ready': self.exchange_client is not None,
            'config': {k: v for k, v in self.config.items() if k != 'indicators'}  # 不包含详细指标配置
        }
    
    def test_components(self) -> Dict[str, Any]:
        """
        测试各个组件的状态
        
        Returns:
            测试结果字典
        """
        results = {}
        
        # 测试交易所连接
        if self.exchange_client:
            try:
                test_result = self.exchange_client.test_connection()
                results['exchange_connection'] = {
                    'success': True,
                    'data': test_result
                }
            except Exception as e:
                results['exchange_connection'] = {
                    'success': False,
                    'error': str(e)
                }
        else:
            results['exchange_connection'] = {
                'success': False,
                'error': '交易所客户端未初始化'
            }
        
        # 测试通知服务
        if self.notification_service:
            results['notification_service'] = self.notification_service.test_email_config()
        else:
            results['notification_service'] = {
                'success': False,
                'error': '通知服务未初始化'
            }
        
        # 测试数据获取
        try:
            if self.monitored_symbols:
                test_data = self._fetch_klines_data()
                results['data_fetch'] = {
                    'success': len(test_data) > 0,
                    'symbols_count': len(test_data),
                    'test_symbols': list(test_data.keys())[:3]  # 显示前3个测试交易对
                }
            else:
                results['data_fetch'] = {
                    'success': False,
                    'error': '没有监控的交易对'
                }
        except Exception as e:
            results['data_fetch'] = {
                'success': False,
                'error': str(e)
            }
        
        return results

    def _generate_analysis_charts(self, symbols_data: Dict[str, pd.DataFrame], 
                                  signals_result: Dict[str, List]) -> List[str]:
        """
        为有信号的交易对生成简化的技术分析图表
        
        Args:
            symbols_data: K线数据
            signals_result: 分析信号结果
            
        Returns:
            生成的图表文件路径列表
        """
        chart_paths = []
        
        try:
            import matplotlib.pyplot as plt
            import mplfinance as mpf
            import os
            from datetime import datetime
            
            # 确保输出目录存在
            chart_dir = 'user_data/charts'
            os.makedirs(chart_dir, exist_ok=True)
            
            # 为前3个有信号的交易对生成简化图表
            signal_symbols = [symbol for symbol, signals in signals_result.items() 
                            if signals and any(s.signal_type != 'NEUTRAL' for s in signals)]
            
            for symbol in signal_symbols[:3]:  # 只生成前3个，避免邮件过大
                if symbol in symbols_data:
                    try:
                        # 获取数据
                        df = symbols_data[symbol].tail(100).copy()  # 最近100个数据点
                        
                        # 生成简单的K线图
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        chart_path = os.path.join(chart_dir, f'{symbol}_{timestamp}.png')
                        
                        # 创建图表
                        fig, axes = mpf.plot(
                            df,
                            type='candle',
                            style='yahoo',
                            title=f'{symbol} 技术分析图表',
                            ylabel='价格',
                            figsize=(12, 8),
                            volume=True,
                            panel_ratios=(3, 1),
                            returnfig=True
                        )
                        
                        # 保存图表
                        fig.savefig(chart_path, bbox_inches='tight', dpi=100)
                        plt.close(fig)
                        
                        chart_paths.append(chart_path)
                        logger.info(f"为 {symbol} 生成简化技术分析图表: {chart_path}")
                        
                    except Exception as e:
                        logger.error(f"为 {symbol} 生成图表失败: {e}")
                        continue
            
            logger.info(f"成功生成 {len(chart_paths)} 个技术分析图表")
            
        except Exception as e:
            logger.error(f"生成技术分析图表时发生错误: {e}")
        
        return chart_paths


# 全局信号引擎实例
_signal_engine = None


def get_signal_engine() -> SignalEngine:
    """获取全局信号引擎实例"""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = SignalEngine()
    return _signal_engine