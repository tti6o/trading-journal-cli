#!/usr/bin/env python3
"""
邮件配置诊断和修复脚本

用于诊断和修复邮件通知服务的常见问题
"""

import configparser
import os
import sys
import logging
import time
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.notification import EmailNotificationService

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_config_file() -> Dict[str, Any]:
    """检查配置文件"""
    config_file = 'config/config.ini'
    
    if not os.path.exists(config_file):
        return {
            'status': 'error',
            'message': f'配置文件不存在: {config_file}',
            'suggestion': 'cp config/config.ini.template config/config.ini'
        }
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        if not config.has_section('email'):
            return {
                'status': 'error',
                'message': '配置文件中缺少 [email] 段',
                'suggestion': '请在配置文件中添加邮件配置段'
            }
        
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password']
        missing_fields = []
        
        for field in required_fields:
            if not config.has_option('email', field) or not config.get('email', field):
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'status': 'error',
                'message': f'配置文件中缺少必要字段: {", ".join(missing_fields)}',
                'suggestion': '请完整填写邮件配置信息'
            }
        
        return {
            'status': 'success',
            'message': '配置文件格式正确',
            'config': {
                'smtp_server': config.get('email', 'smtp_server'),
                'smtp_port': config.getint('email', 'smtp_port'),
                'username': config.get('email', 'username'),
                'enabled': config.getboolean('email', 'enabled', fallback=False)
            }
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'读取配置文件失败: {e}',
            'suggestion': '请检查配置文件格式是否正确'
        }


def test_email_connection() -> Dict[str, Any]:
    """测试邮件连接"""
    try:
        service = EmailNotificationService()
        
        if not service.enabled:
            return {
                'status': 'warning',
                'message': '邮件服务未启用',
                'suggestion': '在配置文件中设置 enabled = true'
            }
        
        # 给工作线程一点时间启动
        import time
        time.sleep(0.5)
        
        result = service.test_email_config()
        return {
            'status': 'success' if result['success'] else 'error',
            'message': result['message'],
            'suggestion': '检查SMTP服务器、端口、用户名和密码设置' if not result['success'] else ''
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'测试邮件连接失败: {e}',
            'suggestion': '请检查网络连接和邮件配置'
        }


def get_common_smtp_configs():
    """获取常见邮箱的SMTP配置"""
    return {
        'Gmail': {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'note': '需要生成应用密码，不能使用登录密码'
        },
                 'QQ邮箱': {
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 587,
            'use_tls': True,
            'note': '需要在邮箱设置中开启SMTP服务并获取授权码。注意：QQ邮箱也支持465端口(SSL)'
        },
        '163邮箱': {
            'smtp_server': 'smtp.163.com',
            'smtp_port': 587,
            'use_tls': True,
            'note': '需要开启SMTP服务并使用授权密码'
        },
        'Outlook': {
            'smtp_server': 'smtp-mail.outlook.com',
            'smtp_port': 587,
            'use_tls': True,
            'note': '可以使用登录密码或应用密码'
        }
    }


def disable_email_service():
    """禁用邮件服务（临时解决方案）"""
    config_file = 'config/config.ini'
    
    if not os.path.exists(config_file):
        print("❌ 配置文件不存在，无法禁用邮件服务")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        if not config.has_section('email'):
            config.add_section('email')
        
        config.set('email', 'enabled', 'false')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print("✅ 邮件服务已禁用，重启程序后生效")
        return True
        
    except Exception as e:
        print(f"❌ 禁用邮件服务失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 邮件配置诊断工具")
    print("=" * 50)
    
    # 1. 检查配置文件
    print("\n1. 检查配置文件...")
    config_result = check_config_file()
    
    if config_result['status'] == 'error':
        print(f"❌ {config_result['message']}")
        print(f"💡 建议: {config_result['suggestion']}")
        return
    elif config_result['status'] == 'success':
        print(f"✅ {config_result['message']}")
        config_info = config_result['config']
        print(f"   SMTP服务器: {config_info['smtp_server']}")
        print(f"   端口: {config_info['smtp_port']}")
        print(f"   用户名: {config_info['username']}")
        print(f"   启用状态: {config_info['enabled']}")
    
    # 2. 测试邮件连接
    print("\n2. 测试邮件连接...")
    connection_result = test_email_connection()
    
    if connection_result['status'] == 'error':
        print(f"❌ {connection_result['message']}")
        if connection_result['suggestion']:
            print(f"💡 建议: {connection_result['suggestion']}")
        
        # 提供解决方案
        print(f"\n🔧 可能的解决方案:")
        print(f"1. 检查网络连接")
        print(f"2. 验证SMTP服务器和端口设置")
        print(f"3. 检查用户名和密码（可能需要应用密码）")
        print(f"4. 确认邮箱服务商的SMTP设置")
        
        # 显示常见配置
        print(f"\n📋 常见邮箱SMTP配置:")
        configs = get_common_smtp_configs()
        for provider, config in configs.items():
            print(f"\n{provider}:")
            print(f"  smtp_server = {config['smtp_server']}")
            print(f"  smtp_port = {config['smtp_port']}")
            print(f"  use_tls = {config['use_tls']}")
            print(f"  注意: {config['note']}")
        
        # 特别提示QQ邮箱465端口问题
        config_info = config_result.get('config', {})
        if 'qq.com' in config_info.get('smtp_server', ''):
            print(f"\n⚠️  QQ邮箱特别说明:")
            print(f"  - 如果使用465端口，请确保使用SSL连接")
            print(f"  - 如果使用587端口，请确保使用TLS连接")
            print(f"  - 密码必须是授权码，不能是登录密码")
            print(f"  - 授权码获取：QQ邮箱设置 -> 账户 -> 开启SMTP服务")
        
        # 询问是否禁用邮件服务
        print(f"\n❓ 是否临时禁用邮件服务以避免错误循环？(y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes', 'Y']:
                disable_email_service()
        except KeyboardInterrupt:
            print(f"\n程序已退出")
            
    elif connection_result['status'] == 'success':
        print(f"✅ {connection_result['message']}")
        
                 # 测试发送邮件
        print(f"\n3. 测试发送邮件...")
        print(f"❓ 是否发送测试邮件？(y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice in ['y', 'yes', 'Y']:
                print(f"正在发送测试邮件...")
                service = EmailNotificationService()
                # 停止工作线程以避免循环错误
                if service.running:
                    service.running = False
                    time.sleep(1)  # 等待工作线程停止
                
                result = service.send_test_email()
                if result['success']:
                    print(f"✅ 测试邮件发送成功到: {result['recipient']}")
                    print(f"📧 请检查邮箱收件箱（可能在垃圾邮件文件夹中）")
                else:
                    print(f"❌ 测试邮件发送失败: {result['message']}")
        except KeyboardInterrupt:
            print(f"\n程序已退出")
    
    elif connection_result['status'] == 'warning':
        print(f"⚠️ {connection_result['message']}")
        print(f"💡 建议: {connection_result['suggestion']}")


if __name__ == '__main__':
    main() 