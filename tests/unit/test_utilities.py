"""
utilities模块单元测试

测试工具函数的正确性和边界情况。
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from common import utilities
from common.exceptions import DataValidationError, FileProcessingError


class TestSymbolNormalization:
    """测试交易对符号标准化功能"""
    
    def test_normalize_symbol_fdusd_to_usdt(self):
        """测试FDUSD到USDT的转换"""
        result = utilities.normalize_symbol("BTCFDUSD")
        assert result == "BTCUSDT"
    
    def test_normalize_symbol_usdc_to_usdt(self):
        """测试USDC到USDT的转换"""
        result = utilities.normalize_symbol("ETHUSDC")
        assert result == "ETHUSDT"
    
    def test_normalize_symbol_already_usdt(self):
        """测试已经是USDT的符号"""
        result = utilities.normalize_symbol("BTCUSDT")
        assert result == "BTCUSDT"
    
    def test_normalize_symbol_lowercase(self):
        """测试小写输入"""
        result = utilities.normalize_symbol("btcfdusd")
        assert result == "BTCUSDT"
    
    def test_normalize_symbol_non_stable_coin(self):
        """测试非稳定币交易对"""
        result = utilities.normalize_symbol("BTCETH")
        assert result == "BTCETH"


class TestCurrencyAmountNormalization:
    """测试货币金额标准化功能"""
    
    def test_normalize_stable_coin_amount(self):
        """测试稳定币之间的转换"""
        result = utilities.normalize_currency_amount(100.0, "FDUSD", "USDT")
        assert result == 100.0
    
    def test_normalize_same_currency(self):
        """测试相同货币的转换"""
        result = utilities.normalize_currency_amount(100.0, "USDT", "USDT")
        assert result == 100.0
    
    def test_normalize_non_stable_currency(self):
        """测试非稳定币的转换"""
        result = utilities.normalize_currency_amount(100.0, "BTC", "USDT")
        assert result == 100.0  # 目前返回原值


class TestTimeConversion:
    """测试时间转换功能"""
    
    def test_convert_utc_to_local_time(self):
        """测试UTC到本地时间转换"""
        utc_time = "2024-01-01 00:00:00"
        result = utilities.convert_utc_to_local_time(utc_time)
        assert result == "2024-01-01 08:00:00"
    
    def test_normalize_excel_time_to_utc(self):
        """测试Excel时间标准化"""
        excel_time = "2024-01-01 00:00:00"
        result = utilities.normalize_excel_time_to_utc(excel_time)
        assert result == "2024-01-01 08:00:00"
    
    def test_time_conversion_invalid_format(self):
        """测试无效时间格式"""
        invalid_time = "invalid-time"
        result = utilities.convert_utc_to_local_time(invalid_time)
        assert result == invalid_time  # 应该返回原值


class TestBaseCurrencyExtraction:
    """测试基础货币提取功能"""
    
    def test_get_base_currency_btc_usdt(self):
        """测试BTC/USDT提取"""
        result = utilities.get_base_currency_from_symbol("BTCUSDT")
        assert result == "BTC"
    
    def test_get_base_currency_eth_usdt(self):
        """测试ETH/USDT提取"""
        result = utilities.get_base_currency_from_symbol("ETHUSDT")
        assert result == "ETH"
    
    def test_get_base_currency_unknown_symbol(self):
        """测试未知交易对"""
        result = utilities.get_base_currency_from_symbol("UNKNOWN")
        assert result == "UNKNOWN"
    
    def test_get_base_currency_case_insensitive(self):
        """测试大小写不敏感"""
        result = utilities.get_base_currency_from_symbol("btcusdt")
        assert result == "BTC"


class TestPnLCalculation:
    """测试盈亏计算功能"""
    
    def test_calculate_realized_pnl_simple_trade(self, sample_trade_data):
        """测试简单的买卖交易PnL计算"""
        symbol = "BTCUSDT"
        result = utilities.calculate_realized_pnl_for_symbol(sample_trade_data, symbol)
        
        # 验证结果结构
        assert isinstance(result, dict)
        assert len(result) == 2  # 应该有两笔交易的PnL
        
        # 买入交易PnL应该为0
        buy_trade_pnl = list(result.values())[0]
        assert buy_trade_pnl == 0.0
        
        # 卖出交易应该有盈利
        sell_trade_pnl = list(result.values())[1]
        assert sell_trade_pnl > 0
    
    def test_calculate_realized_pnl_empty_trades(self):
        """测试空交易列表"""
        result = utilities.calculate_realized_pnl_for_symbol([], "BTCUSDT")
        assert result == {}
    
    def test_calculate_realized_pnl_no_matching_symbol(self, sample_trade_data):
        """测试没有匹配的交易对"""
        result = utilities.calculate_realized_pnl_for_symbol(sample_trade_data, "ETHUSDT")
        assert result == {}


class TestCurrencyPnLCalculation:
    """测试币种盈亏统计功能"""
    
    def test_calculate_currency_pnl_with_trades(self, sample_trade_data):
        """测试有交易数据的币种统计"""
        result = utilities.calculate_currency_pnl(sample_trade_data, "BTC")
        
        # 验证结果结构
        assert isinstance(result, dict)
        assert result['base_currency'] == "BTC"
        assert result['total_trades'] == 2
        assert result['buy_trades'] == 1
        assert result['sell_trades'] == 1
        assert result['total_buy_quantity'] == 0.1
        assert result['total_sell_quantity'] == 0.1
        assert result['current_holding'] == 0.0
    
    def test_calculate_currency_pnl_no_trades(self):
        """测试没有交易数据的币种"""
        result = utilities.calculate_currency_pnl([], "BTC")
        
        # 验证默认值
        assert result['base_currency'] == "BTC"
        assert result['total_trades'] == 0
        assert result['total_pnl'] == 0.0
        assert result['win_rate'] == 0.0


class TestTradeStatistics:
    """测试交易统计功能"""
    
    def test_calculate_trade_statistics_with_data(self, sample_trade_data):
        """测试有数据的统计计算"""
        result = utilities.calculate_trade_statistics(sample_trade_data)
        
        assert result['total_trades'] == 2
        assert result['buy_trades_count'] == 1
        assert result['sell_trades_count'] == 1
        assert result['total_buy_volume'] == 4500.0
        assert result['total_sell_volume'] == 4600.0
    
    def test_calculate_trade_statistics_empty_data(self):
        """测试空数据的统计计算"""
        result = utilities.calculate_trade_statistics([])
        
        assert result['total_trades'] == 0
        assert result['total_pnl'] == 0.0
        assert result['win_rate'] == 0.0
        assert result['profit_loss_ratio'] == 0.0


class TestFormatFunctions:
    """测试格式化函数"""
    
    def test_format_currency_large_amount(self):
        """测试大金额格式化"""
        result = utilities.format_currency(12345.67)
        assert "12,345.67" in result
        assert "USDT" in result
    
    def test_format_currency_small_amount(self):
        """测试小金额格式化"""
        result = utilities.format_currency(123.4567)
        assert "123.4567" in result
        assert "USDT" in result
    
    def test_format_percentage(self):
        """测试百分比格式化"""
        result = utilities.format_percentage(0.1234)
        assert "12.34%" in result
    
    def test_format_percentage_zero(self):
        """测试零百分比格式化"""
        result = utilities.format_percentage(0.0)
        assert "0.00%" in result


@pytest.mark.integration
class TestExcelParsing:
    """测试Excel解析功能（集成测试）"""
    
    @patch('pandas.read_excel')
    def test_parse_binance_excel_success(self, mock_read_excel):
        """测试成功解析Excel文件"""
        # 模拟Excel数据
        mock_df = pd.DataFrame({
            'Date(UTC)': ['2024-01-01 10:00:00', '2024-01-01 11:00:00'],
            'Pair': ['BTC/USDT', 'BTC/USDT'],
            'Side': ['BUY', 'SELL'],
            'Price': [45000.0, 46000.0],
            'Executed': [0.1, 0.1],
            'Amount': [4500.0, 4600.0],
            'Fee': [0.1, 0.1]
        })
        mock_read_excel.return_value = mock_df
        
        result = utilities.parse_binance_excel('test.xlsx')
        
        assert len(result) == 2
        assert result[0]['symbol'] == 'BTCUSDT'
        assert result[0]['side'] == 'BUY'
        assert result[1]['side'] == 'SELL'
    
    @patch('pandas.read_excel')
    def test_parse_binance_excel_missing_columns(self, mock_read_excel):
        """测试缺少必要列的Excel文件"""
        # 模拟缺少列的Excel数据
        mock_df = pd.DataFrame({
            'Date(UTC)': ['2024-01-01 10:00:00'],
            'Pair': ['BTC/USDT']
            # 缺少其他必要列
        })
        mock_read_excel.return_value = mock_df
        
        result = utilities.parse_binance_excel('test.xlsx')
        
        assert result == []  # 应该返回空列表
    
    def test_parse_binance_excel_file_not_found(self):
        """测试文件不存在的情况"""
        result = utilities.parse_binance_excel('nonexistent.xlsx')
        assert result == []


# 测试数据生成器
@pytest.fixture
def sample_pnl_trades():
    """带有PnL数据的示例交易"""
    return [
        {
            'utc_time': '2024-01-01 10:00:00',
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'price': 45000.0,
            'quantity': 0.1,
            'quote_quantity': 4500.0,
            'fee': 0.1,
            'fee_currency': 'BNB',
            'pnl': 0.0
        },
        {
            'utc_time': '2024-01-01 11:00:00',
            'symbol': 'BTCUSDT',
            'side': 'SELL',
            'price': 46000.0,
            'quantity': 0.1,
            'quote_quantity': 4600.0,
            'fee': 0.1,
            'fee_currency': 'BNB',
            'pnl': 100.0
        }
    ]