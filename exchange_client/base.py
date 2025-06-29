"""
交易所客户端抽象基类

定义了所有交易所客户端必须实现的接口规范。
遵循依赖倒置原则，使得上层业务逻辑依赖于抽象而不是具体实现。
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import Trade, AccountInfo, Symbol, TradeData, SyncResult
from .exceptions import ExchangeAPIError

logger = logging.getLogger(__name__)


class ExchangeClient(ABC):
    """交易所客户端抽象基类"""
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        """
        初始化交易所客户端
        
        Args:
            api_key: API 密钥
            api_secret: API 密钥密码
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_connected = False
        self.exchange_name = self._get_exchange_name()
    
    @abstractmethod
    def _get_exchange_name(self) -> str:
        """获取交易所名称"""
        pass
    
    @abstractmethod
    def connect(self) -> tuple[bool, str]:
        """
        连接到交易所 API
        
        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接并获取账户信息
        
        Returns:
            Dict[str, Any]: 包含连接状态和账户信息的字典
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """
        获取账户信息
        
        Returns:
            AccountInfo: 账户信息对象
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def get_trading_symbols(self) -> List[Symbol]:
        """
        获取所有交易对信息
        
        Returns:
            List[Symbol]: 交易对列表
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def get_active_symbols(self) -> List[str]:
        """
        获取账户活跃的交易对
        
        Returns:
            List[str]: 活跃交易对列表
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def fetch_trades(
        self, 
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000,
        historical_symbols: Optional[List[str]] = None
    ) -> TradeData:
        """
        获取交易记录
        
        Args:
            symbol: 交易对符号，为 None 时获取所有交易对
            since: 开始时间，为 None 时获取所有历史记录
            limit: 每次请求的记录数量限制
            historical_symbols: 历史交易对列表（用于改进交易对检测）
            
        Returns:
            TradeData: 交易数据对象
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def fetch_symbol_trades(
        self, 
        symbol: str,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Trade]:
        """
        获取指定交易对的交易记录
        
        Args:
            symbol: 交易对符号
            since: 开始时间
            limit: 记录数量限制
            
        Returns:
            List[Trade]: 交易记录列表
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def fetch_klines(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 500,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            interval: K线间隔 (1m, 5m, 15m, 1h, 4h, 1d等)
            limit: 数据条数限制
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: K线数据列表，每条包含 [timestamp, open, high, low, close, volume]
            
        Raises:
            ExchangeAPIError: API 调用失败
        """
        pass
    
    @abstractmethod
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """
        解析交易所特定的时间戳格式为标准的 UTC datetime 对象。

        每个子类都必须实现此方法，以处理其特定的时间戳格式
        （例如，毫秒、秒、ISO 8601 字符串等）。

        Args:
            timestamp: 从交易所 API 返回的原始时间戳。

        Returns:
            一个时区为 UTC 的 datetime 对象。
        """
        pass
    
    @abstractmethod
    def _format_symbol_for_market(self, symbol: str) -> str:
        """
        将内部统一的交易对格式转换为交易所API特定的市场格式。

        例如: 'BTCUSDT' -> 'BTC/USDT' (Binance)
              'BTCUSDT' -> 'BTC-USDT' (Coinbase)

        Args:
            symbol: 内部标准格式的交易对。

        Returns:
            交易所API所需的格式。
        """
        pass
    
    def sync_trades(self, days: int = 7) -> SyncResult:
        """
        同步交易记录（模板方法）
        
        Args:
            days: 同步最近几天的数据
            
        Returns:
            SyncResult: 同步结果对象
        """
        try:
            # 计算开始时间
            since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            since = since.replace(day=since.day - days)
            
            # 获取历史交易对列表（用于改进交易对检测）
            historical_symbols = None
            try:
                from core.database import get_historical_symbols
                historical_symbols = get_historical_symbols()
                logger.info(f"从数据库获取到 {len(historical_symbols)} 个历史交易对")
            except ImportError:
                logger.warning("无法导入数据库模块，跳过历史交易对检测")
            except Exception as e:
                logger.warning(f"获取历史交易对失败: {e}")
            
            # 获取交易数据 - 使用历史交易对信息
            trade_data = self.fetch_trades(since=since, historical_symbols=historical_symbols)
            
            return SyncResult(
                success=True,
                trades=trade_data.trades,
                new_count=len(trade_data.trades),
                duplicate_count=0,
                total_count=trade_data.total_count,
                sync_period=f"{days} 天",
                since_date=since.strftime('%Y-%m-%d')
            )
            
        except ExchangeAPIError as e:
            return SyncResult(
                success=False,
                trades=[],
                new_count=0,
                duplicate_count=0,
                total_count=0,
                error_message=str(e)
            )
    
    def sync_symbol_trades(self, symbol: str, days: int = 30) -> SyncResult:
        """
        同步指定交易对的交易记录（模板方法）
        
        Args:
            symbol: 交易对符号
            days: 同步最近几天的数据
            
        Returns:
            SyncResult: 同步结果对象
        """
        try:
            # 计算开始时间
            since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            since = since.replace(day=since.day - days)
            
            # 获取交易数据
            trades = self.fetch_symbol_trades(symbol, since=since)
            
            return SyncResult(
                success=True,
                trades=trades,
                new_count=len(trades),
                duplicate_count=0,
                total_count=len(trades),
                sync_period=f"{days} 天",
                since_date=since.strftime('%Y-%m-%d')
            )
            
        except ExchangeAPIError as e:
            return SyncResult(
                success=False,
                trades=[],
                new_count=0,
                duplicate_count=0,
                total_count=0,
                error_message=str(e)
            )
    
    def __str__(self) -> str:
        return f"{self.exchange_name}Client(connected={self.is_connected})"


class SymbolDiscoveryStrategy(ABC):
    """
    用于发现活跃交易对的策略接口 (Interface)。
    """
    @abstractmethod
    def discover(
        self,
        client: 'ExchangeClient',
        markets: dict,
        historical_symbols: Optional[List[str]] = None
    ) -> set:
        """
        执行发现逻辑。

        Args:
            client: ExchangeClient 实例，用于进行 API 调用（如获取余额）。
            markets: 从交易所加载的市场信息。
            historical_symbols: 从数据库中获取的历史交易对列表。

        Returns:
            一个包含新发现的交易对字符串的集合。
        """
        pass 