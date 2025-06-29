"""
pytest配置文件

定义测试的全局配置、fixtures和测试工具。
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import MagicMock
from datetime import datetime

# 测试数据目录
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录fixture"""
    return TEST_DATA_DIR

@pytest.fixture
def temp_database():
    """临时数据库fixture"""
    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    yield temp_db.name
    
    # 清理临时文件
    try:
        os.unlink(temp_db.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def temp_excel_file():
    """临时Excel文件fixture"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    temp_file.close()
    
    yield temp_file.name
    
    # 清理临时文件
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def sample_trade_data():
    """示例交易数据fixture"""
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
            'data_source': 'test'
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
            'data_source': 'test'
        }
    ]

@pytest.fixture
def mock_binance_client():
    """模拟币安客户端fixture"""
    mock_client = MagicMock()
    
    # 模拟API响应
    mock_client.test_connection.return_value = {
        'success': True,
        'account_info': {
            'assets_count': 5,
            'assets': {
                'BTC': {'total': 0.1},
                'USDT': {'total': 1000.0}
            }
        }
    }
    
    mock_client.get_trades.return_value = {
        'success': True,
        'trades': [],
        'count': 0
    }
    
    return mock_client

@pytest.fixture
def mock_config():
    """模拟配置fixture"""
    return {
        'binance': {
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret'
        },
        'exchange': {
            'name': 'binance',
            'sandbox': True,
            'rate_limit': True
        },
        'scheduler': {
            'enabled': False,
            'sync_interval_hours': 4,
            'initial_sync_days': 30
        }
    }

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """自动设置测试环境"""
    # 设置环境变量
    monkeypatch.setenv('TESTING', 'true')
    
    # 确保测试数据目录存在
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # 创建测试数据目录
    os.makedirs('data/test', exist_ok=True)

@pytest.fixture
def capture_logs(caplog):
    """捕获日志fixture"""
    return caplog

# 测试标记
pytest.mark.slow = pytest.mark.slowtest
pytest.mark.integration = pytest.mark.integration
pytest.mark.unit = pytest.mark.unit

# 测试配置
def pytest_configure(config):
    """pytest配置"""
    # 注册自定义标记
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "api: mark test as API test")

def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if not any(marker.name in ['unit', 'integration', 'slow', 'api'] 
                  for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)