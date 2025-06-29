# 交易日志 CLI 工具 (Trading Journal CLI)

一个轻量级的命令行工具，专为希望通过终端快速分析币安交易记录的交易者设计。

## 🎯 核心功能

- **快速导入**: 支持币安Excel交易历史文件的一键导入（支持中英文列名）
- **稳定币标准化**: 自动将FDUSD、USDC等稳定币统一为USDT处理，避免跨币种交易计算错误
- **精确计算**: 使用加权平均成本法计算已实现盈亏
- **币种分析**: 支持按币种查看详细的净盈亏分析
- **智能分析**: 自动计算胜率、盈亏比等关键指标
- **灵活筛选**: 支持按交易对、时间范围、交易方向筛选
- **去重保护**: 自动识别并忽略重复的交易记录

## 🚀 最新功能：技术分析与智能通知

**🎉 v3.0 新增：技术分析与通知功能！**

在 API 集成的基础上，现在支持自动技术分析和邮件通知：

### 📊 技术分析功能
- ✅ **多指标分析**: 支持 MA、RSI、MACD、布林带、随机指标等
- ✅ **智能信号**: 基于多指标综合判断生成买入/卖出信号  
- ✅ **置信度评估**: 根据触发指标数量计算信号置信度
- ✅ **灵活配置**: 支持自定义指标参数和权重

### 📧 智能通知系统
- ✅ **实时邮件**: 自动发送技术分析结果到指定邮箱
- ✅ **精美模板**: HTML 格式邮件，包含图表和详细分析
- ✅ **多收件人**: 支持同时发送给多个邮箱地址
- ✅ **队列处理**: 后台线程处理，确保发送稳定性

### ⏰ 自动化运行
- ✅ **定时分析**: 集成到调度器，可定时执行技术分析
- ✅ **智能监控**: 自动检测历史交易对并监控
- ✅ **灵活间隔**: 支持分钟级分析间隔配置

### 🚀 币安 API 集成 (v2.0)
- ✅ **自动同步**: 一键同步最新交易记录
- ✅ **智能去重**: 自动识别并跳过重复数据
- ✅ **实时连接测试**: 验证 API 配置和网络状态
- ✅ **增量更新**: 只同步新增的交易记录
- ✅ **安全性**: 仅需只读权限的 API 密钥

## 📦 安装要求

- Python 3.8+
- 必要的Python包（见 `requirements.txt`）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

首次使用时需要初始化数据库：

```bash
python main.py init
```

### 3. 导入交易数据

将你的币安交易历史Excel文件放在项目根目录，然后导入：

```bash
python main.py import your_binance_trades.xlsx
```

**🔥 稳定币自动标准化**: 导入过程中会自动将 `XRPFDUSD` → `XRPUSDT`，`ETHUSDC` → `ETHUSDT` 等，确保计算准确性。

### 4. 查看报告

```bash
# 生成汇总统计报告
python main.py report

# 查看指定币种的详细净盈亏
python main.py currency XRP

# 列出所有已交易币种
python main.py list-currencies
```

## 📊 详细用法

### 命令概览

| 命令 | 功能 | 示例 |
|------|------|------|
| `init` | 初始化数据库 | `python main.py init` |
| `import <file>` | 导入Excel交易文件 | `python main.py import trades.xlsx` |
| `report [选项]` | 显示汇总统计报告 | `python main.py report --symbol BTCUSDT` |
| `currency <币种> [--details]` | 查看指定币种净盈亏 | `python main.py currency BTC` |
| `list-currencies` | 列出所有已交易币种 | `python main.py list-currencies` |

### 📈 汇总报告选项

```bash
# 查看所有历史交易汇总
python main.py report

# 查看指定交易对的报告
python main.py report --symbol BTCUSDT

# 查看最近N天的报告
python main.py report --days 30
```

### 💰 币种分析功能

```bash
# 查看XRP的汇总净盈亏分析
python main.py currency XRP

# 查看XRP的所有交易记录详情（便于核对）
python main.py currency XRP --details

# 查看BTC的净盈亏分析
python main.py currency BTC

# 列出所有币种及其净盈亏
python main.py list-currencies
```

## 📋 Excel文件格式要求

支持币安导出的Excel文件，包含**中文**和**英文**列名：

### 英文列名（原版）
- `Date(UTC)` - 交易时间
- `Pair` - 交易对 (如 BTCUSDT)
- `Side` - 买卖方向 (BUY/SELL)
- `Price` - 成交价格
- `Executed` - 成交数量
- `Amount` - 成交金额
- `Fee` - 手续费

### 中文列名（中国版）
- `时间` - 交易时间
- `交易对` - 交易对 (如 BTC/USDT)
- `类型` - 买卖方向 (BUY/SELL)
- `价格` - 成交价格
- `数量` - 成交数量
- `成交额` - 成交金额
- `手续费` - 手续费
- `手续费结算币种` - 手续费币种

## 💡 稳定币标准化

### 支持的稳定币
自动标准化以下稳定币为 USDT：
- FDUSD → USDT
- USDC → USDT
- BUSD → USDT
- DAI → USDT

### 好处
- ✅ **解决跨稳定币交易问题**: 用FDUSD买入然后用USDT卖出，现在能正确计算盈亏
- ✅ **统一计算基准**: 所有计算以USDT为基准，更加准确
- ✅ **简化分析**: 减少交易对数量，分析更清晰

### 示例
```bash
# 导入时会显示标准化信息
📝 稳定币交易对标准化:
   XRPFDUSD -> XRPUSDT
   DOGEFDUSD -> DOGEUSDT
   SOLFDUSD -> SOLUSDT
   BTCFDUSD -> BTCUSDT
```

