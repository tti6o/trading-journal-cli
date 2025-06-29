"""
交易所客户端包

提供统一的接口来访问不同的加密货币交易所 API。
支持多种交易所的无缝切换和扩展。
"""

from .base import ExchangeClient, TradeData, AccountInfo
from .binance_client import BinanceClient
from .exceptions import (
    ExchangeAPIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
    DataFormatError
)
from .models import Trade, Balance, Symbol, SyncResult
from .factory import ExchangeClientFactory

__version__ = "2.0.0"
__all__ = [
    "ExchangeClient",
    "BinanceClient", 
    "TradeData",
    "AccountInfo",
    "Trade",
    "Balance", 
    "Symbol",
    "SyncResult",
    "ExchangeClientFactory",
    "ExchangeAPIError",
    "AuthenticationError",
    "RateLimitError", 
    "NetworkError",
    "DataFormatError"
] 