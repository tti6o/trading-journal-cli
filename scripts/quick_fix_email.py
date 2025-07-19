#!/usr/bin/env python3
"""
快速修复邮件循环错误脚本

专门解决邮件工作线程陷入无限循环的问题
"""

import configparser
import os
import sys

def quick_fix_email_loop():
    """快速修复邮件循环错误"""
    config_file = 'config/config.ini'
    
    print("🚀 快速修复邮件循环错误")
    print("=" * 40)
    
    if not os.path.exists(config_file):
        print("❌ 配置文件不存在")
        return False
    
    try:
        # 读取配置
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        # 临时禁用邮件服务
        if not config.has_section('email'):
            config.add_section('email')
        
        original_enabled = config.getboolean('email', 'enabled', fallback=False)
        
        if original_enabled:
            print("🔧 临时禁用邮件服务...")
            config.set('email', 'enabled', 'false')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            print("✅ 邮件服务已暂时禁用")
            print("💡 这将停止邮件循环错误")
            print("📋 修复完成后，可以重新启用邮件服务")
            
            print(f"\n🔄 要重新启用邮件服务，请运行:")
            print(f"   python scripts/quick_fix_email.py --enable")
            
            return True
        else:
            print("ℹ️ 邮件服务已经是禁用状态")
            return True
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def enable_email_service():
    """重新启用邮件服务"""
    config_file = 'config/config.ini'
    
    print("🔄 重新启用邮件服务")
    print("=" * 30)
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        if not config.has_section('email'):
            config.add_section('email')
        
        config.set('email', 'enabled', 'true')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print("✅ 邮件服务已重新启用")
        print("💡 请测试邮件功能是否正常")
        print("🧪 测试命令: python main.py notification test --send")
        
        return True
        
    except Exception as e:
        print(f"❌ 启用失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--enable':
        enable_email_service()
    else:
        quick_fix_email_loop()

if __name__ == '__main__':
    main() 