"""
币安交易所客户端实现

实现了 ExchangeClient 抽象基类，提供币安特定的 API 集成功能。
"""

import ccxt
import time
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any

from .base import ExchangeClient, SymbolDiscoveryStrategy
from .models import Trade, AccountInfo, Symbol, Balance, TradeData, TradeSide
from .exceptions import (
    ExchangeAPIError, 
    AuthenticationError, 
    RateLimitError, 
    NetworkError,
    DataFormatError
)

logger = logging.getLogger(__name__)


class HistoricalDataStrategy(SymbolDiscoveryStrategy):
    """策略1: 从历史数据库记录中发现交易对。"""
    def discover(self, client: 'ExchangeClient', markets: dict, historical_symbols: Optional[List[str]] = None) -> set:
        discovered_symbols = set()
        if not historical_symbols:
            return discovered_symbols
            
        logger.info(f"策略1 (历史): 发现 {len(historical_symbols)} 个历史交易对: {historical_symbols}")
        for symbol in historical_symbols:
            symbol_id = client._format_symbol_for_market(symbol)
            if symbol_id in markets and markets[symbol_id]['active']:
                discovered_symbols.add(symbol)
        return discovered_symbols

class BalanceStrategy(SymbolDiscoveryStrategy):
    """策略2: 从当前账户非零余额推断交易对。"""
    def discover(self, client: 'ExchangeClient', markets: dict, historical_symbols: Optional[List[str]] = None) -> set:
        discovered_symbols = set()
        account_info = client.get_account_info()
        potential_assets = {
            balance.asset 
            for balance in account_info.balances 
            if balance.total > Decimal('0.00000001')
        }
        
        base_assets = [asset for asset in potential_assets if asset not in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'DAI', 'TUSD']]
        quote_assets = ['USDT', 'USDC', 'FDUSD', 'BTC', 'ETH', 'BNB']
        
        for base in base_assets:
            for quote in quote_assets:
                symbol_id = f"{base}/{quote}"
                if symbol_id in markets and markets[symbol_id]['active']:
                    discovered_symbols.add(symbol_id.replace('/', ''))
        
        logger.info(f"策略2 (余额): 基于余额发现 {len(discovered_symbols)} 个潜在交易对。")
        return discovered_symbols

class CommonSymbolsStrategy(SymbolDiscoveryStrategy):
    """策略3: 使用一个硬编码的常见交易对列表作为兜底。"""
    def discover(self, client: 'ExchangeClient', markets: dict, historical_symbols: Optional[List[str]] = None) -> set:
        discovered_symbols = set()
        common_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
            'BTCFDUSD', 'ETHFDUSD', 'XRPFDUSD'
        ]
        for symbol in common_symbols:
            symbol_id = client._format_symbol_for_market(symbol)
            if symbol_id in markets and markets[symbol_id]['active']:
                discovered_symbols.add(symbol)
        
        logger.info(f"策略3 (常见): 检查 {len(common_symbols)} 个常见交易对，发现 {len(discovered_symbols)} 个可用。")
        return discovered_symbols


