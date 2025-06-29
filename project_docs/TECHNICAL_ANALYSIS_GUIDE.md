# 技术分析与通知功能使用指南

本指南详细介绍了交易日志 CLI 工具新增的技术分析和通知功能的配置、使用和原理。

## 🎯 功能概览

技术分析功能为用户提供了以下核心能力：

- **📊 多指标技术分析**: 支持 MA、RSI、MACD、布林带等多种技术指标
- **🚨 智能信号检测**: 基于多指标综合判断，生成买入/卖出信号
- **📧 实时邮件通知**: 自动发送技术分析结果到指定邮箱
- **⏰ 定时自动分析**: 集成到调度器，可定时执行技术分析
- **🎛️ 灵活配置管理**: 支持指标参数、监控交易对等灵活配置

## 🏗️ 架构设计

### 核心组件

1. **技术分析器 (TechnicalAnalyzer)**: 计算各种技术指标
2. **市场分析器 (MarketAnalyzer)**: 管理多个交易对的分析
3. **信号引擎 (SignalEngine)**: 集成分析和通知的核心组件
4. **通知服务 (EmailNotificationService)**: 处理邮件通知
5. **调度器扩展**: 支持定时技术分析任务

### 数据流

```
K线数据获取 → 技术指标计算 → 信号识别 → 通知发送
     ↓              ↓            ↓         ↓
交易所API → pandas DataFrame → 规则引擎 → 邮件队列
```

## ⚙️ 配置说明

### 1. 基础配置 (config.ini)

```ini
[technical_analysis]
# 功能开关
enabled = true
# 分析间隔 (分钟)
analysis_interval_minutes = 60
# K线数据间隔
kline_interval = 1h
# K线数据数量
kline_limit = 200
# 自动检测交易对
auto_detect_symbols = true
# 手动指定交易对
monitored_symbols = BTCUSDT,ETHUSDT,BNBUSDT
# 信号触发条件
min_indicators = 3
confidence_threshold = 0.6
# 通知收件人
notification_recipients = your_email@example.com
```

### 2. 技术指标配置

```ini
[indicators]
# 各指标的启用状态和权重
sma_enabled = true
sma_weight = 1.0
rsi_enabled = true
rsi_weight = 1.2
macd_enabled = true
macd_weight = 1.1
# ... 其他指标
```

### 3. 邮件配置

```ini
[email]
enabled = true
smtp_server = smtp.gmail.com
smtp_port = 587
use_tls = true
username = your_email@gmail.com
password = your_app_password_here
sender_name = 交易分析助手
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包：
- `pandas-ta`: 技术分析库
- `numpy`: 数值计算
- `smtplib`: 邮件发送 (Python 内置)
- `email-validator`: 邮件地址验证

### 2. 配置设置

1. 复制配置模板：
```bash
cp config/config.ini.template config/config.ini
```

2. 编辑配置文件，填入：
   - 币安 API 密钥
   - 邮件账户信息
   - 监控的交易对
   - 技术分析参数

### 3. 初始化数据库

```bash
python main.py init
```

### 4. 测试组件

```bash
# 测试邮件配置
python main.py notification test

# 测试技术分析组件
python main.py technical test
```

## 📋 命令使用

### 技术分析命令

```bash
# 执行技术分析
python main.py technical run

# 查看详细结果
python main.py technical run --verbose

# 查看分析状态
python main.py technical status

# 测试组件
python main.py technical test

# 管理监控交易对
python main.py technical add-symbol BTCUSDT
python main.py technical remove-symbol BTCUSDT
```

### 通知命令

```bash
# 测试邮件配置
python main.py notification test

# 查看通知服务状态
python main.py notification status
```

### 调度器命令 (已扩展)

```bash
# 启动调度器 (包含技术分析)
python main.py scheduler start

