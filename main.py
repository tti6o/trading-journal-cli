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

# 这是一个使用 @click.group() 创建的主命令组
# 后续的命令 (init, import, report) 都会注册到这个组里
@click.group()
def cli():
    """
    交易日志 CLI 工具 - 分析币安交易记录的盈亏情况
    
    🔧 基础功能:
    - 初始化数据库: python main.py init
    - 导入交易记录: python main.py import 交易文件.xlsx 
    - 生成盈亏报告: python main.py report summary
    - 查看指定币种净盈亏: python main.py currency XRP
    
    🚀 API 功能:
    - 测试 API 连接: python main.py api test
    - 同步交易记录: python main.py api sync --days 7
    - 查看活跃交易对: python main.py api symbols
    - 同步特定交易对: python main.py api sync-symbol BTCUSDT
    - 配置 API 密钥: python main.py api config
    
    ⏰ 定时同步功能 (新增):
    - 启动定时同步: python main.py scheduler start
    - 查看调度器状态: python main.py scheduler status
    - 立即触发同步: python main.py scheduler sync-now
    - 查看调度器配置: python main.py scheduler config
    
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
    pass

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

@report.command()
@click.option('--since', default=None, help='只统计该日期之后的交易 (格式: YYYY-MM-DD)。')
def summary(since):
    """
    显示全面的汇总统计报告。
    """
    click.echo("正在生成汇总统计报告...")
    
    stats = journal_core.generate_summary_report(since=since)
    
    # 格式化并显示报告
    report_output = utilities.format_summary_report(stats, stats.get('time_range'))
    click.echo(report_output)

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

@cli.command()
@click.option('--symbol', help='筛选特定交易对 (例如: BTCUSDT)')
@click.option('--days', type=int, help='显示最近N天的数据')
def report(symbol, days):
    """
    生成盈亏分析报告
    
    可选参数:
    --symbol: 只显示指定交易对的数据
    --days: 只显示最近N天的数据
    """
    try:
        # 设置筛选条件
        filters = {}
        if symbol:
            filters['symbol'] = symbol.upper()
        if days:
            filters['days'] = days
            
        result = journal_core.generate_pnl_report(filters)
        
        if result['success']:
            click.echo(result['report'])
        else:
            click.echo(f"❌ 生成报告失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 生成报告时发生错误: {e}")

@cli.command()
@click.argument('symbol')
@click.option('--details', is_flag=True, help='显示该币种的所有交易记录详情')
def currency(symbol, details):
    """
    查看指定币种的净盈亏详情
    
    SYMBOL: 币种符号 (例如: BTC, ETH, XRP)
    """
    try:
        if details:
            # 显示详细交易记录
            result = journal_core.get_currency_trades_details(symbol.upper())
        else:
            # 显示汇总分析
            result = journal_core.analyze_currency_pnl(symbol.upper())
        click.echo(result)
    except Exception as e:
        click.echo(f"❌ 查看币种数据失败: {e}")

@cli.command('list-currencies')
def list_currencies():
    """列出所有已交易的币种"""
    try:
        result = journal_core.list_all_currencies()
        
        if result['success']:
            click.echo("📊 已交易币种列表:")
            click.echo("=" * 50)
            for currency_info in result['currencies']:
                click.echo(f"{currency_info['currency']:8} - {currency_info['trades']:3}笔交易 - "
                          f"净盈亏: {currency_info['pnl']:>10.2f} USDT")
        else:
            click.echo(f"❌ 获取币种列表失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 获取币种列表时发生错误: {e}")

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

@api.command('sync')
@click.option('--days', default=7, type=int, help='同步最近N天的交易记录 (默认: 7)')
def sync_trades(days):
    """
    从币安 API 同步交易记录
    """
    try:
        click.echo(f"正在从币安 API 同步最近 {days} 天的交易记录...")
        
        result = journal_core.sync_binance_trades(days=days)
        
        if result['success']:
            click.echo("✅ 交易记录同步成功!")
            click.echo(f"📅 同步时间范围: {result['sync_period']} (从 {result['since_date']} 开始)")
            click.echo(f"📊 新增交易记录: {result['new_count']} 条")
            click.echo(f"⏭️  跳过重复记录: {result['duplicate_count']} 条")
            click.echo(f"📈 数据库总记录数: {result['total_count']} 条")
            
            if result['new_count'] > 0:
                click.echo("\n💡 建议使用 'python main.py report summary' 查看更新后的统计报告")
        else:
            click.echo(f"❌ 同步失败: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ 同步交易记录时发生错误: {e}")

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
            click.echo(f"同步间隔: {status['sync_interval_hours']} 小时")
            
            if status.get('next_run_time'):
                next_run = datetime.fromisoformat(status['next_run_time'])
                click.echo(f"下次同步: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if status.get('last_sync'):
                last_sync = datetime.fromisoformat(status['last_sync'])
                click.echo(f"上次同步: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                click.echo("上次同步: 暂无记录")
        
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

if __name__ == '__main__':
    cli() 