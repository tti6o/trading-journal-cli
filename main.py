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
from services.signal_engine import get_signal_engine
import configparser

# 这是一个使用 @click.group() 创建的主命令组
# 后续的命令 (init, import, report) 都会注册到这个组里
@click.group()
def cli():
    """
    交易日志 CLI 工具 - 分析币安交易记录的盈亏情况
    
    🚀 核心功能:
    - 数据同步和完整报告: python main.py sync
    - 初始化数据库: python main.py init
    - 导入交易记录: python main.py import 交易文件.xlsx

    ⚙️ API 管理:
    - 测试 API 连接: python main.py api test
    - 查看活跃交易对: python main.py api symbols
    - 同步特定交易对: python main.py api sync-symbol BTCUSDT
    - 配置 API 密钥: python main.py api config
    
    ⏰ 定时同步功能:
    - 启动定时同步: python main.py scheduler start
    - 查看调度器状态: python main.py scheduler status
    - 立即触发同步: python main.py scheduler sync-now
    - 查看调度器配置: python main.py scheduler config
    
    🔍 技术分析功能 (新增):
    - 执行技术分析: python main.py technical run
    - 查看分析状态: python main.py technical status
    - 测试分析组件: python main.py technical test
    - 添加监控交易对: python main.py technical add-symbol BTCUSDT
    - 移除监控交易对: python main.py technical remove-symbol BTCUSDT
    
    📧 通知功能 (新增):
    - 测试邮件配置: python main.py notification test
    - 发送测试邮件: python main.py notification test --send
    - 指定收件人测试: python main.py notification test --send --recipient email@example.com
    - 查看通知状态: python main.py notification status
    
    📖 使用步骤:
    1. 首次使用: python main.py init (初始化数据库，如已存在会提示确认)
    2. 配置 API: python main.py api config (设置币安 API 密钥)
    3. 测试连接: python main.py api test (验证 API 连接)
    4. 启动定时同步: python main.py scheduler start (后台自动同步)
    5. 查看报告: python main.py report summary (生成分析报告)
    
    💡 定时同步说明:
    - 默认每4小时自动同步一次交易数据
    - 支持智能增量同步，只获取新的交易记录
    - 可在 config.ini 中配置同步间隔和初始同步天数
    - 调度器在后台运行，不影响其他操作
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
def technical():
    """
    技术分析和信号通知功能
    """
    pass

@technical.command('run')
@click.option('--symbols', default=None, help='指定要分析的交易对，多个交易对用逗号分隔')
@click.option('--interval', default='1h', help='K线间隔，默认为1小时')
@click.option('--limit', default=150, type=int, help='K线数量限制，默认为150')
@click.pass_context
def run_technical_analysis(ctx, symbols, interval, limit):
    """执行一次技术分析并输出结果（不发送通知）"""
    console = Console()
    try:
        # 获取信号引擎实例
        signal_engine = get_signal_engine()
        
        # 准备执行分析的配置覆盖
        config_override = {
            'symbols': symbols,
            'kline_interval': interval,
            'kline_limit': limit
        }
        
        with console.status("[bold cyan]正在执行技术分析...[/]", spinner="dots"):
            # 执行技术分析，但不发送通知
            result = signal_engine.run_analysis(send_notification=False)

        if not result['success']:
            click.secho(f"技术分析失败: {result.get('error', '未知错误')}", fg='red')
        else:
            click.secho("✅ 技术分析完成", bold=True, fg='green')

    except Exception as e:
        click.secho(f"执行技术分析时出错: {e}", fg='red')

@technical.command('notify')
@click.pass_context
def run_and_notify(ctx):
    """执行技术分析并将结果通过邮件发送"""
    console = Console()
    try:
        signal_engine = get_signal_engine()

        with console.status("[bold cyan]正在执行技术分析并准备发送通知...[/]", spinner="dots"):
            result = signal_engine.run_analysis(send_notification=True)

        if not result.get('success'):
            click.secho(f"技术分析失败: {result.get('error', '未知错误')}", fg='red')
            return

        click.secho("✅ 分析完成!", bold=True, fg='green')
        
        signals_found = result.get('signals_found', 0)
        notification_sent = result.get('notification_sent', False)

        if signals_found > 0:
            if notification_sent:
                click.secho(f"📈 发现 {signals_found} 个信号，已成功发送邮件通知。", fg='green')
            else:
                click.secho(f"📈 发现 {signals_found} 个信号，但邮件通知发送失败或已禁用。", fg='yellow')
        else:
            click.secho("📉 本次分析未发现符合条件的交易信号，无需发送通知。", fg='cyan')

    except Exception as e:
        click.secho(f"执行技术分析和通知时出错: {e}", fg='red')

@technical.command('status')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def tech_status(verbose):
    """
    查看技术分析状态
    """
    try:
        from services.signal_engine import get_signal_engine
        
        signal_engine = get_signal_engine()
        status = signal_engine.get_status()
        
        click.echo("📊 技术分析状态:")
        click.echo("=" * 40)
        click.echo(f"启用状态: {'✅ 已启用' if status['enabled'] else '❌ 未启用'}")
        click.echo(f"监控交易对: {status['monitored_symbols_count']} 个")
        click.echo(f"通知收件人: {status['notification_recipients_count']} 个")
        click.echo(f"组件状态:")
        click.echo(f"  - 市场分析器: {'✅' if status['market_analyzer_ready'] else '❌'}")
        click.echo(f"  - 通知服务: {'✅' if status['notification_service_ready'] else '❌'}")
        click.echo(f"  - 交易所客户端: {'✅' if status['exchange_client_ready'] else '❌'}")
        
        if verbose and status['monitored_symbols']:
            click.echo(f"\n监控的交易对: {', '.join(status['monitored_symbols'])}")
            
    except Exception as e:
        click.echo(f"❌ 获取技术分析状态失败: {e}")

@technical.command('test')
def test_components():
    """
    测试技术分析组件
    """
    try:
        from services.signal_engine import get_signal_engine
        
        click.echo("🧪 测试技术分析组件...")
        signal_engine = get_signal_engine()
        test_results = signal_engine.test_components()
        
        for component, result in test_results.items():
            status_icon = '✅' if result['success'] else '❌'
            click.echo(f"{component}: {status_icon}")
            if not result['success']:
                click.echo(f"   错误: {result.get('error', '未知错误')}")
                
    except Exception as e:
        click.echo(f"❌ 测试组件时发生错误: {e}")

@technical.command('add-symbol')
@click.argument('symbol')
def add_monitored_symbol(symbol):
    """
    添加监控的交易对
    
    SYMBOL: 交易对符号 (如 BTCUSDT)
    """
    try:
        from services.signal_engine import get_signal_engine
        
        symbol = symbol.upper()
        signal_engine = get_signal_engine()
        
        if signal_engine.add_monitored_symbol(symbol):
            click.echo(f"✅ 已添加监控交易对: {symbol}")
        else:
            click.echo(f"⚠️ 交易对 {symbol} 已在监控列表中")
            
    except Exception as e:
        click.echo(f"❌ 添加监控交易对失败: {e}")

@technical.command('remove-symbol')
@click.argument('symbol')
def remove_monitored_symbol(symbol):
    """
    移除监控的交易对
    
    SYMBOL: 交易对符号 (如 BTCUSDT)
    """
    try:
        from services.signal_engine import get_signal_engine
        
        symbol = symbol.upper()
        signal_engine = get_signal_engine()
        
        if signal_engine.remove_monitored_symbol(symbol):
            click.echo(f"✅ 已移除监控交易对: {symbol}")
        else:
            click.echo(f"⚠️ 交易对 {symbol} 不在监控列表中")
            
    except Exception as e:
        click.echo(f"❌ 移除监控交易对失败: {e}")

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
        import configparser
        
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
@click.option('--days', default=None, type=int, help='同步最近N天的数据 (默认: 智能增量同步)')
def sync(days):
    """
    📊 数据同步和统计报告

    智能同步最新交易数据并生成包含详细交易明细的完整统计报告
    """
    console = Console()

    try:
        # 步骤1: 智能计算同步天数
        from core import database as database_setup
        from datetime import datetime, timedelta

        if days is None:
            # 智能同步: 从上次同步时间开始
            try:
                last_sync = database_setup.get_last_sync_timestamp()
                if last_sync:
                    # 计算增量同步天数
                    last_sync_time = datetime.fromisoformat(last_sync)
                    time_diff = datetime.now() - last_sync_time
                    actual_days = int(time_diff.total_seconds() / 86400) + 1

                    sync_days = actual_days
                    console.print(f"🧠 智能同步模式: 从上次同步时间 ({last_sync_time.strftime('%Y-%m-%d %H:%M')}) 开始")
                    console.print(f"📅 本次同步范围: {sync_days} 天")
                else:
                    # 首次同步，使用30天
                    sync_days = 30
                    console.print("🆕 首次同步模式: 获取最近30天数据")
            except Exception as e:
                # 如果获取同步时间戳失败，使用默认7天
                sync_days = 7
                console.print(f"⚠️  无法获取上次同步时间 ({e})，使用默认7天同步")
        else:
            # 用户指定天数
            sync_days = days
            console.print(f"🎯 手动同步模式: 最近 {sync_days} 天")

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
                        database_setup.update_last_sync_timestamp()
                        if new_count > 0:
                            console.print("📝 已更新同步时间戳")
                    except:
                        pass  # 忽略时间戳更新错误

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

def get_manager() -> journal_core.TradingJournalManager:
    """获取交易日志管理器实例"""
    config = configparser.ConfigParser()
    config.read('config/config.ini', encoding='utf-8')
    return journal_core.TradeJournalManager(config)

if __name__ == '__main__':
    cli() 