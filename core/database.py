# 2_Source_Code/database_setup.py
"""
数据访问 (Data Access) 层

- 封装所有与数据库的直接交互 (SQL语句)。
- 提供数据库初始化、数据插入、数据查询等函数。
- 确保使用参数化查询来防止SQL注入。
"""
import sqlite3
import os
import hashlib
from datetime import datetime
from typing import List

# 数据库存储在data目录下，根据用户说明调整
DB_PATH = "data/trading_journal.db"

def init_db():
    """
    创建数据库和 trades 表。
    """
    # 确保data目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 使用 '''...''' 来写多行SQL语句，更清晰
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            trade_id TEXT UNIQUE NOT NULL,
            utc_time DATETIME NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            quote_quantity REAL NOT NULL,
            fee REAL NOT NULL,
            fee_currency TEXT NOT NULL,
            pnl REAL,
            data_source TEXT DEFAULT 'excel'
        )
    ''')
    
    # 创建应用元数据表，用于存储应用级别的状态信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_utc_time ON trades(utc_time)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side)')
    
    conn.commit()
    conn.close()
    print("数据访问层: 数据库表已创建或已存在。")
    return True

def generate_trade_id(trade_data: dict) -> str:
    """
    为交易数据生成唯一的trade_id，用于去重。
    基于交易时间、交易对、价格、数量等生成SHA256哈希。
    """
    # 使用更精确的时间戳和更多字段来生成唯一ID
    key_string = f"{trade_data['utc_time']}-{trade_data['symbol']}-{trade_data['side']}-{trade_data['price']}-{trade_data['quantity']}-{trade_data.get('quote_quantity', 0)}"
    print("generate_trade_id key_string: ", key_string)
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()[:16]

def save_trades(trades_data: list) -> tuple:
    """
    将一批交易数据保存到数据库中。
    使用 INSERT OR IGNORE 来自动处理重复的 trade_id。
    
    :param trades_data: 一个包含交易数据字典的列表。
    :return: (成功插入数量, 忽略数量)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 先查询总数以计算忽略的数量
    initial_count = len(trades_data)
    
    # 为每个交易生成trade_id并转换为元组格式
    prepared_data = []
    for trade in trades_data:
        trade_id = generate_trade_id(trade)
        prepared_data.append((
            trade_id,
            trade['utc_time'],
            trade['symbol'],
            trade['side'],
            trade['price'],
            trade['quantity'],
            trade['quote_quantity'],
            trade['fee'],
            trade['fee_currency'],
            trade.get('data_source', 'excel')
        ))

    # executemany 效率远高于单条循环插入
    cursor.executemany('''
        INSERT OR IGNORE INTO trades (trade_id, utc_time, symbol, side, price, quantity, quote_quantity, fee, fee_currency, data_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', prepared_data)
    
    conn.commit()
    # 获取成功插入的行数
    inserted_rows = cursor.rowcount 
    ignored_rows = initial_count - inserted_rows
    conn.close()
    
    print(f"数据访问层: 尝试插入 {initial_count} 条记录，成功插入 {inserted_rows} 条新记录，忽略 {ignored_rows} 条重复记录。")
    return (inserted_rows, ignored_rows)

def get_trades(since: str = None, symbol: str = None, side: str = None, limit: int = None) -> list:
    """
    从数据库中获取交易记录。
    
    :param since: 如果提供，则只返回该日期之后的记录 (格式 'YYYY-MM-DD')。
    :param symbol: 如果提供，则只返回该交易对的记录。
    :param side: 如果提供，则只返回该方向的记录 ('BUY' 或 'SELL')。
    :param limit: 如果提供，则限制返回的记录数量。
    :return: 一个包含交易数据的字典列表。
    """
    conn = sqlite3.connect(DB_PATH)
    # 让查询结果以字典形式返回，更易于使用
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = "SELECT * FROM trades"
    params = []
    conditions = []
    
    if since:
        conditions.append("utc_time >= ?")
        params.append(since)
    
    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol)
        
    if side:
        conditions.append("side = ?")
        params.append(side)
        
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
        
    sql += " ORDER BY utc_time ASC"
    
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    # 将 sqlite3.Row 对象转换为标准的字典对象
    return [dict(row) for row in rows]

