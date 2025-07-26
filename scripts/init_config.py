#!/usr/bin/env python3
"""
安全配置文件初始化脚本

帮助用户安全地创建和管理本地配置文件，避免敏感信息泄漏风险。
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    print("🔧 配置文件安全初始化")
    print("=" * 50)
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    
    # 模板文件和目标文件路径
    template_file = config_dir / "config.ini.template"
    target_file = config_dir / "config.ini"
    
    # 检查模板文件
    if not template_file.exists():
        print("❌ 配置模板文件不存在:", template_file)
        return False
    
    # 检查目标文件是否已存在
    if target_file.exists():
        print("⚠️  配置文件已存在:", target_file)
        response = input("是否要覆盖现有配置? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("✅ 保留现有配置文件")
            return True
    
    try:
        # 复制模板文件
        shutil.copy2(template_file, target_file)
        print(f"✅ 配置文件已创建: {target_file}")
        
        # 设置文件权限（仅用户可读写）
        os.chmod(target_file, 0o600)
        print("🔒 配置文件权限已设置为仅用户可访问")
        
        # 显示安全提醒
        print("\n🛡️  安全提醒:")
        print("1. ✅ 配置文件已被 .gitignore 忽略，不会提交到git")
        print("2. ✅ 文件权限已设置，仅当前用户可访问")
        print("3. ⚠️  请在配置文件中填入真实的API密钥和邮箱信息")
        print("4. ⚠️  不要将配置文件发送给他人或上传到公共位置")
        
        # 显示下一步操作
        print(f"\n📝 下一步操作:")
        print(f"1. 编辑配置文件: {target_file}")
        print("2. 填入你的币安API密钥、邮箱设置等信息")
        print("3. 运行 python main.py scheduler start 开始使用")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建配置文件时出错: {e}")
        return False

def check_security():
    """检查安全配置是否正确"""
    print("\n🔍 安全配置检查:")
    
    project_root = Path(__file__).parent.parent
    gitignore_file = project_root / ".gitignore"
    
    # 检查 .gitignore
    if gitignore_file.exists():
        with open(gitignore_file, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
            
        if "config/config.ini" in gitignore_content:
            print("✅ .gitignore 已配置，配置文件不会被提交")
        else:
            print("⚠️  建议在 .gitignore 中添加配置文件忽略规则")
    else:
        print("⚠️  .gitignore 文件不存在")
    
    # 检查现有配置文件
    config_file = project_root / "config" / "config.ini"
    if config_file.exists():
        print("✅ 本地配置文件已存在")
        
        # 检查文件权限
        file_stat = config_file.stat()
        if oct(file_stat.st_mode)[-3:] == '600':
            print("✅ 配置文件权限正确 (600)")
        else:
            print("⚠️  建议设置配置文件权限为 600")
    else:
        print("⚠️  本地配置文件不存在，请运行初始化")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_security()
    else:
        success = main()
        if success:
            check_security() 