# 技术分析和通知设置指南

本指南将帮助您设置和运行定时技术分析功能，包括信号检测和邮件通知。

## 📋 功能概述

- **定时技术分析**: 自动分析多个交易对的技术指标
- **智能信号检测**: 基于多种技术指标的交叉信号
- **邮件通知**: 发现高置信度信号时自动发送邮件
- **可配置规则**: 灵活的指标和规则配置
- **市场摘要**: 提供整体市场情绪分析

## 🚀 快速开始

### 1. 复制配置文件

```bash
cp config/config.ini.template config/config.ini
```

### 2. 配置技术分析

编辑 `config/config.ini` 文件：

```ini
[technical_analysis]
# 启用技术分析
enabled = true
# 分析间隔（分钟）
analysis_interval_minutes = 60
# 监控的交易对（用逗号分隔）
monitored_symbols = BTCUSDT,ETHUSDT,ADAUSDT,BNBUSDT
# K线数据间隔
kline_interval = 1h
# K线数据数量
kline_limit = 200
# 是否自动检测历史交易对
auto_detect_symbols = true
# 置信度阈值（只有高于此值的信号才会发送通知）
confidence_threshold = 0.6
# 通知收件人邮箱（用逗号分隔）
notification_recipients = your_email@example.com
```

### 3. 配置邮件通知

```ini
[email]
# 启用邮件通知
enabled = true
smtp_server = smtp.gmail.com
smtp_port = 587
username = your_email@gmail.com
password = your_app_password
use_tls = true
sender_name = 交易信号助手
```

### 4. 配置调度器

```ini
[scheduler]
# 启用调度器
enabled = true
# 数据同步间隔（小时）
sync_interval_hours = 4
# 初始同步天数
initial_sync_days = 30
```

### 5. 配置交易所API

```ini
[exchange]
name = binance
api_key = your_api_key_here
api_secret = your_api_secret_here
testnet = false
```

## 🔐 邮箱配置详解

### Gmail 配置步骤

1. **启用两步验证**:
   - 登录 Gmail 账户
   - 进入"账户设置" → "安全性"
   - 启用"两步验证"

2. **生成应用密码**:
   - 在"安全性"页面找到"应用密码"
   - 选择"邮件"和"其他设备"
   - 生成16位应用密码
   - 将此密码填入配置文件的 `password` 字段

3. **其他邮箱服务商**:
   ```ini
   # QQ邮箱
   smtp_server = smtp.qq.com
   smtp_port = 587
   
   # 163邮箱
   smtp_server = smtp.163.com
   smtp_port = 25
   
   # Outlook
   smtp_server = smtp-mail.outlook.com
   smtp_port = 587
   ```

## 📊 技术指标配置

### 启用/禁用指标

```ini
[indicators]
# 简单移动平均线
SMA_10_enabled = true
SMA_20_enabled = true
SMA_50_enabled = true
# 指数移动平均线
EMA_12_enabled = true
EMA_26_enabled = true
# RSI
RSI_14_enabled = true
# MACD
MACD_enabled = true
# 布林带
BBANDS_20_enabled = true
# 成交量移动平均
volume_SMA_20_enabled = true
```

### 信号规则配置

```ini
[signal_rules]
# 移动平均交叉
ma_cross_enabled = true
ma_cross_weight = 1.0
# RSI反转
rsi_reversal_enabled = true
rsi_reversal_weight = 0.8
# MACD交叉
macd_cross_enabled = true
macd_cross_weight = 0.9
# 布林带突破
bollinger_bands_enabled = true
bollinger_bands_weight = 0.7
# 成交量确认
volume_confirmation_enabled = true
volume_confirmation_weight = 0.5
```

## 🎯 信号规则说明

### 1. 移动平均交叉 (MA Cross)
- **买入信号**: 快线(MA10)上穿慢线(MA20)
- **卖出信号**: 快线(MA10)下穿慢线(MA20)
- **置信度**: 基于交叉幅度计算

### 2. RSI反转 (RSI Reversal)
- **买入信号**: RSI从超卖区域(≤30)向上突破
- **卖出信号**: RSI从超买区域(≥70)向下突破
- **置信度**: 基于RSI偏离程度计算

### 3. MACD交叉 (MACD Cross)
- **买入信号**: MACD线上穿信号线(金叉)
- **卖出信号**: MACD线下穿信号线(死叉)
- **置信度**: 基于柱状图变化幅度计算

