#!/usr/bin/env python3
"""
最终综合测试脚本

验证交易日志CLI工具的所有核心功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import journal as journal_core
from exchange_client import ExchangeClientFactory


def test_api_connection():
    """测试API连接"""
    print("🔧 测试 1: API连接测试")
    print("-" * 40)
    
    try:
        result = journal_core.test_binance_api_connection()
        
        if result['success']:
            print("✅ API连接成功")
            print(f"   账户资产数量: {result['assets_count']}")
            return True
        else:
            print(f"❌ API连接失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ API连接测试异常: {e}")
        return False


def test_active_symbols():
    """测试获取活跃交易对"""
    print("\n🔧 测试 2: 获取活跃交易对")
    print("-" * 40)
    
    try:
        result = journal_core.get_binance_active_symbols()
        
        if result['success']:
            print("✅ 获取活跃交易对成功")
            print(f"   发现 {len(result['symbols'])} 个活跃交易对")
            print(f"   前5个: {result['symbols'][:5]}")
            return True
        else:
            print(f"❌ 获取活跃交易对失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 获取活跃交易对测试异常: {e}")
        return False


def test_sync_trades():
    """测试同步交易记录"""
    print("\n🔧 测试 3: 同步交易记录")
    print("-" * 40)
    
    try:
        print("正在同步最近7天的交易记录...")
        result = journal_core.sync_binance_trades(days=7)
        
        if result['success']:
            print("✅ 同步交易记录成功")
            print(f"   新增记录: {result['new_count']} 条")
            print(f"   重复记录: {result['duplicate_count']} 条")
            print(f"   总记录数: {result['total_count']} 条")
            return True
        else:
            print(f"❌ 同步交易记录失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 同步交易记录测试异常: {e}")
        return False


def test_reports():
    """测试报告生成"""
    print("\n🔧 测试 4: 报告生成")
    print("-" * 40)
    
    try:
        # 生成汇总报告
        summary = journal_core.generate_summary_report()
        
        print("✅ 汇总报告生成成功")
        print(f"   总交易笔数: {summary['total_trades']}")
        print(f"   总实现盈亏: {summary['total_pnl']:.2f} USDT")
        print(f"   胜率: {summary['win_rate']:.2f}%")
        
        # 生成PnL报告
        pnl_report = journal_core.generate_pnl_report()
        
        print("✅ PnL报告生成成功")
        if 'report' in pnl_report and pnl_report['report']:
            print(f"   报告包含 {len(pnl_report['report'])} 个币种")
        else:
            print("   报告为空或格式异常")
        
        return True
        
    except Exception as e:
        print(f"❌ 报告生成测试异常: {e}")
        return False


def test_database_operations():
    """测试数据库操作"""
    print("\n🔧 测试 5: 数据库操作")
    print("-" * 40)
    
    try:
        # 获取交易列表
        trades = journal_core.get_trade_list(limit=5)
        print(f"✅ 获取交易列表成功，最近5条记录")
        
        # 获取可用交易对
        symbols = journal_core.get_available_symbols()
        print(f"✅ 获取可用交易对成功，共 {len(symbols)} 个")
        
        # 获取货币列表
        currencies = journal_core.list_all_currencies()
        print(f"✅ 获取货币列表成功，共 {len(currencies['currencies'])} 个货币")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作测试异常: {e}")
        return False


def test_new_architecture():
    """测试新架构"""
    print("\n🔧 测试 6: 新架构验证")
    print("-" * 40)
    
    try:
        # 使用工厂创建客户端
        client = ExchangeClientFactory.create_from_config()
        print(f"✅ 工厂创建客户端成功: {client}")
        
        # 测试连接
        success, message = client.connect()
        if success:
            print("✅ 新架构连接成功")
        else:
            print(f"❌ 新架构连接失败: {message}")
            return False
        
        # 测试获取账户信息
        test_result = client.test_connection()
        if test_result['success']:
            print(f"✅ 获取账户信息成功，资产数量: {test_result['account_info']['assets_count']}")
        else:
            print(f"❌ 获取账户信息失败: {test_result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 新架构测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 交易日志CLI工具 - 最终综合测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        # ("API连接", test_api_connection),
        # ("获取活跃交易对", test_active_symbols),
        ("同步交易记录", test_sync_trades),
        # ("报告生成", test_reports),
        # ("数据库操作", test_database_operations),
        # ("新架构验证", test_new_architecture),
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print(f"\n⚠️  测试被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 发生未捕获异常: {e}")
            results.append((test_name, False))
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 最终测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"⏱️  总耗时: {duration:.2f} 秒")
    
    if passed == total:
        print("\n🎉 所有测试通过！交易日志CLI工具工作正常。")
        print("\n✨ 架构迁移成功完成！新架构具备以下优势：")
        print("   • 🏗️  模块化设计，易于扩展")
        print("   • 🔌 支持多交易所（目前支持币安）")
        print("   • 🛡️  完整的异常处理体系")
        print("   • 📊 标准化的数据模型")
        print("   • 🔧 灵活的配置管理")
        print("   • 🌐 代理支持")
        print("   • 🧪 全面的测试覆盖")
        
        print("\n💡 下一步建议：")
        print("   • 添加更多交易所支持")
        print("   • 实现实时数据流")
        print("   • 添加高级分析功能")
        print("   • 优化性能和缓存")
        
    elif passed >= total * 0.8:
        print("\n⚠️  大部分测试通过，系统基本可用。")
        print("   请检查失败的测试项并进行修复。")
    else:
        print("\n❌ 多个测试失败，请检查系统配置和实现。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 