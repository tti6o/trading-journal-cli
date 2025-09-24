# 高级功能文档

> 面向高级用户的详细命令参考

## 📋 完整命令列表

### 🔧 核心命令（推荐）
- `setup` - 一键设置工具
- `sync` - 数据同步和统计
- `analyze` - 技术分析

### ⚙️ 基础功能
- `init` - 初始化数据库
- `import` - 导入Excel文件
- `currency` - 查看币种详情
- `list-currencies` - 列出所有交易币种

### 🌐 API功能
```bash
python main.py api test              # 测试API连接
python main.py api sync --days 7    # 同步最近7天数据
python main.py api symbols          # 查看活跃交易对
python main.py api config           # 配置API密钥
```

### 📊 报告功能
```bash
python main.py report summary       # 汇总统计报告
python main.py report list-trades   # 交易记录列表
python main.py report symbols       # 交易对列表
```

### 🔍 技术分析
```bash
python main.py technical run        # 执行技术分析
python main.py technical status     # 查看分析状态
python main.py technical test       # 测试分析组件
```

### 📧 通知功能
```bash
python main.py notification test    # 测试邮件配置
python main.py notification status  # 查看通知状态
```

### ⏰ 调度器
```bash
python main.py scheduler start      # 启动定时同步
python main.py scheduler status     # 查看调度器状态
python main.py scheduler sync-now   # 立即触发同步
```

## 🛠️ 配置文件详解

### config/config.ini 结构
```ini
[binance]
apiKey = YOUR_API_KEY
secret = YOUR_SECRET_KEY

[scheduler]
enabled = true
sync_interval_hours = 4
initial_sync_days = 30

[technical_analysis]
enabled = true
symbols = BTCUSDT,ETHUSDT,ADAUSDT
rsi_period = 14
rsi_oversold = 30
rsi_overbought = 70

[email]
enabled = true
smtp_server = smtp.gmail.com
smtp_port = 587
from_email = your_email@gmail.com
password = your_app_password
to_emails = recipient@email.com
```

## 📈 高级分析功能

### 单币种详细分析
```bash
python main.py currency BTC --details
```

### 按时间筛选交易
```bash
python main.py report list-trades --since 2024-01-01 --symbol BTCUSDT
```

### 技术分析参数调整
```bash
python main.py technical run --symbols BTCUSDT,ETHUSDT --interval 1h
```

## 🔄 定时同步配置

### 启动后台调度器
```bash
python main.py scheduler start
```

### 配置同步间隔
编辑 `config/config.ini`：
```ini
[scheduler]
sync_interval_hours = 2  # 每2小时同步一次
```

## 📧 邮件通知设置

### Gmail配置示例
1. 启用两步验证
2. 生成应用专用密码
3. 配置config.ini：
```ini
[email]
smtp_server = smtp.gmail.com
smtp_port = 587
from_email = your_email@gmail.com
password = your_app_password
to_emails = recipient@email.com
```

## 🚨 故障排除

### 常见错误及解决方案

**API连接失败**
```bash
python main.py api test  # 检查API配置
```

**数据库问题**
```bash
python main.py init --force  # 重新初始化数据库
```

**技术分析失败**
```bash
python main.py technical test  # 测试分析组件
```

## 🔧 开发者选项

### 调试模式
设置环境变量：
```bash
export DEBUG=1
python main.py sync
```

### 自定义数据源
扩展 `exchange_client/` 目录下的客户端实现

### 添加新技术指标
修改 `services/technical_analysis.py`

## 🔍 数据验证工具

### 独立数据核对验证
为确保API同步数据的准确性，项目提供了独立的验证工具：

```bash
python verify_trades.py
```

**验证原理：**
- 对比币安官方导出的CSV文件与数据库记录
- 自动处理稳定币标准化（FDUSD/USDC → USDT）
- 容错匹配：允许±5分钟时间差异
- 完全独立实现，避免代码逻辑污染

**验证过程：**
1. **时区处理**：CSV的UTC时间自动转换为本地时间（UTC+8）
2. **稳定币映射**：XRPFDUSD ↔ XRPUSDT，ETHUSDC ↔ ETHUSDT
3. **智能匹配**：基于时间、交易对、数量、价格四维度匹配
4. **准确率报告**：显示匹配、差异、缺失记录的详细统计

**使用场景：**
- API同步后验证数据完整性
- 发现稳定币处理逻辑问题
- 时区转换准确性检查
- 交易记录缺失排查

**验证结果示例：**
```
✅ 完全匹配: 48 条
⚠️  数据差异: 0 条
📄 仅CSV存在: 0 条
🗄️ 仅数据库存在: 0 条
📈 数据准确率: 100.0%
```

**获取CSV文件：**
1. 登录币安网页版
2. 资产 → 交易历史 → 导出历史成交记录
3. 选择时间范围，导出CSV格式
4. 将文件放到 `user_data/` 目录

### 验证发现的问题案例

**时区处理问题（已修复）：**
- 初期验证显示0%匹配率
- 发现API存储的是本地时间，CSV是UTC时间
- 解决方案：CSV时间转换为本地时间进行对比

**稳定币标准化验证：**
- 验证了FDUSD→USDT的1:1转换准确性
- 确认了交易对名称标准化的正确性
- 数量、价格、金额完全匹配

---

💡 **提示**: 大部分情况下，使用核心命令就足够了。这些高级功能适合需要精细控制的场景。