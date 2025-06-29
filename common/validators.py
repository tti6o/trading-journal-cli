"""
输入验证模块

提供安全的输入验证功能，防范各种安全风险。
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from .exceptions import DataValidationError, SecurityError, FileProcessingError


class InputValidator:
    """输入验证器"""
    
    # 允许的文件扩展名
    ALLOWED_EXCEL_EXTENSIONS = ['.xlsx', '.xls']
    
    # 最大文件大小（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # 交易对符号正则表达式
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}[A-Z]{3,6}$')
    
    # 交易方向
    VALID_SIDES = ['BUY', 'SELL']
    
    @staticmethod
    def validate_file_path(file_path: str, check_exists: bool = True) -> str:
        """
        验证文件路径的安全性
        
        Args:
            file_path: 文件路径
            check_exists: 是否检查文件存在性
            
        Returns:
            规范化的文件路径
            
        Raises:
            SecurityError: 路径遍历攻击风险
            FileProcessingError: 文件不存在或无效
        """
        if not file_path:
            raise DataValidationError("文件路径不能为空")
        
        # 规范化路径
        try:
            normalized_path = os.path.normpath(file_path)
            resolved_path = os.path.abspath(normalized_path)
        except Exception as e:
            raise FileProcessingError(f"无效的文件路径: {e}", file_path)
        
        # 检查路径遍历攻击
        if '..' in normalized_path or '~' in normalized_path:
            raise SecurityError(f"检测到潜在的路径遍历攻击: {file_path}")
        
        # 检查文件存在性
        if check_exists and not os.path.exists(resolved_path):
            raise FileProcessingError(f"文件不存在: {resolved_path}", file_path)
        
        return resolved_path
    
    @staticmethod
    def validate_excel_file(file_path: str) -> str:
        """
        验证Excel文件的有效性
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            验证通过的文件路径
            
        Raises:
            FileProcessingError: 文件验证失败
        """
        # 基本路径验证
        validated_path = InputValidator.validate_file_path(file_path, check_exists=True)
        
        # 检查文件扩展名
        file_ext = Path(validated_path).suffix.lower()
        if file_ext not in InputValidator.ALLOWED_EXCEL_EXTENSIONS:
            raise FileProcessingError(
                f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(InputValidator.ALLOWED_EXCEL_EXTENSIONS)}",
                file_path
            )
        
        # 检查文件大小
        try:
            file_size = os.path.getsize(validated_path)
            if file_size > InputValidator.MAX_FILE_SIZE:
                raise FileProcessingError(
                    f"文件过大: {file_size / 1024 / 1024:.2f}MB，最大允许: {InputValidator.MAX_FILE_SIZE / 1024 / 1024}MB",
                    file_path
                )
        except OSError as e:
            raise FileProcessingError(f"无法读取文件信息: {e}", file_path)
        
        # 检查文件权限
        if not os.access(validated_path, os.R_OK):
            raise FileProcessingError("文件无读取权限", file_path)
        
        return validated_path
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """
        验证交易对符号格式
        
        Args:
            symbol: 交易对符号
            
        Returns:
            规范化的交易对符号
            
        Raises:
            DataValidationError: 格式无效
        """
        if not symbol:
            raise DataValidationError("交易对符号不能为空")
        
        # 转换为大写并去除空格
        normalized_symbol = symbol.strip().upper()
        
        # 正则表达式验证
        if not InputValidator.SYMBOL_PATTERN.match(normalized_symbol):
            raise DataValidationError(
                f"无效的交易对格式: {symbol}。格式应为: 基础货币+计价货币，如BTCUSDT",
                field="symbol",
                value=symbol
            )
        
        return normalized_symbol
    
    @staticmethod
    def validate_trade_side(side: str) -> str:
        """
        验证交易方向
        
        Args:
            side: 交易方向
            
        Returns:
            规范化的交易方向
            
        Raises:
            DataValidationError: 交易方向无效
        """
        if not side:
            raise DataValidationError("交易方向不能为空")
        
        normalized_side = side.strip().upper()
        
        if normalized_side not in InputValidator.VALID_SIDES:
            raise DataValidationError(
                f"无效的交易方向: {side}。有效值: {', '.join(InputValidator.VALID_SIDES)}",
                field="side",
                value=side
            )
        
        return normalized_side
    
    @staticmethod
    def validate_numeric_value(value, field_name: str, min_value: float = 0, max_value: Optional[float] = None) -> float:
        """
        验证数值型字段
        
        Args:
            value: 待验证的值
            field_name: 字段名称
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            验证通过的数值
            
        Raises:
            DataValidationError: 数值无效
        """
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise DataValidationError(
                f"{field_name}必须是有效的数字",
                field=field_name,
                value=str(value)
            )
        
        if numeric_value < min_value:
            raise DataValidationError(
                f"{field_name}不能小于{min_value}",
                field=field_name,
                value=str(value)
            )
        
        if max_value is not None and numeric_value > max_value:
            raise DataValidationError(
                f"{field_name}不能大于{max_value}",
                field=field_name,
                value=str(value)
            )
        
        return numeric_value
    
    @staticmethod
    def validate_datetime_string(datetime_str: str, field_name: str = "datetime") -> str:
        """
        验证日期时间字符串格式
        
        Args:
            datetime_str: 日期时间字符串
            field_name: 字段名称
            
        Returns:
            验证通过的日期时间字符串
            
        Raises:
            DataValidationError: 日期时间格式无效
        """
        if not datetime_str:
            raise DataValidationError(f"{field_name}不能为空")
        
        # 支持的日期时间格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(datetime_str.strip(), fmt)
                return datetime_str.strip()
            except ValueError:
                continue
        
        raise DataValidationError(
            f"无效的日期时间格式: {datetime_str}。支持的格式: YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD",
            field=field_name,
            value=datetime_str
        )
    
    @staticmethod
    def validate_trade_data(trade_data: dict) -> dict:
        """
        验证交易数据完整性
        
        Args:
            trade_data: 交易数据字典
            
        Returns:
            验证并规范化后的交易数据
            
        Raises:
            DataValidationError: 数据验证失败
        """
        if not isinstance(trade_data, dict):
            raise DataValidationError("交易数据必须是字典格式")
        
        required_fields = ['utc_time', 'symbol', 'side', 'price', 'quantity', 'quote_quantity', 'fee', 'fee_currency']
        
        # 检查必需字段
        for field in required_fields:
            if field not in trade_data:
                raise DataValidationError(f"缺少必需字段: {field}")
        
        validated_data = {}
        
        # 验证时间
        validated_data['utc_time'] = InputValidator.validate_datetime_string(
            trade_data['utc_time'], 'utc_time'
        )
        
        # 验证交易对
        validated_data['symbol'] = InputValidator.validate_symbol(trade_data['symbol'])
        
        # 验证交易方向
        validated_data['side'] = InputValidator.validate_trade_side(trade_data['side'])
        
        # 验证数值字段
        validated_data['price'] = InputValidator.validate_numeric_value(
            trade_data['price'], 'price', min_value=0
        )
        
        validated_data['quantity'] = InputValidator.validate_numeric_value(
            trade_data['quantity'], 'quantity', min_value=0
        )
        
        validated_data['quote_quantity'] = InputValidator.validate_numeric_value(
            trade_data['quote_quantity'], 'quote_quantity', min_value=0
        )
        
        validated_data['fee'] = InputValidator.validate_numeric_value(
            trade_data['fee'], 'fee', min_value=0
        )
        
        # 验证手续费货币
        if not trade_data['fee_currency']:
            raise DataValidationError("手续费货币不能为空", field='fee_currency')
        
        validated_data['fee_currency'] = trade_data['fee_currency'].strip().upper()
        
        # 复制其他可选字段
        for field in ['data_source', 'original_symbol', 'original_quote_currency']:
            if field in trade_data:
                validated_data[field] = trade_data[field]
        
        return validated_data
    
    @staticmethod
    def sanitize_api_key(api_key: str) -> str:
        """
        清理和验证API密钥格式
        
        Args:
            api_key: API密钥
            
        Returns:
            清理后的API密钥
            
        Raises:
            DataValidationError: API密钥格式无效
        """
        if not api_key:
            raise DataValidationError("API密钥不能为空")
        
        # 去除首尾空格
        cleaned_key = api_key.strip()
        
        # 检查长度（一般API密钥长度在16-256字符之间）
        if len(cleaned_key) < 16 or len(cleaned_key) > 256:
            raise DataValidationError("API密钥长度无效")
        
        # 检查字符集（只允许字母数字和常见符号）
        allowed_chars = re.compile(r'^[A-Za-z0-9\-_=+/]+$')
        if not allowed_chars.match(cleaned_key):
            raise DataValidationError("API密钥包含无效字符")
        
        return cleaned_key


class TradeDataSanitizer:
    """交易数据清理器"""
    
    @staticmethod
    def sanitize_excel_data(raw_data: List[dict]) -> List[dict]:
        """
        清理从Excel解析的原始数据
        
        Args:
            raw_data: 原始交易数据列表
            
        Returns:
            清理后的交易数据列表
        """
        sanitized_data = []
        errors = []
        
        for i, trade in enumerate(raw_data):
            try:
                validated_trade = InputValidator.validate_trade_data(trade)
                sanitized_data.append(validated_trade)
            except DataValidationError as e:
                errors.append(f"第{i+1}行数据错误: {e.get_user_message()}")
        
        if errors and len(errors) > len(raw_data) * 0.5:  # 如果超过50%的数据有错误
            raise DataValidationError(f"数据质量过低，错误详情:\n" + "\n".join(errors[:10]))
        
        return sanitized_data