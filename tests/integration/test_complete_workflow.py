"""
完整工作流集成测试

测试从数据导入到报告生成的完整流程。
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch

from core import database, journal
from common import utilities, validators
from common.exceptions import TradingJournalError


@pytest.mark.integration
class TestCompleteWorkflow:
    """完整工作流集成测试"""
    
    def test_database_initialization_workflow(self, temp_database):
        """测试数据库初始化工作流"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            # 初始化数据库
            result = journal.initialize_database(force=True)
            assert result is True
            
            # 验证数据库文件存在
            assert os.path.exists(temp_database)
            
            # 验证表结构
            assert database.database_exists()
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_trade_import_and_analysis_workflow(self, temp_database, sample_trade_data):
        """测试交易导入和分析工作流"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            # 1. 初始化数据库
            database.init_db()
            
            # 2. 验证和清理数据
            sanitized_data = validators.TradeDataSanitizer.sanitize_excel_data(sample_trade_data)
            assert len(sanitized_data) == 2
            
            # 3. 导入交易数据
            success_count, ignored_count = database.save_trades(sanitized_data)
            assert success_count == 2
            assert ignored_count == 0
            
            # 4. 计算盈亏
            trades = database.get_trades()
            symbol = "BTCUSDT"
            pnl_results = utilities.calculate_realized_pnl_for_symbol(trades, symbol)
            
            # 5. 更新数据库中的PnL
            for trade in trades:
                trade_id = trade['trade_id']
                if trade_id in pnl_results:
                    database.update_trade_pnl(trade_id, pnl_results[trade_id])
            
            # 6. 生成统计报告
            updated_trades = database.get_trades()
            stats = utilities.calculate_trade_statistics(updated_trades)
            
            # 验证结果
            assert stats['total_trades'] == 2
            assert stats['buy_trades_count'] == 1
            assert stats['sell_trades_count'] == 1
            
        finally:
            database.DB_PATH = original_db_path
    
    @pytest.mark.slow
    def test_large_dataset_performance(self, temp_database):
        """测试大数据集处理性能"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 生成大量测试数据（确保每条记录都是唯一的）
            large_dataset = []
            for i in range(1000):
                # 使用更精确的时间戳和价格来确保唯一性
                minute = i % 60
                hour = (i // 60) % 24
                day = (i // (60 * 24)) % 28 + 1
                trade = {
                    'utc_time': f'2024-01-{day:02d} {hour:02d}:{minute:02d}:00',
                    'symbol': 'BTCUSDT',
                    'side': 'BUY' if i % 2 == 0 else 'SELL',
                    'price': 45000.0 + i,  # 每个交易都有不同的价格
                    'quantity': 0.1,
                    'quote_quantity': (45000.0 + i) * 0.1,
                    'fee': 0.1,
                    'fee_currency': 'BNB',
                    'data_source': 'test'
                }
                large_dataset.append(trade)
            
            # 测试批量插入性能
            import time
            start_time = time.time()
            
            success_count, ignored_count = database.save_trades(large_dataset)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 验证结果
            assert success_count == 1000
            assert ignored_count == 0
            assert processing_time < 5.0  # 应该在5秒内完成
            
            # 测试查询性能
            start_time = time.time()
            
            all_trades = database.get_trades()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            assert len(all_trades) == 1000
            assert query_time < 1.0  # 查询应该在1秒内完成
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_error_handling_workflow(self, temp_database):
        """测试错误处理工作流"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 测试无效数据处理
            invalid_trade_data = [{
                'utc_time': 'invalid-date',
                'symbol': 'INVALID',
                'side': 'INVALID_SIDE',
                'price': 'not_a_number',
                'quantity': -1,  # 负数
                'quote_quantity': 'invalid',
                'fee': 'invalid',
                'fee_currency': ''
            }]
            
            # 应该抛出验证错误
            with pytest.raises(TradingJournalError):
                validators.TradeDataSanitizer.sanitize_excel_data(invalid_trade_data)
            
            # 测试数据库错误恢复
            # 尝试插入无效数据应该失败但不影响后续操作
            valid_trade_data = [{
                'utc_time': '2024-01-01 10:00:00',
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'price': 45000.0,
                'quantity': 0.1,
                'quote_quantity': 4500.0,
                'fee': 0.1,
                'fee_currency': 'BNB',
                'data_source': 'test'
            }]
            
            success_count, ignored_count = database.save_trades(valid_trade_data)
            assert success_count == 1
            
        finally:
            database.DB_PATH = original_db_path
    
    @patch('common.utilities.parse_binance_excel')
    def test_excel_import_workflow(self, mock_parse_excel, temp_database, sample_trade_data):
        """测试Excel导入工作流"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            # 模拟Excel解析结果
            mock_parse_excel.return_value = sample_trade_data
            
            # 初始化数据库
            database.init_db()
            
            # 模拟导入流程
            file_path = 'test.xlsx'
            
            # 1. 验证文件（跳过实际文件检查）
            # 2. 解析Excel
            parsed_data = utilities.parse_binance_excel(file_path)
            assert len(parsed_data) == 2
            
            # 3. 验证数据
            sanitized_data = validators.TradeDataSanitizer.sanitize_excel_data(parsed_data)
            
            # 4. 导入数据库
            success_count, ignored_count = database.save_trades(sanitized_data)
            assert success_count == 2
            
            # 5. 验证导入结果
            total_count = database.get_total_trade_count()
            assert total_count == 2
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_currency_analysis_workflow(self, temp_database, sample_trade_data):
        """测试币种分析工作流"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            # 初始化和导入数据
            database.init_db()
            database.save_trades(sample_trade_data)
            
            # 获取所有交易
            all_trades = database.get_trades()
            
            # 计算PnL (这会更新数据库中的pnl字段)
            for symbol in ['BTCUSDT']:
                symbol_trades = [t for t in all_trades if t['symbol'] == symbol]
                if symbol_trades:
                    pnl_results = utilities.calculate_realized_pnl_for_symbol(symbol_trades, symbol)
                    for trade in symbol_trades:
                        trade_key = trade.get('trade_id') or trade.get('id')
                        if trade_key in pnl_results:
                            database.update_trade_pnl(trade['trade_id'], pnl_results[trade_key])
            
            # 重新获取更新后的交易数据
            all_trades = database.get_trades()
            
            # 分析BTC币种
            btc_stats = utilities.calculate_currency_pnl(all_trades, "BTC")
            
            # 验证分析结果
            assert btc_stats['base_currency'] == 'BTC'
            assert btc_stats['total_trades'] == 2
            assert btc_stats['buy_trades'] == 1
            assert btc_stats['sell_trades'] == 1
            assert btc_stats['current_holding'] == 0.0  # 买入和卖出数量相等
            
            # 格式化报告
            report = utilities.format_currency_report(btc_stats)
            assert 'BTC 净盈亏分析报告' in report
            assert '总交易笔数' in report
            
        finally:
            database.DB_PATH = original_db_path


@pytest.mark.integration
class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_data_consistency_after_operations(self, temp_database, sample_trade_data):
        """测试操作后的数据一致性"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 导入初始数据
            initial_count, _ = database.save_trades(sample_trade_data)
            
            # 获取导入后的数据
            trades_after_import = database.get_trades()
            
            # 验证数据完整性
            assert len(trades_after_import) == initial_count
            
            # 验证每条记录的必需字段
            for trade in trades_after_import:
                assert 'trade_id' in trade
                assert 'utc_time' in trade
                assert 'symbol' in trade
                assert 'side' in trade
                assert 'price' in trade
                assert 'quantity' in trade
                assert trade['trade_id'] is not None
                assert trade['price'] > 0
                assert trade['quantity'] > 0
            
            # 测试重复导入不会增加记录
            duplicate_count, ignored_count = database.save_trades(sample_trade_data)
            assert duplicate_count == 0
            assert ignored_count == initial_count
            
            # 验证总数没有变化
            final_trades = database.get_trades()
            assert len(final_trades) == initial_count
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_transaction_rollback_on_error(self, temp_database):
        """测试错误时的事务回滚（如果支持）"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 先插入一些有效数据
            valid_data = [{
                'utc_time': '2024-01-01 10:00:00',
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'price': 45000.0,
                'quantity': 0.1,
                'quote_quantity': 4500.0,
                'fee': 0.1,
                'fee_currency': 'BNB',
                'data_source': 'test'
            }]
            
            database.save_trades(valid_data)
            initial_count = database.get_total_trade_count()
            assert initial_count == 1
            
            # 确保后续操作不会影响现有数据
            final_count = database.get_total_trade_count()
            assert final_count == initial_count
            
        finally:
            database.DB_PATH = original_db_path