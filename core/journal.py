# 2_Source_Code/journal_core.py
"""
业务逻辑 (Business Logic) 层 - v2.0

- 基于新的交易所客户端架构
- 使用依赖倒置原则，支持多交易所扩展
- 实现应用的核心功能
- 协调数据访问层和工具层来完成复杂任务
- 函数返回结构化的Python数据 (dict, list)
"""

import configparser
from core import database as database_setup
from common import utilities
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os

from exchange_client import (
    ExchangeClientFactory, 
    ExchangeClient,
    ExchangeAPIError,
    Trade as ExchangeTrade,
    SyncResult as ExchangeSyncResult
)

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
    # 静默模式，减少调试输出
    # print("业务逻辑层：开始生成汇总报告...")

    try:
        # 获取交易数据
        trades = database_setup.get_trades(since=since)
        if not trades:
            # print("没有找到符合条件的交易记录。")
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
        
        # print("业务逻辑层：汇总报告生成完成。")
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

def initialize_database(force: bool = False) -> bool:
    """
    初始化数据库的业务逻辑。
    
    :param force: 是否强制重新初始化，不提示确认
    :return: 初始化是否成功
    """
    import click
    
    # 检查数据库是否已存在
    if database_setup.database_exists():
        if not force:
            # 提示用户确认
            click.echo("⚠️  数据库文件已存在!")
            click.echo("重新初始化将会删除所有现有的交易数据。")
            
            if not click.confirm("是否确认重新初始化数据库?"):
                click.echo("❌ 初始化已取消。")
                return False
        
        # 删除现有数据库文件
        try:
            import os
            os.remove(database_setup.DB_PATH)
            click.echo("🗑️  已删除现有数据库文件。")
        except Exception as e:
            click.echo(f"❌ 删除现有数据库文件失败: {e}")
            return False
    
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
    # 获取所有交易记录
    all_trades = database_setup.get_all_trades()

    # 计算该币种的盈亏情况
    pnl_data = utilities.calculate_currency_pnl(all_trades, currency)
    
    if not pnl_data:
        return f"❌ 未找到 {currency} 的交易记录"
    
    # 格式化报告
    return utilities.format_currency_report(pnl_data)

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

