"""
命令行接口 (CLI) 层

- 使用 Click 库来构建命令行应用。
- 解析用户输入的命令和参数。
- 调用业务逻辑层的函数来执行核心任务。
- 格式化并打印最终结果给用户。
- 不包含任何核心业务逻辑。
"""
import click
from core import journal as journal_core
from common import utilities
from datetime import datetime
import os
import time
from rich.console import Console
import configparser
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# 这是一个使用 @click.group() 创建的主命令组
# 后续的命令 (init, import, report) 都会注册到这个组里
@click.group()
def cli():
    """
    交易日志 CLI 工具 - 第六版技术分析MVP

    🚀 核心命令 (日常使用):
    - 数据同步和统计: python main.py sync
    - 技术分析和决策: python main.py analyze

    ⚙️ 基础功能:
    - 初始化数据库: python main.py init
    - 导入交易记录: python main.py import 交易文件.xlsx
    - 配置 API 密钥: python main.py api config
    - 测试 API 连接: python main.py api test

    📖 快速上手:
    1. 初始化: python main.py init
    2. 配置API: python main.py api config
    3. 同步数据: python main.py sync
    4. 技术分析: python main.py analyze

    💡 技术分析说明:
    - analyze 命令基于 config.ini 中的 monitored_symbols 配置
    - 自动显示系统状态、批量分析所有监控币种(RSI + 斐波那契)
    - 提供买入/卖出信号和市场情绪分析，自动邮件通知
    - 专注于"现在应该买还是卖？"的实用决策

    🔧 高级功能 (使用 --help-all 查看):
    - scheduler: 定时同步功能
    - notification: 邮件通知管理
    - report: 详细报告生成
    - api: API管理功能
    """
    utilities.setup_logging()

@cli.command()
@click.option('--force', is_flag=True, help='强制重新初始化，不提示确认')
def init(force):
    """
    初始化数据库。如果数据库文件已存在，会提示用户确认是否重新初始化。
    """
    try:
        success = journal_core.initialize_database(force=force)
        if success:
            click.echo("✅ 数据库初始化成功!")
        else:
            click.echo("❌ 数据库初始化失败!")
    except Exception as e:
        click.echo(f"❌ 初始化时发生错误: {e}")

@cli.command('import')
@click.argument('file_path', type=click.Path(exists=True))
def import_data(file_path):
    """
    从指定的Excel文件导入交易记录。
    
    FILE_PATH: 指向你的交易历史Excel文件的路径。
    """
    try:
        result = journal_core.import_trades_from_excel(file_path)
        
        if result['success']:
            click.echo(f"✅ 导入成功!")
            click.echo(f"   新增交易记录: {result['new_count']} 条")
            click.echo(f"   跳过重复记录: {result['duplicate_count']} 条") 
            click.echo(f"   总交易记录数: {result['total_count']} 条")
            
            if result.get('standardized_symbols'):
                click.echo(f"\n📝 稳定币交易对标准化:")
                for original, normalized in result['standardized_symbols'].items():
                    click.echo(f"   {original} -> {normalized}")
        else:
            click.echo(f"❌ 导入失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 导入过程中发生错误: {e}")

@cli.group()
def report():
    """
    生成并显示各种分析报告。
    """
    pass

# report summary 命令已删除 - 请使用 'python main.py sync' 获得更完整的报告

@report.command('list-trades')
@click.option('--symbol', default=None, help='只显示特定交易对的记录 (例如: BTCUSDT)。')
@click.option('--side', default=None, type=click.Choice(['BUY', 'SELL'], case_sensitive=False), help='只显示特定方向的交易。')
@click.option('--limit', default=20, type=int, help='显示的记录数量限制 (默认: 20)。')
@click.option('--since', default=None, help='只显示该日期之后的交易 (格式: YYYY-MM-DD)。')
def list_trades(symbol, side, limit, since):
    """
    以表格形式列出详细的交易记录。
    """
    click.echo("正在获取交易记录...")
    
    # 标准化参数
    if symbol:
        symbol = symbol.upper()
    if side:
        side = side.upper()
    
    trades = journal_core.get_trade_list(since=since, symbol=symbol, side=side, limit=limit)
    
    # 格式化并显示交易记录表格
    table_output = utilities.format_trades_table(trades, limit)
    click.echo(table_output)

@report.command('symbols')
def show_symbols():
    """
    显示数据库中所有可用的交易对符号。
    """
    click.echo("正在获取交易对列表...")
    
    symbols = journal_core.get_available_symbols()
    
    if symbols:
        click.echo("📊 可用的交易对符号:")
        for symbol in symbols:
            click.echo(f"  - {symbol}")
    else:
        click.echo("没有找到任何交易对。请先导入交易数据。")



