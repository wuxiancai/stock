from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class NineTurnSignalResponse(BaseModel):
    """九转信号响应"""
    id: int
    ts_code: str
    stock_name: Optional[str] = None
    trade_date: date
    signal_type: str  # 'buy' or 'sell'
    turn_count: int
    price: Decimal
    volume: Decimal
    strength: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class NineTurnCalculateRequest(BaseModel):
    """九转计算请求"""
    ts_code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class NineTurnScreenRequest(BaseModel):
    """九转选股请求"""
    signal_type: Optional[str] = None  # 'buy', 'sell', or None for both
    min_turn_count: Optional[int] = 9
    date_range: Optional[int] = 30  # 最近多少天
    market: Optional[str] = None
    industry: Optional[str] = None

class TechnicalAnalysisRequest(BaseModel):
    """技术分析请求"""
    ts_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    indicators: Optional[List[str]] = None  # 指定要计算的指标

class TechnicalAnalysisResponse(BaseModel):
    """技术分析响应"""
    ts_code: str
    stock_name: Optional[str] = None
    analysis_date: date
    price_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    signals: List[Dict[str, Any]]
    summary: Optional[str] = None

class SupportResistanceLevel(BaseModel):
    """支撑阻力位"""
    level: Decimal
    type: str  # 'support' or 'resistance'
    strength: Decimal  # 强度 0-1
    touch_count: int  # 触及次数
    last_touch_date: date

class SupportResistanceResponse(BaseModel):
    """支撑阻力位响应"""
    ts_code: str
    stock_name: Optional[str] = None
    current_price: Decimal
    support_levels: List[SupportResistanceLevel]
    resistance_levels: List[SupportResistanceLevel]
    analysis_date: date

class CustomScreenRequest(BaseModel):
    """自定义选股请求"""
    conditions: Dict[str, Any]
    market: Optional[str] = None
    industry: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_volume: Optional[Decimal] = None
    min_market_cap: Optional[Decimal] = None
    technical_conditions: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 100

class CustomScreenResponse(BaseModel):
    """自定义选股响应"""
    ts_code: str
    stock_name: str
    current_price: Decimal
    change: Decimal
    pct_chg: Decimal
    volume: Decimal
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    pb_ratio: Optional[Decimal] = None
    match_conditions: List[str]
    score: Optional[Decimal] = None

class PatternRecognitionRequest(BaseModel):
    """形态识别请求"""
    ts_code: str
    pattern_types: Optional[List[str]] = None
    period: Optional[int] = 60  # 分析周期（天数）

class PatternRecognitionResponse(BaseModel):
    """形态识别响应"""
    ts_code: str
    stock_name: Optional[str] = None
    patterns: List[Dict[str, Any]]
    analysis_date: date
    confidence: Decimal  # 置信度