# 查看调度器状态
python main.py scheduler status
```

## 🔧 技术指标说明

### 支持的指标

1. **移动平均线 (SMA/EMA)**
   - SMA: 简单移动平均
   - EMA: 指数移动平均
   - 信号: 价格突破、均线交叉

2. **相对强弱指数 (RSI)**
   - 范围: 0-100
   - 超买: > 70
   - 超卖: < 30

3. **MACD**
   - 计算: 快线、慢线、信号线
   - 信号: 金叉、死叉

4. **布林带 (Bollinger Bands)**
   - 上轨、中轨、下轨
   - 信号: 价格触碰上下轨

5. **随机指标 (Stochastic)**
   - %K 和 %D 线
   - 超买超卖信号

6. **成交量分析**
   - 成交量移动平均
   - 成交量放大信号

### 信号生成规则

信号生成基于以下逻辑：

1. **多指标综合**: 至少满足配置的最少指标数量
2. **置信度计算**: 根据触发的指标数量计算置信度
3. **阈值过滤**: 只有置信度超过阈值的信号才会被发送
4. **防重复**: 避免短时间内重复发送相同信号

## 📧 通知系统

### 邮件模板

系统会发送 HTML 格式的邮件，包含：

- 📊 信号概览
- 📈 市场情绪分析
- 💰 具体交易对信号
- 📊 技术指标数值
- ⚠️ 风险提示

### 通知队列

- 使用后台线程处理邮件发送
- 支持多收件人
- 失败重试机制
- 队列状态监控

## 🔄 自动化运行

### 定时任务

调度器现在支持两种定时任务：

1. **数据同步**: 定期从交易所同步交易记录
2. **技术分析**: 定期执行技术分析和信号检测

### 配置示例

```ini
[scheduler]
enabled = true
sync_interval_hours = 4

[technical_analysis]
enabled = true
analysis_interval_minutes = 60
```

这样配置会：
- 每 4 小时同步一次交易数据
- 每 60 分钟执行一次技术分析

## 🛠️ 故障排除

### 常见问题

1. **技术分析失败**
   - 检查 K线数据是否足够 (至少 50 条)
   - 验证交易所 API 连接
   - 查看日志文件 `data/scheduler.log`

2. **邮件发送失败**
   - 验证 SMTP 配置
   - 检查网络连接
   - 确认邮箱密码 (可能需要应用专用密码)

3. **指标计算错误**
   - 确保安装了 `pandas-ta` 库
   - 检查数据格式是否正确
   - 验证指标参数设置

### 调试命令

```bash
# 测试所有组件
python main.py technical test

# 查看详细状态
python main.py technical status --verbose
python main.py notification status
python main.py scheduler status
```

## 📈 性能优化

### 建议配置

1. **监控交易对数量**: 建议不超过 20 个，避免 API 限制
2. **分析间隔**: 建议不少于 30 分钟，避免频繁分析
3. **K线数据量**: 建议 100-500 条，平衡准确性和性能

### 资源使用

- **内存**: 每个交易对约 1-5MB 数据
- **网络**: 取决于监控的交易对数量
- **CPU**: 指标计算相对轻量

## 🔒 安全注意事项

1. **API 密钥**: 确保只使用只读权限的 API 密钥
2. **邮件密码**: 使用应用专用密码，避免使用主密码
3. **配置文件**: 不要将包含敏感信息的配置文件提交到版本控制
4. **网络安全**: 如果使用代理，确保代理服务器安全

## 🚀 未来扩展

可能的功能扩展方向：

1. **更多技术指标**: 支持更多高级技术指标
2. **机器学习**: 集成 AI 模型进行信号预测
3. **多交易所**: 支持更多交易所的数据
4. **实时数据流**: 使用 WebSocket 获取实时数据
5. **Web 界面**: 提供可视化的 Web 管理界面

## 💡 最佳实践

1. **渐进式配置**: 先从少量交易对开始，逐步增加
2. **参数调优**: 根据市场情况调整指标参数
3. **信号验证**: 定期验证信号的准确性
4. **风险控制**: 技术分析仅供参考，投资需谨慎

---

📞 **技术支持**: 如遇问题，请查看日志文件或提交 Issue
⚠️ **免责声明**: 本工具仅用于技术分析参考，不构成投资建议