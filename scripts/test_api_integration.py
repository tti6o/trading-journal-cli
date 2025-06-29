#!/usr/bin/env python3
"""
测试 Binance API 集成功能

测试内容:
1. API 连接测试
2. 数据同步测试
3. 数据标准化测试
4. 数据库集成测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import journal_core
import database_setup


def test_api_connection():
    """测试 API 连接"""
    print("=" * 60)
    print("🔧 测试 1: API 连接测试")
    print("=" * 60)
    
    try:
        result = journal_core.test_binance_api_connection()
        
        if result['success']:
            print("✅ API 连接成功!")
            print(f"📊 账户资产数量: {result['assets_count']}")
            
            if result['assets_count'] > 0:
                print("\n💰 账户资产情况:")
                for currency, balance in result['account_info']['assets'].items():
                    if balance['total'] > 0.01:
                        print(f"   {currency}: {balance['total']:.6f}")
        else:
            print(f"❌ API 连接失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False
    
    return True


def test_data_sync():
    """测试数据同步"""
    print("\n" + "=" * 60)
    print("📊 测试 2: 数据同步测试")
    print("=" * 60)
    
    try:
        # 同步最近3天的数据
        result = journal_core.sync_binance_trades(days=3)
        
        if result['success']:
            print("✅ 数据同步成功!")
            print(f"📅 同步时间范围: {result['sync_period']}")
            print(f"📊 新增记录: {result['new_count']} 条")
            print(f"⏭️  重复记录: {result['duplicate_count']} 条")
            print(f"📈 总记录数: {result['total_count']} 条")
            
            return result['new_count'] > 0 or result['duplicate_count'] > 0
        else:
            print(f"❌ 数据同步失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 同步测试异常: {e}")
        return False


def test_active_symbols():
    """测试活跃交易对获取"""
    print("\n" + "=" * 60)
    print("🔍 测试 3: 活跃交易对获取")
    print("=" * 60)
    
    try:
        result = journal_core.get_binance_active_symbols()
        
        if result['success']:
            print(f"✅ 成功获取 {result['count']} 个活跃交易对:")
            for symbol in result['symbols'][:10]:  # 只显示前10个
                print(f"   - {symbol}")
            
            if result['count'] > 10:
                print(f"   ... 还有 {result['count'] - 10} 个交易对")
                
            return result['count'] > 0
        else:
            print(f"❌ 获取活跃交易对失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 获取活跃交易对异常: {e}")
        return False


def test_data_normalization():
    """测试数据标准化"""
    print("\n" + "=" * 60)
    print("🔄 测试 4: 数据标准化测试")
    print("=" * 60)
    
    try:
        # 使用新架构测试数据标准化
        from exchange_client.models import Trade, TradeSide
        from decimal import Decimal
        from datetime import datetime
        
        # 创建测试交易对象
        test_trade = Trade(
            id='12345',
            order_id='67890',
            symbol='BTCUSDT',
            side=TradeSide.BUY,
            price=Decimal('45000.0'),
            quantity=Decimal('0.001'),
            quote_quantity=Decimal('45.0'),
            fee=Decimal('0.045'),
            fee_asset='BNB',
            timestamp=datetime.fromtimestamp(1640995200)  # 2022-01-01 00:00:00
        )
        
        # 转换为字典格式
        normalized = test_trade.to_dict()
        
        if normalized:
            print("✅ 数据标准化成功!")
            print(f"📅 时间: {normalized['utc_time']}")
            print(f"📊 交易对: {normalized['symbol']}")
            print(f"📈 方向: {normalized['side']}")
            print(f"💰 价格: {normalized['price']}")
            print(f"📦 数量: {normalized['quantity']}")
            print(f"💵 成交额: {normalized['quote_quantity']}")
            print(f"🏷️  手续费: {normalized['fee']} {normalized['fee_currency']}")
            
            return True
        else:
            print("❌ 数据标准化失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据标准化测试异常: {e}")
        return False


def test_database_integration():
    """测试数据库集成"""
    print("\n" + "=" * 60)
    print("💾 测试 5: 数据库集成测试")
    print("=" * 60)
    
    try:
        # 检查数据库是否存在
        if not database_setup.database_exists():
            print("⚠️  数据库不存在，请先运行 'python main.py init'")
            return False
        
        # 获取数据库统计信息
        total_count = database_setup.get_total_trade_count()
        print(f"📊 数据库总记录数: {total_count}")
        
        # 获取最近的几条记录
        recent_trades = database_setup.get_trades(limit=5)
        
        if recent_trades:
            print(f"📋 最近 {len(recent_trades)} 条交易记录:")
            for trade in recent_trades:
                print(f"   {trade['utc_time']} | {trade['symbol']} | {trade['side']} | {trade['price']:.2f}")
                
            # 检查是否有 API 同步的数据
            api_trades = [t for t in recent_trades if t.get('data_source', '').startswith('binance_api')]
            if api_trades:
                print(f"✅ 发现 {len(api_trades)} 条来自 API 的交易记录")
            else:
                print("ℹ️  暂无来自 API 的交易记录")
                
            return True
        else:
            print("⚠️  数据库中没有交易记录")
            return False
            
    except Exception as e:
        print(f"❌ 数据库集成测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 Binance API 集成功能测试")
    print("=" * 60)
    
    # 运行测试
    tests = [
        ("API 连接测试", test_api_connection),
        ("数据同步测试", test_data_sync),
        ("活跃交易对获取", test_active_symbols),
        ("数据标准化测试", test_data_normalization),
        ("数据库集成测试", test_database_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "✅ 通过" if passed_test else "❌ 失败"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试都通过了！API 集成功能正常运行。")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 