# currency 和 list-currencies 命令已删除 - 请使用 'python main.py sync' 查看完整的币种分析和交易明细

@cli.group()
def api():
    """
    币安 API 相关功能
    """
    pass

@api.command('test')
def test_api():
    """
    测试币安 API 连接状态
    """
    try:
        click.echo("正在测试币安 API 连接...")
        
        result = journal_core.test_binance_api_connection()
        
        if result['success']:
            click.echo("✅ API 连接成功!")
            click.echo(f"📊 账户资产数量: {result['assets_count']}")
            
            if result['assets_count'] > 0:
                click.echo("\n💰 账户资产情况:")
                for currency, balance in result['account_info']['assets'].items():
                    if balance['total'] > 0.01:  # 只显示余额大于0.01的资产
                        click.echo(f"   {currency}: {balance['total']:.6f}")
        else:
            click.echo(f"❌ API 连接失败: {result['error']}")
            click.echo("💡 请检查 config.ini 文件中的 API 密钥配置")
            
    except Exception as e:
        click.echo(f"❌ 测试 API 连接时发生错误: {e}")

# api sync 命令已删除 - 请使用 'python main.py sync' 进行数据同步和查看报告

@api.command('symbols')
def show_active_symbols():
    """
    显示币安账户中的活跃交易对
    """
    try:
        click.echo("正在获取活跃交易对...")
        
        result = journal_core.get_binance_active_symbols()
        
        if result['success']:
            click.echo(f"📊 发现 {result['count']} 个活跃交易对:")
            click.echo("=" * 40)
            for symbol in result['symbols']:
                click.echo(f"  - {symbol}")
                
            if result['count'] > 0:
                click.echo(f"\n💡 可以使用 'python main.py api sync-symbol <交易对>' 同步特定交易对的数据")
        else:
            click.echo(f"❌ 获取活跃交易对失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 获取活跃交易对时发生错误: {e}")

@api.command('sync-symbol')
@click.argument('symbol')
@click.option('--days', default=30, type=int, help='同步最近N天的数据 (默认: 30)')
def sync_symbol_trades(symbol, days):
    """
    同步指定交易对的交易记录
    
    SYMBOL: 交易对符号 (例如: BTCUSDT, ETHUSDT)
    """
    try:
        symbol = symbol.upper()
        click.echo(f"正在同步交易对 {symbol} 最近 {days} 天的交易记录...")
        
        result = journal_core.sync_specific_symbol_trades(symbol, days)
        
        if result['success']:
            click.echo(f"✅ 交易对 {symbol} 同步成功!")
            click.echo(f"📅 同步时间范围: {result['sync_period']} (从 {result['since_date']} 开始)")
            click.echo(f"📊 新增交易记录: {result['new_count']} 条")
            click.echo(f"⏭️  跳过重复记录: {result['duplicate_count']} 条")
            
            if result['new_count'] > 0:
                click.echo(f"\n💡 使用 'python main.py report list-trades --symbol {symbol}' 查看该交易对的详细记录")
        else:
            click.echo(f"❌ 同步失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 同步交易对数据时发生错误: {e}")

@api.command('config')
def setup_config():
    """
    通过复制模板文件来创建新的 config.ini 配置文件
    """
    try:
        config_path = 'config/config.ini'
        template_path = 'config/config.ini.template'
        
        if not os.path.exists(template_path):
            click.echo(f"❌ 错误: 模板文件 {template_path} 不存在!")
            return
            
        if os.path.exists(config_path):
            if not click.confirm(f"⚠️ 配置文件 {config_path} 已存在，是否要覆盖? (旧文件将被备份)"):
                click.echo("操作已取消。")
                return
            
            # 备份旧文件
            backup_path = f"{config_path}.bak.{int(time.time())}"
            os.rename(config_path, backup_path)
            click.echo(f"旧配置文件已备份到: {backup_path}")

        # 从模板复制
        import shutil
        shutil.copy(template_path, config_path)
        
        click.echo("✅ 配置文件已成功创建: config/config.ini")
        click.echo("📝 请打开 config/config.ini 文件，并填入您的 API 密钥。")
        
    except Exception as e:
        click.echo(f"❌ 创建配置文件失败: {e}")


@cli.group()
def notification():
    """
    邮件通知功能
    """
    pass

