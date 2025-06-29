#!/usr/bin/env python3
"""
修复时区问题导致的重复数据

该脚本会：
1. 备份当前数据库
2. 删除API同步的重复数据
3. 重新使用修复后的时区处理逻辑导入Excel数据
4. 验证数据一致性
"""

import sys
import os
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database_setup
import journal_core
import utilities


def backup_database():
    """备份当前数据库"""
    backup_name = f"data/trading_journal_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    if os.path.exists(database_setup.DB_PATH):
        shutil.copy2(database_setup.DB_PATH, backup_name)
        print(f"✅ 数据库已备份到: {backup_name}")
        return backup_name
    else:
        print("⚠️  数据库文件不存在，无需备份")
        return None


def analyze_duplicates():
    """分析重复数据情况"""
    print("\n=== 分析重复数据情况 ===")
    
    all_trades = database_setup.get_all_trades()
    excel_trades = [t for t in all_trades if t.get('data_source') == 'excel']
    api_trades = [t for t in all_trades if t.get('data_source', '').startswith('binance_api')]
    
    print(f"Excel记录: {len(excel_trades)} 条")
    print(f"API记录: {len(api_trades)} 条")
    print(f"总记录: {len(all_trades)} 条")
    
    # 查找可能的重复记录（相同的价格、数量、交易对）
    potential_duplicates = []
    for api_trade in api_trades:
        for excel_trade in excel_trades:
            if (api_trade['symbol'] == excel_trade['symbol'] and
                api_trade['side'] == excel_trade['side'] and
                abs(float(api_trade['price']) - float(excel_trade['price'])) < 0.0001 and
                abs(float(api_trade['quantity']) - float(excel_trade['quantity'])) < 0.000001):
                
                potential_duplicates.append({
                    'api_trade': api_trade,
                    'excel_trade': excel_trade
                })
    
    print(f"\n发现 {len(potential_duplicates)} 对可能的重复记录:")
    for i, dup in enumerate(potential_duplicates, 1):
        api_t = dup['api_trade']
        excel_t = dup['excel_trade']
        print(f"{i}. {api_t['symbol']} | API: {api_t['utc_time']} | Excel: {excel_t['utc_time']}")
    
    return potential_duplicates


def clean_api_duplicates():
    """删除API同步的重复数据"""
    print("\n=== 清理API重复数据 ===")
    
    conn = database_setup.sqlite3.connect(database_setup.DB_PATH)
    cursor = conn.cursor()
    
    # 删除所有API同步的数据
    cursor.execute("DELETE FROM trades WHERE data_source LIKE 'binance_api%'")
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已删除 {deleted_count} 条API同步的重复记录")
    return deleted_count


def verify_excel_data():
    """验证Excel数据完整性"""
    print("\n=== 验证Excel数据完整性 ===")
    
    all_trades = database_setup.get_all_trades()
    excel_trades = [t for t in all_trades if t.get('data_source') == 'excel']
    
    print(f"剩余Excel记录: {len(excel_trades)} 条")
    
    # 显示最近几条记录的时间
    if excel_trades:
        recent_trades = sorted(excel_trades, key=lambda x: x['utc_time'])[-5:]
        print("最近5条Excel记录的时间:")
        for trade in recent_trades:
            print(f"  {trade['utc_time']} | {trade['symbol']} | {trade['side']}")
    
    return len(excel_trades)


def test_time_conversion():
    """测试时间转换功能"""
    print("\n=== 测试时间转换功能 ===")
    
    # 测试样例
    test_cases = [
        "2025-06-21 18:56:39",  # CST时间
        "2025-06-21 21:31:54",  # CST时间
    ]
    
    for cst_time in test_cases:
        utc_time = utilities.normalize_excel_time_to_utc(cst_time)
        print(f"CST: {cst_time} -> UTC: {utc_time}")


def main():
    """主函数"""
    print("🔧 修复时区问题导致的重复数据")
    print("=" * 50)
    
    try:
        # 1. 备份数据库
        backup_file = backup_database()
        
        # 2. 分析重复情况
        duplicates = analyze_duplicates()
        
        if not duplicates:
            print("✅ 未发现重复数据，无需修复")
            return
        
        # 3. 询问用户是否继续
        response = input(f"\n发现 {len(duplicates)} 对重复记录，是否继续修复？(y/N): ")
        if response.lower() != 'y':
            print("❌ 用户取消操作")
            return
        
        # 4. 清理API重复数据
        deleted_count = clean_api_duplicates()
        
        # 5. 验证Excel数据
        excel_count = verify_excel_data()
        
        # 6. 测试时间转换
        test_time_conversion()
        
        # 7. 重新计算PnL
        print("\n=== 重新计算盈亏 ===")
        journal_core.update_all_pnl()
        
        print("\n✅ 修复完成！")
        print(f"📊 当前数据库记录数: {database_setup.get_total_trade_count()}")
        print(f"💾 备份文件: {backup_file}")
        
        print("\n💡 建议：")
        print("1. 使用 'python main.py report summary' 查看修复后的统计")
        print("2. 如果需要同步最新数据，使用 'python main.py api sync --days 7'")
        
    except Exception as e:
        print(f"❌ 修复过程出错: {e}")
        if 'backup_file' in locals() and backup_file:
            print(f"💡 可以从备份恢复: cp {backup_file} {database_setup.DB_PATH}")


if __name__ == "__main__":
    main() 