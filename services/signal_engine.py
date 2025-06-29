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

from .technical_analysis import MarketAnalyzer, TechnicalSignal
from .notification import get_notification_service
from exchange_client.factory import get_client
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
                
                # 通知收件人
                recipients_str = config.get('technical_analysis', 'notification_recipients', fallback='')
                if recipients_str:
                    self.notification_recipients = [email.strip() for email in recipients_str.split(',')]
                
                # 技术分析参数
                self.config = {
                    'kline_interval': config.get('technical_analysis', 'kline_interval', fallback='1h'),
                    'kline_limit': config.getint('technical_analysis', 'kline_limit', fallback=200),
                    'analysis_enabled': config.getboolean('technical_analysis', 'analysis_enabled', fallback=True),
                    'auto_detect_symbols': config.getboolean('technical_analysis', 'auto_detect_symbols', fallback=True),
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
        """解析技术指标配置"""
        indicators_config = {
            'sma': {'enabled': True, 'params': {'window': 20}, 'weight': 1.0},
            'ema': {'enabled': True, 'params': {'window': 12}, 'weight': 1.0},
            'rsi': {'enabled': True, 'params': {'window': 14}, 'weight': 1.2},
            'macd': {'enabled': True, 'params': {'fast': 12, 'slow': 26, 'signal': 9}, 'weight': 1.1},
            'bollinger': {'enabled': True, 'params': {'window': 20, 'std': 2}, 'weight': 1.0},
            'volume_sma': {'enabled': True, 'params': {'window': 20}, 'weight': 0.8},
            'stoch': {'enabled': True, 'params': {'k': 14, 'd': 3}, 'weight': 1.0}
        }
        
        # 从配置文件读取具体的指标设置
        try:
            if config.has_section('indicators'):
                for indicator in indicators_config:
                    if config.has_option('indicators', f'{indicator}_enabled'):
                        indicators_config[indicator]['enabled'] = config.getboolean('indicators', f'{indicator}_enabled')
                    if config.has_option('indicators', f'{indicator}_weight'):
                        indicators_config[indicator]['weight'] = config.getfloat('indicators', f'{indicator}_weight')
        except Exception as e:
            logger.warning(f"解析指标配置失败，使用默认配置: {e}")
        
        return {
            'indicators': indicators_config,
            'signal_rules': {
                'min_indicators': config.getint('technical_analysis', 'min_indicators', fallback=3),
                'confidence_threshold': config.getfloat('technical_analysis', 'confidence_threshold', fallback=0.6)
            }
        }
    
    def _initialize_components(self) -> None:
        """初始化各个组件"""
        try:
            # 初始化市场分析器
            self.market_analyzer = MarketAnalyzer(self.config)
            
            # 获取通知服务
            self.notification_service = get_notification_service()
            
            # 获取交易所客户端
            self.exchange_client = get_client()
            
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
    
    def run_analysis(self) -> Dict[str, Any]:
        """
        执行技术分析
        
        Returns:
            分析结果字典
        """
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
            
            # 执行技术分析
            signals_result = self.market_analyzer.analyze_symbols(symbols_data)
            
            # 生成市场摘要
            market_summary = self.market_analyzer.get_market_summary(signals_result)
            
            # 处理信号通知
            notification_result = self._process_signals(signals_result)
            
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'analyzed_symbols': len(symbols_data),
                'signals_found': sum(len(signals) for signals in signals_result.values()),
                'market_summary': market_summary,
                'notification_sent': notification_result.get('sent', False),
                'signals_detail': signals_result
            }
            
            logger.info(f"技术分析完成: 分析了 {result['analyzed_symbols']} 个交易对，"
                       f"发现 {result['signals_found']} 个信号")
            
            return result
            
        except Exception as e:
            logger.error(f"执行技术分析失败: {e}")
            return {'success': False, 'error': str(e)}
    
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
                    
                    # 按时间排序
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    
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
    
    def _process_signals(self, signals_result: Dict[str, List[TechnicalSignal]]) -> Dict[str, Any]:
        """
        处理信号并发送通知
        
        Args:
            signals_result: 技术分析信号结果
            
        Returns:
            处理结果字典
        """
        if not signals_result:
            return {'sent': False, 'reason': '没有信号需要处理'}
        
        # 收集所有信号
        all_signals = []
        for symbol, signals in signals_result.items():
            all_signals.extend(signals)
        
        if not all_signals:
            return {'sent': False, 'reason': '没有有效信号'}
        
        # 发送通知
        if self.notification_recipients and self.notification_service:
            try:
                sent_count = 0
                for recipient in self.notification_recipients:
                    success = self.notification_service.send_signal_notification(
                        signals=all_signals,
                        recipient=recipient
                    )
                    if success:
                        sent_count += 1
                
                return {
                    'sent': sent_count > 0,
                    'sent_count': sent_count,
                    'total_recipients': len(self.notification_recipients),
                    'signals_count': len(all_signals)
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
                test_symbol = list(self.monitored_symbols)[0]
                test_data = self._fetch_klines_data()
                results['data_fetch'] = {
                    'success': len(test_data) > 0,
                    'symbols_count': len(test_data),
                    'test_symbol': test_symbol
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


# 全局信号引擎实例
_signal_engine = None


def get_signal_engine() -> SignalEngine:
    """获取全局信号引擎实例"""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = SignalEngine()
    return _signal_engine