## 🧮 PnL计算方法

本工具使用**加权平均成本法**计算已实现盈亏：

1. **买入时**: 更新持仓的加权平均成本
2. **卖出时**: 基于当前平均成本计算实现盈亏
3. **手续费**: 自动扣除交易手续费（稳定币手续费）
4. **稳定币**: 所有稳定币按1:1兑换率处理

这种方法符合主流交易所的计算标准，比FIFO方法更准确。

## 🔧 测试与验证

运行测试脚本验证所有功能：

```bash
# 运行综合功能测试
python scripts/test_sample.py

# 验证稳定币标准化功能
python scripts/verify_stable_coins.py

# 演示所有功能
python scripts/demo_all_features.py

# 验证交易记录详情功能
python scripts/verify_trade_details.py
```

## 📁 项目结构

```
trading_journal_cli/
├── main.py                    # CLI入口
├── core/                      # 核心模块
│   ├── journal.py             # 业务逻辑层
│   └── database.py            # 数据访问层
├── services/                  # 服务模块 (新增)
│   ├── scheduler.py           # 定时任务调度器
│   ├── technical_analysis.py  # 技术分析服务
│   ├── notification.py        # 邮件通知服务
│   └── signal_engine.py       # 信号引擎
├── exchange_client/           # 交易所客户端
│   ├── base.py                # 抽象基类
│   ├── binance_client.py      # 币安客户端
│   └── factory.py             # 客户端工厂
├── common/                    # 通用模块
│   ├── utilities.py           # 工具函数（含稳定币标准化）
│   └── validators.py          # 数据验证
├── config/                    # 配置文件
│   └── config.ini.template    # 配置模板
├── requirements.txt           # 依赖包
├── data/                      # 数据库目录
├── scripts/                   # 测试与验证脚本
├── tests/                     # 单元测试目录
└── project_docs/              # 项目文档
    ├── TECHNICAL_ANALYSIS_GUIDE.md # 技术分析使用指南
    └── ...                    # 其他文档
```

## 📈 输出示例

### 币种净盈亏分析
```
============================================================
XRP 净盈亏分析报告
============================================================
交易概况:
  总交易笔数:    8
  买入交易:      6
  卖出交易:      2

数量统计:
  总买入数量:    9,497.5000 XRP
  总卖出数量:    4,748.7000 XRP
  当前持仓:      4,748.8000 XRP

金额统计 (USDT):
  总买入金额:    21,545.79 USDT
  总卖出金额:    10,541.64 USDT

盈亏分析:
  已实现盈亏:    -231.14 USDT
  胜率:          0.00%
  持仓成本价:    2.2686 USDT/XRP
  持仓价值:      10,773.01 USDT
============================================================
```

### 币种列表
```
📊 已交易币种列表:
==================================================
BTC      -  13笔交易 - 净盈亏:    2920.40 USDT
DOGE     -   6笔交易 - 净盈亏:       0.00 USDT
FDUSD    -   1笔交易 - 净盈亏:       0.00 USDT
SOL      -   1笔交易 - 净盈亏:       0.00 USDT
XRP      -   8笔交易 - 净盈亏:    -231.14 USDT
```

### 汇总报告
```
==================================================
交易汇总统计 (从 2023-10-01 到 2023-10-27)
==================================================
总交易笔数:      29
买入交易:        19
卖出交易:        10

=== 核心指标 ===
总实现盈亏:      +2,689.26 USDT
胜率:           60.00%
盈亏比:         2.50 : 1

=== 交易量统计 ===
总买入量:       65,142.58 USDT
总卖出量:       32,124.92 USDT
总手续费:       23.45 USDT
==================================================
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 📜 许可证

MIT License

---

**注意**: 此工具仅用于分析历史交易数据，不提供任何投资建议。交易有风险，投资需谨慎。 

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置模板
cp config/config.ini.template config/config.ini

# 编辑配置文件，填入 API 密钥和邮箱信息
```

### 3. 初始化和测试

```bash
# 初始化数据库
python main.py init

# 配置 API 并测试
python main.py api config
python main.py api test

# 测试技术分析组件
python main.py technical test
python main.py notification test
```

### 4. 使用功能

```bash
# 数据同步
python main.py api sync

# 执行技术分析
python main.py technical run

# 启动自动化调度器
python main.py scheduler start
```

### 快速入门脚本
```bash
python scripts/quick_start_api.py
```

## 📖 详细文档

- [技术分析功能使用指南](project_docs/TECHNICAL_ANALYSIS_GUIDE.md)
- [项目架构文档](project_docs/ARCHITECTURE.md)  
- [API 集成说明](project_docs/README_API_INTEGRATION.md)
- [调度器使用指南](project_docs/README_SCHEDULER.md)

## 🆕 新增命令

### 技术分析命令
```bash
python main.py technical run              # 执行技术分析
python main.py technical status           # 查看分析状态
python main.py technical test             # 测试组件
python main.py technical add-symbol BTCUSDT    # 添加监控交易对
```

### 通知功能命令  
```bash
python main.py notification test          # 测试邮件配置
python main.py notification status        # 查看通知状态
```

### 扩展的调度器命令
```bash
python main.py scheduler start            # 启动调度器(含技术分析)
python main.py scheduler status           # 查看状态
```

---

📞 **技术支持**: 如遇问题，请查看日志文件或提交 Issue  
⚠️ **免责声明**: 本工具仅用于技术分析参考，不构成投资建议