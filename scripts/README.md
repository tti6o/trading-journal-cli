# Scripts 目录

此目录包含项目的演示脚本、验证脚本和其他辅助工具。

## 📁 文件说明

### 🎯 演示脚本
- **`demo_all_features.py`** - 完整功能演示脚本
  - 展示所有CLI命令的使用方法
  - 演示稳定币标准化功能
  - 显示各种报告输出格式

### 🔍 验证脚本
- **`verify_trade_details.py`** - 交易记录详情验证
  - 展示 `--details` 选项的使用
  - 演示如何查看币种的所有交易记录
  - 用于核对数据和验证计算结果

- **`verify_stable_coins.py`** - 稳定币标准化验证
  - 验证稳定币自动标准化功能
  - 展示 FDUSD→USDT、USDC→USDT 等转换
  - 确保跨稳定币交易计算正确

### 🧪 测试脚本
- **`test_sample.py`** - 综合测试脚本
  - 测试所有核心功能模块
  - 验证数据库操作
  - 检查Excel文件解析
  - 测试PnL计算逻辑

## 🚀 使用方法

从项目根目录运行脚本：

```bash
# 运行完整功能演示
python scripts/demo_all_features.py

# 验证交易记录详情功能
python scripts/verify_trade_details.py

# 验证稳定币标准化
python scripts/verify_stable_coins.py

# 运行综合测试
python scripts/test_sample.py
```

## 📋 注意事项

1. **运行前确保已初始化**: 确保已运行 `python main.py init` 初始化数据库
2. **需要测试数据**: 某些脚本需要先导入交易数据才能正常运行
3. **依赖检查**: 确保所有依赖包已正确安装（`pip install -r requirements.txt`）

## 🔧 脚本维护

- 当添加新功能时，应相应更新演示脚本
- 验证脚本应与功能变更保持同步
- 所有脚本都应包含错误处理和清晰的输出信息 