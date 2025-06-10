# 2_Source_Code/journal_core.py
"""
业务逻辑 (Business Logic) 层

- 实现应用的核心功能。
- 协调数据访问层和工具层来完成复杂任务。
- 函数应返回结构化的Python数据 (dict, list)，而不是用于显示的字符串。
"""

import database_setup
import utilities
from datetime import datetime, timedelta

def init_database():
    """
    初始化数据库。
    - 调用数据访问层来创建表结构。
    """
    print("业务逻辑层：开始初始化数据库...")
    
    # 检查数据库是否已存在
    if database_setup.database_exists():
        print("注意：数据库文件已存在。")
        response = input("是否要重新初始化数据库？这将清空所有现有数据。(y/N): ")
        if response.lower() != 'y':
            print("初始化已取消。")
            return False
    
    try:
        database_setup.init_db() 
        print("业务逻辑层：数据库初始化成功！")
        return True
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def import_trades(file_path: str) -> tuple:
    """
    处理交易记录导入的业务逻辑。
    - 调用工具层解析Excel文件。
    - 对解析出的数据进行清洗和转换。
    - 生成唯一的交易ID用于去重。
    - 调用数据访问层将数据批量存入数据库。
    - 返回一个元组，包含成功导入和忽略的记录数。
    """
    print(f"业务逻辑层：开始从 {file_path} 导入交易...")
    
    try:
        # 1. 解析Excel文件
        raw_trades = utilities.parse_binance_excel(file_path)
        if not raw_trades:
            print("没有解析到有效的交易记录。")
            return (0, 0)
        
        # 2. 保存到数据库（数据访问层会自动处理去重和ID生成）
        success_count, ignored_count = database_setup.save_trades(raw_trades)
        
        # 3. 计算并更新所有交易对的PnL
        update_all_pnl()
        
        print(f"业务逻辑层：导入完成。成功 {success_count} 条，忽略 {ignored_count} 条重复记录。")
        return (success_count, ignored_count)
        
    except Exception as e:
        print(f"导入交易记录时发生错误: {e}")
        return (0, 0)

def update_all_pnl():
    """
    为所有交易记录计算并更新PnL
    """
    try:
        # 获取所有唯一的交易对
        symbols = database_setup.get_all_symbols()
        
        for symbol in symbols:
            print(f"正在计算交易对 {symbol} 的PnL...")
            
            # 获取该交易对的所有交易
            trades = database_setup.get_trades_by_symbol(symbol)
            
            # 计算PnL
            pnl_results = utilities.calculate_realized_pnl_for_symbol(trades, symbol)
            
            # 更新数据库中的PnL
            for trade in trades:
                trade_key = trade.get('trade_id') or trade.get('id')
                if trade_key in pnl_results:
                    database_setup.update_trade_pnl(trade['id'], pnl_results[trade_key])
        
        print("PnL计算完成")
        
    except Exception as e:
        print(f"计算PnL时发生错误: {e}")

def generate_summary_report(since: str = None) -> dict:
    """
    生成汇总统计报告的核心逻辑。
    - 调用数据访问层获取指定时间范围内的所有交易。
    - 调用工具层的函数计算各项核心指标（净盈亏、胜率、盈亏比等）。
    - 组装成一个包含所有报告数据的字典并返回。
    """
    print("业务逻辑层：开始生成汇总报告...")
    
    try:
        # 获取交易数据
        trades = database_setup.get_trades(since=since)
        if not trades:
            print("没有找到符合条件的交易记录。")
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'profit_loss_ratio': 0.0,
                'time_range': since or '全部历史'
            }
        
        # 计算统计数据
        stats = utilities.calculate_trade_statistics(trades)
        
        # 添加时间范围信息
        if since:
            stats['time_range'] = f"从 {since} 至今"
        else:
            # 获取最早和最晚的交易时间
            earliest = min(t['utc_time'] for t in trades)
            latest = max(t['utc_time'] for t in trades)
            stats['time_range'] = f"从 {earliest[:10]} 到 {latest[:10]}"
        
        print("业务逻辑层：汇总报告生成完成。")
        return stats
        
    except Exception as e:
        print(f"生成报告时发生错误: {e}")
        return {
            'total_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'profit_loss_ratio': 0.0,
            'time_range': '错误'
        }

def get_trade_list(since: str = None, symbol: str = None, side: str = None, limit: int = 20) -> list:
    """
    获取交易记录列表。
    
    :param since: 开始日期
    :param symbol: 交易对筛选
    :param side: 交易方向筛选  
    :param limit: 记录数量限制
    :return: 交易记录列表
    """
    print("业务逻辑层：获取交易记录列表...")
    
    try:
        trades = database_setup.get_trades(since=since, symbol=symbol, side=side, limit=limit)
        print(f"业务逻辑层：找到 {len(trades)} 条符合条件的交易记录。")
        return trades
    except Exception as e:
        print(f"获取交易记录时发生错误: {e}")
        return []

def get_available_symbols() -> list:
    """
    获取数据库中所有可用的交易对符号。
    """
    try:
        all_trades = database_setup.get_trades()
        symbols = list(set(trade['symbol'] for trade in all_trades))
        return sorted(symbols)
    except Exception as e:
        print(f"获取交易对列表时发生错误: {e}")
        return []

