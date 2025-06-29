"""
database模块单元测试

测试数据库操作的正确性和错误处理。
"""

import pytest
import sqlite3
import os
import tempfile
from unittest.mock import patch, MagicMock

from core import database
from common.exceptions import DatabaseError


class TestDatabaseInitialization:
    """测试数据库初始化功能"""
    
    def test_init_db_creates_tables(self, temp_database):
        """测试数据库初始化创建表"""
        # 临时修改数据库路径
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            result = database.init_db()
            assert result is True
            
            # 验证表是否创建
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            
            # 检查trades表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            assert cursor.fetchone() is not None
            
            # 检查sync_metadata表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_metadata'")
            assert cursor.fetchone() is not None
            
            # 检查索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_trades_symbol'")
            assert cursor.fetchone() is not None
            
            conn.close()
        finally:
            database.DB_PATH = original_db_path
    
    def test_database_exists_true(self, temp_database):
        """测试数据库文件存在检查"""
        # 创建一个空文件
        with open(temp_database, 'w') as f:
            f.write('')
        
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            result = database.database_exists()
            assert result is True
        finally:
            database.DB_PATH = original_db_path
    
    def test_database_exists_false(self):
        """测试数据库文件不存在检查"""
        original_db_path = database.DB_PATH
        database.DB_PATH = '/nonexistent/path/test.db'
        
        try:
            result = database.database_exists()
            assert result is False
        finally:
            database.DB_PATH = original_db_path


class TestTradeIdGeneration:
    """测试交易ID生成功能"""
    
    def test_generate_trade_id_consistent(self):
        """测试相同数据生成相同ID"""
        trade_data = {
            'utc_time': '2024-01-01 10:00:00',
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'price': 45000.0,
            'quantity': 0.1,
            'quote_quantity': 4500.0
        }
        
        id1 = database.generate_trade_id(trade_data)
        id2 = database.generate_trade_id(trade_data)
        
        assert id1 == id2
        assert len(id1) == 16  # SHA256前16位
    
    def test_generate_trade_id_different_data(self):
        """测试不同数据生成不同ID"""
        trade_data1 = {
            'utc_time': '2024-01-01 10:00:00',
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'price': 45000.0,
            'quantity': 0.1,
            'quote_quantity': 4500.0
        }
        
        trade_data2 = {
            'utc_time': '2024-01-01 10:00:00',
            'symbol': 'BTCUSDT',
            'side': 'BUY',
            'price': 45000.0,
            'quantity': 0.2,  # 不同的数量
            'quote_quantity': 9000.0
        }
        
        id1 = database.generate_trade_id(trade_data1)
        id2 = database.generate_trade_id(trade_data2)
        
        assert id1 != id2


class TestTradeInsertion:
    """测试交易记录插入功能"""
    
    def test_insert_trade_success(self, temp_database, sample_trade_data):
        """测试成功插入交易记录"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            trade_data = sample_trade_data[0]
            result = database.insert_trade(trade_data)
            
            assert result is True
            
            # 验证数据是否插入
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            assert count == 1
            conn.close()
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_insert_trade_duplicate(self, temp_database, sample_trade_data):
        """测试插入重复交易记录"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            trade_data = sample_trade_data[0]
            
            # 第一次插入应该成功
            result1 = database.insert_trade(trade_data)
            assert result1 is True
            
            # 第二次插入应该失败（重复）
            result2 = database.insert_trade(trade_data)
            assert result2 is False
            
            # 验证只有一条记录
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            assert count == 1
            conn.close()
            
        finally:
            database.DB_PATH = original_db_path


class TestBatchTradeInsertion:
    """测试批量交易记录插入功能"""
    
    def test_save_trades_success(self, temp_database, sample_trade_data):
        """测试成功批量插入交易记录"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            success_count, ignored_count = database.save_trades(sample_trade_data)
            
            assert success_count == 2
            assert ignored_count == 0
            
            # 验证数据是否插入
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            assert count == 2
            conn.close()
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_save_trades_with_duplicates(self, temp_database, sample_trade_data):
        """测试批量插入包含重复记录"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 第一次插入
            success_count1, ignored_count1 = database.save_trades(sample_trade_data)
            assert success_count1 == 2
            assert ignored_count1 == 0
            
            # 第二次插入相同数据（应该全部被忽略）
            success_count2, ignored_count2 = database.save_trades(sample_trade_data)
            assert success_count2 == 0
            assert ignored_count2 == 2
            
            # 验证总记录数没有变化
            conn = sqlite3.connect(temp_database)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            assert count == 2
            conn.close()
            
        finally:
            database.DB_PATH = original_db_path


