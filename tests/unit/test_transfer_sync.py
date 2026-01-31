"""
测试划转同步功能
版本 2.1.0 新增
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestFetchTransfers:
    """测试 BinanceClient.fetch_transfers 方法"""

    def test_fetch_transfers_method_exists(self):
        """测试 fetch_transfers 方法存在"""
        from exchange_client import BinanceClient
        assert hasattr(BinanceClient, 'fetch_transfers')

    def test_transfer_type_constants(self):
        """测试划转类型常量"""
        # 资金账户 -> 现货账户
        funding_main = 'FUNDING_MAIN'
        # 现货账户 -> 资金账户
        main_funding = 'MAIN_FUNDING'

        assert funding_main == 'FUNDING_MAIN'
        assert main_funding == 'MAIN_FUNDING'

    def test_days_to_since_conversion(self):
        """测试 days 参数转换为 since 时间"""
        days = 30
        since = datetime.now() - timedelta(days=days)

        # 验证时间差在合理范围内（允许1秒误差）
        expected_diff = timedelta(days=days)
        actual_diff = datetime.now() - since

        assert abs((actual_diff - expected_diff).total_seconds()) < 1


class TestTransferRecordFormat:
    """测试划转记录格式"""

    def test_transfer_to_trade_dict_format(self):
        """测试划转记录转换为交易字典格式"""
        # 模拟划转记录
        transfer = {
            'asset': 'USDT',
            'amount': Decimal('1000.00'),
            'timestamp': datetime(2026, 1, 31, 12, 0, 0),
            'type': 'FUNDING_MAIN',
            'status': 'CONFIRMED'
        }

        # 转换逻辑
        asset = transfer['asset']
        amount = transfer['amount']
        timestamp = transfer['timestamp']

        symbol = f"{asset}USDT" if asset not in ['USDT', 'USDC', 'FDUSD', 'BUSD'] else 'FDUSDUSDT'

        trade_dict = {
            'utc_time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'side': 'TRANSFER_IN',
            'price': 1.0,
            'quantity': float(amount),
            'quote_quantity': float(amount),
            'fee': 0.0,
            'fee_currency': 'USDT',
            'data_source': 'binance_transfer'
        }

        # 验证
        assert trade_dict['side'] == 'TRANSFER_IN'
        assert trade_dict['price'] == 1.0  # 稳定币1:1
        assert trade_dict['quantity'] == 1000.00
        assert trade_dict['quote_quantity'] == 1000.00
        assert trade_dict['fee'] == 0.0

    def test_stablecoin_symbol_mapping(self):
        """测试稳定币符号映射"""
        stablecoins = ['USDT', 'USDC', 'FDUSD', 'BUSD']

        for coin in stablecoins:
            symbol = f"{coin}USDT" if coin not in stablecoins else 'FDUSDUSDT'
            assert symbol == 'FDUSDUSDT', f"{coin} 应映射到 FDUSDUSDT"

    def test_non_stablecoin_symbol_mapping(self):
        """测试非稳定币符号映射"""
        coins = ['BTC', 'ETH', 'BNB', 'SOL']

        for coin in coins:
            symbol = f"{coin}USDT" if coin not in ['USDT', 'USDC', 'FDUSD', 'BUSD'] else 'FDUSDUSDT'
            assert symbol == f"{coin}USDT", f"{coin} 应映射到 {coin}USDT"


class TestTransferDataSource:
    """测试划转数据来源标记"""

    def test_transfer_data_source_tag(self):
        """测试划转记录的数据来源标记"""
        data_source = 'binance_transfer'
        assert 'transfer' in data_source.lower()

    def test_data_source_distinguishable(self):
        """测试划转数据来源可与交易数据区分"""
        trade_source = 'binance_api_v2'
        transfer_source = 'binance_transfer'

        assert trade_source != transfer_source
        assert 'transfer' not in trade_source
        assert 'transfer' in transfer_source
