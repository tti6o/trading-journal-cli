# 交易日志分析工具 🚀

> 快速分析币安交易记录的命令行工具

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚡ 5分钟快速上手

### 1. 下载和安装
```bash
git clone https://github.com/your-repo/trading-journal-cli.git
cd trading-journal-cli
pip install -r requirements.txt
```

### 2. 三个核心命令
```bash
# 🔧 首次设置（一键配置）
python main.py setup

# 📊 同步数据和查看统计
python main.py sync

# 🔍 技术分析
python main.py analyze
```

## 🎯 核心功能

- **📈 智能盈亏计算** - 自动计算已实现盈亏和成本基础
- **🤖 币安API集成** - 自动同步最新交易数据
- **📊 核心统计报告** - 胜率、盈亏比、总盈亏
- **🔍 技术分析** - RSI、MACD、斐波那契分析
- **📧 智能通知** - 技术信号邮件提醒
- **💱 稳定币标准化** - 自动处理FDUSD/USDC转换

## 🛠️ 使用场景

### 日常复盘
```bash
python main.py sync    # 查看最新统计
```

### 深度分析
```bash
python main.py analyze BTC    # 分析BTC表现
python main.py analyze        # 全市场技术分析
```

### 首次配置或重置
```bash
python main.py setup    # 交互式设置向导
```

## 📊 输出示例

```
📊 核心统计报告 (最近7天)
==================================================
📈 总盈亏:     +1,234.56 USDT
🎯 胜率:       68.5%
💪 盈亏比:     1.85
📊 交易笔数:   25 笔
📈 整体盈利 🎉
```

## 🔧 高级用法

使用 `--help-all` 查看所有高级命令：
```bash
python main.py --help-all
```

详细的高级功能请查看 [ADVANCED.md](ADVANCED.md)

## 🔒 数据安全

- ✅ **本地处理** - 所有数据在本地处理
- ✅ **只读权限** - API只需要读取权限
- ✅ **配置保护** - 敏感信息被gitignore保护

## ❓ 常见问题

**Q: 首次使用如何配置？**
A: 运行 `python main.py setup` 按向导配置

**Q: 没有币安API可以使用吗？**
A: 可以，选择Excel导入模式

**Q: 支持哪些交易所？**
A: 目前支持币安，架构支持扩展其他交易所

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**快速开始：** `python main.py setup` → `python main.py sync` → `python main.py analyze`