class TestTradeQuery:
    """测试交易记录查询功能"""
    
    def test_get_trades_all(self, temp_database, sample_trade_data):
        """测试获取所有交易记录"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            trades = database.get_trades()
            
            assert len(trades) == 2
            assert trades[0]['symbol'] == 'BTCUSDT'
            assert trades[1]['symbol'] == 'BTCUSDT'
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_trades_by_symbol(self, temp_database, sample_trade_data):
        """测试按交易对筛选"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            trades = database.get_trades(symbol='BTCUSDT')
            
            assert len(trades) == 2
            for trade in trades:
                assert trade['symbol'] == 'BTCUSDT'
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_trades_by_side(self, temp_database, sample_trade_data):
        """测试按交易方向筛选"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            buy_trades = database.get_trades(side='BUY')
            sell_trades = database.get_trades(side='SELL')
            
            assert len(buy_trades) == 1
            assert len(sell_trades) == 1
            assert buy_trades[0]['side'] == 'BUY'
            assert sell_trades[0]['side'] == 'SELL'
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_trades_with_limit(self, temp_database, sample_trade_data):
        """测试限制返回记录数"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            trades = database.get_trades(limit=1)
            
            assert len(trades) == 1
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_trades_since_date(self, temp_database):
        """测试按日期筛选"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 创建不同日期的交易数据
            trades_data = [
                {
                    'utc_time': '2024-01-01 10:00:00',
                    'symbol': 'BTCUSDT',
                    'side': 'BUY',
                    'price': 45000.0,
                    'quantity': 0.1,
                    'quote_quantity': 4500.0,
                    'fee': 0.1,
                    'fee_currency': 'BNB',
                    'data_source': 'test'
                },
                {
                    'utc_time': '2024-01-05 10:00:00',
                    'symbol': 'BTCUSDT',
                    'side': 'SELL',
                    'price': 46000.0,
                    'quantity': 0.1,
                    'quote_quantity': 4600.0,
                    'fee': 0.1,
                    'fee_currency': 'BNB',
                    'data_source': 'test'
                }
            ]
            
            database.save_trades(trades_data)
            
            # 查询2024-01-03之后的交易
            trades = database.get_trades(since='2024-01-03')
            
            assert len(trades) == 1
            assert trades[0]['utc_time'] == '2024-01-05 10:00:00'
            
        finally:
            database.DB_PATH = original_db_path


class TestPnLUpdate:
    """测试PnL更新功能"""
    
    def test_update_trade_pnl(self, temp_database, sample_trade_data):
        """测试更新交易PnL"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            # 获取第一个交易的ID
            trades = database.get_trades()
            trade_id = trades[0]['trade_id']
            
            # 更新PnL
            database.update_trade_pnl(trade_id, 100.0)
            
            # 验证更新
            updated_trades = database.get_trades()
            updated_trade = next(t for t in updated_trades if t['trade_id'] == trade_id)
            assert updated_trade['pnl'] == 100.0
            
        finally:
            database.DB_PATH = original_db_path


class TestMetadata:
    """测试元数据操作功能"""
    
    def test_set_and_get_metadata(self, temp_database):
        """测试设置和获取元数据"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 设置元数据
            result = database.set_metadata('test_key', 'test_value')
            assert result is True
            
            # 获取元数据
            value = database.get_metadata('test_key')
            assert value == 'test_value'
            
            # 获取不存在的元数据
            none_value = database.get_metadata('nonexistent_key')
            assert none_value is None
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_last_sync_timestamp(self, temp_database):
        """测试同步时间戳功能"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            
            # 初始状态应该为None
            timestamp = database.get_last_sync_timestamp()
            assert timestamp is None
            
            # 更新时间戳
            result = database.update_last_sync_timestamp()
            assert result is True
            
            # 获取更新后的时间戳
            timestamp = database.get_last_sync_timestamp()
            assert timestamp is not None
            assert isinstance(timestamp, str)
            
        finally:
            database.DB_PATH = original_db_path


class TestUtilityFunctions:
    """测试工具函数"""
    
    def test_get_all_symbols(self, temp_database, sample_trade_data):
        """测试获取所有交易对"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            symbols = database.get_all_symbols()
            
            assert len(symbols) == 1
            assert symbols[0] == 'BTCUSDT'
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_total_trade_count(self, temp_database, sample_trade_data):
        """测试获取总交易记录数"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            count = database.get_total_trade_count()
            
            assert count == 2
            
        finally:
            database.DB_PATH = original_db_path
    
    def test_get_historical_symbols(self, temp_database, sample_trade_data):
        """测试获取历史交易对"""
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_database
        
        try:
            database.init_db()
            database.save_trades(sample_trade_data)
            
            symbols = database.get_historical_symbols()
            
            assert len(symbols) == 1
            assert symbols[0] == 'BTCUSDT'
            
        finally:
            database.DB_PATH = original_db_path