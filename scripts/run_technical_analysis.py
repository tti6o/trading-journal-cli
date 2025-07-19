#!/usr/bin/env python3
"""
技术分析和通知演示脚本

演示如何设置和运行定时技术分析，包括信号检测和邮件通知功能。
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.signal_engine import get_signal_engine
from services.scheduler import SchedulerService
from services.notification import get_notification_service


def test_signal_engine():
    """测试信号引擎功能"""
    print("=" * 60)
    print("🔍 测试信号引擎功能")
    print("=" * 60)
    
    # 获取信号引擎实例
    signal_engine = get_signal_engine()
    
    # 检查状态
    status = signal_engine.get_status()
    print(f"信号引擎状态:")
    print(f"  启用状态: {status['enabled']}")
    print(f"  监控交易对: {status['monitored_symbols_count']} 个")
    print(f"  通知收件人: {status['notification_recipients_count']} 个")
    print(f"  组件就绪: 分析器={status['market_analyzer_ready']}, "
          f"通知={status['notification_service_ready']}, "
          f"交易所={status['exchange_client_ready']}")
    
    if not status['enabled']:
        print("\n⚠️ 信号引擎未启用，请检查配置文件")
        return False
    
    # 测试组件
    print("\n🧪 测试各组件连接...")
    test_results = signal_engine.test_components()
    
    for component, result in test_results.items():
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {status_icon} {component}: {result.get('message', result.get('error', ''))}")
    
    return True


def run_single_analysis():
    """运行单次技术分析"""
    print("\n" + "=" * 60)
    print("📊 执行单次技术分析")
    print("=" * 60)
    
    signal_engine = get_signal_engine()
    
    if not signal_engine.enabled:
        print("❌ 信号引擎未启用")
        return
    
    print("🔄 开始分析...")
    start_time = time.time()
    
    # 执行分析
    result = signal_engine.run_analysis()
    
    execution_time = time.time() - start_time
    
    if result['success']:
        print(f"✅ 分析完成! 耗时: {execution_time:.2f}秒")
        print(f"📈 分析结果:")
        print(f"  分析交易对: {result['analyzed_symbols']} 个")
        print(f"  发现信号: {result['signals_found']} 个")
        print(f"  总信号数: {result['total_signals']} 个")
        print(f"  通知发送: {'已发送' if result['notification_sent'] else '未发送'}")
        
        # 显示市场摘要
        market_summary = result.get('market_summary', {})
        if market_summary:
            print(f"\n📊 市场摘要:")
            print(f"  市场情绪: {market_summary.get('market_sentiment', 'NEUTRAL')}")
            print(f"  买入信号: {market_summary.get('buy_signals', 0)}")
            print(f"  卖出信号: {market_summary.get('sell_signals', 0)}")
            print(f"  中性信号: {market_summary.get('neutral_signals', 0)}")
            print(f"  平均置信度: {market_summary.get('avg_confidence', 0):.2f}")
        
        # 显示高置信度信号详情
        high_confidence_signals = result.get('high_confidence_signals', [])
        if high_confidence_signals:
            print(f"\n🚨 高置信度信号详情:")
            for signal in high_confidence_signals:
                print(f"  {signal.symbol}: {signal.signal_type} "
                      f"(置信度: {signal.confidence:.2f}, 价格: {signal.price:.6f})")
                print(f"    描述: {signal.message}")
                print(f"    触发规则: {len(signal.triggered_rules)} 个")
        else:
            print("\n📊 当前无高置信度信号")
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")


def test_notification():
    """测试通知功能"""
    print("\n" + "=" * 60)
    print("📧 测试邮件通知功能")
    print("=" * 60)
    
    notification_service = get_notification_service()
    
    # 检查通知服务状态
    status = notification_service.get_status()
    print(f"通知服务状态:")
    print(f"  启用状态: {status['enabled']}")
    print(f"  运行状态: {status['running']}")
    print(f"  队列大小: {status['queue_size']}")
    print(f"  配置加载: {status['config_loaded']}")
    
    if not status['enabled']:
        print("\n⚠️ 邮件通知未启用，请检查配置文件")
        return
    
    # 测试邮件配置
    print("\n🧪 测试邮件配置...")
    test_result = notification_service.test_email_config()
    
    if test_result['success']:
        print(f"✅ {test_result['message']}")
    else:
        print(f"❌ {test_result['message']}")


def run_scheduler_demo():
    """演示调度器功能"""
    print("\n" + "=" * 60)
    print("⏰ 调度器功能演示")
    print("=" * 60)
    
    # 创建调度器服务
    scheduler = SchedulerService()
    
    # 检查状态
    status = scheduler.get_status()
    print(f"调度器状态:")
    print(f"  启用状态: {status['enabled']}")
    print(f"  运行状态: {status['running']}")
    print(f"  技术分析: {status['technical_analysis_enabled']}")
    print(f"  同步间隔: {status['sync_interval_hours']} 小时")
    
    if status['technical_analysis_enabled']:
        print(f"  分析间隔: {status['technical_analysis_interval_minutes']} 分钟")
        if status['next_technical_analysis_time']:
            print(f"  下次分析: {status['next_technical_analysis_time']}")
    
    if not status['enabled']:
        print("\n⚠️ 调度器未启用，请检查配置文件")
        return
    
    print(f"\n💡 要启动定时服务，请运行:")
    print(f"   python -m services.scheduler")
    print(f"   或者")
    print(f"   python scripts/start_scheduler.py")


def show_configuration_guide():
    """显示配置指南"""
    print("\n" + "=" * 60)
    print("📋 配置指南")
    print("=" * 60)
    
    print("""
要启用定时技术分析和通知功能，请按以下步骤配置：

1. 📝 复制配置模板文件:
   cp config/config.ini.template config/config.ini

2. ⚙️ 编辑配置文件 config/config.ini:

   [technical_analysis]
   enabled = true                           # 启用技术分析
   analysis_interval_minutes = 60           # 分析间隔（分钟）
   monitored_symbols = BTCUSDT,ETHUSDT     # 监控的交易对
   confidence_threshold = 0.6               # 信号置信度阈值
   notification_recipients = your@email.com # 通知收件人

   [email]
   enabled = true                           # 启用邮件通知
   smtp_server = smtp.gmail.com            # SMTP服务器
   smtp_port = 587                         # SMTP端口
   username = your_email@gmail.com         # 邮箱用户名
   password = your_app_password            # 应用密码
   
   [scheduler]
   enabled = true                           # 启用调度器

3. 🔐 设置邮箱应用密码（以Gmail为例）:
   - 登录Gmail账户
   - 进入"账户设置" -> "安全性"
   - 启用"两步验证"
   - 生成"应用密码"
   - 将应用密码填入配置文件

4. 🚀 启动定时服务:
   python -m services.scheduler

5. 📊 手动测试:
   python scripts/run_technical_analysis.py
""")


def main():
    """主函数"""
    print("🚀 技术分析和通知系统演示")
    print("当前时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # 显示配置指南
        show_configuration_guide()
        
        # 测试信号引擎
        if test_signal_engine():
            # 测试通知功能
            test_notification()
            
            # 运行单次分析
            run_single_analysis()
        
        # 演示调度器功能
        run_scheduler_demo()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 