# 定时同步功能使用指南

## 功能概述

定时同步功能为交易日志CLI工具增加了自动化的数据同步能力，可以在后台定期从币安API获取最新的交易记录，无需手动操作。

### 核心特性

- **🕐 定时自动同步**: 支持可配置的同步间隔（默认4小时）
- **🧠 智能增量同步**: 只同步上次同步后的新数据，避免重复处理
- **📊 状态管理**: 自动记录同步状态和时间戳
- **🔧 灵活配置**: 通过配置文件轻松调整同步参数
- **📝 详细日志**: 完整的同步过程日志记录
- **🛡️ 错误处理**: 健壮的异常处理和恢复机制

## 快速开始

### 1. 安装依赖

确保已安装APScheduler依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置调度器

编辑 `config.ini` 文件，添加或修改 `[scheduler]` 部分：

```ini
[scheduler]
# 是否启用定时同步功能 (true/false)
enabled = true
# 同步间隔，单位：小时
sync_interval_hours = 4
# 首次同步或找不到上次同步记录时，同步过去多少天的数据
initial_sync_days = 30
```

### 3. 启动定时同步

```bash
# 启动调度器（会持续运行直到手动停止）
python main.py scheduler start
```

### 4. 管理调度器

```bash
# 查看调度器状态
python main.py scheduler status

# 立即触发一次同步
python main.py scheduler sync-now

# 查看当前配置
python main.py scheduler config
```

## 详细功能说明

### 启动调度器

```bash
python main.py scheduler start
```

启动后，调度器会：
1. 读取配置文件中的设置
2. 初始化后台任务调度器
3. 按配置的间隔时间执行同步任务
4. 在控制台和日志文件中记录详细信息

**注意**: 
- 调度器会持续运行，按 `Ctrl+C` 可以优雅退出
- 日志文件保存在 `data/scheduler.log`
- 建议在服务器环境中使用进程管理工具（如systemd、supervisor）来管理调度器

### 查看状态

```bash
python main.py scheduler status
```

显示信息包括：
- 运行状态（运行中/已停止）
- 启用状态（已启用/已禁用）
- 同步间隔设置
- 下次同步时间
- 上次同步时间

### 手动触发同步

```bash
python main.py scheduler sync-now
```

立即执行一次同步任务，不影响定时调度。适用于：
- 测试同步功能
- 紧急数据更新
- 验证配置是否正确

### 配置管理

```bash
python main.py scheduler config
```

查看当前调度器配置。要修改配置，请直接编辑 `config.ini` 文件。

## 配置参数详解

### [scheduler] 部分

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | boolean | true | 是否启用定时同步功能 |
| `sync_interval_hours` | integer | 4 | 同步间隔（小时） |
| `initial_sync_days` | integer | 30 | 首次同步的天数范围 |

### 配置示例

```ini
[scheduler]
# 启用定时同步
enabled = true

# 每2小时同步一次（适合活跃交易者）
sync_interval_hours = 2

# 首次同步获取最近7天的数据
initial_sync_days = 7
```

## 智能同步机制

定时同步采用智能增量同步策略：

1. **首次同步**: 如果没有同步记录，获取最近 `initial_sync_days` 天的数据
2. **增量同步**: 如果有同步记录，只获取上次同步时间之后的新数据
3. **状态记录**: 每次成功同步后，更新同步时间戳到数据库

这种机制的优势：
- 减少API调用次数
- 提高同步效率
- 避免数据重复处理
- 节省网络带宽

## 日志管理

### 日志文件位置

- 调度器日志: `data/scheduler.log`
- 日志格式: `时间戳 - 模块名 - 级别 - 消息`

### 日志级别

- **INFO**: 正常操作信息
- **WARNING**: 警告信息（如配置问题）
- **ERROR**: 错误信息（如同步失败）

### 日志示例

```
2024-01-15 10:00:00,123 - scheduler - INFO - 🕐 开始执行定时同步任务...
2024-01-15 10:00:05,456 - scheduler - INFO - 📅 上次同步时间: 2024-01-15 06:00:00
2024-01-15 10:00:05,457 - scheduler - INFO - 📊 本次增量同步: 1 天
2024-01-15 10:00:30,789 - scheduler - INFO - ✅ 定时同步任务完成!
2024-01-15 10:00:30,790 - scheduler - INFO - 📊 新增交易记录: 5 条
```

## 高级用法

### 在服务器上部署

#### 使用 systemd（推荐）

1. 创建服务文件 `/etc/systemd/system/trading-scheduler.service`:

```ini
[Unit]
Description=Trading Journal Scheduler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/trading_journal_cli
ExecStart=/usr/bin/python3 main.py scheduler start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. 启用并启动服务:

```bash
sudo systemctl enable trading-scheduler
sudo systemctl start trading-scheduler
sudo systemctl status trading-scheduler
```

#### 使用 screen/tmux

```bash
# 使用 screen
screen -S trading-scheduler
python main.py scheduler start
# 按 Ctrl+A, D 分离会话

# 重新连接
screen -r trading-scheduler
```

### 禁用定时同步

如果要临时禁用定时同步，可以：

1. 修改配置文件:
```ini
[scheduler]
enabled = false
```

2. 或者停止调度器进程

### 自定义同步策略

如果需要更复杂的同步策略，可以：

1. 修改 `scheduler.py` 中的 `_do_sync` 方法
2. 调整同步间隔和数据范围
3. 添加额外的业务逻辑

## 故障排除

### 常见问题

1. **调度器启动失败**
   - 检查配置文件格式是否正确
   - 确认API密钥配置是否有效
   - 查看错误日志获取详细信息

2. **同步任务失败**
   - 检查网络连接
   - 验证API密钥权限
   - 确认币安API服务状态

3. **重复数据问题**
   - 系统会自动去重，无需担心
   - 检查数据库完整性

### 调试方法

1. 查看日志文件: `tail -f data/scheduler.log`
2. 手动测试同步: `python main.py scheduler sync-now`
3. 检查数据库状态: `python main.py scheduler status`

## 性能优化

### 推荐配置

- **轻度交易者**: 同步间隔 8-12 小时
- **中度交易者**: 同步间隔 4-6 小时  
- **活跃交易者**: 同步间隔 1-2 小时

### 注意事项

- 过于频繁的同步可能触发API限制
- 建议根据实际交易频率调整同步间隔
- 监控日志确保同步任务正常执行

## 扩展功能

未来可能的扩展方向：

1. **多交易所支持**: 支持其他交易所的定时同步
2. **通知功能**: 同步完成后发送邮件/微信通知
3. **数据分析**: 自动生成定期报告
4. **Web界面**: 提供Web管理界面
5. **集群部署**: 支持分布式部署

## 技术架构

定时同步功能采用模块化设计：

- **scheduler.py**: 调度器核心逻辑
- **database_setup.py**: 元数据存储
- **journal_core.py**: 业务逻辑调用
- **config.ini**: 配置管理

这种设计确保了：
- 关注点分离
- 高内聚，低耦合
- 易于维护和扩展
- 良好的可测试性 