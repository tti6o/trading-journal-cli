#!/usr/bin/env python3
"""
独立交易数据验证工具
用于对比币安导出的CSV文件与数据库记录
完全独立实现，避免复用项目代码逻辑
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta, timezone
import re
import sys
from pathlib import Path
import pytz

def parse_binance_csv(csv_file):
    """解析币安导出的CSV文件"""
    print(f"📁 读取币安CSV文件: {csv_file}")

    # 读取CSV，处理UTF-8 BOM
    df = pd.read_csv(csv_file, encoding='utf-8-sig')

    print(f"📊 CSV文件包含 {len(df)} 条记录")
    print(f"📋 CSV列名: {list(df.columns)}")

    # 标准化数据格式
    trades = []
    utc_tz = pytz.UTC
    local_tz = pytz.timezone('Asia/Shanghai')  # 中国时区 UTC+8

    for _, row in df.iterrows():
        # 解析时间 - CSV是UTC时间，转换为本地时间
        utc_time = pd.to_datetime(row['Date(UTC)']).replace(tzinfo=utc_tz)
        local_time = utc_time.astimezone(local_tz)
        timestamp = local_time.strftime('%Y-%m-%d %H:%M:%S')

        # 解析数量和手续费 (去掉币种后缀)
        executed = float(re.sub(r'[A-Z]+$', '', str(row['Executed'])))
        fee_text = str(row['Fee'])
        fee = 0.0
        if fee_text != '0BNB' and fee_text != 'nan':
            fee = float(re.sub(r'[A-Z]+$', '', fee_text))

        # 解析金额 (去掉币种后缀)
        amount = float(re.sub(r'[A-Z]+$', '', str(row['Amount'])))

        trade = {
            'timestamp': timestamp,
            'symbol': row['Pair'],
            'side': row['Side'].lower(),
            'price': float(row['Price']),
            'quantity': executed,
            'amount': amount,
            'fee': fee,
            'source': 'binance_csv'
        }
        trades.append(trade)

    return trades

def read_database_trades(db_file):
    """读取数据库中的交易记录"""
    print(f"🗄️ 读取数据库: {db_file}")

    if not Path(db_file).exists():
        print(f"❌ 数据库文件不存在: {db_file}")
        return []

    conn = sqlite3.connect(db_file)

    # 查询交易表结构
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 数据库表: {tables}")

    # 查询trades表
    if 'trades' in tables:
        cursor = conn.execute("PRAGMA table_info(trades)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 trades表列: {columns}")

        query = """
        SELECT utc_time as timestamp, symbol, side, price, quantity, quote_quantity as amount, fee
        FROM trades
        ORDER BY utc_time DESC
        """
        df = pd.read_sql_query(query, conn)

        print(f"📊 数据库包含 {len(df)} 条交易记录")

        trades = []
        for _, row in df.iterrows():
            trade = {
                'timestamp': row['timestamp'],
                'symbol': row['symbol'],
                'side': row['side'],
                'price': float(row['price']) if row['price'] else 0.0,
                'quantity': float(row['quantity']) if row['quantity'] else 0.0,
                'amount': float(row['amount']) if row['amount'] else 0.0,
                'fee': float(row['fee']) if row['fee'] else 0.0,
                'source': 'database'
            }
            trades.append(trade)

        conn.close()
        return trades
    else:
        print("❌ 数据库中未找到trades表")
        conn.close()
        return []

def compare_trades(csv_trades, db_trades):
    """对比交易数据"""
    print("\n🔍 开始数据对比分析...")

    # 创建DataFrame便于分析
    csv_df = pd.DataFrame(csv_trades)
    db_df = pd.DataFrame(db_trades)

    print(f"📊 CSV记录数: {len(csv_df)}")
    print(f"📊 数据库记录数: {len(db_df)}")

    # 获取时间范围
    if csv_trades:
        csv_times = [pd.to_datetime(t['timestamp']) for t in csv_trades]
        csv_start = min(csv_times)
        csv_end = max(csv_times)
        current_time = datetime.now()

        print(f"📅 CSV时间范围: {csv_start} 到 {csv_end}")
        print(f"📅 当前时间: {current_time}")

        # 筛选数据库中对应时间范围的记录
        db_in_range = []
        for db_trade in db_trades:
            db_time = pd.to_datetime(db_trade['timestamp'])
            if csv_start <= db_time <= current_time:
                db_in_range.append(db_trade)

        print(f"📊 数据库中时间范围内记录: {len(db_in_range)} 条")
        db_trades = db_in_range

    # 按时间戳和交易对分组对比
    results = {
        'csv_only': [],      # 只在CSV中的记录
        'db_only': [],       # 只在数据库中的记录
        'matches': [],       # 完全匹配的记录
        'differences': []    # 有差异的记录
    }

    # 稳定币映射函数
    def normalize_symbol_for_comparison(symbol):
        """将稳定币交易对标准化为USDT进行对比"""
        stable_coins = ['FDUSD', 'USDC', 'BUSD', 'DAI']
        for stable in stable_coins:
            if symbol.endswith(stable):
                base = symbol[:-len(stable)]
                return f"{base}USDT"
        return symbol

    # 改进的匹配逻辑：考虑稳定币转换和时间差异
    for csv_trade in csv_trades:
        csv_time = pd.to_datetime(csv_trade['timestamp'])
        csv_symbol_normalized = normalize_symbol_for_comparison(csv_trade['symbol'])
        csv_qty = csv_trade['quantity']
        csv_price = csv_trade['price']

        # 查找对应的数据库记录
        matching_db = None
        for db_trade in db_trades:
            db_time = pd.to_datetime(db_trade['timestamp'])
            db_symbol_normalized = normalize_symbol_for_comparison(db_trade['symbol'])
            db_qty = db_trade['quantity']
            db_price = db_trade['price']

            # 匹配条件：标准化后交易对相同、数量相近、价格相近、时间差在5分钟内
            time_diff = abs((csv_time - db_time).total_seconds())
            qty_diff = abs(csv_qty - db_qty)
            price_diff = abs(csv_price - db_price)

            if (csv_symbol_normalized == db_symbol_normalized and
                time_diff <= 300 and  # 5分钟内
                qty_diff < 0.00001 and  # 数量几乎相同
                price_diff < 0.01):  # 价格几乎相同
                matching_db = db_trade
                break

        if matching_db:
            # 检查数值是否匹配
            price_match = abs(csv_trade['price'] - matching_db['price']) < 0.01
            qty_match = abs(csv_trade['quantity'] - matching_db['quantity']) < 0.00001
            amount_match = abs(csv_trade['amount'] - matching_db['amount']) < 0.01

            if price_match and qty_match and amount_match:
                results['matches'].append({
                    'csv': csv_trade,
                    'db': matching_db
                })
            else:
                results['differences'].append({
                    'csv': csv_trade,
                    'db': matching_db,
                    'issues': {
                        'price': not price_match,
                        'quantity': not qty_match,
                        'amount': not amount_match
                    }
                })
        else:
            results['csv_only'].append(csv_trade)

    # 查找只在数据库中的记录
    for db_trade in db_trades:
        db_time = pd.to_datetime(db_trade['timestamp'])
        db_symbol_normalized = normalize_symbol_for_comparison(db_trade['symbol'])
        db_qty = db_trade['quantity']
        db_price = db_trade['price']

        found_in_csv = False
        for csv_trade in csv_trades:
            csv_time = pd.to_datetime(csv_trade['timestamp'])
            csv_symbol_normalized = normalize_symbol_for_comparison(csv_trade['symbol'])
            csv_qty = csv_trade['quantity']
            csv_price = csv_trade['price']

            # 同样的匹配逻辑
            time_diff = abs((csv_time - db_time).total_seconds())
            qty_diff = abs(csv_qty - db_qty)
            price_diff = abs(csv_price - db_price)

            if (csv_symbol_normalized == db_symbol_normalized and
                time_diff <= 300 and  # 5分钟内
                qty_diff < 0.00001 and  # 数量几乎相同
                price_diff < 0.01):  # 价格几乎相同
                found_in_csv = True
                break

        if not found_in_csv:
            results['db_only'].append(db_trade)

    return results

def generate_report(comparison_results):
    """生成验证报告"""
    print("\n" + "="*60)
    print("📋 交易数据验证报告")
    print("="*60)

    matches = len(comparison_results['matches'])
    differences = len(comparison_results['differences'])
    csv_only = len(comparison_results['csv_only'])
    db_only = len(comparison_results['db_only'])

    total_csv = matches + differences + csv_only
    total_db = matches + differences + db_only

    print(f"✅ 完全匹配: {matches} 条")
    print(f"⚠️  数据差异: {differences} 条")
    print(f"📄 仅CSV存在: {csv_only} 条")
    print(f"🗄️ 仅数据库存在: {db_only} 条")
    print(f"📊 CSV总数: {total_csv} 条")
    print(f"📊 数据库总数: {total_db} 条")

    if differences > 0:
        print(f"\n⚠️  发现 {differences} 条数据差异:")
        for i, diff in enumerate(comparison_results['differences'][:10]):
            print(f"\n差异 #{i+1}:")
            csv_trade = diff['csv']
            db_trade = diff['db']
            issues = diff['issues']

            print(f"  CSV:  {csv_trade['timestamp']} {csv_trade['symbol']} {csv_trade['side']} "
                  f"{csv_trade['quantity']:.8f}@{csv_trade['price']:.2f} amt:{csv_trade['amount']:.2f}")
            print(f"  DB:   {db_trade['timestamp']} {db_trade['symbol']} {db_trade['side']} "
                  f"{db_trade['quantity']:.8f}@{db_trade['price']:.2f} amt:{db_trade['amount']:.2f}")

            if issues['price']:
                print(f"  ❌ 价格差异: {abs(csv_trade['price'] - db_trade['price']):.2f}")
            if issues['quantity']:
                print(f"  ❌ 数量差异: {abs(csv_trade['quantity'] - db_trade['quantity']):.8f}")
            if issues['amount']:
                print(f"  ❌ 金额差异: {abs(csv_trade['amount'] - db_trade['amount']):.2f}")

    if matches > 0:
        print(f"\n✅ 完全匹配的记录示例 (前3条):")
        for i, match in enumerate(comparison_results['matches'][:3]):
            csv_trade = match['csv']
            print(f"  {i+1}. {csv_trade['timestamp']} {csv_trade['symbol']} {csv_trade['side']} "
                  f"{csv_trade['quantity']:.8f}@{csv_trade['price']:.2f}")

    if csv_only > 0:
        print(f"\n📄 仅在CSV中存在的记录:")
        print("    ⚠️  这些交易可能在数据库中缺失!")
        for i, trade in enumerate(comparison_results['csv_only'][:10]):
            print(f"  {i+1:2d}. {trade['timestamp']} {trade['symbol']:8} {trade['side']:4} "
                  f"{trade['quantity']:12.8f}@{trade['price']:10.2f} amt:{trade['amount']:10.2f}")

    if db_only > 0:
        print(f"\n🗄️ 仅在数据库中存在的记录:")
        print("    ℹ️  这些可能是API同步的额外数据")
        for i, trade in enumerate(comparison_results['db_only'][:10]):
            print(f"  {i+1:2d}. {trade['timestamp']} {trade['symbol']:8} {trade['side']:4} "
                  f"{trade['quantity']:12.8f}@{trade['price']:10.2f} amt:{trade['amount']:10.2f}")

    # 计算准确率
    if total_csv > 0:
        accuracy = (matches / total_csv) * 100
        print(f"\n📈 数据准确率: {accuracy:.1f}%")

    print("\n" + "="*60)

def main():
    """主函数"""
    csv_file = "/Users/admin/work/projects/src/study/trading-journal-cli/user_data/09419044-96c6-11f0-8c03-0e3291b69067-1.csv"
    db_file = "/Users/admin/work/projects/src/study/trading-journal-cli/data/trading_journal.db"

    print("🔍 独立交易数据验证工具")
    print("=" * 40)

    try:
        # 读取数据
        csv_trades = parse_binance_csv(csv_file)
        db_trades = read_database_trades(db_file)

        if not csv_trades:
            print("❌ CSV文件为空或读取失败")
            return

        if not db_trades:
            print("❌ 数据库为空或读取失败")
            return

        # 对比数据
        results = compare_trades(csv_trades, db_trades)

        # 生成报告
        generate_report(results)

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()