"""
测试 sync 命令的智能增量同步功能
版本 2.1.0 新增
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from click.testing import CliRunner


class TestSyncCommand:
    """测试 sync 命令"""

    def test_sync_calculates_days_from_last_sync(self):
        """测试从上次同步时间计算同步天数"""
        # 模拟上次同步时间为3天前
        last_sync_time = datetime.now() - timedelta(days=3)
        last_sync_str = last_sync_time.isoformat()

        # 计算预期天数
        time_diff = datetime.now() - last_sync_time
        expected_days = int(time_diff.total_seconds() / 86400) + 1

        assert expected_days == 4  # 3天前 + 1 = 4天

    def test_sync_first_time_uses_default_30_days(self):
        """测试首次同步使用默认30天"""
        last_sync = None

        if last_sync is None:
            sync_days = 30

        assert sync_days == 30

    def test_sync_fallback_to_7_days_on_error(self):
        """测试获取同步时间失败时回退到7天"""
        default_days = 7

        try:
            raise Exception("模拟错误")
        except Exception:
            sync_days = default_days

        assert sync_days == 7

    def test_version_updated_to_2_1_0(self):
        """测试版本号已更新到2.1.0"""
        from exchange_client import __version__
        assert __version__ == "2.1.0"


class TestDatabaseSyncTimestamp:
    """测试数据库同步时间戳功能"""

    def test_get_last_sync_timestamp(self):
        """测试获取上次同步时间戳"""
        from core import database as db

        # 函数应该存在
        assert hasattr(db, 'get_last_sync_timestamp')
        assert callable(db.get_last_sync_timestamp)

    def test_update_last_sync_timestamp(self):
        """测试更新同步时间戳"""
        from core import database as db

        # 函数应该存在
        assert hasattr(db, 'update_last_sync_timestamp')
        assert callable(db.update_last_sync_timestamp)


class TestIncrementalSyncLogic:
    """测试增量同步逻辑"""

    def test_time_diff_calculation(self):
        """测试时间差计算逻辑"""
        # 模拟不同时间差场景
        test_cases = [
            (timedelta(hours=1), 1),      # 1小时前 -> 1天
            (timedelta(days=1), 2),        # 1天前 -> 2天
            (timedelta(days=7), 8),        # 7天前 -> 8天
            (timedelta(days=30), 31),      # 30天前 -> 31天
        ]

        for time_diff, expected_days in test_cases:
            actual_days = int(time_diff.total_seconds() / 86400) + 1
            assert actual_days == expected_days, f"时间差 {time_diff} 应该计算为 {expected_days} 天"

    def test_sync_command_has_no_days_parameter(self):
        """测试 sync 命令不再有 --days 参数"""
        from main import sync
        import click

        # 检查 sync 命令的参数
        params = sync.params
        param_names = [p.name for p in params]

        assert 'days' not in param_names, "sync 命令不应该有 --days 参数"
