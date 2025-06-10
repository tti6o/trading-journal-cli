# 交易日志 CLI 工具 (Trading Journal CLI) - MVP

## 1. 这是什么？

这是一个轻量级、无需界面的**命令行工具（CLI）**，专为希望通过终端快速分析交易记录的交易者和开发者设计。

它专注于解决一个核心问题：**高效地从币安（Binance）交易历史Excel文件中提取关键业绩指标，帮助你进行快速、数据驱动的交易复盘。**

## 2. 解决了什么问题？

- **告别手动计算：** 无需再手动复制粘贴到Excel表格中计算盈亏、胜率。
- **快速获得洞察：** 只需一两个命令，即可获得本周或历史总体的核心交易表现。
- **专注与轻量：** 没有复杂的Web界面，启动迅速，资源占用极低。
- **建立复盘系统：** 鼓励形成"导入数据 -> 分析报告"的周期性复盘习惯，让你的交易系统不断进化。

## 3. 如何安装？

**前提：** 您的电脑已安装 Python 3.8+。

```bash
# 1. 克隆项目到本地
git clone <项目仓库地址>
cd trading_journal_cli

# 2. 创建并激活Python虚拟环境 (推荐)
python3 -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .\.venv\Scripts\activate  # Windows

# 3. 安装所需依赖
pip install -r requirements.txt
```

## 4. 如何快速使用？ (三步上手)

**第1步：初始化数据库**
首次使用时，运行此命令在 `3_Data/` 目录下创建一个空的数据库文件。
```bash
python 2_Source_Code/main.py init
```
> ✅ 成功提示: "数据库 trading_journal.db 初始化成功！"

**第2步：导入您的交易记录**
将您的币安交易历史Excel文件（例如 `Binance-History.xlsx`）放入项目根目录，然后运行：
```bash
python 2_Source_Code/main.py import Binance-History.xlsx
```
> ✅ 成功提示: "成功导入 150 条新交易，忽略 12 条重复交易。"

**第3步：查看您的第一个报告**
运行以下命令，查看您所有交易的汇总统计报告。
```bash
python 2_Source_Code/main.py report summary
```
> ✅ 你将会在终端看到类似这样的格式化报告:
> ```
> --- 交易汇总统计 (截至 2023-10-27) ---
> 总交易周期:    365天
> 总交易笔数:    1,234
>
> === 核心指标 ===
> 总实现盈亏 (USDT):  +15,023.88
> 胜率:               62.50%
> 盈亏比:             2.5 : 1
> ```

---
至此，您已经完成了最核心的用户流程！更详细的用法，请查阅 `1_Project_Docs/USAGE_GUIDE.md`。 