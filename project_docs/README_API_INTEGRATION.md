# 币安 API 集成功能使用指南

## 🚀 功能概览

本项目新增了币安 API 集成功能，可以自动从币安账户同步交易记录，无需手动导入 Excel 文件。

### 主要特性

- ✅ **自动数据同步**: 通过 API 直接获取交易记录
- ✅ **实时连接测试**: 验证 API 密钥和网络连接
- ✅ **智能去重**: 自动识别并跳过重复的交易记录
- ✅ **数据标准化**: 统一处理不同格式的交易数据
- ✅ **安全性**: 仅需只读权限的 API 密钥
- ✅ **增量同步**: 支持按时间范围同步最新数据

## 📋 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

运行配置向导：
```bash
python main.py api config
```

或者手动配置：
1. 在币安官网创建 API Key（只需要【读取】权限）
2. 创建 `config.ini` 文件：

```ini
[binance]
api_key = 您的API_KEY
api_secret = 您的API_SECRET
```

**⚠️ 重要安全提示:**
- 只给予 API Key 【读取】权限，不要给予交易权限
- 不要在公共场所或版本控制中暴露 API 密钥
- 建议定期更换 API 密钥

### 3. 测试连接

```bash
python main.py api test
```

## 🔧 使用方法

### 基础命令

```bash
# 查看所有 API 相关命令
python main.py api --help

# 测试 API 连接
python main.py api test

# 同步最近 7 天的交易记录
python main.py api sync

# 同步最近 30 天的交易记录
python main.py api sync --days 30

# 查看活跃交易对
python main.py api symbols

# 同步特定交易对
python main.py api sync-symbol BTCUSDT --days 30
```

### 完整工作流程

```bash
# 1. 初始化数据库（首次使用）
python main.py init

# 2. 配置 API 密钥
python main.py api config

# 3. 测试连接
python main.py api test

# 4. 同步交易数据
python main.py api sync --days 30

# 5. 生成报告
python main.py report summary
```

## 📊 数据同步说明

### 同步逻辑

1. **时间范围**: 默认同步最近 7 天的数据，可通过 `--days` 参数调整
2. **自动去重**: 系统会自动识别并跳过已存在的交易记录
3. **数据标准化**: 将 API 数据格式统一为内部标准格式
4. **稳定币处理**: 自动将不同稳定币交易对标准化为 USDT 计价

### 数据来源标识

- Excel 导入的数据: `data_source = 'excel'`
- API 同步的数据: `data_source = 'binance_api_v2'`

### 支持的交易类型

- ✅ 现货交易 (Spot Trading)
- ❌ 合约交易 (Futures Trading) - 暂不支持
- ❌ 期权交易 (Options Trading) - 暂不支持

## 🛠️ 高级功能

### 1. 批量同步特定交易对

```bash
# 同步多个交易对
python main.py api sync-symbol BTCUSDT --days 30
python main.py api sync-symbol ETHUSDT --days 30
python main.py api sync-symbol XRPUSDT --days 30
```

### 2. 定期自动同步

可以设置定时任务自动同步：

```bash
# Linux/Mac - 添加到 crontab
# 每天早上 8 点同步前一天的数据
0 8 * * * cd /path/to/project && python main.py api sync --days 1

# Windows - 使用任务计划程序
# 创建计划任务运行: python main.py api sync --days 1
```

### 3. 监控和日志

```bash
# 查看同步结果
python main.py api sync --days 7

# 查看数据库状态
python main.py report summary

# 查看特定交易对的数据
python main.py report list-trades --symbol BTCUSDT
```

## 🔍 故障排除

### 常见问题

1. **API 连接失败**
   - 检查网络连接
   - 验证 API 密钥是否正确
   - 确认 API 密钥权限设置

2. **同步数据为空**
   - 检查指定时间范围内是否有交易
   - 确认交易对符号是否正确
   - 验证 API 密钥是否有足够权限

3. **数据重复**
   - 系统会自动去重，重复数据会被跳过
   - 可以通过同步结果查看去重统计

### 调试模式

```bash
# 运行测试脚本
python scripts/test_api_integration.py

# 查看详细错误信息
python -c "
import journal_core
result = journal_core.test_binance_api_connection()  # 兼容接口，内部使用新架构
print(result)
"
```

## 📈 性能优化

### 1. API 请求限制

- 系统已启用自动限流，避免触发 API 请求限制
- 建议分批次同步大量历史数据
- 避免频繁调用 API 同步功能

### 2. 数据存储优化

- 使用增量同步，只获取新增数据
- 定期清理过期的测试数据
- 建议定期备份数据库文件

### 3. 网络优化

- 使用稳定的网络连接
- 考虑使用 VPN 改善连接质量
- 避免网络高峰期进行大量同步

## 🔒 安全最佳实践

1. **API 密钥管理**
   - 只给予最小必要权限（只读）
   - 定期更换 API 密钥
   - 不要在代码中硬编码密钥

2. **数据安全**
   - 定期备份交易数据
   - 保护 config.ini 文件不被泄露
   - 使用强密码保护系统账户

3. **访问控制**
   - 限制对配置文件的访问
   - 使用安全的网络环境
   - 定期检查 API 使用日志

## 📞 技术支持

如遇到问题，可以：

1. 查看系统日志和错误信息
2. 运行测试脚本诊断问题
3. 检查 API 密钥配置和权限
4. 验证网络连接和防火墙设置

## 🔄 版本更新

当前版本功能：
- ✅ 基础 API 连接和认证
- ✅ 交易记录同步
- ✅ 数据标准化和去重
- ✅ 多交易对支持
- ✅ 增量同步

计划中的功能：
- 🔄 合约交易支持
- 🔄 实时价格监控
- 🔄 自动化策略分析
- 🔄 风险管理功能 