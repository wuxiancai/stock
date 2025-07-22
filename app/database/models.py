from sqlalchemy import Column, Integer, String, Date, DateTime, BigInteger, Text, Boolean, ForeignKey, UniqueConstraint, Index, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    market = Column(String(10), nullable=False)  # SH, SZ, HK, US
    industry = Column(String(50))
    concept = Column(String(200))
    region = Column(String(50))
    list_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    daily_data = relationship("StockDaily", back_populates="stock")
    technical_indicators = relationship("TechnicalIndicator", back_populates="stock")
    nine_turn_signals = relationship("NineTurnSignal", back_populates="stock")
    user_favorites = relationship("UserFavorite", back_populates="stock")

class StockDaily(Base):
    """历史行情数据表"""
    __tablename__ = "stock_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    open_price = Column(Numeric(10, 3))
    high_price = Column(Numeric(10, 3))
    low_price = Column(Numeric(10, 3))
    close_price = Column(Numeric(10, 3))
    volume = Column(BigInteger)
    amount = Column(Numeric(15, 2))
    turnover_rate = Column(Numeric(8, 4))
    pe_ratio = Column(Numeric(8, 2))
    pb_ratio = Column(Numeric(8, 2))
    market_cap = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    stock = relationship("Stock", back_populates="daily_data")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_stock_daily_code_date'),
        Index('idx_stock_daily_date', 'trade_date'),
        Index('idx_stock_daily_code_date', 'stock_code', 'trade_date'),
    )

class TechnicalIndicator(Base):
    """技术指标表"""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    macd_dif = Column(Numeric(8, 4))
    macd_dea = Column(Numeric(8, 4))
    macd_histogram = Column(Numeric(8, 4))
    kdj_k = Column(Numeric(8, 4))
    kdj_d = Column(Numeric(8, 4))
    kdj_j = Column(Numeric(8, 4))
    rsi_6 = Column(Numeric(8, 4))
    rsi_12 = Column(Numeric(8, 4))
    rsi_24 = Column(Numeric(8, 4))
    ma_5 = Column(Numeric(10, 3))
    ma_10 = Column(Numeric(10, 3))
    ma_20 = Column(Numeric(10, 3))
    ma_60 = Column(Numeric(10, 3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    stock = relationship("Stock", back_populates="technical_indicators")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_technical_code_date'),
        Index('idx_technical_date', 'trade_date'),
        Index('idx_technical_code_date', 'stock_code', 'trade_date'),
    )

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    favorites = relationship("UserFavorite", back_populates="user")

class UserFavorite(Base):
    """自选股表"""
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    user = relationship("User", back_populates="favorites")
    stock = relationship("Stock", back_populates="user_favorites")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'stock_code', name='uq_user_favorite'),
        Index('idx_user_favorites_user', 'user_id'),
    )

class NineTurnSignal(Base):
    """九转选股结果表"""
    __tablename__ = "nine_turn_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    signal_date = Column(Date, nullable=False)
    signal_type = Column(String(20), nullable=False)  # buy_setup, sell_setup, buy_countdown, sell_countdown
    signal_value = Column(Integer)
    price = Column(Numeric(10, 3))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    stock = relationship("Stock", back_populates="nine_turn_signals")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'signal_date', 'signal_type', name='uq_nine_turn_signal'),
        Index('idx_nine_turn_date', 'signal_date'),
        Index('idx_nine_turn_type', 'signal_type'),
        Index('idx_nine_turn_code_date', 'stock_code', 'signal_date'),
    )

class DailyBasic(Base):
    """每日基本面数据表"""
    __tablename__ = "daily_basic"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    close_price = Column(Numeric(10, 3))
    turnover_rate = Column(Numeric(8, 4))
    turnover_rate_f = Column(Numeric(8, 4))
    volume_ratio = Column(Numeric(8, 4))
    pe_ratio = Column(Numeric(8, 2))
    pe_ratio_ttm = Column(Numeric(8, 2))
    pb_ratio = Column(Numeric(8, 2))
    ps_ratio = Column(Numeric(8, 2))
    ps_ratio_ttm = Column(Numeric(8, 2))
    dv_ratio = Column(Numeric(8, 4))
    dv_ttm = Column(Numeric(8, 4))
    total_share = Column(Numeric(15, 2))
    float_share = Column(Numeric(15, 2))
    free_share = Column(Numeric(15, 2))
    total_mv = Column(Numeric(15, 2))
    circ_mv = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_daily_basic_code_date'),
        Index('idx_daily_basic_date', 'trade_date'),
        Index('idx_daily_basic_code_date', 'stock_code', 'trade_date'),
    )

class MoneyFlow(Base):
    """资金流向数据表"""
    __tablename__ = "money_flow"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False)
    trade_date = Column(Date, nullable=False)
    buy_sm_vol = Column(Numeric(15, 2))
    buy_sm_amount = Column(Numeric(15, 2))
    sell_sm_vol = Column(Numeric(15, 2))
    sell_sm_amount = Column(Numeric(15, 2))
    buy_md_vol = Column(Numeric(15, 2))
    buy_md_amount = Column(Numeric(15, 2))
    sell_md_vol = Column(Numeric(15, 2))
    sell_md_amount = Column(Numeric(15, 2))
    buy_lg_vol = Column(Numeric(15, 2))
    buy_lg_amount = Column(Numeric(15, 2))
    sell_lg_vol = Column(Numeric(15, 2))
    sell_lg_amount = Column(Numeric(15, 2))
    buy_elg_vol = Column(Numeric(15, 2))
    buy_elg_amount = Column(Numeric(15, 2))
    sell_elg_vol = Column(Numeric(15, 2))
    sell_elg_amount = Column(Numeric(15, 2))
    net_mf_vol = Column(Numeric(15, 2))
    net_mf_amount = Column(Numeric(15, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_money_flow_code_date'),
        Index('idx_money_flow_date', 'trade_date'),
        Index('idx_money_flow_code_date', 'stock_code', 'trade_date'),
    )