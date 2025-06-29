"""
交易所客户端工厂

使用工厂模式创建不同的交易所客户端实例。
支持通过配置文件或参数动态创建客户端。
"""

from typing import Dict, Type, Optional, Any
from .base import ExchangeClient
from .binance_client import BinanceClient
from .exceptions import ExchangeAPIError


class ExchangeClientFactory:
    """交易所客户端工厂类"""
    
    # 注册的交易所客户端类
    _clients: Dict[str, Type[ExchangeClient]] = {
        'binance': BinanceClient,
        # 'okx': OKXClient,           # 未来可扩展
        # 'kucoin': KucoinClient,     # 未来可扩展
        # 'huobi': HuobiClient,       # 未来可扩展
    }
    
    @classmethod
    def create_client(
        self, 
        exchange_name: str, 
        api_key: str, 
        api_secret: str, 
        **kwargs
    ) -> ExchangeClient:
        """
        创建交易所客户端实例
        
        Args:
            exchange_name: 交易所名称（如 'binance', 'okx'）
            api_key: API 密钥
            api_secret: API 密钥密码
            **kwargs: 其他配置参数
            
        Returns:
            ExchangeClient: 交易所客户端实例
            
        Raises:
            ExchangeAPIError: 不支持的交易所
        """
        exchange_name = exchange_name.lower()
        
        if exchange_name not in self._clients:
            supported = ', '.join(self._clients.keys())
            raise ExchangeAPIError(
                f"不支持的交易所: \"{exchange_name}\"。支持的交易所: {supported}"
            )
        
        client_class = self._clients[exchange_name]
        return client_class(api_key, api_secret, **kwargs)
    
    @classmethod
    def from_config(
        cls, 
        config: Dict[str, Any], 
        exchange_name: Optional[str] = None
    ) -> ExchangeClient:
        """
        从配置字典创建客户端
        
        Args:
            config: 配置字典，包含 API 密钥等信息
            exchange_name: 交易所名称，如果为 None 则从配置中读取
            
        Returns:
            ExchangeClient: 交易所客户端实例
            
        Raises:
            ExchangeAPIError: 配置不完整或交易所不支持
        """
        if exchange_name is None:
            exchange_name = config.get('exchange', 'binance')
        
        api_key = config.get('api_key')
        api_secret = config.get('api_secret')
        
        if not api_key or not api_secret:
            raise ExchangeAPIError("API 密钥配置不完整")
        
        # 提取其他配置参数
        extra_config = {k: v for k, v in config.items() 
                       if k not in ['exchange', 'api_key', 'api_secret']}
        
        return cls.create_client(exchange_name, api_key, api_secret, **extra_config)
    
    @classmethod
    def register_client(cls, exchange_name: str, client_class: Type[ExchangeClient]):
        """
        注册新的交易所客户端类
        
        Args:
            exchange_name: 交易所名称
            client_class: 客户端类
        """
        cls._clients[exchange_name.lower()] = client_class
    
    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """
        获取支持的交易所列表
        
        Returns:
            list[str]: 支持的交易所名称列表
        """
        return list(cls._clients.keys())
    
    @classmethod
    def is_supported(cls, exchange_name: str) -> bool:
        """
        检查是否支持指定的交易所
        
        Args:
            exchange_name: 交易所名称
            
        Returns:
            bool: 是否支持
        """
        return exchange_name.lower() in cls._clients
    
    @classmethod
    def create_from_config(cls, config_file: str = 'config.ini') -> ExchangeClient:
        """
        从配置文件创建交易所客户端
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            交易所客户端实例
        """
        import configparser
        
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # 读取交易所配置
        exchange_name = config.get('exchange', 'name', fallback='binance')
        
        # 读取API密钥
        api_key = config.get(exchange_name, 'api_key')
        api_secret = config.get(exchange_name, 'api_secret')
        
        # 读取其他配置
        sandbox = config.getboolean('exchange', 'sandbox', fallback=False)
        rate_limit = config.getboolean('exchange', 'rate_limit', fallback=True)
        
        # 读取代理配置
        proxies = None
        if config.has_section('proxy') and config.getboolean('proxy', 'enabled', fallback=False):
            proxies = {
                'http': config.get('proxy', 'http_proxy'),
                'https': config.get('proxy', 'https_proxy')
            }
        
        return cls.create_client(
            exchange_name, 
            api_key, 
            api_secret,
            sandbox=sandbox,
            rate_limit=rate_limit,
            proxies=proxies
        ) 