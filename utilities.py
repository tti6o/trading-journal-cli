# 2_Source_Code/utilities.py
"""
工具 (Utility) 层

- 提供与具体业务无关的、可重用的"纯函数"。
- 例如：文件解析、数据格式转换、单个指标的计算等。
"""
import pandas as pd
from datetime import datetime
import re

# 稳定币列表 - 这些币种将被视为等价
STABLE_COINS = ['USDT', 'USDC', 'FDUSD', 'BUSD', 'DAI']

def normalize_symbol(symbol: str) -> str:
    """
    标准化交易对符号，将稳定币统一为USDT。
    例如: BTCFDUSD -> BTCUSDT, ETHUSDC -> ETHUSDT
    
    :param symbol: 原始交易对符号
    :return: 标准化后的交易对符号
    """
    symbol = symbol.upper()
    
    # 找到基础货币和报价货币
    for stable_coin in STABLE_COINS:
        if symbol.endswith(stable_coin):
            base_currency = symbol[:-len(stable_coin)]
            return f"{base_currency}USDT"
    
    return symbol

def normalize_currency_amount(amount: float, from_currency: str, to_currency: str = 'USDT') -> float:
    """
    标准化货币金额。目前稳定币之间按1:1兑换。
    
    :param amount: 金额
    :param from_currency: 源货币
    :param to_currency: 目标货币
    :return: 转换后的金额
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # 稳定币之间1:1兑换
    if from_currency in STABLE_COINS and to_currency in STABLE_COINS:
        return amount
    
    # 如果不是稳定币转换，暂时返回原值
    return amount

def parse_binance_excel(file_path: str) -> list:
    """
    解析币安导出的交易历史Excel文件。
    支持英文和中文列名，并自动标准化稳定币交易对。
    
    :param file_path: Excel文件路径。
    :return: 一个包含原始交易数据字典的列表。
    """
    try:
        df = pd.read_excel(file_path)
        
        # 定义列名映射（中文->英文）
        column_mapping = {
            # 中文列名
            '时间': 'Date(UTC)',
            '交易对': 'Pair', 
            '类型': 'Side',
            '价格': 'Price',
            '数量': 'Executed',
            '成交额': 'Amount',
            '成交额 ': 'Amount',  # 注意这里可能有空格
            '手续费': 'Fee',
            '手续费结算币种': 'Fee_Currency',
            # 英文列名（保持不变）
            'Date(UTC)': 'Date(UTC)',
            'Pair': 'Pair',
            'Side': 'Side', 
            'Price': 'Price',
            'Executed': 'Executed',
            'Amount': 'Amount',
            'Fee': 'Fee'
        }
        
        # 重命名列
        df_columns = list(df.columns)
        print(f"原始列名: {df_columns}")
        
        # 创建新的列名映射
        new_columns = {}
        for col in df_columns:
            if col in column_mapping:
                new_columns[col] = column_mapping[col]
            else:
                new_columns[col] = col
        
        df = df.rename(columns=new_columns)
        print(f"重命名后列名: {list(df.columns)}")
        
        # 验证必要的列是否存在
        required_columns = ['Date(UTC)', 'Pair', 'Side', 'Price', 'Executed', 'Amount', 'Fee']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"错误: Excel文件缺少必要的列: {missing_columns}")
            print(f"可用的列: {list(df.columns)}")
            return []
        
        # 数据清洗和格式转换
        cleaned_trades = []
        for _, row in df.iterrows():
            try:
                # 处理交易对格式 XRP/FDUSD -> XRPFDUSD
                pair = str(row['Pair']).replace('/', '')
                
                # 标准化交易对（将稳定币统一为USDT）
                normalized_pair = normalize_symbol(pair)
                
                # 获取原始报价货币
                original_quote_currency = None
                for stable_coin in STABLE_COINS:
                    if pair.upper().endswith(stable_coin):
                        original_quote_currency = stable_coin
                        break
                
                # 处理执行数量 - 直接使用数量列的值
                quantity = float(row['Executed'])
                
                # 处理金额 - 标准化为USDT
                original_amount = float(row['Amount'])
                normalized_amount = normalize_currency_amount(
                    original_amount, 
                    original_quote_currency or 'USDT', 
                    'USDT'
                )
                
                # 处理手续费 - 直接使用手续费列的值
                fee = float(row['Fee']) if pd.notna(row['Fee']) else 0.0
                fee_currency = str(row.get('Fee_Currency', 'BNB')) if 'Fee_Currency' in df.columns else 'BNB'
                
                # 标准化时间格式
                utc_time = pd.to_datetime(row['Date(UTC)']).strftime('%Y-%m-%d %H:%M:%S')
                
                # 标准化交易方向
                side = str(row['Side']).upper()
                if side not in ['BUY', 'SELL']:
                    print(f"跳过未知的交易方向: {side}")
                    continue
                
                trade = {
                    'utc_time': utc_time,
                    'symbol': normalized_pair.upper(),  # 使用标准化的交易对
                    'side': side,
                    'price': float(row['Price']),
                    'quantity': quantity,
                    'quote_quantity': normalized_amount,  # 使用标准化的金额
                    'fee': fee,
                    'fee_currency': fee_currency,
                    'original_symbol': pair.upper(),  # 保存原始交易对
                    'original_quote_currency': original_quote_currency or 'USDT'
                }
                cleaned_trades.append(trade)
                
            except (ValueError, IndexError, KeyError) as e:
                print(f"跳过格式错误的交易记录: {e}")
                print(f"问题行数据: {dict(row)}")
                continue
        
        print(f"成功解析 {len(cleaned_trades)} 条交易记录")
        if cleaned_trades:
            print("标准化示例:")
            for trade in cleaned_trades[:3]:
                if trade['original_symbol'] != trade['symbol']:
                    print(f"  {trade['original_symbol']} -> {trade['symbol']}")
        
        return cleaned_trades
        
    except FileNotFoundError:
        print(f"错误: 文件未找到 {file_path}")
        return []
    except Exception as e:
        print(f"解析Excel文件时发生错误: {e}")
        return []

def get_base_currency_from_symbol(symbol: str) -> str:
    """
    从交易对符号中提取基础货币。
    例如: BTCUSDT -> BTC, ETHUSDT -> ETH
    
    :param symbol: 交易对符号
    :return: 基础货币符号
    """
    symbol = symbol.upper()
    
    # 移除已知的报价货币后缀
    quote_currencies = ['USDT', 'USDC', 'FDUSD', 'BUSD', 'BTC', 'ETH', 'BNB']
    
    for quote in quote_currencies:
        if symbol.endswith(quote):
            return symbol[:-len(quote)]
    
    # 如果没有匹配的后缀，返回原符号
    return symbol

def calculate_realized_pnl_for_symbol(trades: list, symbol: str) -> dict:
    """
    使用加权平均成本法为指定交易对计算已实现盈亏。
    
    :param trades: 该交易对的所有交易记录，必须按时间排序
    :param symbol: 交易对符号
    :return: 包含每笔交易PnL的字典
    """
    # 按时间排序确保处理顺序正确
    symbol_trades = [t for t in trades if t['symbol'] == symbol]
    symbol_trades.sort(key=lambda x: x['utc_time'])
    
    current_quantity = 0.0
    average_cost = 0.0
    pnl_results = {}
    
    for trade in symbol_trades:
        # 获取trade_id，如果没有则使用数据库主键id作为fallback
        trade_key = trade.get('trade_id') or trade.get('id')
        if not trade_key:
            # 如果都没有，生成一个临时的key
            import database_setup
            trade_key = database_setup.generate_trade_id(trade)
        
        if trade['side'] == 'BUY':
            # 买入：更新加权平均成本
            if current_quantity > 0:
                # 计算新的加权平均成本
                total_cost = (current_quantity * average_cost) + (trade['quantity'] * trade['price'])
                new_quantity = current_quantity + trade['quantity']
                average_cost = total_cost / new_quantity
            else:
                # 首次买入或重新建仓
                average_cost = trade['price']
            
            current_quantity += trade['quantity']
            pnl_results[trade_key] = 0.0  # 买入交易PnL为0
            
        elif trade['side'] == 'SELL':
            # 卖出：计算已实现盈亏
            if current_quantity > 0:
                base_pnl = (trade['price'] - average_cost) * trade['quantity']
                # 减去手续费（简化处理，假设手续费已折算为报价货币）
                net_pnl = base_pnl - (trade['fee'] if trade['fee_currency'] in STABLE_COINS else 0)
                pnl_results[trade_key] = net_pnl
                current_quantity -= trade['quantity']
            else:
                # 无持仓情况下卖出（做空或数据异常）
                pnl_results[trade_key] = 0.0
    
    return pnl_results

def calculate_currency_pnl(trades: list, base_currency: str) -> dict:
    """
    计算指定基础货币的总体盈亏统计。
    
    :param trades: 所有交易记录
    :param base_currency: 基础货币符号（如BTC、ETH、XRP）
    :return: 包含盈亏统计的字典
    """
    # 筛选出该基础货币的所有交易
    currency_trades = []
    for trade in trades:
        trade_base_currency = get_base_currency_from_symbol(trade['symbol'])
        if trade_base_currency.upper() == base_currency.upper():
            currency_trades.append(trade)
    
    if not currency_trades:
        return {
            'base_currency': base_currency.upper(),
            'total_trades': 0,
            'total_pnl': 0.0,
            'buy_trades': 0,
            'sell_trades': 0,
            'total_buy_amount': 0.0,
            'total_sell_amount': 0.0,
            'total_buy_quantity': 0.0,
            'total_sell_quantity': 0.0,
            'current_holding': 0.0,
            'win_rate': 0.0
        }
    
    # 按时间排序
    currency_trades.sort(key=lambda x: x['utc_time'])
    
    # 分别统计买入和卖出
    buy_trades = [t for t in currency_trades if t['side'] == 'BUY']
    sell_trades = [t for t in currency_trades if t['side'] == 'SELL']
    
    total_buy_quantity = sum(t['quantity'] for t in buy_trades)
    total_sell_quantity = sum(t['quantity'] for t in sell_trades)
    total_buy_amount = sum(t['quote_quantity'] for t in buy_trades)
    total_sell_amount = sum(t['quote_quantity'] for t in sell_trades)
    
    # 计算总PnL
    total_pnl = sum(t.get('pnl', 0) or 0 for t in currency_trades)
    
    # 计算胜率（只考虑有PnL的卖出交易）
    profitable_sells = sum(1 for t in sell_trades if t.get('pnl', 0) > 0)
    total_sells = len([t for t in sell_trades if t.get('pnl') is not None])
    win_rate = profitable_sells / total_sells if total_sells > 0 else 0.0
    
    return {
        'base_currency': base_currency.upper(),
        'total_trades': len(currency_trades),
        'total_pnl': total_pnl,
        'buy_trades': len(buy_trades),
        'sell_trades': len(sell_trades),
        'total_buy_amount': total_buy_amount,
        'total_sell_amount': total_sell_amount,
        'total_buy_quantity': total_buy_quantity,
        'total_sell_quantity': total_sell_quantity,
        'current_holding': total_buy_quantity - total_sell_quantity,
        'win_rate': win_rate
    }

def format_currency_report(stats: dict) -> str:
    """
    格式化单个币种的盈亏报告。
    
    :param stats: 币种统计数据
    :return: 格式化的报告字符串
    """
    currency = stats['base_currency']
    lines = []
    
    lines.append("=" * 60)
    lines.append(f"{currency} 净盈亏分析报告")
    lines.append("=" * 60)
    
    lines.append(f"交易概况:")
    lines.append(f"  总交易笔数:    {stats['total_trades']:,}")
    lines.append(f"  买入交易:      {stats['buy_trades']:,}")
    lines.append(f"  卖出交易:      {stats['sell_trades']:,}")
    lines.append("")
    
    lines.append(f"数量统计:")
    lines.append(f"  总买入数量:    {stats['total_buy_quantity']:,.4f} {currency}")
    lines.append(f"  总卖出数量:    {stats['total_sell_quantity']:,.4f} {currency}")
    lines.append(f"  当前持仓:      {stats['current_holding']:,.4f} {currency}")
    lines.append("")
    
    lines.append(f"金额统计 (USDT):")
    lines.append(f"  总买入金额:    {format_currency(stats['total_buy_amount'])}")
    lines.append(f"  总卖出金额:    {format_currency(stats['total_sell_amount'])}")
    lines.append("")
    
    lines.append(f"盈亏分析:")
    pnl_color = "+" if stats['total_pnl'] >= 0 else ""
    lines.append(f"  已实现盈亏:    {pnl_color}{format_currency(stats['total_pnl'])}")
    lines.append(f"  胜率:          {format_percentage(stats['win_rate'])}")
    
    if stats['current_holding'] > 0:
        avg_cost = stats['total_buy_amount'] / stats['total_buy_quantity'] if stats['total_buy_quantity'] > 0 else 0
        lines.append(f"  持仓成本价:    {avg_cost:.4f} USDT/{currency}")
        lines.append(f"  持仓价值:      {format_currency(stats['current_holding'] * avg_cost)}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

def calculate_total_pnl(trades: list) -> float:
    """
    计算总的已实现盈亏。
    """
    return sum(trade.get('pnl', 0) for trade in trades if trade.get('pnl') is not None)

def calculate_win_rate(trades: list) -> float:
    """
    计算胜率。
    胜率 = (盈利的交易次数 / 总的有效交易次数)
    """
    valid_trades = [t for t in trades if t.get('pnl') is not None and t.get('pnl') != 0]
    if not valid_trades:
        return 0.0
    
    winning_trades = sum(1 for t in valid_trades if t['pnl'] > 0)
    return winning_trades / len(valid_trades)

def calculate_profit_loss_ratio(trades: list) -> float:
    """
    计算盈亏比。
    盈亏比 = (平均盈利 / 平均亏损)
    """
    valid_trades = [t for t in trades if t.get('pnl') is not None and t.get('pnl') != 0]
    
    profit_trades = [t['pnl'] for t in valid_trades if t['pnl'] > 0]
    loss_trades = [abs(t['pnl']) for t in valid_trades if t['pnl'] < 0]
    
    if not profit_trades or not loss_trades:
        return float('inf') if profit_trades else 0.0
    
    avg_profit = sum(profit_trades) / len(profit_trades)
    avg_loss = sum(loss_trades) / len(loss_trades)
    
    return avg_profit / avg_loss if avg_loss > 0 else float('inf')

def calculate_trade_statistics(trades: list) -> dict:
    """
    计算交易统计信息。
    
    :param trades: 交易记录列表
    :return: 包含各种统计指标的字典
    """
    if not trades:
        return {
            'total_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'profit_loss_ratio': 0.0,
            'total_buy_volume': 0.0,
            'total_sell_volume': 0.0,
            'total_fees': 0.0
        }
    
    # 基础统计
    total_trades = len(trades)
    total_pnl = calculate_total_pnl(trades)
    win_rate = calculate_win_rate(trades)
    profit_loss_ratio = calculate_profit_loss_ratio(trades)
    
    # 交易量统计
    buy_trades = [t for t in trades if t['side'] == 'BUY']
    sell_trades = [t for t in trades if t['side'] == 'SELL']
    
    total_buy_volume = sum(t['quote_quantity'] for t in buy_trades)
    total_sell_volume = sum(t['quote_quantity'] for t in sell_trades)
    total_fees = sum(t['fee'] for t in trades if t['fee_currency'] in ['USDT', 'BUSD'])
    
    return {
        'total_trades': total_trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'total_buy_volume': total_buy_volume,
        'total_sell_volume': total_sell_volume,
        'total_fees': total_fees,
        'buy_trades_count': len(buy_trades),
        'sell_trades_count': len(sell_trades)
    }

def format_currency(amount: float, currency: str = 'USDT') -> str:
    """
    格式化货币显示。
    """
    if abs(amount) >= 1000:
        return f"{amount:,.2f} {currency}"
    else:
        return f"{amount:.4f} {currency}"

def format_percentage(value: float) -> str:
    """
    格式化百分比显示。
    
    :param value: 百分比值 (0.75 表示 75%)
    :return: 格式化的百分比字符串
    """
    return f"{value:.2%}"

def format_ratio(ratio: float) -> str:
    """
    格式化比率显示。
    """
    if ratio == float('inf'):
        return "∞ : 1"
    elif ratio == 0:
        return "0 : 1"
    else:
        return f"{ratio:.2f} : 1"

def format_summary_report(stats: dict, time_range: str = None) -> str:
    """
    格式化汇总报告输出。
    
    :param stats: 统计数据字典
    :param time_range: 时间范围描述
    :return: 格式化的报告字符串
    """
    lines = []
    lines.append("=" * 50)
    
    if time_range:
        lines.append(f"交易汇总统计 ({time_range})")
    else:
        lines.append(f"交易汇总统计 (截至 {datetime.now().strftime('%Y-%m-%d')})")
    
    lines.append("=" * 50)
    lines.append(f"总交易笔数:      {stats['total_trades']:,}")
    lines.append(f"买入交易:        {stats['buy_trades_count']:,}")
    lines.append(f"卖出交易:        {stats['sell_trades_count']:,}")
    lines.append("")
    
    lines.append("=== 核心指标 ===")
    lines.append(f"总实现盈亏:      {format_currency(stats['total_pnl'])}")
    lines.append(f"胜率:           {format_percentage(stats['win_rate'])}")
    lines.append(f"盈亏比:         {format_ratio(stats['profit_loss_ratio'])}")
    lines.append("")
    
    lines.append("=== 交易量统计 ===")
    lines.append(f"总买入量:       {format_currency(stats['total_buy_volume'])}")
    lines.append(f"总卖出量:       {format_currency(stats['total_sell_volume'])}")
    lines.append(f"总手续费:       {format_currency(stats['total_fees'])}")
    lines.append("=" * 50)
    
    return "\n".join(lines)

def format_trades_table(trades: list, limit: int = 20) -> str:
    """
    格式化交易记录表格输出。
    
    :param trades: 交易记录列表
    :param limit: 显示记录数量限制
    :return: 格式化的表格字符串
    """
    if not trades:
        return "没有找到符合条件的交易记录。"
    
    # 限制显示数量
    display_trades = trades[-limit:] if len(trades) > limit else trades
    
    lines = []
    lines.append(f"最近 {len(display_trades)} 笔交易记录:")
    lines.append("-" * 100)
    lines.append(f"{'时间':<19} {'交易对':<10} {'方向':<4} {'价格':<12} {'数量':<12} {'金额':<12} {'PnL':<10}")
    lines.append("-" * 100)
    
    for trade in display_trades:
        pnl_str = f"{trade.get('pnl', 0):.2f}" if trade.get('pnl') is not None else "N/A"
        lines.append(
            f"{trade['utc_time']:<19} "
            f"{trade['symbol']:<10} "
            f"{trade['side']:<4} "
            f"{trade['price']:<12.4f} "
            f"{trade['quantity']:<12.6f} "
            f"{trade['quote_quantity']:<12.2f} "
            f"{pnl_str:<10}"
        )
    
    lines.append("-" * 100)
    return "\n".join(lines)

def format_pnl_report(trades: list, filters: dict = None) -> str:
    """
    格式化生成PnL报告的主函数
    
    :param trades: 交易记录列表
    :param filters: 筛选条件字典
    :return: 格式化的报告字符串
    """
    if not trades:
        return "没有找到交易记录。"
    
    # 计算统计数据
    stats = calculate_pnl_statistics(trades)
    
    # 添加筛选信息到标题
    title_suffix = ""
    if filters:
        if 'symbol' in filters:
            title_suffix = f" - {filters['symbol']}"
        elif 'days' in filters:
            title_suffix = f" - 最近{filters['days']}天"
    
    # 生成报告
    lines = []
    lines.append("=" * 60)
    lines.append(f"交易汇总统计报告{title_suffix}")
    lines.append("=" * 60)
    
    lines.append(f"交易概况:")
    lines.append(f"  总交易笔数:    {stats['total_trades']:,}")
    lines.append(f"  买入交易:      {stats['buy_trades']:,}")
    lines.append(f"  卖出交易:      {stats['sell_trades']:,}")
    lines.append("")
    
    lines.append(f"=== 核心指标 ===")
    pnl_color = "+" if stats['total_pnl'] >= 0 else ""
    lines.append(f"总实现盈亏:      {pnl_color}{format_currency(stats['total_pnl'])}")
    lines.append(f"胜率:           {format_percentage(stats['win_rate'])}")
    
    if stats['avg_profit'] > 0 and stats['avg_loss'] < 0:
        profit_loss_ratio = abs(stats['avg_profit'] / stats['avg_loss'])
        lines.append(f"盈亏比:         {profit_loss_ratio:.2f} : 1")
    
    lines.append("")
    lines.append(f"=== 交易量统计 ===")
    lines.append(f"总买入量:       {format_currency(stats['total_buy_volume'])}")
    lines.append(f"总卖出量:       {format_currency(stats['total_sell_volume'])}")
    lines.append(f"总手续费:       {format_currency(stats['total_fees'])}")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def calculate_pnl_statistics(trades: list) -> dict:
    """
    计算交易统计数据
    
    :param trades: 交易记录列表
    :return: 统计数据字典
    """
    buy_trades = [t for t in trades if t['side'] == 'BUY']
    sell_trades = [t for t in trades if t['side'] == 'SELL']
    
    total_buy_volume = sum(t['quote_quantity'] for t in buy_trades)
    total_sell_volume = sum(t['quote_quantity'] for t in sell_trades)
    total_fees = sum(t.get('fee', 0) for t in trades)
    
    # 计算PnL相关统计
    profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0
    
    avg_profit = sum(t.get('pnl', 0) for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0
    avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    return {
        'total_trades': len(trades),
        'buy_trades': len(buy_trades),
        'sell_trades': len(sell_trades),
        'total_pnl': total_pnl,
        'total_buy_volume': total_buy_volume,
        'total_sell_volume': total_sell_volume,
        'total_fees': total_fees,
        'win_rate': win_rate,
        'avg_profit': avg_profit,
        'avg_loss': avg_loss
    }

def format_trades_details(currency: str, trades: list) -> str:
    """
    格式化显示币种的所有交易记录详情，包含平均成本计算过程
    
    :param currency: 币种符号
    :param trades: 交易记录列表
    :return: 格式化的交易记录详情字符串
    """
    if not trades:
        return f"❌ 未找到 {currency} 的交易记录"
    
    lines = []
    lines.append("=" * 115)
    lines.append(f"{currency} 所有交易记录详情（含平均成本计算）")
    lines.append("=" * 115)
    lines.append(f"总共 {len(trades)} 笔交易\n")
    
    # 表头 - 精确调整列宽
    header = f"{'序号':<4} {'日期':<12} {'交易对':<10} {'方向':<4} {'数量':>13} {'价格':>10} {'金额':>12} {'手续费':>10} {'平均成本':>10} {'盈亏':>12}"
    lines.append(header)
    lines.append("-" * 115)
    
    # 重新计算平均成本和盈亏
    current_quantity = 0.0
    average_cost = 0.0
    
    # 按时间排序确保计算顺序正确
    sorted_trades = sorted(trades, key=lambda x: x.get('date', x.get('utc_time', '')))
    
    for i, trade in enumerate(sorted_trades, 1):
        date_str = trade.get('date', trade.get('utc_time', 'N/A'))[:10] if trade.get('date') or trade.get('utc_time') else "N/A"
        symbol = trade['symbol']
        side = trade['side']
        quantity = trade['quantity']
        price = trade['price']
        quote_qty = trade['quote_quantity']
        fee = trade.get('fee', 0)
        
        # 计算当前交易后的平均成本和盈亏
        if side == 'BUY':
            # 买入：更新加权平均成本
            if current_quantity > 0:
                # 计算新的加权平均成本
                total_cost = (current_quantity * average_cost) + (quantity * price)
                new_quantity = current_quantity + quantity
                average_cost = total_cost / new_quantity
            else:
                # 首次买入或重新建仓
                average_cost = price
            
            current_quantity += quantity
            pnl = 0.0  # 买入交易PnL为0
            pnl_str = "-"
            
        elif side == 'SELL':
            # 卖出：计算已实现盈亏
            if current_quantity > 0:
                base_pnl = (price - average_cost) * quantity
                # 减去手续费（如果手续费是稳定币）
                net_pnl = base_pnl - (fee if trade.get('fee_currency') in STABLE_COINS else 0)
                current_quantity -= quantity
                pnl = net_pnl
                
                if pnl > 0:
                    pnl_str = f"+{pnl:.2f}"
                else:
                    pnl_str = f"{pnl:.2f}"
            else:
                # 无持仓情况下卖出
                pnl = 0.0
                pnl_str = "0.00"
        
        # 格式化显示 - 数字右对齐，文本左对齐
        quantity_str = f"{quantity:.4f}"
        price_str = f"{price:.4f}"
        quote_qty_str = f"{quote_qty:.2f}"
        fee_str = f"{fee:.4f}" if fee else "0"
        avg_cost_str = f"{average_cost:.4f}" if current_quantity > 0 or side == 'BUY' else "-"
        
        row = f"{i:<4} {date_str:<12} {symbol:<10} {side:<4} {quantity_str:>13} {price_str:>10} {quote_qty_str:>12} {fee_str:>10} {avg_cost_str:>10} {pnl_str:>12}"
        lines.append(row)
    
    lines.append("-" * 115)
    
    # 添加汇总信息
    buy_trades = [t for t in trades if t['side'] == 'BUY']
    sell_trades = [t for t in trades if t['side'] == 'SELL']
    total_buy_qty = sum(t['quantity'] for t in buy_trades)
    total_sell_qty = sum(t['quantity'] for t in sell_trades)
    total_pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl'))
    
    lines.append("")
    lines.append("📊 交易汇总:")
    lines.append(f"  买入次数: {len(buy_trades)}  |  卖出次数: {len(sell_trades)}")
    lines.append(f"  总买入量: {total_buy_qty:.4f} {currency}")
    lines.append(f"  总卖出量: {total_sell_qty:.4f} {currency}")
    lines.append(f"  当前持仓: {current_quantity:.4f} {currency}")
    
    if current_quantity > 0:
        lines.append(f"  当前平均成本: {average_cost:.4f} USDT/{currency}")
        lines.append(f"  持仓价值: {current_quantity * average_cost:.2f} USDT")
    
    if total_pnl != 0:
        pnl_symbol = "+" if total_pnl > 0 else ""
        lines.append(f"  已实现盈亏: {pnl_symbol}{total_pnl:.2f} USDT")
    
    lines.append("")
    lines.append("💡 说明:")
    lines.append("  - 平均成本：当前持仓的加权平均买入价格")
    lines.append("  - 盈亏计算：(卖出价格 - 平均成本) × 卖出数量 - 手续费")
    lines.append("  - 买入交易不产生已实现盈亏，只更新平均成本")
    lines.append("=" * 115)
    
    return "\n".join(lines) 