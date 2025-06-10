# 核心业务逻辑设计

本文档详细阐述项目中的核心业务逻辑和算法，特别是关键指标的计算方法。

## 1. 已实现盈亏 (Realized PnL) 计算

为了准确反映交易组合的真实盈利情况，本项目**不采用**简单的先进先出 (FIFO) 方法，而是选择**加权平均成本 (Weighted Average Cost, WAC)** 方法来计算已实现盈亏。该方法更符合频繁交易场景下的成本核算，与币安等主流交易所的计算方式保持一致。

### 1.1 加权平均成本法原理

加权平均成本法通过计算持有仓位的平均买入价格来确定卖出资产时的成本。每当有新的买入交易时，持仓成本会根据新交易的价格和数量进行重新计算。

-   **平均成本 (Average Cost) 的计算公式:**
    \[
    \text{New Avg Cost} = \frac{(\text{Old Quantity} \times \text{Old Avg Cost}) + (\text{New Buy Quantity} \times \text{New Buy Price})}{\text{Old Quantity} + \text{New Buy Quantity}}
    \]

-   **已实现盈亏 (Realized PnL) 的计算公式:**
    \[
    \text{Realized PnL} = (\text{Sell Price} - \text{Current Avg Cost}) \times \text{Sell Quantity}
    \]

### 1.2 计算流程与状态维护

PnL的计算是针对**特定交易对 (Symbol)** 的。因此，在计算过程中，我们需要为每个交易对（例如 'BTCUSDT'）在内存中维护以下状态：

-   `current_quantity`: 当前持有的该资产数量。
-   `average_cost`: 当前持有资产的加权平均成本。

**计算步骤:**

1.  **数据准备:** 从数据库中获取**单个交易对**的所有交易记录，并严格按照交易时间 (`utc_time`) 从早到晚排序。
2.  **初始化:** 对于该交易对，`current_quantity` 和 `average_cost` 初始值都为 0。
3.  **遍历交易:**
    -   **遇到买入 (BUY) 交易:**
        a. 使用上面的"平均成本计算公式"更新 `average_cost`。
        b. 增加 `current_quantity` (`current_quantity += trade.quantity`)。
        c. 这笔买入交易的 `pnl` 字段为 0 或 `NULL`，因为它没有实现盈亏。
    -   **遇到卖出 (SELL) 交易:**
        a. 使用当前的 `average_cost` 作为这笔卖出交易的成本，计算已实现盈亏：`pnl = (trade.price - average_cost) * trade.quantity`。
        b. 将计算出的 `pnl` 值更新到该笔交易记录中。
        c. 减少 `current_quantity` (`current_quantity -= trade.quantity`)。
        d. `average_cost` 在卖出时**保持不变**。
4.  **处理手续费:** 最终的净盈亏需要减去交易产生的手续费。这可以在计算完基础 PnL 后进行调整。

### 1.3 示例

假设有以下 'BTCUSDT' 交易：

1.  `2023-01-01`: BUY 1 BTC @ $20,000
2.  `2023-01-05`: BUY 1 BTC @ $30,000
3.  `2023-01-10`: SELL 1.5 BTC @ $28,000

**计算过程:**

1.  **处理第一笔 BUY:**
    -   `current_quantity` = 1 BTC
    -   `average_cost` = $20,000

2.  **处理第二笔 BUY:**
    -   `new_average_cost` = ((1 * 20000) + (1 * 30000)) / (1 + 1) = $25,000
    -   `current_quantity` = 2 BTC
    -   `average_cost` 更新为 $25,000

3.  **处理第三笔 SELL:**
    -   该笔卖出的成本价为当前的 `average_cost`，即 $25,000。
    -   **已实现 PnL** = ($28,000 - $25,000) * 1.5 = **$4,500**
    -   `current_quantity` = 2 - 1.5 = 0.5 BTC
    -   `average_cost` 仍然是 $25,000，用于后续的卖出交易。

### 1.4 实现位置

该计算逻辑应在 **业务逻辑层 (`journal_core.py`)** 中实现，可能作为一个名为 `calculate_realized_pnl_for_symbol` 的函数。该函数会从数据访问层获取某个交易对的所有交易，按时间排序后执行上述计算逻辑，并最终调用数据访问层的更新函数，将计算出的 PnL 写回数据库。

## 2. 其他核心逻辑 (待补充)

(此部分可用于将来记录其他复杂逻辑，如：年化收益率计算、夏普比率计算等。) 