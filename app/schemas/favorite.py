from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class FavoriteBase(BaseModel):
    ts_code: str
    note: Optional[str] = None

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteUpdate(BaseModel):
    note: Optional[str] = None

class FavoriteResponse(FavoriteBase):
    id: int
    user_id: int
    stock_name: Optional[str] = None
    current_price: Optional[Decimal] = None
    change: Optional[Decimal] = None
    pct_chg: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FavoriteRealtimeData(BaseModel):
    ts_code: str
    name: str
    note: Optional[str] = None
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