@notification.command('test')
@click.option('--send', is_flag=True, help='实际发送测试邮件（默认只测试连接）')
@click.option('--recipient', default=None, help='测试邮件收件人（默认发送给配置的邮箱）')
def test_email(send, recipient):
    """
    测试邮件配置
    """
    try:
        from services.notification import get_notification_service
        
        notification_service = get_notification_service()
        
        # 首先测试连接和认证
        click.echo("📧 测试邮件配置...")
        result = notification_service.test_email_config()
        
        if result['success']:
            click.echo("✅ 邮件配置测试成功")
            
            # 如果指定了 --send 选项，则实际发送测试邮件
            if send:
                click.echo("\n📮 正在发送测试邮件...")
                send_result = notification_service.send_test_email(recipient)
                
                if send_result['success']:
                    click.echo(f"✅ 测试邮件发送成功到: {send_result['recipient']}")
                    click.echo(f"📅 发送时间: {send_result['timestamp']}")
                    click.echo("💡 请检查您的邮箱收件箱（可能在垃圾邮件文件夹中）")
                else:
                    click.echo(f"❌ 测试邮件发送失败: {send_result['message']}")
            else:
                click.echo("💡 使用 --send 选项可以实际发送测试邮件")
        else:
            click.echo(f"❌ 邮件配置测试失败: {result['message']}")
            
    except Exception as e:
        click.echo(f"❌ 测试邮件配置时发生错误: {e}")

@notification.command('status')
def notification_status():
    """
    查看通知服务状态
    """
    try:
        from services.notification import get_notification_service
        
        notification_service = get_notification_service()
        status = notification_service.get_status()
        
        click.echo("📧 通知服务状态:")
        click.echo("=" * 30)
        click.echo(f"启用状态: {'✅ 已启用' if status['enabled'] else '❌ 未启用'}")
        click.echo(f"运行状态: {'✅ 运行中' if status['running'] else '❌ 已停止'}")
        click.echo(f"队列大小: {status['queue_size']}")
        click.echo(f"配置状态: {'✅ 已加载' if status['config_loaded'] else '❌ 未加载'}")
        click.echo(f"工作线程: {'✅ 活跃' if status['worker_alive'] else '❌ 非活跃'}")
        
    except Exception as e:
        click.echo(f"❌ 获取通知服务状态失败: {e}")

@cli.group()
def scheduler():
    """
    定时同步调度器管理
    """
    pass

@scheduler.command('start')
def start_scheduler():
    """
    启动定时同步调度器
    """
    try:
        from services import scheduler as scheduler_module
        
        click.echo("🚀 正在启动定时同步调度器...")
        
        # 运行调度器守护进程
        scheduler_module.run_scheduler_daemon()
        
    except KeyboardInterrupt:
        click.echo("\n🛑 调度器已停止")
    except Exception as e:
        click.echo(f"❌ 启动调度器失败: {e}")