### 4. 布林带突破 (Bollinger Bands)
- **买入信号**: 价格从下轨反弹
- **卖出信号**: 价格从上轨回落
- **置信度**: 基于突破幅度计算

### 5. 成交量确认 (Volume Confirmation)
- **信号**: 成交量放大1.5倍以上
- **作用**: 为其他信号提供确认
- **权重**: 通常设置较低(0.5)

## 🚀 运行方式

### 1. 测试配置

```bash
# 测试技术分析功能
python scripts/run_technical_analysis.py
```

### 2. 启动定时服务

```bash
# 方式1: 直接运行调度器模块
python -m services.scheduler

# 方式2: 使用启动脚本
python scripts/start_scheduler.py
```

### 3. 手动触发分析

```python
from services.signal_engine import get_signal_engine

# 获取信号引擎
engine = get_signal_engine()

# 执行一次分析
result = engine.run_analysis()
print(result)
```

## 📈 监控和日志

### 日志文件位置

- **调度器日志**: `data/scheduler.log`
- **应用日志**: 控制台输出

### 日志级别配置

```ini
[logging]
level = INFO
file_enabled = true
console_enabled = true
```

### 监控指标

- 分析交易对数量
- 发现信号数量
- 通知发送状态
- 市场情绪指标
- 组件健康状态

## 🔧 故障排除

### 常见问题

1. **信号引擎未启用**
   - 检查 `[technical_analysis]` 配置段是否存在
   - 确认 `enabled = true`

2. **邮件发送失败**
   - 检查邮箱配置和应用密码
   - 运行邮件配置测试: `notification_service.test_email_config()`

3. **交易所连接失败**
   - 检查API密钥配置
   - 确认网络连接正常

4. **数据获取失败**
   - 检查交易对符号是否正确
   - 确认交易所API限制

### 调试命令

```bash
# 测试所有组件
python -c "
from services.signal_engine import get_signal_engine
engine = get_signal_engine()
print(engine.test_components())
"

# 检查信号引擎状态
python -c "
from services.signal_engine import get_signal_engine
engine = get_signal_engine()
print(engine.get_status())
"
```

## 📧 邮件通知示例

收到的邮件通知包含以下信息：

- **信号概览**: 交易对、信号类型、置信度
- **技术指标**: 当前各项指标数值
- **触发规则**: 具体触发的信号规则
- **市场摘要**: 整体市场情绪分析

## ⚙️ 高级配置

### 自定义分析间隔

```ini
# 高频分析 (15分钟)
analysis_interval_minutes = 15

# 低频分析 (4小时)
analysis_interval_minutes = 240
```

### 多时间周期分析

```ini
# 使用不同K线间隔
kline_interval = 15m  # 15分钟
kline_interval = 4h   # 4小时
kline_interval = 1d   # 日线
```

### 置信度阈值调整

```ini
# 保守策略 (只接收高置信度信号)
confidence_threshold = 0.8

# 激进策略 (接收更多信号)
confidence_threshold = 0.4
```

## 📊 性能优化

### 监控交易对数量

- **建议**: 不超过20个交易对
- **原因**: 避免API限制和分析延迟

### 分析间隔设置

- **短期交易**: 15-30分钟
- **中期交易**: 1-4小时  
- **长期投资**: 4-24小时

### 资源使用

- **内存**: 约50-100MB
- **CPU**: 低负载，分析时短暂升高
- **网络**: 取决于监控交易对数量

## 🔄 系统维护

### 定期检查

1. **日志文件大小**: 定期清理旧日志
2. **配置更新**: 根据市场变化调整参数
3. **API密钥**: 确保密钥有效性
4. **邮箱配置**: 检查邮件发送状态

### 备份配置

```bash
# 备份配置文件
cp config/config.ini config/config.ini.backup.$(date +%Y%m%d)
```

---

## 💡 使用建议

1. **从小规模开始**: 先监控2-3个主要交易对
2. **调整阈值**: 根据实际效果调整置信度阈值
3. **组合使用**: 结合多种指标提高信号质量
4. **风险管理**: 技术分析仅供参考，请谨慎投资
5. **持续优化**: 根据市场变化调整策略参数

通过以上配置，您就可以运行一个完整的定时技术分析和通知系统了！ 