def update_trade_pnl(trade_id: str, pnl: float):
    """
    更新指定交易的已实现盈亏。
    
    :param trade_id: 交易的唯一标识符
    :param pnl: 已实现盈亏值
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE trades SET pnl = ? WHERE trade_id = ?
    ''', (pnl, trade_id))
    
    conn.commit()
    conn.close()

def get_trades_by_symbol(symbol: str) -> list:
    """
    获取指定交易对的所有交易记录，按时间排序。
    用于计算该交易对的已实现盈亏。
    
    :param symbol: 交易对符号
    :return: 该交易对的所有交易记录
    """
    return get_trades(symbol=symbol)

def database_exists() -> bool:
    """
    检查数据库文件是否存在。
    """
    return os.path.exists(DB_PATH)

def insert_trade(trade_data: dict) -> bool:
    """
    插入单条交易记录到数据库。
    
    :param trade_data: 交易数据字典
    :return: 插入是否成功（True=新记录，False=重复记录）
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 生成trade_id
    trade_id = generate_trade_id(trade_data)
    
    try:
        cursor.execute('''
            INSERT INTO trades (trade_id, utc_time, symbol, side, price, quantity, quote_quantity, fee, fee_currency, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_id,
            trade_data['utc_time'],
            trade_data['symbol'],
            trade_data['side'],
            trade_data['price'],
            trade_data['quantity'],
            trade_data['quote_quantity'],
            trade_data['fee'],
            trade_data['fee_currency'],
            trade_data.get('data_source', 'excel')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.IntegrityError:
        # 重复的trade_id
        conn.close()
        return False

def get_all_trades() -> list:
    """
    获取所有交易记录。
    
    :return: 所有交易记录的列表
    """
    return get_trades()

def get_all_symbols() -> list:
    """
    获取所有唯一的交易对符号。
    
    :return: 交易对符号列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT symbol FROM trades ORDER BY symbol")
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]

def get_total_trade_count() -> int:
    """
    获取数据库中的总交易记录数。
    
    :return: 总记录数
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM trades")
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def get_currency_pnl_summary():
    """
    获取所有币种的盈亏汇总数据
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        symbol,
        COUNT(*) as trade_count,
        SUM(CASE WHEN pnl IS NOT NULL THEN pnl ELSE 0 END) as total_pnl
    FROM trades 
    GROUP BY symbol 
    ORDER BY symbol
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return [{'symbol': row[0], 'trade_count': row[1], 'total_pnl': row[2]} for row in results]

def get_trades_by_currency(currency: str):
    """
    获取指定币种的所有交易记录
    
    :param currency: 币种符号 (例如: BTC, ETH)
    :return: 交易记录列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询指定币种的所有交易记录，按时间排序
    query = """
    SELECT trade_id, utc_time, symbol, side, quantity, price, quote_quantity, 
           fee, fee_currency, pnl
    FROM trades 
    WHERE symbol LIKE ? 
    ORDER BY utc_time ASC
    """
    
    cursor.execute(query, (f"{currency}%",))
    results = cursor.fetchall()
    conn.close()
    
    # 转换为字典列表
    trades = []
    for row in results:
        trade = {
            'trade_id': row[0],
            'date': row[1],  # utc_time字段作为date使用
            'symbol': row[2],
            'side': row[3],
            'quantity': row[4],
            'price': row[5],
            'quote_quantity': row[6],
            'fee': row[7],
            'fee_coin': row[8],  # fee_currency字段作为fee_coin使用
            'pnl': row[9]
        }
        trades.append(trade)
    
    return trades

def get_historical_symbols() -> List[str]:
    """
    从数据库中获取历史交易对列表
    
    Returns:
        历史上交易过的交易对符号列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 查询数据库中所有不同的交易对
        cursor.execute("SELECT DISTINCT symbol FROM trades WHERE symbol IS NOT NULL")
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
        
    except Exception as e:
        print(f"获取历史交易对失败: {e}")
        return []
    finally:
        conn.close()

def set_metadata(key: str, value: str) -> bool:
    """
    设置应用元数据
    
    Args:
        key: 元数据键
        value: 元数据值
        
    Returns:
        设置是否成功
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"设置元数据失败 ({key}={value}): {e}")
        return False

def get_metadata(key: str) -> str:
    """
    获取应用元数据
    
    Args:
        key: 元数据键
        
    Returns:
        元数据值，如果不存在则返回None
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM sync_metadata WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
        
    except Exception as e:
        print(f"获取元数据失败 ({key}): {e}")
        return None

def get_last_sync_timestamp() -> str:
    """
    获取上次同步的时间戳
    
    Returns:
        上次同步的ISO格式时间戳，如果没有记录则返回None
    """
    return get_metadata('last_sync_timestamp')

def update_last_sync_timestamp() -> bool:
    """
    更新上次同步的时间戳为当前时间
    
    Returns:
        更新是否成功
    """
    current_time = datetime.now().isoformat()
    return set_metadata('last_sync_timestamp', current_time) 