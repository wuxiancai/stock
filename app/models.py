"""
数据库模型定义
基于SQLAlchemy 2.0，支持异步操作
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric, Boolean, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class StockBasic(Base, TimestampMixin):
    """股票基础信息表"""
    __tablename__ = "stock_basic"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    ts_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, comment="TS代码")
    symbol: Mapped[str] = mapped_column(String(10), index=True, comment="股票代码")
    name: Mapped[str] = mapped_column(String(50), comment="股票名称")
    area: Mapped[Optional[str]] = mapped_column(String(20), comment="地域")
    industry: Mapped[Optional[str]] = mapped_column(String(50), comment="所属行业")
    market: Mapped[str] = mapped_column(String(10), comment="市场类型")
    exchange: Mapped[str] = mapped_column(String(10), comment="交易所代码")
    curr_type: Mapped[Optional[str]] = mapped_column(String(10), comment="交易货币")
    list_status: Mapped[str] = mapped_column(String(1), comment="上市状态")
    list_date: Mapped[Optional[date]] = mapped_column(Date, comment="上市日期")
    delist_date: Mapped[Optional[date]] = mapped_column(Date, comment="退市日期")
    is_hs: Mapped[str] = mapped_column(String(1), comment="是否沪深港通标的")
    
    # 关系
    daily_quotes = relationship("DailyQuote", back_populates="stock", cascade="all, delete-orphan")
    technical_indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    nine_turn_signals = relationship("NineTurnSignal", back_populates="stock", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_stock_basic_symbol', 'symbol'),
        Index('idx_stock_basic_name', 'name'),
        Index('idx_stock_basic_industry', 'industry'),
        Index('idx_stock_basic_list_status', 'list_status'),
    )


class DailyQuote(Base, TimestampMixin):
    """日线行情数据表"""
    __tablename__ = "daily_quotes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    ts_code: Mapped[str] = mapped_column(String(20), ForeignKey("stock_basic.ts_code"), comment="TS代码")
    trade_date: Mapped[date] = mapped_column(Date, comment="交易日期")
    open: Mapped[Decimal] = mapped_column(Numeric(10, 3), comment="开盘价")
    high: Mapped[Decimal] = mapped_column(Numeric(10, 3), comment="最高价")
    low: Mapped[Decimal] = mapped_column(Numeric(10, 3), comment="最低价")
    close: Mapped[Decimal] = mapped_column(Numeric(10, 3), comment="收盘价")
    pre_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="昨收价")
    change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="涨跌额")
    pct_chg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="涨跌幅")
    vol: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="成交量(手)")
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 3), comment="成交额(千元)")
    
    # 关系
    stock = relationship("StockBasic", back_populates="daily_quotes")
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uq_daily_quotes_ts_code_date'),
        Index('idx_daily_quotes_trade_date', 'trade_date'),
        Index('idx_daily_quotes_ts_code_date', 'ts_code', 'trade_date'),
    )


class TechnicalIndicator(Base, TimestampMixin):
    """技术指标数据表"""
    __tablename__ = "technical_indicators"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    ts_code: Mapped[str] = mapped_column(String(20), ForeignKey("stock_basic.ts_code"), comment="TS代码")
    trade_date: Mapped[date] = mapped_column(Date, comment="交易日期")
    
    # 移动平均线
    ma5: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="5日均线")
    ma10: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="10日均线")
    ma20: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="20日均线")
    ma60: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="60日均线")
    
    # MACD指标
    macd_dif: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), comment="MACD DIF")
    macd_dea: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), comment="MACD DEA")
    macd_macd: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), comment="MACD MACD")
    
    # RSI指标
    rsi_6: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="6日RSI")
    rsi_12: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="12日RSI")
    rsi_24: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="24日RSI")
    
    # KDJ指标
    kdj_k: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="KDJ K值")
    kdj_d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="KDJ D值")
    kdj_j: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="KDJ J值")
    
    # 布林带指标
    boll_upper: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="布林带上轨")
    boll_mid: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="布林带中轨")
    boll_lower: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="布林带下轨")
    
    # 成交量指标
    vol_ma5: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="5日成交量均线")
    vol_ma10: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="10日成交量均线")
    vol_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="量比")
    
    # TD Sequential指标
    td_setup_buy: Mapped[Optional[int]] = mapped_column(Integer, comment="TD买入设置计数")
    td_setup_sell: Mapped[Optional[int]] = mapped_column(Integer, comment="TD卖出设置计数")
    td_countdown_buy: Mapped[Optional[int]] = mapped_column(Integer, comment="TD买入倒计时")
    td_countdown_sell: Mapped[Optional[int]] = mapped_column(Integer, comment="TD卖出倒计时")
    
    # 关系
    stock = relationship("StockBasic", back_populates="technical_indicators")
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uq_technical_indicators_ts_code_date'),
        Index('idx_technical_indicators_trade_date', 'trade_date'),
        Index('idx_technical_indicators_ts_code_date', 'ts_code', 'trade_date'),
    )


class NineTurnSignal(Base, TimestampMixin):
    """九转信号表"""
    __tablename__ = "nine_turn_signals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    ts_code: Mapped[str] = mapped_column(String(20), ForeignKey("stock_basic.ts_code"), comment="TS代码")
    trade_date: Mapped[date] = mapped_column(Date, comment="交易日期")
    signal_type: Mapped[str] = mapped_column(String(10), comment="信号类型(buy/sell)")
    signal_strength: Mapped[Decimal] = mapped_column(Numeric(5, 2), comment="信号强度(0-100)")
    setup_count: Mapped[int] = mapped_column(Integer, comment="设置计数")
    countdown_count: Mapped[Optional[int]] = mapped_column(Integer, comment="倒计时计数")
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否确认信号")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 3), comment="信号价格")
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="成交量")
    
    # 技术指标辅助
    rsi_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="RSI值")
    macd_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), comment="MACD值")
    volume_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="量比")
    
    # 关系
    stock = relationship("StockBasic", back_populates="nine_turn_signals")
    
    __table_args__ = (
        Index('idx_nine_turn_signals_trade_date', 'trade_date'),
        Index('idx_nine_turn_signals_ts_code_date', 'ts_code', 'trade_date'),
        Index('idx_nine_turn_signals_type', 'signal_type'),
        Index('idx_nine_turn_signals_confirmed', 'is_confirmed'),
        CheckConstraint("signal_type IN ('buy', 'sell')", name='ck_signal_type'),
        CheckConstraint('signal_strength >= 0 AND signal_strength <= 100', name='ck_signal_strength'),
    )


class MarketData(Base, TimestampMixin):
    """市场数据表"""
    __tablename__ = "market_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    trade_date: Mapped[date] = mapped_column(Date, unique=True, comment="交易日期")
    
    # 市场概况
    total_market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="总市值")
    total_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="总成交量")
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), comment="总成交额")
    
    # 涨跌统计
    up_count: Mapped[Optional[int]] = mapped_column(Integer, comment="上涨家数")
    down_count: Mapped[Optional[int]] = mapped_column(Integer, comment="下跌家数")
    flat_count: Mapped[Optional[int]] = mapped_column(Integer, comment="平盘家数")
    limit_up_count: Mapped[Optional[int]] = mapped_column(Integer, comment="涨停家数")
    limit_down_count: Mapped[Optional[int]] = mapped_column(Integer, comment="跌停家数")
    
    # 指数数据
    sh_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), comment="上证指数")
    sh_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="上证涨跌幅")
    sz_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), comment="深证成指")
    sz_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="深证涨跌幅")
    cy_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), comment="创业板指")
    cy_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), comment="创业板涨跌幅")
    
    __table_args__ = (
        Index('idx_market_data_trade_date', 'trade_date'),
    )


class UserWatchlist(Base, TimestampMixin):
    """用户自选股表"""
    __tablename__ = "user_watchlist"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    user_id: Mapped[int] = mapped_column(Integer, comment="用户ID")
    ts_code: Mapped[str] = mapped_column(String(20), ForeignKey("stock_basic.ts_code"), comment="TS代码")
    group_name: Mapped[str] = mapped_column(String(50), default="默认分组", comment="分组名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    notes: Mapped[Optional[str]] = mapped_column(Text, comment="备注")
    
    # 关系
    stock = relationship("StockBasic")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'ts_code', name='uq_user_watchlist_user_stock'),
        Index('idx_user_watchlist_user_id', 'user_id'),
        Index('idx_user_watchlist_group', 'user_id', 'group_name'),
    )


class DataUpdateLog(Base, TimestampMixin):
    """数据更新日志表"""
    __tablename__ = "data_update_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    task_name: Mapped[str] = mapped_column(String(100), comment="任务名称")
    data_source: Mapped[str] = mapped_column(String(20), comment="数据源")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), comment="开始时间")
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="结束时间")
    status: Mapped[str] = mapped_column(String(20), comment="状态")
    records_processed: Mapped[int] = mapped_column(Integer, default=0, comment="处理记录数")
    error_message: Mapped[Optional[str]] = mapped_column(Text, comment="错误信息")
    
    __table_args__ = (
        Index('idx_data_update_logs_task_name', 'task_name'),
        Index('idx_data_update_logs_status', 'status'),
        Index('idx_data_update_logs_start_time', 'start_time'),
        CheckConstraint("status IN ('running', 'success', 'failed', 'cancelled')", name='ck_update_status'),
    )


class SystemConfig(Base, TimestampMixin):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="主键ID")
    config_key: Mapped[str] = mapped_column(String(100), unique=True, comment="配置键")
    config_value: Mapped[str] = mapped_column(Text, comment="配置值")
    config_type: Mapped[str] = mapped_column(String(20), comment="配置类型")
    description: Mapped[Optional[str]] = mapped_column(String(200), comment="描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    
    __table_args__ = (
        Index('idx_system_config_key', 'config_key'),
        Index('idx_system_config_active', 'is_active'),
    )


# 导出所有模型
__all__ = [
    "Base",
    "TimestampMixin",
    "StockBasic",
    "DailyQuote",
    "TechnicalIndicator",
    "NineTurnSignal",
    "MarketData",
    "UserWatchlist",
    "DataUpdateLog",
    "SystemConfig",
]