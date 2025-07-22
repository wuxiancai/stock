from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class MarketOverview(BaseModel):
    """市场概览"""
    total_stocks: int
    rising_stocks: int
    falling_stocks: int
    unchanged_stocks: int
    total_volume: Decimal
    total_amount: Decimal
    avg_pct_chg: Decimal

class IndexData(BaseModel):
    """指数数据"""
    code: str
    name: str
    current: Decimal
    change: Decimal
    pct_chg: Decimal
    volume: Decimal
    amount: Decimal
    timestamp: datetime

class HotStock(BaseModel):
    """热门股票"""
    ts_code: str
    name: str
    price: Decimal
    change: Decimal
    pct_chg: Decimal
    volume: Decimal
    amount: Decimal
    reason: Optional[str] = None

class RankingStock(BaseModel):
    """排行榜股票"""
    ts_code: str
    name: str
    price: Decimal
    change: Decimal
    pct_chg: Decimal
    volume: Decimal
    amount: Decimal
    rank: int

class IndustryPerformance(BaseModel):
    """行业表现"""
    industry: str
    avg_pct_chg: Decimal
    rising_count: int
    falling_count: int
    total_count: int
    leading_stock: Optional[str] = None
    leading_stock_pct_chg: Optional[Decimal] = None

class TradingCalendar(BaseModel):
    """交易日历"""
    date: date
    is_trading_day: bool
    description: Optional[str] = None

class MarketNews(BaseModel):
    """市场新闻"""
    id: str
    title: str
    summary: Optional[str] = None
    source: str
    publish_time: datetime
    url: Optional[str] = None
    category: Optional[str] = None