#!/usr/bin/env python3
"""
定时同步功能测试脚本

用于验证调度器的各项功能是否正常工作。
"""

import sys
import os
import time
import configparser
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import scheduler
from core import database as database_setup
from core import journal as journal_core


def test_config_loading():
    """测试配置文件加载"""
    print("🔧 测试配置文件加载...")
    
    try:
        service = scheduler.SchedulerService()
        print(f"   ✅ 配置加载成功:")
        print(f"      - 启用状态: {service.enabled}")
        print(f"      - 同步间隔: {service.sync_interval_hours} 小时")
        print(f"      - 初始同步天数: {service.initial_sync_days} 天")
        return True
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False


def test_database_metadata():
    """测试数据库元数据功能"""
    print("\n📊 测试数据库元数据功能...")
    
    try:
        # 确保数据库已初始化
        database_setup.init_db()
        
        # 测试设置和获取元数据
        test_key = "test_timestamp"
        test_value = datetime.now().isoformat()
        
        # 设置元数据
        success = database_setup.set_metadata(test_key, test_value)
        if not success:
            print("   ❌ 设置元数据失败")
            return False
        
        # 获取元数据
        retrieved_value = database_setup.get_metadata(test_key)
        if retrieved_value != test_value:
            print(f"   ❌ 元数据不匹配: 期望 {test_value}, 实际 {retrieved_value}")
            return False
        
        # 测试同步时间戳功能
        timestamp_success = database_setup.update_last_sync_timestamp()
        if not timestamp_success:
            print("   ❌ 更新同步时间戳失败")
            return False
        
        last_sync = database_setup.get_last_sync_timestamp()
        if not last_sync:
            print("   ❌ 获取同步时间戳失败")
            return False
        
        print("   ✅ 数据库元数据功能正常")
        print(f"      - 测试元数据: {test_key} = {retrieved_value}")
        print(f"      - 上次同步时间: {last_sync}")
        return True
        
    except Exception as e:
        print(f"   ❌ 数据库元数据测试失败: {e}")
        return False


def test_scheduler_initialization():
    """测试调度器初始化"""
    print("\n⚙️ 测试调度器初始化...")
    
    try:
        service = scheduler.SchedulerService()
        
        if service.scheduler is None and service.enabled:
            print("   ❌ 调度器初始化失败（已启用但调度器为空）")
            return False
        
        if not service.enabled:
            print("   ⚠️ 调度器已禁用，跳过初始化测试")
            return True
        
        print("   ✅ 调度器初始化成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 调度器初始化失败: {e}")
        return False


def test_scheduler_status():
    """测试调度器状态查询"""
    print("\n📋 测试调度器状态查询...")
    
    try:
        service = scheduler.SchedulerService()
        status = service.get_status()
        
        required_keys = ['running', 'enabled', 'sync_interval_hours']
        for key in required_keys:
            if key not in status:
                print(f"   ❌ 状态信息缺少必需字段: {key}")
                return False
        
        print("   ✅ 调度器状态查询正常")
        print(f"      - 运行状态: {status['running']}")
        print(f"      - 启用状态: {status['enabled']}")
        print(f"      - 同步间隔: {status['sync_interval_hours']} 小时")
        if status.get('last_sync'):
            print(f"      - 上次同步: {status['last_sync']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 调度器状态查询失败: {e}")
        return False


def test_manual_sync():
    """测试手动触发同步"""
    print("\n🔥 测试手动触发同步...")
    
    try:
        # 检查API配置是否可用
        manager = journal_core.get_manager()
        connection_test = manager.test_connection()
        
        if not connection_test['success']:
            print(f"   ⚠️ API连接不可用，跳过同步测试: {connection_test['error']}")
            return True
        
        print("   🔄 执行手动同步...")
        service = scheduler.SchedulerService()
        result = service.trigger_sync_now()
        
        if result['success']:
            print(f"   ✅ 手动同步成功: {result['message']}")
        else:
            print(f"   ❌ 手动同步失败: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 手动同步测试失败: {e}")
        return False


def test_scheduler_lifecycle():
    """测试调度器生命周期（启动/停止）"""
    print("\n🔄 测试调度器生命周期...")
    
    try:
        service = scheduler.SchedulerService()
        
        if not service.enabled:
            print("   ⚠️ 调度器已禁用，跳过生命周期测试")
            return True
        
        # 测试启动
        print("   🚀 测试启动调度器...")
        start_success = service.start()
        
        if not start_success:
            print("   ❌ 调度器启动失败")
            return False
        
        # 等待一小段时间确保调度器正常运行
        time.sleep(2)
        
        # 检查状态
        status = service.get_status()
        if not status['running']:
            print("   ❌ 调度器启动后状态显示未运行")
            return False
        
        print("   ✅ 调度器启动成功")
        
        # 测试停止
        print("   🛑 测试停止调度器...")
        service.stop()
        
        # 再次检查状态
        status = service.get_status()
        if status['running']:
            print("   ❌ 调度器停止后状态显示仍在运行")
            return False
        
        print("   ✅ 调度器停止成功")
        return True
        
    except Exception as e:
        print(f"   ❌ 调度器生命周期测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 定时同步功能测试开始")
    print("=" * 50)
    
    tests = [
        ("配置文件加载", test_config_loading),
        ("数据库元数据", test_database_metadata),
        ("调度器初始化", test_scheduler_initialization),
        ("调度器状态查询", test_scheduler_status),
        ("手动触发同步", test_manual_sync),
        ("调度器生命周期", test_scheduler_lifecycle),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ 测试 '{test_name}' 发生异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🧪 测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！定时同步功能工作正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查配置和环境。")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 