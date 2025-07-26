#!/usr/bin/env python3
"""
交互式配置助手

帮助用户一步步填写配置文件，确保所有必要信息都正确配置。
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 交易系统配置助手")
    print("=" * 50)
    print("我将帮助你填写必要的配置信息")
    
    config_file = Path(__file__).parent.parent / "config" / "config.ini"
    
    if not config_file.exists():
        print("❌ 配置文件不存在，请先运行: python scripts/init_config.py")
        return
    
    print(f"📝 当前配置文件位置: {config_file}")
    print("\n需要配置的关键信息:")
    
    # 1. 币安API配置
    print("\n1️⃣ 币安API配置 (必需)")
    print("   📍 获取地址: https://www.binance.com/cn/my/settings/api-management")
    print("   ⚠️  权限设置: 只需要「现货与杠杆交易」-「启用阅读」即可")
    print("   💡 安全提示: 不要开启「启用交易」权限")
    api_key = input("   请输入API Key: ").strip()
    api_secret = input("   请输入API Secret: ").strip()
    
    # 2. 代理设置
    print("\n2️⃣ 网络代理设置")
    use_proxy = input("   是否需要代理访问币安? (中国大陆通常需要) [y/N]: ").strip().lower()
    proxy_enabled = use_proxy in ['y', 'yes']
    
    proxy_host = "127.0.0.1:7890"  # 默认
    if proxy_enabled:
        proxy_input = input(f"   代理地址 (默认: {proxy_host}): ").strip()
        if proxy_input:
            proxy_host = proxy_input
    
    # 3. 邮箱配置
    print("\n3️⃣ 邮件通知配置")
    setup_email = input("   是否设置邮件通知? [Y/n]: ").strip().lower()
    
    email_config = {}
    if setup_email not in ['n', 'no']:
        print("   支持的邮箱服务:")
        print("   1. Gmail (推荐)")
        print("   2. QQ邮箱")
        print("   3. 163邮箱")
        
        email_choice = input("   选择邮箱服务 [1-3]: ").strip()
        
        if email_choice == '1':
            email_config = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'service': 'Gmail'
            }
            print("   📝 Gmail设置说明:")
            print("      - 需要开启「两步验证」")
            print("      - 密码使用「应用专用密码」而非登录密码")
            print("      - 获取应用专用密码: https://myaccount.google.com/apppasswords")
            
        elif email_choice == '2':
            email_config = {
                'smtp_server': 'smtp.qq.com',
                'smtp_port': 587,
                'service': 'QQ邮箱'
            }
            print("   📝 QQ邮箱设置说明:")
            print("      - 需要在QQ邮箱设置中开启SMTP服务")
            print("      - 密码使用「授权码」而非QQ密码")
            
        elif email_choice == '3':
            email_config = {
                'smtp_server': 'smtp.163.com',
                'smtp_port': 587,
                'service': '163邮箱'
            }
            print("   📝 163邮箱设置说明:")
            print("      - 需要在邮箱设置中开启SMTP服务")
            print("      - 密码使用「客户端授权密码」")
        else:
            email_config = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'service': 'Gmail'
            }
        
        email_username = input(f"   {email_config['service']}用户名: ").strip()
        email_password = input(f"   {email_config['service']}密码/授权码: ").strip()
        notification_email = input("   通知接收邮箱 (可以是同一个): ").strip()
    
    # 4. 监控设置
    print("\n4️⃣ 监控设置")
    analysis_interval = input("   技术分析间隔 (分钟, 默认30): ").strip()
    if not analysis_interval:
        analysis_interval = "30"
    
    print("   推荐监控的交易对: BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT")
    custom_symbols = input("   自定义监控交易对 (逗号分隔, 回车使用推荐): ").strip()
    
    # 5. 应用配置
    print("\n🔄 正在应用配置...")
    
    try:
        # 读取当前配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置项
        content = content.replace("在这里填入你的币安API_KEY", api_key)
        content = content.replace("在这里填入你的币安API_SECRET", api_secret)
        
        # 代理配置
        if proxy_enabled:
            content = content.replace("enabled = true", "enabled = true", 1)
            content = content.replace("http://127.0.0.1:7890", f"http://{proxy_host}")
        else:
            content = content.replace("enabled = true", "enabled = false", 1)
        
        # 邮箱配置
        if email_config:
            content = content.replace("你的邮箱@gmail.com", email_username)
            content = content.replace("你的应用专用密码", email_password)
            content = content.replace("smtp.gmail.com", email_config['smtp_server'])
            content = content.replace("587", str(email_config['smtp_port']))
            content = content.replace("你的邮箱@example.com", notification_email)
        
        # 分析间隔
        content = content.replace("analysis_interval_minutes = 30", f"analysis_interval_minutes = {analysis_interval}")
        
        # 监控交易对
        if custom_symbols:
            content = content.replace("monitored_symbols = BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT,DOTUSDT,LINKUSDT,AVAXUSDT", 
                                    f"monitored_symbols = {custom_symbols}")
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 配置已成功应用!")
        
        # 6. 测试建议
        print(f"\n🧪 测试建议:")
        print("1. 测试API连接: python main.py api test")
        print("2. 测试邮件功能: python main.py notification test --send")
        print("3. 运行技术分析: python main.py technical run")
        print("4. 启动监控系统: python main.py scheduler start")
        
        print(f"\n🎉 配置完成! 现在你可以开始使用交易系统了")
        
    except Exception as e:
        print(f"❌ 配置过程中出现错误: {e}")
        print("请手动编辑配置文件或重新运行此脚本")

if __name__ == "__main__":
    main() 