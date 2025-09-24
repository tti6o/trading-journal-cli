# CLAUDE.md

Claude Code 项目协作指南 - 交易日志分析工具

## 🚀 核心命令 (新的简化版本)

### 基本使用流程
```bash
# 1. 首次设置 (一键配置)
python main.py setup

# 2. 智能同步 (自动增量同步+统计)
python main.py sync

# 3. 技术分析 (深度洞察)
python main.py analyze [币种]
```

## 🏗️ 项目架构

### 4层架构设计
- **CLI层** (`main.py`): Click命令行接口，核心3命令工作流
- **业务逻辑层** (`core/journal.py`): 核心交易分析逻辑，PnL计算
- **数据访问层** (`core/database.py`): SQLite数据库操作
- **工具层** (`common/utilities.py`): 通用功能，稳定币标准化等

### 服务模块 (`services/`)
- **技术分析服务** (`technical_analysis.py`): RSI、斐波那契等技术指标
- **通知服务** (`notification.py`): 邮件通知系统
- **调度器** (`scheduler.py`): 定时任务管理
- **信号引擎** (`signal_engine.py`): 交易信号处理

### 交易所客户端 (`exchange_client/`)
- **基础抽象类** (`base.py`): 交易所客户端接口定义
- **币安客户端** (`binance_client.py`): 币安API集成
- **工厂模式** (`factory.py`): 客户端实例化管理

## 📋 开发注意事项

### 命令设计原则
- **功能边界清晰**: setup(配置) / sync(同步+统计) / analyze(技术分析)
- **零思考使用**: 每个命令都有明确的使用场景
- **渐进式复杂度**: 核心命令简单，高级功能在--help-all中

### 代码规范
- 项目使用中文注释，CLI界面支持中英文
- 遵循4层架构模式，避免层级混淆
- 数据安全：所有敏感数据在`.gitignore`中被保护
- 稳定币处理：修改稳定币相关代码时需考虑向后兼容性

### 核心功能特性

#### 稳定币标准化
- 自动将FDUSD、USDC、BUSD等转换为USDT
- 解决跨稳定币交易的计算问题
- 在`common/utilities.py:normalize_stablecoin_pairs()`中实现

#### PnL计算方法
- 使用加权平均成本法计算已实现盈亏
- 支持中英文币安导出格式
- 核心逻辑在`core/journal.py`中实现

#### 智能同步系统 (第五版超级命令)
- **数据同步**: 首次运行自动同步最近30天数据，后续基于上次同步时间进行增量同步
- **统计整合**: sync命令整合了原 `report summary`、`list-currencies`、`currency` 的所有功能
- **分层展示**: 核心指标 → 交易量统计 → 币种分组 → 主要币种详细分析
- **智能筛选**: 自动识别主要币种(交易≥5笔且盈亏≥100 USDT)进行详细分析
- **一键体验**: 从数据同步到完整统计分析的完整工作流，用户只需记住 `python main.py sync`
- 核心实现在 `main.py:sync()` 和 `core/database.py` 中

#### 技术分析系统
- RSI超买超卖分析
- 斐波那契回调扩展分析
- 多指标综合信号评估
- 邮件通知集成

## 📊 数据文件说明

- 数据库文件默认位置: `data/trading_journal.db`
- 支持的导入格式: 币安Excel导出文件（中英文）
- 用户数据目录: `user_data/` (被gitignore保护)
- 配置文件: `config/config.ini` (从template复制)

## 🔧 开发环境设置

### 依赖安装
```bash
pip install -r requirements.txt
```

### 初始化和测试
```bash
# 初始化数据库
python main.py setup

# 测试核心功能
python main.py sync
python main.py analyze
```

### 高级命令 (兼容性保留)
```bash
# 查看所有命令
python main.py --help-all

# 直接使用高级功能
python main.py api test
python main.py technical run
python main.py scheduler start
```

## 💡 重要提醒

1. **优先使用核心3命令** - setup/sync/analyze 覆盖90%使用场景
2. **sync超级命令** - 第五版整合后，一个sync命令涵盖数据同步+完整统计分析
3. **保持向后兼容** - 所有原有命令都保留，只是重新组织
4. **文档简洁性** - README专注快速上手，复杂功能在ADVANCED.md
5. **数据安全优先** - 永远不要提交API密钥或真实交易数据

## 📈 第五版核心改进 (2025.9.21)

### 命令整合优化
- **整合前**: 需要4个命令 (`sync` + `report summary` + `list-currencies` + `currency`)
- **整合后**: 1个超级命令 (`sync` 包含所有功能)
- **效果**: 命令操作次数减少75%，学习成本显著降低

### 技术要点
- **字段匹配修复**: 修正统计函数与显示逻辑的字段名不一致问题
- **数据完整性**: 修复PnL字段更新逻辑，确保统计准确性
- **智能筛选**: 主要币种自动识别，避免信息过载
- **向下兼容**: 保持所有原有API接口不变

---
*本文档随项目命令整合优化更新 (2025)*