@scheduler.command('status')
def scheduler_status():
    """
    查看调度器状态
    """
    try:
        from services import scheduler as scheduler_module
        
        service = scheduler_module.SchedulerService()
        status = service.get_status()
        
        click.echo("📊 定时同步调度器状态:")
        click.echo("=" * 40)
        click.echo(f"运行状态: {'🟢 运行中' if status['running'] else '🔴 已停止'}")
        click.echo(f"启用状态: {'✅ 已启用' if status['enabled'] else '❌ 已禁用'}")
        
        if status['enabled']:
            click.echo(f"数据同步间隔: {status['sync_interval_hours']} 小时")
            
            if status.get('next_sync_time'):
                next_run = datetime.fromisoformat(status['next_sync_time'])
                click.echo(f"下次数据同步: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if status.get('last_sync'):
                last_sync = datetime.fromisoformat(status['last_sync'])
                click.echo(f"上次数据同步: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                click.echo("上次数据同步: 暂无记录")
        
        # 显示技术分析状态
        tech_enabled = status.get('technical_analysis_enabled', False)
        click.echo(f"技术分析: {'✅ 已启用' if tech_enabled else '❌ 未启用'}")
        
        if tech_enabled:
            click.echo(f"技术分析间隔: {status.get('technical_analysis_interval_minutes', 60)} 分钟")
            
            if status.get('next_technical_analysis_time'):
                next_tech = datetime.fromisoformat(status['next_technical_analysis_time'])
                click.echo(f"下次技术分析: {next_tech.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status.get('error'):
            click.echo(f"错误信息: {status['error']}")
            
    except Exception as e:
        click.echo(f"❌ 获取调度器状态失败: {e}")

@scheduler.command('sync-now')
def trigger_sync_now():
    """
    立即触发一次同步任务
    """
    try:
        from services import scheduler as scheduler_module
        
        click.echo("🔥 正在手动触发同步任务...")
        
        service = scheduler_module.SchedulerService()
        result = service.trigger_sync_now()
        
        if result['success']:
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 手动触发同步失败: {e}")

@scheduler.command('config')
def scheduler_config():
    """
    查看和修改调度器配置
    """
    try:
        config = configparser.ConfigParser()
        config.read('config/config.ini', encoding='utf-8')
        
        click.echo("📋 当前调度器配置:")
        click.echo("=" * 30)
        
        if config.has_section('scheduler'):
            enabled = config.getboolean('scheduler', 'enabled', fallback=True)
            interval = config.getint('scheduler', 'sync_interval_hours', fallback=4)
            initial_days = config.getint('scheduler', 'initial_sync_days', fallback=30)
            
            click.echo(f"启用状态: {'✅ 已启用' if enabled else '❌ 已禁用'}")
            click.echo(f"同步间隔: {interval} 小时")
            click.echo(f"初始同步天数: {initial_days} 天")
        else:
            click.echo("⚠️  未找到调度器配置，将使用默认值")
            click.echo("启用状态: ✅ 已启用")
            click.echo("同步间隔: 4 小时")
            click.echo("初始同步天数: 30 天")
        
        click.echo("\n💡 要修改配置，请编辑 config/config.ini 文件中的 [scheduler] 部分")
        
    except Exception as e:
        click.echo(f"❌ 查看配置失败: {e}")

# ============================================================================
# 🚀 sync超级命令 - 第五版整合命令（数据同步+详细统计报告+交易明细）
# ============================================================================

@cli.command()
def sync():
    """
    📊 数据同步和统计报告

    智能增量同步：自动从上次同步时间开始，无需指定天数
    """
    console = Console()

    try:
        # 步骤1: 智能计算同步天数（基于上次同步时间）
        from core import database as database_setup
        from datetime import timedelta

        # 智能同步: 从上次同步时间开始
        try:
            last_sync = database_setup.get_last_sync_timestamp()
            if last_sync:
                # 计算增量同步天数
                last_sync_time = datetime.fromisoformat(last_sync)
                time_diff = datetime.now() - last_sync_time
                actual_days = int(time_diff.total_seconds() / 86400) + 1

                sync_days = actual_days
                console.print(f"📅 上次同步时间: {last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
                console.print(f"🧠 智能增量同步: 同步最近 {sync_days} 天的数据")
            else:
                # 首次同步，使用30天
                sync_days = 30
                console.print("🆕 首次同步模式: 获取最近30天数据")
        except Exception as e:
            # 如果获取同步时间戳失败，使用默认7天
            sync_days = 7
            console.print(f"⚠️  无法获取上次同步时间 ({e})，使用默认7天同步")

        # 步骤2: 数据同步
        console.print("🔄 [bold cyan]正在同步最新交易数据...[/]")

        # 检查是否配置了API
        config_exists = os.path.exists('config/config.ini')
        sync_success = False

        if config_exists:
            try:
                # 尝试API同步
                result = journal_core.sync_binance_trades(days=sync_days)
                if result['success']:
                    new_count = result.get('new_count', 0)
                    if new_count > 0:
                        console.print(f"✅ 同步成功！新增 {new_count} 条交易记录")
                    else:
                        console.print("✅ 同步完成，数据已是最新状态")

                    # 无论是否有新交易都更新时间戳（表示检查过了）
                    try:
                        success = database_setup.update_last_sync_timestamp()
                        if success:
                            console.print("📝 已更新同步时间戳")
                        else:
                            console.print("⚠️  同步时间戳更新失败")
                    except Exception as e:
                        console.print(f"⚠️  同步时间戳更新出错: {e}")

                    sync_success = True
                else:
                    console.print(f"⚠️  API同步失败: {result.get('error', '未知错误')}")
                    console.print("💡 将显示现有数据的统计报告")
            except Exception as e:
                console.print(f"⚠️  API同步出错: {e}")
                console.print("💡 将显示现有数据的统计报告")
        else:
            console.print("⚠️  未找到API配置文件")
            console.print("💡 使用 'python main.py api config' 进行API配置")
            console.print("💡 或使用 'python main.py import <文件>' 导入Excel数据")

        # 步骤3: 生成详细统计报告 (无论是否同步成功都显示)
        console.print(f"\n📊 [bold cyan]交易统计报告 (全部历史交易)[/]")
        console.print("=" * 50)

        # 获取全部历史交易统计数据
        all_stats = journal_core.generate_summary_report()

        if all_stats and all_stats.get('total_trades', 0) > 0:
            # === 核心指标 ===
            console.print("=== [bold cyan]核心指标[/] ===")
            console.print(f"📈 历史总盈亏: {all_stats.get('total_pnl', 0):+,.2f} USDT")
            console.print(f"🎯 历史胜率:   {all_stats.get('win_rate', 0)*100:.1f}%")
            console.print(f"💪 历史盈亏比: {all_stats.get('profit_loss_ratio', 0):.2f}")
            console.print(f"📊 历史交易:   {all_stats.get('total_trades', 0)} 笔")

            # 显示收益状态
            pnl = all_stats.get('total_pnl', 0)
            if pnl > 0:
                console.print("📈 [bold green]整体盈利[/] 🎉")
            elif pnl < 0:
                console.print("📉 [bold red]整体亏损[/] ⚠️")
            else:
                console.print("➖ 盈亏平衡")

            # === 交易量统计 ===
            console.print(f"\n=== [bold cyan]交易量统计[/] ===")
            console.print(f"📊 买入交易:   {all_stats.get('buy_trades_count', 0)} 笔")
            console.print(f"📊 卖出交易:   {all_stats.get('sell_trades_count', 0)} 笔")
            console.print(f"💰 总买入量:   {all_stats.get('total_buy_volume', 0):,.2f} USDT")
            console.print(f"💰 总卖出量:   {all_stats.get('total_sell_volume', 0):,.2f} USDT")
            console.print(f"💸 总手续费:   {all_stats.get('total_fees', 0):,.4f} USDT")

            # === 按币种分组统计 ===
            console.print(f"\n=== [bold cyan]按币种分组统计[/] ===")
            try:
                currencies_result = journal_core.list_all_currencies()
                if currencies_result.get('success') and currencies_result.get('currencies'):
                    # 按盈亏排序，盈利的在前
                    currencies = currencies_result['currencies']
                    currencies.sort(key=lambda x: x['pnl'], reverse=True)

                    for currency_info in currencies[:8]:  # 显示前8个币种
                        pnl = currency_info['pnl']
                        pnl_symbol = "+" if pnl >= 0 else ""
                        pnl_color = "green" if pnl > 0 else "red" if pnl < 0 else "white"
                        console.print(f"💎 {currency_info['currency']:6} - {currency_info['trades']:2}笔 - [{pnl_color}]{pnl_symbol}{pnl:>8.2f} USDT[/]")

                    if len(currencies) > 8:
                        console.print(f"   ... 还有 {len(currencies) - 8} 个币种")

                    # === 主要币种详细分析 ===
                    # 只显示交易数量>=5且盈亏绝对值>=100的主要币种
                    major_currencies = [c for c in currencies if c['trades'] >= 5 and abs(c['pnl']) >= 100]
                    if major_currencies[:3]:  # 最多显示前3个主要币种
                        console.print(f"\n=== [bold cyan]主要币种详细分析[/] ===")
                        for currency_info in major_currencies[:3]:
                            try:
                                currency = currency_info['currency']
                                console.print(f"\n🔍 [bold yellow]{currency} 详细分析[/]")
                                console.print("-" * 40)

                                # 获取详细分析数据
                                all_trades = database_setup.get_all_trades()
                                pnl_data = utilities.calculate_currency_pnl(all_trades, currency)

                                if pnl_data and pnl_data.get('total_trades', 0) > 0:
                                    # 币种分析显示
                                    console.print(f"📊 交易笔数: {pnl_data['total_trades']} 笔 (买:{pnl_data['buy_trades']} / 卖:{pnl_data['sell_trades']})")
                                    console.print(f"💰 已实现盈亏: {pnl_data['total_pnl']:+,.2f} USDT")
                                    console.print(f"🎯 胜率: {pnl_data['win_rate']*100:.1f}%")

                                    if pnl_data.get('current_holdings', 0) > 0:
                                        console.print(f"📦 当前持仓: {pnl_data['current_holdings']:.6f} {currency}")
                                        console.print(f"💲 持仓成本价: {pnl_data['avg_cost_price']:,.2f} USDT/{currency}")

                                    # 显示交易明细
                                    console.print(f"\n📋 [bold yellow]{currency} 交易明细:[/]")
                                    try:
                                        details_result = journal_core.get_currency_trades_details(currency)
                                        console.print(details_result)
                                    except Exception as detail_error:
                                        console.print(f"⚠️  获取交易明细失败: {detail_error}")

                            except Exception as e:
                                console.print(f"⚠️  {currency} 详细分析失败: {e}")
                else:
                    console.print("⚠️  暂无币种数据")
            except Exception as e:
                console.print(f"⚠️  币种统计获取失败: {e}")

            # 显示最近30天统计作为补充信息
            try:
                recent_30_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                recent_stats = journal_core.generate_summary_report(since=recent_30_date)
                if recent_stats and recent_stats.get('total_trades', 0) > 0:
                    console.print(f"\n📅 [dim]最近30天概况:[/]")
                    console.print(f"   📊 近期交易: {recent_stats.get('total_trades', 0)} 笔")
                    console.print(f"   📈 近期盈亏: {recent_stats.get('total_pnl', 0):+,.2f} USDT")
            except:
                pass  # 忽略近期统计错误

            # 给出操作建议
            console.print("\n💡 [bold yellow]操作建议:[/]")
            console.print("  • 使用 'python main.py analyze' 进行技术分析")
            console.print("  • 使用 'python main.py currency <币种>' 查看单币种详细信息")
            if sync_success:
                console.print("  • 使用 'python main.py sync --days <天数>' 指定同步时间范围")
            else:
                console.print("  • 使用 'python main.py api config' 配置API以启用自动同步")
        else:
            console.print("⚠️  暂无交易数据")
            console.print("\n💡 [bold yellow]数据源配置建议:[/]")
            console.print("  • 使用 'python main.py api config' 配置API数据源")
            console.print("  • 或使用 'python main.py import <文件>' 导入Excel数据")

    except Exception as e:
        console.print(f"\n❌ 同步过程中发生错误: {e}")
        console.print("💡 请检查网络连接和配置")


# ============================================================================
# 🔬 analyze命令 - 第六版技术分析MVP（批量监控币种智能分析）
# ============================================================================

@cli.command()
def analyze():
    """
    📈 技术分析超级命令 - 一键完成所有分析

    自动执行以下功能：
    1. 显示技术分析系统状态
    2. 批量分析所有监控币种(RSI + 斐波那契)
    3. 生成市场概览和投资建议
    4. 自动发送邮件通知(如有信号)

    基于 config.ini 中的 monitored_symbols 配置
    """
    console = Console()

    try:
        console.print("🚀 [bold cyan]技术分析 - 批量币种分析[/]")

        # 1. 检查系统状态并获取监控币种
        try:
            from services.signal_engine import get_signal_engine
            signal_engine = get_signal_engine()
            status_info = signal_engine.get_status()

            # 简洁的状态显示
            status_indicators = []
            status_indicators.append('✅' if status_info['enabled'] else '❌')
            status_indicators.append(f"{status_info['monitored_symbols_count']}币种")
            status_indicators.append('📧' if status_info['notification_recipients_count'] > 0 else '📪')
            status_indicators.append('🔗' if status_info['exchange_client_ready'] else '❌')

            console.print(f"📊 系统状态: {' | '.join(status_indicators)}")

        except Exception as e:
            console.print(f"⚠️ 系统检查失败: {e}")

        # 2. 读取监控币种和分析配置
        config = configparser.ConfigParser()
        config.read('config/config.ini', encoding='utf-8')

        monitored_symbols = []
        if config.has_section('technical_analysis'):
            symbols_str = config.get('technical_analysis', 'monitored_symbols', fallback='')
            if symbols_str:
                monitored_symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]

        if not monitored_symbols:
            console.print("⚠️  配置文件中未找到监控币种列表")
            console.print("💡 请在 config.ini 中配置 monitored_symbols")
            return

        # 3. 读取分析参数配置
        interval = config.get('technical_analysis', 'kline_interval', fallback='1h')
        kline_limit = config.getint('technical_analysis', 'kline_limit', fallback=200)

        console.print(f"📊 [bold cyan]分析配置[/]: {interval} K线图，{kline_limit} 根K线数据")

        # 4. 检查API配置
        if not os.path.exists('config/config.ini'):
            console.print("❌ 未找到API配置文件")
            console.print("💡 请使用 'python main.py api config' 配置API")
            return

        # 5. 批量分析 - 静默处理
        console.print(f"🔍 正在分析 {len(monitored_symbols)} 个币种...")

        analysis_results = []
        klines_data = {}
        successful_analyses = 0

        from exchange_client.factory import ExchangeClientFactory
        client = ExchangeClientFactory.create_from_config('config/config.ini')

        for symbol in monitored_symbols:
            try:
                # 获取K线数据
                klines = client.fetch_klines(symbol, interval, kline_limit)
                if not klines or len(klines) < 30:
                    continue

                # 转换为DataFrame
                df = pd.DataFrame(klines)
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])

                # 保存K线数据用于图表生成
                klines_data[symbol] = df.copy()

                # 执行技术分析
                current_price = float(df['close'].iloc[-1])
                price_change = ((current_price - float(df['close'].iloc[-2])) / float(df['close'].iloc[-2])) * 100

                # RSI分析
                from services.technical_analysis import RsiAnalyzer, FibonacciAnalyzer
                rsi_analyzer = RsiAnalyzer()
                rsi_signal = rsi_analyzer.analyze(symbol, df)

                # 斐波那契分析
                fib_analyzer = FibonacciAnalyzer()
                fib_signals = fib_analyzer.analyze(symbol, df)

                # 汇总结果
                signals = []
                high_confidence_fib = []

                if rsi_signal and rsi_signal.signal_type != 'NEUTRAL':
                    signals.append(f"RSI:{rsi_signal.signal_type}")

                if fib_signals:
                    high_confidence_fib = [s for s in fib_signals if s.confidence >= 0.6 and s.signal_type != 'NEUTRAL']
                    for fib_signal in high_confidence_fib:
                        signals.append(f"FIB:{fib_signal.signal_type}")

                # 综合信号评分
                buy_count = sum(1 for s in signals if 'BUY' in s)
                sell_count = sum(1 for s in signals if 'SELL' in s)

                if buy_count > sell_count:
                    overall_signal = "BUY"
                elif sell_count > buy_count:
                    overall_signal = "SELL"
                else:
                    overall_signal = "NEUTRAL"

                # 保存详细结果
                analysis_results.append({
                    'symbol': symbol,
                    'price': current_price,
                    'change': price_change,
                    'signal': overall_signal,
                    'signals_detail': signals,
                    'signal_count': len(signals),
                    'rsi_signal': rsi_signal,
                    'fib_signals': fib_signals,
                    'high_confidence_fib': high_confidence_fib if fib_signals else []
                })

                successful_analyses += 1

                # 添加友好的分析输出
                _display_analysis_summary(console, symbol, current_price, price_change,
                                        overall_signal, rsi_signal, fib_signals, signals)

            except Exception as e:
                continue  # 静默跳过失败的币种

        # 5. 生成市场概览 - 关键结果
        if analysis_results:
            console.print(f"✅ 分析完成 {successful_analyses}/{len(monitored_symbols)} 个币种\n")

            # 统计信号分布
            buy_symbols = [r for r in analysis_results if r['signal'] == 'BUY']
            sell_symbols = [r for r in analysis_results if r['signal'] == 'SELL']
            neutral_symbols = [r for r in analysis_results if r['signal'] == 'NEUTRAL']

            console.print("📊 [bold cyan]市场概览[/]")
            console.print(f"🟢 买入信号: {len(buy_symbols)} | 🔴 卖出信号: {len(sell_symbols)} | 🟡 中性: {len(neutral_symbols)}")

            # 显示有明确信号的币种
            actionable_symbols = buy_symbols + sell_symbols
            if actionable_symbols:
                console.print(f"\n📈 [bold yellow]重点关注币种[/]")
                # 按信号强度排序
                actionable_symbols.sort(key=lambda x: x['signal_count'], reverse=True)

                for r in actionable_symbols[:5]:  # 显示前5个
                    signal_color = "green" if r['signal'] == 'BUY' else "red"
                    change_color = "green" if r['change'] >= 0 else "red"
                    change_symbol = "+" if r['change'] >= 0 else ""
                    console.print(f"  💎 {r['symbol']:8} - [{signal_color}]{r['signal']:4}[/] - {r['price']:>8.4f} ([{change_color}]{change_symbol}{r['change']:>5.1f}%[/]) - {len(r['signals_detail'])}个信号")

            # 市场情绪
            if len(buy_symbols) > len(sell_symbols) * 1.5:
                market_sentiment = "偏多"
                sentiment_color = "green"
            elif len(sell_symbols) > len(buy_symbols) * 1.5:
                market_sentiment = "偏空"
                sentiment_color = "red"
            else:
                market_sentiment = "中性"
                sentiment_color = "white"

            console.print(f"\n💭 市场情绪: [{sentiment_color}]{market_sentiment}[/]")

        # 6. 自动发送邮件通知（如有信号）- 简化过程
        if analysis_results:
            actionable_results = [r for r in analysis_results if r['signal'] != 'NEUTRAL']

            if actionable_results:
                # 构造信号数据
                from services.technical_analysis import TechnicalSignal

                signals_for_notification = []
                for result in actionable_results:
                    signal = TechnicalSignal(
                        symbol=result['symbol'],
                        timestamp=datetime.now(),
                        signal_type=result['signal'],
                        price=result['price'],
                        message=f"{result['symbol']} {result['signal']} 信号 (价格: {result['price']:.4f}, 变化: {result['change']:+.1f}%)"
                    )
                    signals_for_notification.append(signal)

                # 使用专业邮件服务发送通知
                try:
                    from services.simple_email import get_simple_email_service
                    from services.chart_professional import get_professional_chart_generator

                    email_service = get_simple_email_service()

                    if email_service.enabled and email_service.recipients:
                        # 生成专业图表文件（TradingView风格）
                        chart_paths = []
                        try:
                            chart_generator = get_professional_chart_generator()
                            actionable_analysis_results = [r for r in analysis_results if r['signal'] != 'NEUTRAL']

                            if actionable_analysis_results:
                                chart_paths = chart_generator.generate_batch_charts(
                                    analysis_results=actionable_analysis_results,
                                    klines_data=klines_data
                                )
                                console.print(f"📊 生成 {len(chart_paths)} 个专业图表文件 (TradingView风格)")
                        except Exception as e:
                            console.print(f"⚠️ 专业图表生成失败: {e}")

                        # 发送邮件给所有收件人
                        success = email_service.send_to_all_recipients_with_files(
                            signals=signals_for_notification,
                            chart_files=chart_paths
                        )

                        if success:
                            console.print(f"\n📧 邮件通知已发送 ({len(signals_for_notification)} 个信号)")
                        else:
                            console.print(f"\n📭 邮件发送失败")

                        # 自动清理临时文件
                        if chart_paths:
                            chart_generator.cleanup_chart_files(chart_paths)
                            console.print(f"🗑️ 已清理 {len(chart_paths)} 个临时文件")
                    else:
                        console.print(f"\n📪 邮件服务未配置")

                except Exception as e:
                    console.print(f"\n⚠️ 邮件发送异常: {e}")

        # 7. 操作建议
        console.print(f"\n💡 [bold yellow]操作建议[/]")
        if analysis_results and actionable_symbols:
            top_symbol = actionable_symbols[0]['symbol']
            console.print(f"🎯 重点关注 {top_symbol} (信号最强)")
        console.print(f"📊 python main.py sync  # 查看交易统计")

    except Exception as e:
        console.print(f"❌ 分析失败: {e}")
        import traceback
        logger.error(f"技术分析错误: {traceback.format_exc()}")


def _display_analysis_summary(console, symbol, current_price, price_change,
                            overall_signal, rsi_signal, fib_signals, signals):
    """显示友好的技术分析摘要"""

    # 价格变化颜色
    change_color = "green" if price_change >= 0 else "red"
    change_symbol = "+" if price_change >= 0 else ""

    # 信号颜色
    signal_color = "green" if overall_signal == "BUY" else "red" if overall_signal == "SELL" else "yellow"

    console.print(f"\n📈 [bold cyan]{symbol}[/] 技术分析结果")
    console.print("=" * 50)

    # 基本信息
    console.print(f"💰 当前价格: [bold white]{current_price:.6f} USDT[/]")
    console.print(f"📊 24h变化: [{change_color}]{change_symbol}{price_change:+.2f}%[/]")
    console.print(f"🎯 综合信号: [{signal_color}]{overall_signal}[/]")

    # RSI分析
    if rsi_signal:
        rsi_desc = _get_rsi_description(rsi_signal)
        console.print(f"📊 RSI(14): {rsi_desc}")

    # 斐波那契分析
    if fib_signals:
        console.print(f"📐 斐波那契分析:")
        high_conf_fibs = [f for f in fib_signals if f.confidence >= 0.6]
        if high_conf_fibs:
            for fib in high_conf_fibs[:2]:  # 显示前2个高置信度信号
                level_desc = _get_fib_level_description(fib)
                console.print(f"   • {level_desc}")
        else:
            console.print(f"   • 未发现强力支撑阻力位")

    # 交易建议
    if overall_signal != "NEUTRAL":
        suggestion = _get_trading_suggestion(overall_signal, current_price, rsi_signal, fib_signals)
        console.print(f"💡 [bold yellow]交易建议[/]: {suggestion}")

    console.print("-" * 50)


def _get_rsi_description(rsi_signal):
    """获取RSI描述"""
    if hasattr(rsi_signal, 'rsi_value'):
        rsi_val = rsi_signal.rsi_value
        if rsi_val >= 70:
            return f"超买区域 ({rsi_val:.1f}) - 警惕回调"
        elif rsi_val <= 30:
            return f"超卖区域 ({rsi_val:.1f}) - 关注反弹"
        elif rsi_val >= 60:
            return f"强势区域 ({rsi_val:.1f}) - 趋势向上"
        elif rsi_val <= 40:
            return f"弱势区域 ({rsi_val:.1f}) - 趋势向下"
        else:
            return f"中性区域 ({rsi_val:.1f}) - 震荡整理"
    return f"{rsi_signal.signal_type} 信号"


def _get_fib_level_description(fib_signal):
    """获取斐波那契水平描述"""
    if hasattr(fib_signal, 'level') and hasattr(fib_signal, 'price'):
        level_name = f"{fib_signal.level:.1f}%" if hasattr(fib_signal, 'level') else "关键"
        price = fib_signal.price
        signal_type = "支撑" if fib_signal.signal_type == "BUY" else "阻力"
        return f"{level_name} {signal_type}位: {price:.6f} (置信度: {fib_signal.confidence*100:.0f}%)"
    return f"{fib_signal.signal_type} 信号 @ {fib_signal.price:.6f}"


def _get_trading_suggestion(signal, price, rsi_signal, fib_signals):
    """获取交易建议"""
    if signal == "BUY":
        return f"建议逢低买入，关注支撑位附近机会"
    elif signal == "SELL":
        return f"建议逢高减仓，关注阻力位附近压力"
    else:
        return f"建议观望，等待明确方向信号"



if __name__ == '__main__':
    cli()