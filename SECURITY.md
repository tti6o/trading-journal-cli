# 安全说明 (Security Guide)

## 🔐 敏感信息保护

本项目包含敏感信息配置，为确保安全性，请遵循以下指南：

### ✅ 配置文件安全

**配置文件处理：**
1. `config/config.ini` - **包含敏感信息，永远不应提交到git**
2. `config/config.ini.template` - 安全的配置模板，已提交到git
3. `config/config.ini.backup` - 本地备份文件（如果存在）

### 🚀 首次配置步骤

```bash
# 1. 复制配置模板
cp config/config.ini.template config/config.ini

# 2. 编辑配置文件，填入你的敏感信息
vim config/config.ini  # 或使用其他编辑器

# 3. 运行安全检查
python scripts/security_check.py
```

### 🛡️ 安全检查

在每次提交前，请运行安全检查：

```bash
python scripts/security_check.py
```

该脚本会检查：
- 代码中是否存在硬编码的密钥或密码
- git暂存区是否包含敏感文件
- 是否有异常大的文件

### 📋 .gitignore 保护

以下文件和目录已被配置为永远不提交：

```
# 敏感配置文件
config/config.ini
config.ini
*.ini
!config/*.template

# 数据和日志文件
data/
*.db
*.sqlite3
*.log

# 其他敏感文件
*.key
*.env
.secrets
```

### 🚨 如果意外提交了敏感信息

如果不小心提交了包含敏感信息的文件：

1. **立即更改所有泄露的密钥/密码**
2. **从git历史中移除敏感信息：**

```bash
# 移除单个文件的历史记录
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/config.ini' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作，慎用）
git push origin --force --all
```

3. **通知所有协作者更新他们的本地仓库**

### 🔑 API 密钥安全建议

1. **最小权限原则**: 只给API密钥必要的最小权限
2. **定期轮换**: 定期更新API密钥
3. **监控使用**: 定期检查API密钥的使用情况
4. **分离环境**: 开发、测试、生产环境使用不同的密钥

### 📞 报告安全问题

如果发现安全漏洞或敏感信息泄露，请：

1. **不要**在公开的issue中报告
2. 通过私人方式联系项目维护者
3. 提供详细的问题描述和复现步骤

---

⚠️ **重要提醒**: 永远不要在代码、注释、文档或commit信息中包含真实的密码、API密钥或其他敏感信息。 