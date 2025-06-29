"""
交易所客户端自定义异常类

定义了所有交易所客户端可能抛出的异常类型，
提供了统一的错误处理机制。
"""

from typing import Optional, Dict, Any


class ExchangeAPIError(Exception):
    """交易所 API 错误的基类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(ExchangeAPIError):
    """API 认证错误"""
    pass


class RateLimitError(ExchangeAPIError):
    """API 请求频率限制错误"""
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NetworkError(ExchangeAPIError):
    """网络连接错误"""
    pass


class DataFormatError(ExchangeAPIError):
    """数据格式错误"""
    pass


class InsufficientPermissionError(ExchangeAPIError):
    """API 权限不足错误"""
    pass


class SymbolNotFoundError(ExchangeAPIError):
    """交易对未找到错误"""
    pass


class TimeoutError(NetworkError):
    """请求超时错误"""
    pass 