class TradingJournalManager:
    """交易日志管理器 - 使用新架构"""
    
    def __init__(self, config_file: str = 'config/config.ini'):
        """
        初始化交易日志管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.exchange_client: Optional[ExchangeClient] = None
        
        if not os.path.exists(self.config_file):
            print(f"❌ 错误: 配置文件 '{self.config_file}' 不存在。")
            print("💡 请先运行 'python main.py api config' 来创建一个新的配置文件。")
            # 在这种情况下，我们可以选择抛出异常或使用一个空的配置继续
            # 这里选择继续，但后续操作可能会因为缺少配置而失败
            self.api_key = ''
            self.api_secret = ''
            self.exchange_name = 'binance'
            self.sandbox = False
            self.rate_limit = True
            return

        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            # 读取交易所配置
            self.exchange_name = config.get('exchange', 'name', fallback='binance')
            self.api_key = config.get('binance', 'api_key', fallback='')
            self.api_secret = config.get('binance', 'api_secret', fallback='')
            
            # 其他配置
            self.sandbox = config.getboolean('exchange', 'sandbox', fallback=False)
            self.rate_limit = config.getboolean('exchange', 'rate_limit', fallback=True)
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用默认配置
            self.exchange_name = 'binance'
            self.api_key = ''
            self.api_secret = ''
            self.sandbox = False
            self.rate_limit = True
    
    def get_exchange_client(self) -> ExchangeClient:
        """获取交易所客户端实例（单例模式）"""
        if self.exchange_client is None:
            self.exchange_client = ExchangeClientFactory.create_from_config(self.config_file)
        return self.exchange_client
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试交易所连接
        
        Returns: 
            Dict[str, Any]: 连接测试结果
        """
        try:
            client = self.get_exchange_client()
            result = client.test_connection()
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'{client.exchange_name} API 连接成功',
                    'assets_count': result['account_info']['assets_count'],
                    'account_info': result['account_info']
                }
            else:
                return {
                    'success': False,
                    'error': result['error']
                }
                
        except ExchangeAPIError as e:
            return {
                'success': False,
                'error': f'连接失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'未知错误: {str(e)}'
            }
    
    def sync_trades(self, days: int = 7) -> Dict[str, Any]:
        """
        同步交易记录
        
        Args:
            days: 同步最近几天的数据
            
        Returns:
            Dict[str, Any]: 同步结果
        """
        try:
            # 静默模式，减少debug输出
            # print(f"正在从 {self.exchange_name} 同步最近 {days} 天的交易记录...")

            # 1. 获取交易所客户端
            client = self.get_exchange_client()

            # 2. 同步交易数据
            sync_result = client.sync_trades(days=days)
            
            if not sync_result.success:
                return {
                    'success': False,
                    'error': sync_result.error_message
                }
            
            # 3. 转换为系统内部格式并导入数据库
            trades = sync_result.trades
            
            if not trades:
                return {
                    'success': True,
                    'message': f'最近 {days} 天没有新的交易记录',
                    'new_count': 0,
                    'duplicate_count': 0,
                    'total_count': database_setup.get_total_trade_count()
                }
            
            # 4. 导入到数据库
            # 静默模式，减少debug输出
            # print(f"正在导入 {len(trades)} 条交易记录到数据库...")

            new_count = 0
            duplicate_count = 0
            duplicate_records = []

            for trade in trades:
                # 转换为旧系统格式
                trade_dict = trade.to_dict()
                trade_dict['data_source'] = f'{self.exchange_name}_api_v2'

                success = database_setup.insert_trade(trade_dict)
                if success:
                    new_count += 1
                else:
                    duplicate_count += 1
                    duplicate_records.append(f"{trade_dict['utc_time']} {trade_dict['symbol']} {trade_dict['side']} {trade_dict['quantity']}@{trade_dict['price']}")

            # 输出去重统计
            if duplicate_count > 0:
                print(f"数据访问层: 尝试插入 {new_count + duplicate_count} 条记录，成功插入 {new_count} 条新记录，忽略 {duplicate_count} 条重复记录:")
                for rec in duplicate_records:
                    print(f"  ⏭️  {rec}")
            elif new_count > 0:
                print(f"数据访问层: 成功插入 {new_count} 条新记录。")
            
            # 5. 计算并更新PnL
            if new_count > 0:
                print("正在计算盈亏...")
                update_all_pnl()
            
            # 6. 获取总数
            total_count = database_setup.get_total_trade_count()
            
            return {
                'success': True,
                'message': f'成功同步最近 {days} 天的交易记录',
                'new_count': new_count,
                'duplicate_count': duplicate_count,
                'total_count': total_count,
                'sync_period': sync_result.sync_period,
                'since_date': sync_result.since_date
            }
            
        except ExchangeAPIError as e:
            return {
                'success': False,
                'error': f'API 错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'同步失败: {str(e)}'
            }
    
    def sync_symbol_trades(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        同步指定交易对的交易记录
        
        Args:
            symbol: 交易对符号
            days: 同步最近几天的数据
            
        Returns:
            Dict[str, Any]: 同步结果
        """
        try:
            print(f"正在同步交易对 {symbol} 最近 {days} 天的交易记录...")
            
            # 1. 获取交易所客户端
            client = self.get_exchange_client()
            
            # 2. 同步指定交易对的数据
            sync_result = client.sync_symbol_trades(symbol, days=days)
            
            if not sync_result.success:
                return {
                    'success': False,
                    'error': sync_result.error_message
                }
            
            # 3. 处理交易数据
            trades = sync_result.trades
            
            if not trades:
                return {
                    'success': True,
                    'message': f'交易对 {symbol} 在最近 {days} 天没有交易记录',
                    'new_count': 0,
                    'duplicate_count': 0
                }
            
            # 4. 导入到数据库
            print(f"正在导入 {len(trades)} 条 {symbol} 交易记录...")
            
            new_count = 0
            duplicate_count = 0
            
            for trade in trades:
                trade_dict = trade.to_dict()
                trade_dict['data_source'] = f'{self.exchange_name}_api_v2'
                
                success = database_setup.insert_trade(trade_dict)
                if success:
                    new_count += 1
                else:
                    duplicate_count += 1
            
            # 5. 计算并更新PnL
            if new_count > 0:
                print(f"正在计算 {symbol} 的盈亏...")
                update_all_pnl()
            
            return {
                'success': True,
                'message': f'成功同步交易对 {symbol} 的交易记录',
                'symbol': symbol,
                'new_count': new_count,
                'duplicate_count': duplicate_count,
                'sync_period': sync_result.sync_period,
                'since_date': sync_result.since_date
            }
            
        except ExchangeAPIError as e:
            return {
                'success': False,
                'error': f'API 错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'同步失败: {str(e)}'
            }
    
    def get_active_symbols(self) -> Dict[str, Any]:
        """
        获取活跃交易对
        
        Returns:
            Dict[str, Any]: 活跃交易对结果
        """
        try:
            client = self.get_exchange_client()
            active_symbols = client.get_active_symbols()
            
            return {
                'success': True,
                'symbols': active_symbols,
                'count': len(active_symbols)
            }
            
        except ExchangeAPIError as e:
            return {
                'success': False,
                'error': f'获取活跃交易对失败: {str(e)}'
            }


# 全局管理器实例
_manager = None

def get_manager() -> TradingJournalManager:
    """获取交易日志管理器单例"""
    global _manager
    if _manager is None:
        _manager = TradingJournalManager()
    return _manager

def test_binance_api_connection() -> Dict[str, Any]:
    """测试币安 API 连接（兼容旧接口）"""
    return get_manager().test_connection()

def sync_binance_trades(days: int = 7) -> Dict[str, Any]:
    """同步币安交易记录（兼容旧接口）"""
    return get_manager().sync_trades(days)

def get_binance_active_symbols() -> Dict[str, Any]:
    """获取币安活跃交易对（兼容旧接口）"""
    return get_manager().get_active_symbols()

def sync_specific_symbol_trades(symbol: str, days: int = 30) -> Dict[str, Any]:
    """同步指定交易对交易记录（兼容旧接口）"""
    return get_manager().sync_symbol_trades(symbol, days)

def get_current_prices(currencies: List[str]) -> Dict[str, float]:
    """
    获取指定货币的当前价格

    Args:
        currencies: 币种列表，如 ['BTC', 'ETH', 'XRP']

    Returns:
        Dict[str, float]: 币种到价格的映射
    """
    try:
        manager = get_manager()

        # 检查是否有可用的交易所客户端
        if not hasattr(manager, 'exchange_client') or manager.exchange_client is None:
            # 尝试初始化交易所客户端
            result = manager.test_connection()
            if not result['success']:
                # API连接失败，返回空价格
                return {currency: 0.0 for currency in currencies}

        # 将币种转换为交易对符号 (添加USDT)
        symbols = [f"{currency}USDT" for currency in currencies if currency != 'USDT']

        if not symbols:
            return {}

        # 获取价格
        prices = manager.exchange_client.get_multiple_prices(symbols)

        # 转换回币种格式
        result = {}
        for currency in currencies:
            if currency == 'USDT':
                result[currency] = 1.0  # USDT价格固定为1
            else:
                symbol = f"{currency}USDT"
                result[currency] = prices.get(symbol, 0.0)

        return result

    except Exception as e:
        logging.error(f"获取价格失败: {e}")
        # 出错时返回0价格
        return {currency: 0.0 for currency in currencies} 