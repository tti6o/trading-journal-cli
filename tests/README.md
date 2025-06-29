# 测试指南

本文档说明如何运行项目的测试套件。

## 测试结构

```
tests/
├── unit/                   # 单元测试
│   ├── test_utilities.py   # 工具函数测试
│   ├── test_database.py    # 数据库操作测试
│   └── test_journal.py     # 业务逻辑测试
├── integration/            # 集成测试
│   └── test_complete_workflow.py
├── fixtures/               # 测试数据
├── conftest.py            # pytest配置
└── README.md              # 本文档
```

## 测试环境准备

### 1. 安装测试依赖

```bash
pip install -r requirements.txt
```

### 2. 验证pytest安装

```bash
pytest --version
```

## 运行测试

### 运行所有测试

```bash
# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 运行并显示覆盖率
pytest --cov=. --cov-report=html
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit/ -v

# 只运行集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/unit/test_utilities.py -v

# 运行特定测试类
pytest tests/unit/test_utilities.py::TestSymbolNormalization -v

# 运行特定测试方法
pytest tests/unit/test_utilities.py::TestSymbolNormalization::test_normalize_symbol_fdusd_to_usdt -v
```

### 按标记运行测试

```bash
# 只运行快速测试（排除慢速测试）
pytest -m "not slow"

# 只运行慢速测试
pytest -m "slow"

# 只运行API相关测试
pytest -m "api"

# 只运行集成测试
pytest -m "integration"
```

### 生成测试报告

```bash
# 生成HTML覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term-missing

# 生成XML覆盖率报告（用于CI）
pytest --cov=. --cov-report=xml

# 生成JUnit XML报告
pytest --junit-xml=test-results.xml
```

## 测试配置

### pytest.ini 配置示例

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=common
    --cov=core
    --cov=services
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API related tests
```

## 编写测试

### 单元测试示例

```python
import pytest
from common import utilities

class TestUtilities:
    """测试工具函数"""
    
    def test_normalize_symbol(self):
        """测试符号标准化"""
        result = utilities.normalize_symbol("BTCFDUSD")
        assert result == "BTCUSDT"
    
    def test_normalize_symbol_invalid(self):
        """测试无效符号"""
        with pytest.raises(ValueError):
            utilities.normalize_symbol("")
```

### 集成测试示例

```python
import pytest

@pytest.mark.integration
class TestWorkflow:
    """测试完整工作流"""
    
    def test_import_and_analyze(self, temp_database, sample_data):
        """测试导入和分析流程"""
        # 测试代码...
        pass
```

### 使用Fixtures

```python
def test_with_temp_database(temp_database):
    """使用临时数据库的测试"""
    # temp_database 是一个临时数据库文件路径
    pass

def test_with_sample_data(sample_trade_data):
    """使用示例交易数据的测试"""
    # sample_trade_data 是预定义的测试数据
    pass
```

## 模拟和补丁

### 模拟外部依赖

```python
from unittest.mock import patch, MagicMock

@patch('pandas.read_excel')
def test_parse_excel(mock_read_excel):
    """模拟Excel读取"""
    mock_read_excel.return_value = mock_dataframe
    # 测试代码...
```

### 模拟API调用

```python
def test_api_call(mock_binance_client):
    """使用模拟客户端测试API调用"""
    mock_binance_client.get_trades.return_value = {'success': True}
    # 测试代码...
```

## 测试数据管理

### 测试数据文件

将测试数据放在 `tests/fixtures/` 目录：

```
fixtures/
├── sample_trades.json
├── test_excel.xlsx
└── mock_api_responses.json
```

### 加载测试数据

```python
import json
import os

def load_test_data(filename):
    """加载测试数据"""
    fixture_path = os.path.join('tests', 'fixtures', filename)
    with open(fixture_path, 'r') as f:
        return json.load(f)
```

## 持续集成

### GitHub Actions

项目包含CI配置（`.github/workflows/ci.yml`），自动运行：

- 单元测试
- 集成测试
- 代码覆盖率检查
- 安全扫描
- 代码质量检查

### 本地CI模拟

```bash
# 运行完整的CI检查
./scripts/run_ci_checks.sh
```

## 性能测试

### 运行性能测试

```bash
# 运行性能基准测试
pytest tests/performance/ -v

# 使用pytest-benchmark
pytest --benchmark-only
```

### 性能测试示例

```python
def test_large_dataset_performance(benchmark):
    """性能基准测试"""
    result = benchmark(process_large_dataset, large_data)
    assert result is not None
```

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保项目根目录在Python路径中
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   pytest
   ```

2. **数据库锁定**
   ```bash
   # 清理临时测试文件
   rm -rf data/test_*.db
   ```

3. **依赖冲突**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall
   ```

### 调试测试

```bash
# 运行时进入调试器
pytest --pdb

# 在失败时进入调试器
pytest --pdb-trace

# 增加日志输出
pytest -v -s --log-cli-level=DEBUG
```

## 最佳实践

1. **测试命名**：使用描述性的测试名称
2. **独立性**：每个测试都应该独立运行
3. **清理**：测试后清理临时文件和数据
4. **覆盖率**：保持高测试覆盖率（目标：>90%）
5. **性能**：避免测试运行时间过长
6. **可读性**：编写易于理解的测试代码

## 测试报告

查看最新的测试报告：

- **覆盖率报告**：`htmlcov/index.html`
- **CI报告**：GitHub Actions页面
- **性能报告**：`pytest-benchmark` 输出

---

如有问题，请参考[项目文档](../project_docs/)或联系开发团队。