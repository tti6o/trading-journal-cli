#!/usr/bin/env python3
"""
验证稳定币标准化和XRP计算的脚本
"""

import database_setup
import utilities
from collections import defaultdict

def verify_stable_coin_normalization():
    """验证稳定币标准化是否正确工作"""
    print("=" * 70)
    print("稳定币标准化验证")
    print("=" * 70)
    
    # 获取所有交易记录
    all_trades = database_setup.get_all_trades()
    
    # 统计原始交易对和标准化交易对
    symbol_mapping = defaultdict(set)
    xrp_trades = []
    
    for trade in all_trades:
        if 'XRP' in trade['symbol']:
            xrp_trades.append(trade)
            # 根据原始数据推断可能的映射
            if 'FDUSD' in trade['symbol']:
                symbol_mapping['XRPFDUSD'].add(trade['symbol'])
            elif 'USDT' in trade['symbol']:
                symbol_mapping['XRPUSDT'].add(trade['symbol'])
    
    print("XRP相关交易对标准化:")
    for original, normalized_set in symbol_mapping.items():
        for normalized in normalized_set:
            print(f"  {original} -> {normalized}")
    
    print(f"\n找到 {len(xrp_trades)} 笔XRP交易")
    
    # 分析XRP交易
    print("\nXRP交易详情:")
    print("-" * 70)
    print(f"{'时间':<19} {'交易对':<12} {'方向':<4} {'价格':<10} {'数量':<12} {'金额':<12}")
    print("-" * 70)
    
    total_buy_amount = 0
    total_sell_amount = 0
    total_buy_quantity = 0
    total_sell_quantity = 0
    
    # 按时间排序
    xrp_trades.sort(key=lambda x: x['utc_time'])
    
    for trade in xrp_trades:
        print(f"{trade['utc_time']:<19} {trade['symbol']:<12} {trade['side']:<4} "
              f"{trade['price']:<10.4f} {trade['quantity']:<12.4f} {trade['quote_quantity']:<12.2f}")
        
        if trade['side'] == 'BUY':
            total_buy_amount += trade['quote_quantity']
            total_buy_quantity += trade['quantity']
        else:
            total_sell_amount += trade['quote_quantity']
            total_sell_quantity += trade['quantity']
    
    print("-" * 70)
    print(f"买入汇总: {total_buy_quantity:.4f} XRP，花费 {total_buy_amount:.2f} USDT")
    print(f"卖出汇总: {total_sell_quantity:.4f} XRP，收入 {total_sell_amount:.2f} USDT") 
    print(f"当前持仓: {total_buy_quantity - total_sell_quantity:.4f} XRP")
    
    # 计算加权平均成本
    if total_buy_quantity > 0:
        avg_cost = total_buy_amount / total_buy_quantity
        print(f"平均成本: {avg_cost:.4f} USDT/XRP")
        
        # 计算已实现盈亏
        realized_pnl = total_sell_amount - (total_sell_quantity * avg_cost)
        print(f"已实现盈亏: {realized_pnl:.4f} USDT")
    
    return xrp_trades

def verify_pnl_calculation():
    """验证PnL计算是否正确"""
    print("\n" + "=" * 70)
    print("PnL计算验证")
    print("=" * 70)
    
    # 获取XRP相关的所有交易
    all_trades = database_setup.get_all_trades()
    xrp_trades = [t for t in all_trades if utilities.get_base_currency_from_symbol(t['symbol']) == 'XRP']
    
    print(f"找到 {len(xrp_trades)} 笔XRP交易（标准化后）")
    
    # 使用工具函数计算PnL
    stats = utilities.calculate_currency_pnl(all_trades, 'XRP')
    
    print("\n工具函数计算结果:")
    print(f"  总交易笔数: {stats['total_trades']}")
    print(f"  买入交易: {stats['buy_trades']}")
    print(f"  卖出交易: {stats['sell_trades']}")
    print(f"  总买入数量: {stats['total_buy_quantity']:.4f} XRP")
    print(f"  总卖出数量: {stats['total_sell_quantity']:.4f} XRP")
    print(f"  总买入金额: {stats['total_buy_amount']:.2f} USDT")
    print(f"  总卖出金额: {stats['total_sell_amount']:.2f} USDT")
    print(f"  当前持仓: {stats['current_holding']:.4f} XRP")
    print(f"  已实现盈亏: {stats['total_pnl']:.4f} USDT")
    print(f"  胜率: {stats['win_rate']:.2%}")

def main():
    """主函数"""
    print("开始验证稳定币标准化和计算准确性...")
    
    # 验证稳定币标准化
    xrp_trades = verify_stable_coin_normalization()
    
    # 验证PnL计算
    verify_pnl_calculation()
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)

if __name__ == "__main__":
    main() 