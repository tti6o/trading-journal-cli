"""
交易所数据模型

定义了标准化的数据结构，用于表示交易所的各种数据类型。
所有交易所客户端都应该返回这些标准化的数据结构。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum


class TradeSide(Enum):
    """交易方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """订单类型"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """订单状态"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


@dataclass
class Symbol:
    """交易对信息"""
    symbol: str                    # 交易对符号，如 BTCUSDT
    base_asset: str               # 基础资产，如 BTC
    quote_asset: str              # 报价资产，如 USDT
    min_qty: Optional[Decimal] = None         # 最小交易数量
    max_qty: Optional[Decimal] = None         # 最大交易数量
    step_size: Optional[Decimal] = None       # 数量步长
    min_price: Optional[Decimal] = None       # 最小价格
    max_price: Optional[Decimal] = None       # 最大价格
    tick_size: Optional[Decimal] = None       # 价格步长
    is_active: bool = True                    # 是否活跃


@dataclass
class Balance:
    """账户余额"""
    asset: str                    # 资产名称
    free: Decimal                 # 可用余额
    locked: Decimal               # 锁定余额
    
    @property
    def total(self) -> Decimal:
        """总余额"""
        return self.free + self.locked


@dataclass
class Trade:
    """交易记录"""
    id: str                       # 交易ID
    order_id: str                 # 订单ID
    symbol: str                   # 交易对
    side: TradeSide               # 交易方向
    price: Decimal                # 成交价格
    quantity: Decimal             # 成交数量
    quote_quantity: Decimal       # 成交金额
    fee: Decimal                  # 手续费
    fee_asset: str                # 手续费资产
    timestamp: datetime           # 成交时间
    is_maker: bool = False        # 是否为挂单方
    commission_asset: Optional[str] = None  # 手续费币种（兼容性）
    
    @property
    def utc_time(self) -> str:
        """UTC 时间字符串格式"""
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def local_time(self) -> str:
        """本地时间字符串格式 (CST = UTC + 8小时)"""
        # 将UTC时间转换为本地时间(CST = UTC + 8小时)
        # 与Excel数据转换后的格式保持一致
        cst_dt = self.timestamp + timedelta(hours=8)
        return cst_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容旧系统）"""
        return {
            'trade_id': self.id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'price': float(self.price),
            'quantity': float(self.quantity),
            'quote_quantity': float(self.quote_quantity),
            'fee': float(self.fee),
            'fee_currency': self.fee_asset,
            'utc_time': self.local_time,  # 使用本地时间以保持与Excel数据一致
            'is_maker': self.is_maker,
            'data_source': 'exchange_api'
        }


@dataclass
class AccountInfo:
    """账户信息"""
    balances: List[Balance]       # 余额列表
    can_trade: bool = True        # 是否可以交易
    can_withdraw: bool = True     # 是否可以提现
    can_deposit: bool = True      # 是否可以充值
    update_time: Optional[datetime] = None  # 更新时间
    
    def get_balance(self, asset: str) -> Optional[Balance]:
        """获取指定资产的余额"""
        for balance in self.balances:
            if balance.asset == asset:
                return balance
        return None
    
    def get_non_zero_balances(self, min_amount: Decimal = Decimal('0.01')) -> List[Balance]:
        """获取非零余额"""
        return [b for b in self.balances if b.total >= min_amount]


@dataclass 
class TradeData:
    """交易数据集合"""
    trades: List[Trade]           # 交易列表
    total_count: int              # 总数量
    has_more: bool = False        # 是否还有更多数据
    next_page_token: Optional[str] = None  # 下一页标记
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表（兼容旧系统）"""
        return [trade.to_dict() for trade in self.trades]


@dataclass
class SyncResult:
    """同步结果"""
    success: bool                 # 是否成功
    trades: List[Trade]           # 交易列表
    new_count: int               # 新增数量
    duplicate_count: int         # 重复数量
    total_count: int             # 总数量
    error_message: Optional[str] = None  # 错误信息
    sync_period: Optional[str] = None    # 同步周期
    since_date: Optional[str] = None     # 开始日期
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容旧系统）"""
        return {
            'success': self.success,
            'trades': [trade.to_dict() for trade in self.trades],
            'new_count': self.new_count,
            'duplicate_count': self.duplicate_count,
            'total_count': self.total_count,
            'error': self.error_message,
            'sync_period': self.sync_period,
            'since_date': self.since_date
        } 