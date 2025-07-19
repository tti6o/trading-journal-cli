#!/usr/bin/env python3
"""
启动定时技术分析和邮件通知服务

功能：
- 启动定时任务调度器
- 定时执行RSI技术分析
- 自动发送邮件通知
- 提供状态监控和手动触发功能
"""

import sys
import os
import time
import signal
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scheduler import SchedulerService
from services.notification import get_notification_service
from core import database as database_setup
from common.utilities import setup_logging

# 设置日志
logger = logging.getLogger(__name__)


def check_prerequisites():
    """检查运行前提条件"""
    print("🔍 检查运行环境...")
    
    # 检查配置文件
    config_file = 'config/config.ini'
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        print("请复制 config/config.ini.template 为 config/config.ini 并填入您的配置")
        return False
    
    # 检查数据目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('user_data', exist_ok=True)
    
    # 初始化数据库
    try:
        database_setup.init_db()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    # 测试邮件配置
    try:
        notification_service = get_notification_service()
        if notification_service.enabled:
            test_result = notification_service.test_email_config()
            if test_result['success']:
                print("✅ 邮件配置测试成功")
            else:
                print(f"⚠️ 邮件配置测试失败: {test_result['message']}")
                print("邮件通知可能无法正常工作")
        else:
            print("⚠️ 邮件通知已禁用")
    except Exception as e:
        print(f"⚠️ 邮件配置检查失败: {e}")
    
    print("✅ 环境检查完成")
    return True


def print_status(scheduler_service):
    """打印服务状态"""
    status = scheduler_service.get_status()
    
    print("\n" + "="*60)
    print("📊 定时技术分析服务状态")
    print("="*60)
    print(f"🔧 调度器状态: {'🟢 运行中' if status['running'] else '🔴 已停止'}")
    print(f"⚙️ 调度器启用: {'是' if status['enabled'] else '否'}")
    print(f"🕐 数据同步间隔: {status['sync_interval_hours']} 小时")
    print(f"🔍 技术分析启用: {'是' if status['technical_analysis_enabled'] else '否'}")
    
    if status['technical_analysis_enabled']:
        print(f"⏰ 技术分析间隔: {status['technical_analysis_interval_minutes']} 分钟")
        if status['next_technical_analysis_time']:
            next_time = datetime.fromisoformat(status['next_technical_analysis_time'])
            print(f"📅 下次技术分析: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if status['next_sync_time']:
        next_sync = datetime.fromisoformat(status['next_sync_time'])
        print(f"📅 下次数据同步: {next_sync.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if status['last_sync']:
        last_sync = datetime.fromisoformat(status['last_sync'])
        print(f"📋 上次数据同步: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"📈 活跃任务数: {status['jobs_count']}")
    print("="*60)


def signal_handler(signum, frame, scheduler_service):
    """信号处理器，用于优雅退出"""
    print(f"\n接收到退出信号 ({signum})，正在关闭服务...")
    scheduler_service.stop()
    print("👋 服务已安全关闭")
    sys.exit(0)


def interactive_mode(scheduler_service):
    """交互模式"""
    print("\n🎮 进入交互模式 (输入 help 查看命令)")
    
    while True:
        try:
            command = input("\n>>> ").strip().lower()
            
            if command == 'help' or command == 'h':
                print("\n可用命令:")
                print("  status (s)     - 显示服务状态")
                print("  sync           - 立即执行数据同步")
                print("  analysis (a)   - 立即执行技术分析")
                print("  test-email     - 发送测试邮件")
                print("  quit (q)       - 退出程序")
                print("  help (h)       - 显示此帮助")
            
            elif command in ['status', 's']:
                print_status(scheduler_service)
            
            elif command == 'sync':
                print("🔄 正在执行数据同步...")
                result = scheduler_service.trigger_sync_now()
                if result['success']:
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ {result['error']}")
            
            elif command in ['analysis', 'a']:
                print("🔍 正在执行技术分析...")
                scheduler_service._do_technical_analysis()
                print("✅ 技术分析完成")
            
            elif command == 'test-email':
                print("📧 正在发送测试邮件...")
                try:
                    notification_service = get_notification_service()
                    if notification_service.enabled:
                        result = notification_service.send_test_email()
                        if result['success']:
                            print(f"✅ {result['message']}")
                        else:
                            print(f"❌ {result['message']}")
                    else:
                        print("⚠️ 邮件通知已禁用")
                except Exception as e:
                    print(f"❌ 发送测试邮件失败: {e}")
            
            elif command in ['quit', 'q', 'exit']:
                print("👋 正在退出...")
                break
            
            elif command == '':
                continue
            
            else:
                print(f"❓ 未知命令: {command}")
                print("输入 'help' 查看可用命令")
                
        except KeyboardInterrupt:
            print("\n👋 正在退出...")
            break
        except EOFError:
            print("\n👋 正在退出...")
            break
        except Exception as e:
            print(f"❌ 命令执行错误: {e}")


def main():
    """主函数"""
    print("🚀 启动定时技术分析和邮件通知服务")
    print("="*60)
    
    # 设置日志
    setup_logging()
    
    # 检查前提条件
    if not check_prerequisites():
        print("❌ 前提条件检查失败，程序退出")
        sys.exit(1)
    
    try:
        # 创建调度器服务
        scheduler_service = SchedulerService()
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, scheduler_service))
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, scheduler_service))
        
        # 启动调度器
        if scheduler_service.start():
            print("✅ 定时服务启动成功!")
            print_status(scheduler_service)
            
            # 提示用户
            print("\n💡 提示:")
            print("  - 按 Ctrl+C 安全退出程序")
            print("  - 输入命令进行交互操作")
            print("  - 技术分析结果将自动发送邮件通知")
            
            # 进入交互模式
            interactive_mode(scheduler_service)
            
        else:
            print("❌ 定时服务启动失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)
    finally:
        if 'scheduler_service' in locals():
            scheduler_service.stop()
        print("👋 程序已退出")


if __name__ == '__main__':
    main() 