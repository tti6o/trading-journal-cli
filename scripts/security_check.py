#!/usr/bin/env python3
"""
安全检查脚本

在提交代码前检查是否存在敏感信息泄露的风险
"""

import os
import re
import sys

def check_sensitive_patterns():
    """检查代码中的敏感模式"""
    sensitive_patterns = [
        (r'api_key\s*=\s*["\'][^"\']*[a-zA-Z0-9]{30,}["\']', 'API密钥'),
        (r'api_secret\s*=\s*["\'][^"\']*[a-zA-Z0-9]{30,}["\']', 'API密钥'),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', '密码'),
        (r'token\s*=\s*["\'][^"\']*[a-zA-Z0-9]{20,}["\']', 'Token'),
        (r'[a-zA-Z0-9]{64}', '疑似哈希或密钥'),
    ]
    
    issues_found = []
    
    for root, dirs, files in os.walk('.'):
        # 跳过这些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.vscode', 'data']]
        
        for file in files:
            if file.endswith(('.py', '.ini', '.env', '.txt', '.md')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern, desc in sensitive_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # 跳过模板文件和文档中的示例
                            if ('template' in file or 'example' in match.group().lower() or 
                                'your_' in match.group().lower() or 'here' in match.group().lower()):
                                continue
                            issues_found.append({
                                'file': file_path,
                                'type': desc,
                                'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                            })
                except:
                    pass
    
    return issues_found

def check_git_status():
    """检查git状态中是否有敏感文件"""
    import subprocess
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        sensitive_files = []
        for line in result.stdout.split('\n'):
            if line.strip():
                file_path = line[3:].strip()
                if any(pattern in file_path.lower() for pattern in 
                      ['config.ini', '.env', '.key', '.secret', 'password', 'data/']):
                    # 跳过模板文件
                    if not file_path.endswith('.template'):
                        sensitive_files.append(file_path)
        
        return sensitive_files
    except:
        return []

def main():
    """主函数"""
    print("🔍 安全检查开始...")
    print("=" * 50)
    
    # 检查敏感模式
    print("1. 检查敏感信息模式...")
    sensitive_issues = check_sensitive_patterns()
    
    if sensitive_issues:
        print("❌ 发现敏感信息:")
        for issue in sensitive_issues:
            print(f"   📁 {issue['file']}")
            print(f"   🚨 {issue['type']}: {issue['match']}")
            print()
    else:
        print("✅ 未发现敏感信息模式")
    
    # 检查git状态
    print("\n2. 检查git暂存区...")
    sensitive_files = check_git_status()
    
    if sensitive_files:
        print("❌ 发现敏感文件将被提交:")
        for file in sensitive_files:
            print(f"   📁 {file}")
    else:
        print("✅ git暂存区安全")
    
    # 总结
    print("\n" + "=" * 50)
    total_issues = len(sensitive_issues) + len(sensitive_files)
    
    if total_issues > 0:
        print(f"❌ 安全检查失败: 发现 {total_issues} 个问题")
        print("🔧 请修复上述问题后再提交代码")
        sys.exit(1)
    else:
        print("✅ 安全检查通过")
        print("🚀 可以安全提交代码")

if __name__ == '__main__':
    main()