def initialize_database() -> bool:
    """
    初始化数据库的业务逻辑。
    
    :return: 初始化是否成功
    """
    return database_setup.init_db()

def import_trades_from_excel(file_path: str) -> dict:
    """
    从Excel文件导入交易数据的业务逻辑。
    
    :param file_path: Excel文件路径
    :return: 包含导入结果的字典
    """
    try:
        # 1. 解析Excel文件
        print(f"正在解析Excel文件: {file_path}")
        trades = utilities.parse_binance_excel(file_path)
        
        if not trades:
            return {
                'success': False,
                'error': 'Excel文件解析失败或无有效数据'
            }
        
        # 2. 检查稳定币标准化情况
        standardized_symbols = {}
        for trade in trades:
            if 'original_symbol' in trade and trade['original_symbol'] != trade['symbol']:
                standardized_symbols[trade['original_symbol']] = trade['symbol']
        
        # 3. 导入到数据库
        print("正在导入交易数据到数据库...")
        new_count = 0
        duplicate_count = 0
        
        for trade_data in trades:
            success = database_setup.insert_trade(trade_data)
            if success:
                new_count += 1
            else:
                duplicate_count += 1
        
        # 4. 获取总数
        total_count = database_setup.get_total_trade_count()
        
        # 5. 计算并更新PnL
        print("正在计算盈亏...")
        update_all_pnl()
        
        return {
            'success': True,
            'new_count': new_count,
            'duplicate_count': duplicate_count,
            'total_count': total_count,
            'standardized_symbols': standardized_symbols if standardized_symbols else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def generate_pnl_report(filters: dict = None) -> dict:
    """
    生成盈亏分析报告的业务逻辑。
    
    :param filters: 筛选条件字典
    :return: 包含报告结果的字典
    """
    try:
        # 获取交易数据
        if filters and 'symbol' in filters:
            trades = database_setup.get_trades_by_symbol(filters['symbol'])
        else:
            trades = database_setup.get_all_trades()
        
        if not trades:
            return {
                'success': False,
                'error': '没有找到交易数据'
            }
        
        # 应用时间筛选
        if filters and 'days' in filters:
            cutoff_date = datetime.now() - timedelta(days=filters['days'])
            trades = [t for t in trades if datetime.strptime(t['utc_time'], '%Y-%m-%d %H:%M:%S') >= cutoff_date]
        
        # 生成报告
        report = utilities.format_pnl_report(trades, filters)
        
        return {
            'success': True,
            'report': report
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_currency_pnl(currency: str) -> dict:
    """
    获取指定币种的净盈亏数据
    
    :param currency: 币种符号 (例如: BTC, ETH)
    :return: 包含成功状态和数据的字典
    """
    try:
        # 计算该币种的盈亏情况
        pnl_data = utilities.calculate_currency_pnl(currency)
        
        if not pnl_data:
            return {"success": False, "error": f"未找到 {currency} 的交易记录"}
        
        # 格式化报告
        report = utilities.format_currency_report(currency, pnl_data)
        
        return {"success": True, "report": report}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_currency_trades_details(currency: str) -> str:
    """
    获取指定币种的所有交易记录详情
    
    :param currency: 币种符号 (例如: BTC, ETH)
    :return: 格式化的交易记录详情字符串
    """
    # 获取该币种的所有交易记录
    trades = database_setup.get_trades_by_currency(currency)
    
    if not trades:
        return f"❌ 未找到 {currency} 的交易记录"
    
    # 格式化详细交易记录
    return utilities.format_trades_details(currency, trades)

def analyze_currency_pnl(currency: str) -> str:
    """
    分析指定币种的净盈亏情况
    
    :param currency: 币种符号 (例如: BTC, ETH)
    :return: 格式化的分析报告字符串
    """
    # 计算该币种的盈亏情况
    pnl_data = utilities.calculate_currency_pnl(currency)
    
    if not pnl_data:
        return f"❌ 未找到 {currency} 的交易记录"
    
    # 格式化报告
    return utilities.format_currency_report(currency, pnl_data)

def list_all_currencies() -> dict:
    """
    列出所有已交易的币种及其基本统计
    
    :return: 包含币种列表的字典
    """
    try:
        # 获取所有交易数据
        all_trades = database_setup.get_all_trades()
        
        if not all_trades:
            return {
                'success': False,
                'error': '没有找到交易数据'
            }
        
        # 获取所有独特的基础货币
        currencies = set()
        for trade in all_trades:
            base_currency = utilities.get_base_currency_from_symbol(trade['symbol'])
            currencies.add(base_currency)
        
        # 为每个币种计算统计数据
        currency_list = []
        for currency in sorted(currencies):
            stats = utilities.calculate_currency_pnl(all_trades, currency)
            currency_list.append({
                'currency': currency,
                'trades': stats['total_trades'],
                'pnl': stats['total_pnl']
            })
        
        # 按净盈亏排序
        currency_list.sort(key=lambda x: x['pnl'], reverse=True)
        
        return {
            'success': True,
            'currencies': currency_list
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 