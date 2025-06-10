"""
命令行接口 (CLI) 层

- 使用 Click 库来构建命令行应用。
- 解析用户输入的命令和参数。
- 调用业务逻辑层的函数来执行核心任务。
- 格式化并打印最终结果给用户。
- 不包含任何核心业务逻辑。
"""
import click
import journal_core
import utilities

# 这是一个使用 @click.group() 创建的主命令组
# 后续的命令 (init, import, report) 都会注册到这个组里
@click.group()
def cli():
    """
    交易日志 CLI 工具 - 分析币安交易记录的盈亏情况
    
    使用示例:
    - 初始化数据库: python main.py init
    - 导入交易记录: python main.py import 交易文件.xlsx 
    - 生成盈亏报告: python main.py report
    - 查看指定币种净盈亏: python main.py currency XRP
    """
    pass

@cli.command()
def init():
    """
    初始化数据库。如果数据库文件已存在，会提示用户确认。
    """
    try:
        success = journal_core.initialize_database()
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

if __name__ == '__main__':
    cli() 