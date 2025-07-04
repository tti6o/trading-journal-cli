# 交易日志 CLI - 详细使用指南

本指南详细介绍了 `trading-journal-cli` 的所有命令、参数和使用示例。

## 目录
1.  [命令概览](#1-命令概览)
2.  [核心命令详解](#2-核心命令详解)
    -   [`init`](#init)
    -   [`import`](#import)
    -   [`report`](#report)
    -   [`currency`](#currency)
    -   [`list-currencies`](#list-currencies)
3.  [稳定币标准化](#3-稳定币标准化)
4.  [支持的数据格式](#4-支持的数据格式)
5.  [推荐工作流](#5-推荐工作流)

---

## 1. 命令概览

本工具提供以下核心命令：

-   `init`: 初始化应用环境，创建数据库。
-   `import <file_path>`: 导入新的交易记录文件（支持中英文列名）。
-   `report [options]`: 生成并显示分析报告。
-   `currency <symbol>`: 查看指定币种的详细净盈亏分析。
-   `list-currencies`: 列出所有已交易币种及其净盈亏。

---

## 2. 核心命令详解

### `init`

**作用：**
此命令用于首次配置应用。它会在 `data/` 目录下创建名为 `trading_journal.db` 的SQLite数据库文件，并建立存储交易数据所需的表结构。

**用法：**
```bash
python main.py init
```
**注意：** 此命令只需在第一次使用时运行一次。

---

### `import`

**作用：**
读取指定的Excel文件，解析其中的交易数据，并将其存入数据库。程序会自动处理重复数据，确保每条交易记录的唯一性。同时会自动应用稳定币标准化。

**用法：**
```bash
python main.py import <file_path>
```

**参数：**
-   `<file_path>` (必需): 指向您的交易历史Excel文件的路径。可以是相对路径或绝对路径。

**示例：**
```bash
# 导入位于项目根目录的文件
python main.py import "Binance Spot Trades 2023.xlsx"

# 导入位于其他目录的文件
python main.py import "/Users/me/Downloads/trades.xlsx"
```

**输出：**
导入完成后，终端会显示导入结果，例如：
```
✅ 导入成功!
   新增交易记录: 29 条
   跳过重复记录: 0 条
   总交易记录数: 29 条

📝 稳定币交易对标准化:
   XRPFDUSD -> XRPUSDT
   DOGEFDUSD -> DOGEUSDT
   SOLFDUSD -> SOLUSDT
   BTCFDUSD -> BTCUSDT
```

---

### `report`

**作用：**
生成交易汇总分析报告。

**用法：**
```bash
python main.py report [options]
```

**可选参数 (Options):**
-   `--symbol <SYMBOL>`: 只显示特定交易对的统计 (例如 `BTCUSDT`)。
-   `--days <N>`: 只显示最近N天的数据。

**示例：**
```bash
# 1. 查看所有历史交易的汇总报告 (最常用)
python main.py report

# 2. 查看BTCUSDT的交易表现
python main.py report --symbol BTCUSDT

# 3. 查看最近30天的业绩报告
python main.py report --days 30
```

---

### `currency`

**作用：**
查看指定币种的详细净盈亏分析，包括交易概况、持仓信息、盈亏统计等。

**用法：**
```bash
python main.py currency <SYMBOL> [OPTIONS]
```

**参数：**
-   `<SYMBOL>` (必需): 币种符号，如 BTC、ETH、XRP 等。

**可选参数：**
-   `--details`: 显示该币种的所有交易记录详情，便于核对数据和验证计算结果。

**示例：**
```bash
# 查看XRP的汇总净盈亏分析
python main.py currency XRP

# 查看XRP的所有交易记录详情
python main.py currency XRP --details

# 查看BTC的净盈亏分析
python main.py currency BTC

# 查看BTC的详细交易记录
python main.py currency BTC --details
```

**汇总模式输出示例：**
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

**详细模式输出示例（使用 --details）：**
```
================================================================================
XRP 所有交易记录详情
================================================================================
总共 8 笔交易

序号   日期           交易对          方向   数量              价格           金额           手续费      盈亏      
--------------------------------------------------------------------------------
1    2025-05-23   XRPUSDT      BUY  5037.1000       2.2953       11561.66     0        -         
2    2025-05-23   XRPUSDT      BUY  1676.4000       2.2953       3847.84      0        -         
3    2025-05-23   XRPUSDT      BUY  759.3000        2.2953       1742.82      0        -         
4    2025-05-23   XRPUSDT      BUY  527.2000        2.2953       1210.08      0        -         
5    2025-05-31   XRPUSDT      BUY  1025.1000       2.1258       2179.16      0        -         
6    2025-05-31   XRPUSDT      BUY  472.4000        2.1258       1004.23      0        -         
7    2025-06-08   XRPUSDT      SELL 3153.8000       2.2199       7001.12      0        -153.51   
8    2025-06-08   XRPUSDT      SELL 1594.9000       2.2199       3540.52      0        -77.63    
--------------------------------------------------------------------------------

📊 交易汇总:
  买入次数: 6  |  卖出次数: 2
  总买入量: 9497.5000 XRP
  总卖出量: 4748.7000 XRP
  当前持仓: 4748.8000 XRP
  已实现盈亏: -231.14 USDT
================================================================================
```

**详细模式的优势：**
- 逐笔核对交易数据，确保时间、价格、数量的准确性
- 验证每笔卖出交易的盈亏计算是否合理
- 核实当前持仓数量的计算是否正确
- 检查手续费扣费是否准确

---

### `list-currencies`

**作用：**
列出所有已交易的币种及其基本统计信息，按净盈亏排序。

**用法：**
```bash
python main.py list-currencies
```

**输出示例：**
```
📊 已交易币种列表:
==================================================
BTC      -  13笔交易 - 净盈亏:    2920.40 USDT
DOGE     -   6笔交易 - 净盈亏:       0.00 USDT
FDUSD    -   1笔交易 - 净盈亏:       0.00 USDT
SOL      -   1笔交易 - 净盈亏:       0.00 USDT
XRP      -   8笔交易 - 净盈亏:    -231.14 USDT
```

---

## 3. 稳定币标准化

### 自动标准化

系统会自动将以下稳定币标准化为USDT：
- **FDUSD** → USDT
- **USDC** → USDT  
- **BUSD** → USDT
- **DAI** → USDT

### 解决的问题

**跨稳定币交易问题：**
- ❌ **之前**: 用FDUSD买入XRP，然后用USDT卖出 → 被当作两个不同交易对，无法正确计算盈亏
- ✅ **现在**: 自动标准化为XRPUSDT → 正确计算盈亏

### 标准化示例

```bash
# 原始交易对 → 标准化后
XRPFDUSD → XRPUSDT
ETHUSDC → ETHUSDT
BTCBUSD → BTCUSDT
SOLUDAI → SOLUSDT
```

---

## 4. 支持的数据格式

目前支持从**币安现货**导出的交易历史 `xlsx` 文件，同时支持中英文列名。

### 英文列名（国际版）
- `Date(UTC)`: 交易日期
- `Pair`: 交易对，例如 `BTCUSDT`
- `Side`: `BUY` 或 `SELL`
- `Price`: 成交价格
- `Executed`: 成交量
- `Amount`: 成交额
- `Fee`: 手续费

### 中文列名（中国版）
- `时间`: 交易日期
- `交易对`: 交易对，例如 `BTC/USDT`
- `类型`: `BUY` 或 `SELL`
- `价格`: 成交价格
- `数量`: 成交量
- `成交额`: 成交额
- `手续费`: 手续费
- `手续费结算币种`: 手续费币种

---

## 5. 推荐工作流

我们推荐以下工作流来最大化此工具的价值：

### 📥 1. 定期导入
每周或每月运行一次 `import` 命令，将最新的交易记录同步到您的本地数据库中。

```bash
python main.py import "latest_trades.xlsx"
```

### 📊 2. 整体分析
导入后，首先查看整体表现：

```bash
# 查看所有币种的表现
python main.py list-currencies

# 查看汇总统计
python main.py report
```

### 🔍 3. 币种深入分析
针对感兴趣的币种进行深入分析：

```bash
# 分析表现最好/最差的币种
python main.py currency BTC
python main.py currency XRP
```

### 📈 4. 短期回顾
分析最近的交易表现：

```bash
# 查看最近30天的表现
python main.py report --days 30

# 查看特定交易对的最近表现
python main.py report --symbol BTCUSDT --days 7
```

### 🎯 5. 策略优化
基于分析结果：
- 识别盈利最多的币种和交易策略
- 找出亏损原因并优化
- 调整仓位配置
- 设定止盈止损策略 