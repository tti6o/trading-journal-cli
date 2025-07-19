# 技术分析模块使用指南

## 🎯 功能简介

本项目的技术分析模块提供了完整的定时技术分析和通知功能，可以：

- 🔍 **自动监控**多个交易对的技术指标
- 📊 **智能分析**基于多种技术指标的交叉信号
- 📧 **及时通知**发现高置信度信号时自动发送邮件
- ⏰ **定时执行**可配置的分析间隔
- 📈 **市场摘要**提供整体市场情绪分析

## 🚀 快速使用

### 1. 配置系统

```bash
# 复制配置模板
cp config/config.ini.template config/config.ini

# 编辑配置文件，设置：
# - 技术分析参数
# - 邮件通知配置  
# - 监控交易对
# - API密钥等
```

### 2. 测试功能

```bash
# 运行演示脚本，测试所有功能
python scripts/run_technical_analysis.py
```

### 3. 启动定时服务

```bash
# 启动定时调度器
python scripts/start_scheduler.py
```

## 📊 支持的技术指标

| 指标类型 | 具体指标 | 信号类型 |
|---------|---------|----------|
| 移动平均 | SMA(10,20,50), EMA(12,26) | 金叉/死叉 |
| 动量指标 | RSI(14) | 超买/超卖反转 |
| 趋势指标 | MACD(12,26,9) | 金叉/死叉 |
| 波动指标 | 布林带(20,2.0) | 上下轨突破 |
| 成交量 | 成交量SMA(20) | 放量确认 |

## 🎯 信号规则

### 买入信号
- MA10上穿MA20 (金叉)
- RSI从超卖区域(≤30)向上突破
- MACD金叉
- 价格从布林带下轨反弹
- 成交量放大确认

### 卖出信号  
- MA10下穿MA20 (死叉)
- RSI从超买区域(≥70)向下突破
- MACD死叉
- 价格从布林带上轨回落
- 成交量放大确认

## 📧 通知功能

### 邮件内容包含：
- 🚨 信号概览（交易对、类型、置信度）
- 📊 技术指标数值
- 📋 触发的具体规则
- 📈 市场整体摘要

### 支持的邮箱服务：
- Gmail
- QQ邮箱
- 163邮箱
- Outlook
- 其他SMTP服务

## ⚙️ 配置选项

### 核心配置
```ini
[technical_analysis]
enabled = true                    # 启用技术分析
analysis_interval_minutes = 60    # 分析间隔
monitored_symbols = BTCUSDT,ETHUSDT # 监控交易对
confidence_threshold = 0.6        # 信号置信度阈值
notification_recipients = your@email.com # 通知收件人
```

### 指标配置
```ini
[indicators]
SMA_10_enabled = true    # 启用SMA10
RSI_14_enabled = true    # 启用RSI14
MACD_enabled = true      # 启用MACD
# ... 其他指标
```

### 规则权重
```ini
[signal_rules]
ma_cross_weight = 1.0           # 移动平均权重
rsi_reversal_weight = 0.8       # RSI反转权重
macd_cross_weight = 0.9         # MACD交叉权重
bollinger_bands_weight = 0.7    # 布林带权重
volume_confirmation_weight = 0.5 # 成交量权重
```

## 🔧 使用示例

### 手动执行分析
```python
from services.signal_engine import get_signal_engine

# 获取信号引擎
engine = get_signal_engine()

# 执行分析
result = engine.run_analysis()

# 查看结果
print(f"分析了 {result['analyzed_symbols']} 个交易对")
print(f"发现 {result['signals_found']} 个信号")
print(f"市场情绪: {result['market_summary']['market_sentiment']}")
```

### 检查系统状态
```python
# 检查信号引擎状态
status = engine.get_status()
print(f"启用状态: {status['enabled']}")
print(f"监控交易对: {status['monitored_symbols_count']} 个")

# 测试各组件
test_results = engine.test_components()
for component, result in test_results.items():
    print(f"{component}: {result['success']}")
```

## 📁 相关文件

- **配置模板**: `config/config.ini.template`
- **详细指南**: `project_docs/TECHNICAL_ANALYSIS_SETUP.md`
- **演示脚本**: `scripts/run_technical_analysis.py`
- **启动脚本**: `scripts/start_scheduler.py`
- **核心模块**: `services/technical_analysis.py`
- **信号引擎**: `services/signal_engine.py`
- **通知服务**: `services/notification.py`
- **调度器**: `services/scheduler.py`

## 💡 使用建议

1. **从小规模开始**: 先监控2-3个主要交易对
2. **调整参数**: 根据实际效果调整置信度阈值
3. **组合分析**: 结合多种指标提高信号质量
4. **风险管理**: 技术分析仅供参考，请谨慎投资
5. **持续优化**: 根据市场变化调整策略参数

## ⚠️ 重要提醒

- 本系统仅提供技术分析信号，不构成投资建议
- 请结合基本面分析和风险管理
- 建议在模拟环境中测试策略效果
- 投资有风险，决策需谨慎

---

详细配置和使用说明请参考：[技术分析设置指南](TECHNICAL_ANALYSIS_SETUP.md) 