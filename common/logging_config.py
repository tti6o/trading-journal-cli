"""
专业日志配置模块 - 交易日志CLI工具

专门优化的日志配置，解决第三方库日志噪音问题，确保CLI用户体验清洁。
特别针对交易分析工具中常见的噪音库进行过滤。
"""

import logging
import logging.handlers
import os
import warnings
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import configparser


class OptimizedFormatter(logging.Formatter):
    """优化的日志格式化器，支持不同级别的格式"""

    def __init__(self):
        super().__init__()
        # 不同级别使用不同格式
        self.formats = {
            logging.DEBUG: "🔍 %(asctime)s [%(name)s] %(message)s",
            logging.INFO: "ℹ️  %(asctime)s %(message)s",
            logging.WARNING: "⚠️  %(asctime)s [%(name)s] %(message)s",
            logging.ERROR: "❌ %(asctime)s [%(name)s] %(levelname)s: %(message)s",
            logging.CRITICAL: "🚨 %(asctime)s [%(name)s] CRITICAL: %(message)s"
        }
        self.default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def format(self, record):
        log_format = self.formats.get(record.levelno, self.default_format)
        formatter = logging.Formatter(log_format, datefmt='%H:%M:%S')
        return formatter.format(record)


class TradingJournalLoggingConfig:
    """交易日志工具专用日志配置器"""

    def __init__(self):
        self.config = None
        self.log_level = logging.INFO
        self.file_log_enabled = True
        self.log_file_path = 'data/app.log'
        self.debug_mode = False

    def load_config(self, config_path: str = None) -> bool:
        """加载配置文件"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')

        if not os.path.exists(config_path):
            return False

        try:
            self.config = configparser.ConfigParser()
            self.config.read(config_path, encoding='utf-8')

            # 读取日志配置
            log_level_str = self.config.get('logging', 'level', fallback='INFO').upper()
            self.log_level = getattr(logging, log_level_str, logging.INFO)
            self.file_log_enabled = self.config.getboolean('logging', 'file_log_enabled', fallback=True)
            self.log_file_path = self.config.get('logging', 'log_file_path', fallback='data/app.log')

            # 检查是否为调试模式
            self.debug_mode = (log_level_str == 'DEBUG')

            return True
        except Exception as e:
            print(f"⚠️  日志配置加载失败: {e}")
            return False

    def setup_logging(self) -> None:
        """设置优化的日志配置"""
        # 1. 首先抑制所有第三方库的警告
        self._suppress_third_party_warnings()

        # 2. 加载配置文件
        config_loaded = self.load_config()

        # 3. 设置根日志器
        self._setup_root_logger()

        # 4. 配置我们自己的模块日志
        self._setup_application_loggers()

        # 5. 抑制第三方库的详细日志
        self._suppress_third_party_logs()

        # 6. 特殊处理异步和网络相关日志
        self._suppress_async_and_network_logs()

        if not config_loaded and not self.debug_mode:
            # 静默处理，不输出配置警告（用户体验优先）
            pass

    def _suppress_third_party_warnings(self) -> None:
        """抑制第三方库的警告信息"""
        # 抑制urllib3的OpenSSL警告
        warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL.*')

        # 抑制matplotlib的字体警告
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

        # 抑制pandas的性能警告
        warnings.filterwarnings('ignore', message='.*PerformanceWarning.*')

        # 抑制numpy的警告
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')

        # 抑制ccxt的网络警告
        warnings.filterwarnings('ignore', module='ccxt')

    def _setup_root_logger(self) -> None:
        """设置根日志器"""
        # 清除现有的handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # 设置根日志器级别为WARNING，避免第三方库噪音
        root_logger.setLevel(logging.WARNING)

        # 创建handlers
        handlers = []

        # 控制台输出 - 使用优化格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(OptimizedFormatter())
        handlers.append(console_handler)

        # 文件输出（如果启用）
        if self.file_log_enabled:
            try:
                # 确保日志目录存在
                log_dir = os.path.dirname(self.log_file_path)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                # 使用RotatingFileHandler避免日志文件过大
                file_handler = logging.handlers.RotatingFileHandler(
                    self.log_file_path,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=3,
                    encoding='utf-8'
                )
                file_handler.setLevel(self.log_level)
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                handlers.append(file_handler)
            except Exception as e:
                print(f"⚠️  文件日志设置失败: {e}")

        # 配置根日志器
        logging.basicConfig(
            level=self.log_level,
            handlers=handlers,
            force=True  # 强制重新配置
        )

    def _setup_application_loggers(self) -> None:
        """配置我们应用程序自己的日志器"""
        app_modules = [
            '__main__',
            'core',
            'services',
            'common',
            'exchange_client',
            'main'
        ]

        for module in app_modules:
            logger = logging.getLogger(module)
            logger.setLevel(self.log_level)
            logger.propagate = True  # 允许传播到根日志器

    def _suppress_third_party_logs(self) -> None:
        """抑制第三方库的详细日志"""
        # 网络和HTTP库
        third_party_configs = {
            # HTTP和网络相关
            'urllib3': logging.WARNING,
            'urllib3.connectionpool': logging.WARNING,
            'urllib3.util.retry': logging.WARNING,
            'requests': logging.WARNING,
            'requests.packages.urllib3': logging.WARNING,
            'requests.packages.urllib3.connectionpool': logging.WARNING,

            # 交易所API库
            'ccxt': logging.WARNING,
            'ccxt.base': logging.WARNING,
            'ccxt.binance': logging.WARNING,

            # 数据处理和分析库
            'pandas': logging.WARNING,
            'numpy': logging.WARNING,
            'scipy': logging.WARNING,
            'ta-lib': logging.WARNING,
            'pandas_ta': logging.WARNING,

            # 图表和可视化库
            'matplotlib': logging.WARNING,
            'matplotlib.font_manager': logging.WARNING,
            'matplotlib.pyplot': logging.WARNING,
            'matplotlib.backends': logging.WARNING,
            'mplfinance': logging.WARNING,
            'plotly': logging.ERROR,
            'kaleido': logging.ERROR,

            # 图表生成和浏览器自动化（如果使用）
            'choreographer': logging.ERROR,
            'choreographer.browser_async': logging.ERROR,
            'choreographer.utils': logging.ERROR,
            'selenium': logging.WARNING,
            'webdriver_manager': logging.WARNING,
        }

        for logger_name, level in third_party_configs.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            logger.propagate = False  # 防止传播到根日志器

    def _suppress_async_and_network_logs(self) -> None:
        """抑制异步和网络相关的详细日志"""
        async_network_configs = {
            # 异步编程相关
            'asyncio': logging.WARNING,
            'aiohttp': logging.WARNING,
            'aiohttp.access': logging.WARNING,
            'aiohttp.client': logging.WARNING,
            'aiohttp.server': logging.WARNING,

            # 邮件服务
            'yagmail': logging.WARNING,
            'smtplib': logging.WARNING,

            # 调度器
            'apscheduler': logging.WARNING,
            'apscheduler.scheduler': logging.WARNING,
            'apscheduler.executors.default': logging.WARNING,

            # 浏览器和进程相关
            'root': logging.WARNING,
            'browser_proc': logging.ERROR,

            # 系统相关
            'urllib.parse': logging.WARNING,
            'ssl': logging.WARNING,
            'socket': logging.WARNING,
        }

        for logger_name, level in async_network_configs.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            logger.propagate = False

    def set_debug_mode(self, enable: bool = True) -> None:
        """动态切换调试模式"""
        self.debug_mode = enable

        if enable:
            # 调试模式：显示更多信息
            self.log_level = logging.DEBUG
            logging.getLogger().setLevel(logging.DEBUG)

            # 允许一些重要的第三方库日志
            logging.getLogger('ccxt').setLevel(logging.INFO)
            logging.getLogger('exchange_client').setLevel(logging.DEBUG)
            logging.getLogger('services').setLevel(logging.DEBUG)
        else:
            # 生产模式：清洁输出
            self.log_level = logging.INFO
            logging.getLogger().setLevel(logging.WARNING)
            self._suppress_third_party_logs()

    def get_logger(self, name: str) -> logging.Logger:
        """获取命名日志器"""
        return logging.getLogger(name)


# 全局配置实例
_logging_config = TradingJournalLoggingConfig()


def setup_optimized_logging(config_path: str = None, debug_mode: bool = False) -> None:
    """
    设置优化的日志配置

    Args:
        config_path: 配置文件路径
        debug_mode: 是否启用调试模式
    """
    global _logging_config

    if debug_mode:
        _logging_config.debug_mode = True

    if config_path:
        _logging_config.load_config(config_path)

    _logging_config.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """获取优化的日志器"""
    return _logging_config.get_logger(name)


def set_debug_mode(enable: bool = True) -> None:
    """动态设置调试模式"""
    global _logging_config
    _logging_config.set_debug_mode(enable)


def suppress_library_warnings(library_name: str, level: int = logging.WARNING) -> None:
    """手动抑制特定库的日志"""
    logger = logging.getLogger(library_name)
    logger.setLevel(level)
    logger.propagate = False


# 兼容性函数，保持向后兼容
def setup_logging() -> None:
    """向后兼容的日志设置函数"""
    setup_optimized_logging()