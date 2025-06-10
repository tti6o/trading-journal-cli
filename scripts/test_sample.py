#!/usr/bin/env python3
"""
测试脚本 - 用于验证交易日志CLI工具的各个功能模块

运行此脚本来测试各个组件是否正常工作。
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

def create_sample_data():
    """
    创建示例交易数据用于测试。
    """
    print("创建示例交易数据...")
    
    # 示例交易数据
    sample_trades = [
        {
            'Date(UTC)': '2023-10-01 10:00:00',
            'Pair': 'BTCUSDT',
            'Side': 'BUY',
            'Price': 28000.0,
            'Executed': '0.1 BTC',
            'Amount': 2800.0,
            'Fee': '0.001 BNB'
        },
        {
            'Date(UTC)': '2023-10-02 14:30:00',
            'Pair': 'BTCUSDT',
            'Side': 'BUY',
            'Executed': '0.05 BTC',
            'Price': 29000.0,
            'Amount': 1450.0,
            'Fee': '0.0005 BNB'
        },
        {
            'Date(UTC)': '2023-10-05 16:15:00',
            'Pair': 'BTCUSDT',
            'Side': 'SELL',
            'Price': 30000.0,
            'Executed': '0.08 BTC',
            'Amount': 2400.0,
            'Fee': '2.4 USDT'
        },
        {
            'Date(UTC)': '2023-10-10 09:45:00',
            'Pair': 'ETHUSDT',
            'Side': 'BUY',
            'Price': 1600.0,
            'Executed': '2.0 ETH',
            'Amount': 3200.0,
            'Fee': '0.002 BNB'
        },
        {
            'Date(UTC)': '2023-10-12 11:20:00',
            'Pair': 'ETHUSDT',
            'Side': 'SELL',
            'Price': 1650.0,
            'Executed': '1.5 ETH',
            'Amount': 2475.0,
            'Fee': '2.475 USDT'
        }
    ]
    
    # 创建DataFrame并保存为Excel文件
    df = pd.DataFrame(sample_trades)
    sample_file = 'sample_trades.xlsx'
    df.to_excel(sample_file, index=False)
    
    print(f"✅ 示例交易数据已保存到 {sample_file}")
    return sample_file

def test_modules():
    """
    测试各个模块的基本功能。
    """
    print("\n=== 开始模块功能测试 ===")
    
    try:
        # 测试导入
        print("1. 测试模块导入...")
        import database_setup
        import utilities
        import journal_core
        print("✅ 所有模块导入成功")
        
        # 测试数据库初始化
        print("\n2. 测试数据库初始化...")
        database_setup.init_db()
        print("✅ 数据库初始化成功")
        
        # 测试Excel解析
        print("\n3. 测试Excel解析...")
        sample_file = create_sample_data()
        trades = utilities.parse_binance_excel(sample_file)
        if trades:
            print(f"✅ 成功解析 {len(trades)} 条交易记录")
            print(f"   示例交易: {trades[0]['symbol']} {trades[0]['side']} @ {trades[0]['price']}")
        else:
            print("❌ Excel解析失败")
            return
        
        # 测试数据保存
        print("\n4. 测试数据保存...")
        success_count, ignored_count = database_setup.save_trades(trades)
        print(f"✅ 数据保存成功: {success_count} 条新记录, {ignored_count} 条重复")
        
        # 测试数据查询
        print("\n5. 测试数据查询...")
        all_trades = database_setup.get_trades()
        print(f"✅ 查询到 {len(all_trades)} 条交易记录")
        
        # 测试PnL计算
        print("\n6. 测试PnL计算...")
        symbols = list(set(t['symbol'] for t in all_trades))
        for symbol in symbols:
            pnl_results = utilities.calculate_realized_pnl_for_symbol(all_trades, symbol)
            print(f"   {symbol}: 计算了 {len(pnl_results)} 笔交易的PnL")
        
        # 测试统计计算
        print("\n7. 测试统计计算...")
        # 先模拟一些PnL数据
        for i, trade in enumerate(all_trades):
            if trade['side'] == 'SELL':
                all_trades[i]['pnl'] = 100.0 if i % 2 == 0 else -50.0
            else:
                all_trades[i]['pnl'] = 0.0
        
        stats = utilities.calculate_trade_statistics(all_trades)
        print(f"✅ 统计计算完成: 总PnL={stats['total_pnl']}, 胜率={stats['win_rate']:.2%}")
        
        # 测试报告格式化
        print("\n8. 测试报告格式化...")
        report = utilities.format_summary_report(stats)
        print("✅ 报告格式化成功")
        
        print("\n=== 所有模块测试通过！ ===")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_cli_commands():
    """
    测试CLI命令（需要手动运行）。
    """
    print("\n=== CLI命令测试指南 ===")
    print("请手动运行以下命令来测试CLI功能：")
    print()
    print("1. 初始化数据库:")
    print("   python main.py init")
    print()
    print("2. 导入示例数据:")
    print("   python main.py import sample_trades.xlsx")
    print()
    print("3. 查看汇总报告:")
    print("   python main.py report summary")
    print()
    print("4. 查看交易记录:")
    print("   python main.py report list-trades --limit 10")
    print()
    print("5. 查看可用交易对:")
    print("   python main.py report symbols")

if __name__ == '__main__':
    print("🚀 交易日志CLI工具 - 功能测试")
    print("=" * 50)
    
    # 运行模块测试
    test_modules()
    
    # 显示CLI测试指南
    test_cli_commands()
    
    print("\n" + "=" * 50)
    print("测试完成！如果所有模块测试都通过，说明代码实现正确。")
    print("接下来可以按照CLI命令测试指南手动测试命令行功能。") 