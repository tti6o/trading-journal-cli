"""
异常处理模块

定义项目中使用的自定义异常类，提供统一的错误处理机制。
"""
from typing import Optional, Dict, Any

class TradingJournalError(Exception):
    """交易日志系统基础异常类"""
    
    def __init__(self, message: str, user_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message: 技术性错误消息（用于日志记录）
            user_message: 用户友好的错误消息（用于界面显示）
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message
        self.details = details or {}
    
    def __str__(self) -> str:
        return self.message
    
    def get_user_message(self) -> str:
        """获取用户友好的错误消息"""
        return self.user_message


class DataValidationError(TradingJournalError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        user_message = f"数据验证失败：{message}"
        details = {}
        if field:
            details['field'] = field
        if value:
            details['value'] = value
        super().__init__(message, user_message, details)


class DatabaseError(TradingJournalError):
    """数据库操作异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        user_message = "数据库操作失败，请稍后重试"
        details = {}
        if operation:
            details['operation'] = operation
        super().__init__(message, user_message, details)


class FileProcessingError(TradingJournalError):
    """文件处理异常"""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        user_message = f"文件处理失败：{message}"
        details = {}
        if file_path:
            details['file_path'] = file_path
        super().__init__(message, user_message, details)


class APIError(TradingJournalError):
    """API调用异常"""
    
    def __init__(self, message: str, api_name: Optional[str] = None, status_code: Optional[int] = None):
        user_message = f"API调用失败：{message}"
        details = {}
        if api_name:
            details['api_name'] = api_name
        if status_code:
            details['status_code'] = status_code
        super().__init__(message, user_message, details)


class ConfigurationError(TradingJournalError):
    """配置错误异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        user_message = f"配置错误：{message}"
        details = {}
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, user_message, details)


class SecurityError(TradingJournalError):
    """安全相关异常"""
    
    def __init__(self, message: str):
        user_message = "安全验证失败，请检查权限设置"
        super().__init__(message, user_message)


def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TradingJournalError:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 包装未预期的异常
            raise TradingJournalError(
                f"未预期的错误：{str(e)}",
                "系统发生未知错误，请联系管理员"
            ) from e
    return wrapper


def format_error_for_user(error: Exception) -> str:
    """将异常格式化为用户友好的消息"""
    if isinstance(error, TradingJournalError):
        return error.get_user_message()
    else:
        return f"系统发生错误：{str(error)}"