class BinanceClient(ExchangeClient):
    """币安交易所客户端"""
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        super().__init__(api_key, api_secret, **kwargs)
        self.exchange = None
        self.sandbox = kwargs.get('sandbox', False)
        self.rate_limit = kwargs.get('rate_limit', True)
        self.proxies = kwargs.get('proxies', None)
    
    def _get_exchange_name(self) -> str:
        return "Binance"
    
    def connect(self) -> tuple[bool, str]:
        """连接到币安 API"""
        try:
            if not self.api_key or not self.api_secret:
                return False, "API 密钥未配置"
            
            exchange_config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'sandbox': self.sandbox,
                'enableRateLimit': self.rate_limit,
                'options': {
                    'defaultType': 'spot',
                }
            }
            
            # 如果有代理设置，添加到配置中
            if self.proxies:
                exchange_config['proxies'] = self.proxies
            
            self.exchange = ccxt.binance(exchange_config)
            
            # 测试连接 - 使用最基础的API调用
            # 首先检查服务器时间（无需认证）
            server_time = self.exchange.fetch_time()
            
            # 然后尝试一个需要认证的调用来验证API密钥
            try:
                # 尝试获取账户状态（更简单的调用）
                account_status = self.exchange.fetch_status()
                self.is_connected = True
            except ccxt.BaseError as e:
                # 如果获取状态失败，但服务器时间获取成功，可能是权限问题
                # 我们认为基本连接是正常的
                self.is_connected = True
                logger.warning(f"获取账户状态失败，但服务器连接正常: {e}")
            
            logger.info(f"{self.exchange_name} API 连接成功")
            return True, "连接成功"
            
        except ccxt.AuthenticationError as e:
            logger.error(f"API 认证失败: {e}")
            return False, "API 密钥验证失败，请检查密钥配置"
        except ccxt.NetworkError as e:
            logger.error(f"网络连接错误: {e}")
            return False, f"网络连接错误: {str(e)}"
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False, f"连接失败: {str(e)}"
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接并获取账户信息"""
        if not self.is_connected:
            success, message = self.connect()
            if not success:
                return {
                    'success': False,
                    'error': message
                }
        
        try:
            account_info = self.get_account_info()
            
            # 获取有余额的资产
            non_zero_balances = account_info.get_non_zero_balances()
            assets_dict = {}
            for balance in non_zero_balances:
                assets_dict[balance.asset] = {
                    'free': float(balance.free),
                    'locked': float(balance.locked),
                    'total': float(balance.total)
                }
            
            return {
                'success': True,
                'account_info': {
                    'assets_count': len(assets_dict),
                    'assets': assets_dict
                }
            }
            
        except ExchangeAPIError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        if not self.is_connected:
            success, message = self.connect()
            if not success:
                raise ExchangeAPIError(f"无法连接到交易所: {message}")
        
        try:
            balance_data = self.exchange.fetch_balance()
            
            balances = []
            for currency, balance_info in balance_data.items():
                if currency != 'info' and isinstance(balance_info, dict):
                    balance = Balance(
                        asset=currency,
                        free=Decimal(str(balance_info.get('free', 0))),
                        locked=Decimal(str(balance_info.get('used', 0)))
                    )
                    balances.append(balance)
            
            return AccountInfo(
                balances=balances,
                can_trade=True,  # 币安默认可以交易
                can_withdraw=True,
                can_deposit=True,
                update_time=datetime.now()
            )
            
        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"获取账户信息失败: {str(e)}")
    
    def get_trading_symbols(self) -> List[Symbol]:
        """获取所有交易对信息"""
        if not self.is_connected:
            success, message = self.connect()
            if not success:
                raise ExchangeAPIError(f"无法连接到交易所: {message}")
        
        try:
            markets = self.exchange.load_markets()
            symbols = []
            
            for symbol_id, market_info in markets.items():
                if market_info['spot']:  # 只获取现货交易对
                    symbol = Symbol(
                        symbol=symbol_id.replace('/', ''),
                        base_asset=market_info['base'],
                        quote_asset=market_info['quote'],
                        min_qty=Decimal(str(market_info['limits']['amount']['min'])) if market_info['limits']['amount']['min'] else None,
                        max_qty=Decimal(str(market_info['limits']['amount']['max'])) if market_info['limits']['amount']['max'] else None,
                        min_price=Decimal(str(market_info['limits']['price']['min'])) if market_info['limits']['price']['min'] else None,
                        max_price=Decimal(str(market_info['limits']['price']['max'])) if market_info['limits']['price']['max'] else None,
                        is_active=market_info['active']
                    )
                    symbols.append(symbol)
            
            return symbols
            
        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"获取交易对信息失败: {str(e)}")
    
    def get_active_symbols(
        self, 
        historical_symbols: Optional[List[str]] = None,
        strategies: Optional[List[SymbolDiscoveryStrategy]] = None
    ) -> List[str]:
        """
        获取账户活跃的交易对，采用可插拔的策略模式。

        Args:
            historical_symbols: 从数据库中提取的历史交易对列表。
            strategies: 一个交易对发现策略的列表。如果为None，则使用默认策略组合。
            
        Returns:
            一个去重且经过验证的活跃交易对列表。
        """
        if not self.is_connected:
            success, message = self.connect()
            if not success:
                raise ExchangeAPIError(f"无法连接到交易所: {message}")
        
        if strategies is None:
            # 定义默认的策略组合
            strategies = [
                HistoricalDataStrategy(),
                BalanceStrategy(),
                CommonSymbolsStrategy()
            ]

        try:
            markets = self.exchange.load_markets()
            active_symbols = set()

            for strategy in strategies:
                discovered = strategy.discover(self, markets, historical_symbols)
                active_symbols.update(discovered)
            
            active_symbols_list = sorted(list(active_symbols))
            logger.info(f"策略组合总共发现 {len(active_symbols_list)} 个活跃交易对: {active_symbols_list}")
            
            # 限制数量以避免API调用过多
            return active_symbols_list[:40]
            
        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"获取活跃交易对失败: {str(e)}")

    def _format_symbol_for_market(self, symbol: str) -> str:
        """将交易对符号格式化为市场格式 (例如: BTCUSDT -> BTC/USDT)"""
        if '/' in symbol:
            return symbol
        
        # 尝试常见的拆分方式
        quote_assets = ['USDT', 'USDC', 'FDUSD', 'BUSD', 'BTC', 'ETH', 'BNB']
        for quote in quote_assets:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        
        # 如果无法拆分，返回原始格式
        return symbol
    
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
            symbol: 指定交易对，如果为None则获取所有活跃交易对
            since: 开始时间
            limit: 每个交易对的记录限制
            historical_symbols: 历史交易对列表（用于改进交易对检测）
        """
        if not self.is_connected:
            success, message = self.connect()
            if not success:
                raise ExchangeAPIError(f"无法连接到交易所: {message}")
        
        try:
            all_trades = []
            
            # 处理时间参数
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)
            
            if symbol:
                # 获取指定交易对的交易记录
                trades = self._fetch_symbol_trades_raw(symbol, since_timestamp, limit)
                all_trades.extend(trades)
            else:
                # 获取所有交易对的交易记录 - 使用改进的检测算法
                active_symbols = self.get_active_symbols(historical_symbols)
                
                logger.info(f"使用多策略检测到 {len(active_symbols)} 个活跃交易对")
                
                for sym in active_symbols:
                    try:
                        trades = self._fetch_symbol_trades_raw(sym, since_timestamp, limit)
                        if trades:
                            logger.info(f"交易对 {sym}: 获取到 {len(trades)} 条记录")
                        all_trades.extend(trades)
                        time.sleep(0.1)  # 避免请求过快
                    except Exception as e:
                        logger.warning(f"获取交易对 {sym} 的交易记录失败: {e}")
                        continue
            
            # 转换为标准化数据格式
            standard_trades = [self._convert_to_standard_trade(trade) for trade in all_trades]
            
            # 按时间排序
            standard_trades.sort(key=lambda x: x.timestamp)
            
            return TradeData(
                trades=standard_trades,
                total_count=len(standard_trades),
                has_more=False
            )
            
        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"获取交易记录失败: {str(e)}")
    
    def fetch_symbol_trades(
        self, 
        symbol: str,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Trade]:
        """获取指定交易对的交易记录"""
        if not self.is_connected:
            raise ExchangeAPIError("未连接到交易所")
        
        try:
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)
            
            raw_trades = self._fetch_symbol_trades_raw(symbol, since_timestamp, limit)
            
            # 转换为标准化数据格式
            standard_trades = [self._convert_to_standard_trade(trade) for trade in raw_trades]
            
            # 按时间排序
            standard_trades.sort(key=lambda x: x.timestamp)
            
            return standard_trades
            
        except ccxt.BaseError as e:
            raise ExchangeAPIError(f"获取交易对 {symbol} 的交易记录失败: {str(e)}")
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """
        解析币安返回的毫秒级 UTC 时间戳。
        使用 timezone.utc 来创建带时区的 'aware' datetime 对象，替代已废弃的 utcfromtimestamp。
        """
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    def _fetch_symbol_trades_raw(
        self, 
        symbol: str, 
        since_timestamp: Optional[int] = None, 
        limit: int = 1000
    ) -> List[Dict]:
        """获取指定交易对的原始交易记录"""
        all_trades = []
        last_trade_id = None
        
        while True:
            try:
                params = {}
                if last_trade_id:
                    params['fromId'] = last_trade_id + 1
                elif since_timestamp:
                    params['startTime'] = since_timestamp
                
                trades = self.exchange.fetch_my_trades(symbol, since_timestamp, limit, params)
                
                if not trades:
                    break
                
                all_trades.extend(trades)
                
                # 检查是否还有更多数据
                if len(trades) < limit:
                    break
                
                last_trade_id = trades[-1]['id']
                time.sleep(0.1)  # 避免请求过快
                
            except ccxt.RateLimitExceeded:
                logger.warning("API 请求频率限制，等待 60 秒...")
                time.sleep(60)
                continue
            except Exception as e:
                logger.error(f"获取交易对 {symbol} 记录时出错: {e}")
                break
        
        return all_trades
    
    def _convert_to_standard_trade(self, raw_trade: Dict) -> Trade:
        """将原始交易数据转换为标准化格式"""
        try:
            # 转换时间格式 - 使用新的抽象方法
            timestamp = self._parse_timestamp(raw_trade['timestamp'])
            
            # 标准化交易对符号 - 导入标准化函数
            # 注意：此处每次调用都导入一次，性能略有影响，但确保了模块化。
            # 如果性能关键，可以考虑在类初始化时进行一次性导入。
            from common import utilities
            symbol = raw_trade['symbol'].replace('/', '')
            symbol = utilities.normalize_symbol(symbol)  # 应用标准化，统一稳定币
            
            # 确定交易方向
            side = TradeSide.BUY if raw_trade['side'] == 'buy' else TradeSide.SELL
            
            trade = Trade(
                id=str(raw_trade['id']),
                order_id=str(raw_trade['order']),
                symbol=symbol,
                side=side,
                price=Decimal(str(raw_trade['price'])),
                quantity=Decimal(str(raw_trade['amount'])),
                quote_quantity=Decimal(str(raw_trade['cost'])),
                fee=Decimal(str(raw_trade['fee']['cost'])) if raw_trade['fee'] else Decimal('0'),
                fee_asset=raw_trade['fee']['currency'] if raw_trade['fee'] else 'BNB',
                timestamp=timestamp,
                is_maker=raw_trade.get('maker', False)
            )
            
            return trade
            
        except (KeyError, ValueError, TypeError) as e:
            raise DataFormatError(f"数据格式转换失败: {str(e)}")
    
    def __str__(self) -> str:
        return f"BinanceClient(connected={self.is_connected}, sandbox={self.sandbox})" 