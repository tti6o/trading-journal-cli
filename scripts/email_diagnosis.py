#!/usr/bin/env python3
"""
邮件系统诊断工具
用于排查邮件发送问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.notification import get_notification_service
import time

def main():
    print("🔍 邮件系统诊断工具")
    print("=" * 50)
    
    # 1. 测试基本连接
    print("\n1. 测试SMTP连接...")
    service = get_notification_service()
    
    if not service.enabled:
        print("❌ 邮件服务未启用")
        return
    
    # 2. 测试连接
    result = service.test_email_config()
    if result['success']:
        print("✅ SMTP连接成功")
    else:
        print(f"❌ SMTP连接失败: {result['message']}")
        return
    
    # 3. 发送简单测试邮件
    print("\n2. 发送简单测试邮件...")
    simple_result = service.send_test_email()
    if simple_result['success']:
        print(f"✅ 简单邮件发送成功到: {simple_result['recipient']}")
    else:
        print(f"❌ 简单邮件发送失败: {simple_result['message']}")
    
    # 4. 等待邮件处理
    print("\n3. 等待邮件处理...")
    time.sleep(5)
    
    # 5. 检查队列状态
    status = service.get_status()
    print(f"邮件队列大小: {status['queue_size']}")
    print(f"工作线程状态: {'活跃' if status['worker_alive'] else '非活跃'}")
    
    # 6. 建议
    print("\n📝 建议检查:")
    print("1. 检查QQ邮箱的收件箱和垃圾邮件文件夹")
    print("2. 检查QQ邮箱是否开启了陌生人邮件过滤")
    print("3. 尝试添加发送邮箱到白名单")
    print("4. 检查QQ邮箱容量是否充足")
    
    print(f"\n✉️  发送邮箱: {service.email_config.username}")
    print(f"📧 收件邮箱: 814718689@qq.com")

if __name__ == "__main__":
    main() 