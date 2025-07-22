from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

class StockBase(BaseModel):
    ts_code: str
    symbol: str
    name: str
    area: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None
    list_date: Optional[date] = None

class StockResponse(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StockDailyBase(BaseModel):
    ts_code: str
    trade_date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    pre_close: Optional[Decimal] = None
    change: Optional[Decimal] = None
    pct_chg: Optional[Decimal] = None
    vol: Optional[Decimal] = None
    amount: Optional[Decimal] = None

class StockDailyResponse(StockDailyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StockSearchRequest(BaseModel):
    keyword: str
    limit: Optional[int] = 20

class StockListRequest(BaseModel):
    market: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20

class StockHistoryRequest(BaseModel):
    ts_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: Optional[int] = 100

class RealtimeQuote(BaseModel):
    ts_code: str
    name: str
    price: Decimal
    change: Decimal
    pct_chg: Decimal
    volume: Decimal
    amount: Decimal
    high: Decimal
    low: Decimal
    open: Decimal
    pre_close: Decimal
    timestamp: datetime

class TechnicalIndicatorResponse(BaseModel):
    id: int
    ts_code: str
    trade_date: date
    ma5: Optional[Decimal] = None
    ma10: Optional[Decimal] = None
    ma20: Optional[Decimal] = None
    ma60: Optional[Decimal] = None
    ema12: Optional[Decimal] = None
    ema26: Optional[Decimal] = None
    macd: Optional[Decimal] = None
    macd_signal: Optional[Decimal] = None
    macd_hist: Optional[Decimal] = None
    rsi: Optional[Decimal] = None
    kdj_k: Optional[Decimal] = None
    kdj_d: Optional[Decimal] = None
    kdj_j: Optional[Decimal] = None
    boll_upper: Optional[Decimal] = None
    boll_mid: Optional[Decimal] = None
    boll_lower: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True