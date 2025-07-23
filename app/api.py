"""
API路由模块
提供股票数据的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from loguru import logger

from app.services import stock_data_service, DataServiceError
from app.data_sources import data_source_manager
from app.technical_analysis import technical_analyzer
from app.cache import StockDataCache


# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["股票数据API"])


# Pydantic模型
class StockBasicResponse(BaseModel):
    """股票基础信息响应"""
    ts_code: str = Field(..., description="股票代码")
    symbol: str = Field(..., description="股票简称")
    name: str = Field(..., description="股票名称")
    area: str = Field(..., description="地域")
    industry: str = Field(..., description="行业")
    market: str = Field(..., description="市场类型")
    exchange: str = Field(..., description="交易所")
    curr_type: str = Field(..., description="货币类型")
    list_status: str = Field(..., description="上市状态")
    list_date: Optional[str] = Field(None, description="上市日期")
    delist_date: Optional[str] = Field(None, description="退市日期")
    is_hs: str = Field(..., description="是否沪深港通")


class DailyQuoteResponse(BaseModel):
    """日线行情响应"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: str = Field(..., description="交易日期")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    pre_close: Optional[float] = Field(None, description="前收盘价")
    change: Optional[float] = Field(None, description="涨跌额")
    pct_chg: Optional[float] = Field(None, description="涨跌幅")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")


class TechnicalIndicatorResponse(BaseModel):
    """技术指标响应"""
    ts_code: str = Field(..., description="股票代码")
    trade_date: str = Field(..., description="交易日期")
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    ema12: Optional[float] = Field(None, description="12日指数均线")
    ema26: Optional[float] = Field(None, description="26日指数均线")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_histogram: Optional[float] = Field(None, description="MACD柱状图")
    rsi: Optional[float] = Field(None, description="RSI")
    kdj_k: Optional[float] = Field(None, description="KDJ-K")
    kdj_d: Optional[float] = Field(None, description="KDJ-D")
    kdj_j: Optional[float] = Field(None, description="KDJ-J")
    bb_upper: Optional[float] = Field(None, description="布林带上轨")
    bb_middle: Optional[float] = Field(None, description="布林带中轨")
    bb_lower: Optional[float] = Field(None, description="布林带下轨")
    obv: Optional[float] = Field(None, description="能量潮")
    ad: Optional[float] = Field(None, description="累积/派发线")
    td_setup_buy: int = Field(0, description="TD买入设置")
    td_setup_sell: int = Field(0, description="TD卖出设置")
    td_countdown_buy: int = Field(0, description="TD买入倒计时")
    td_countdown_sell: int = Field(0, description="TD卖出倒计时")
    nine_turn_signal: int = Field(0, description="九转信号")
    signal_strength: float = Field(0.0, description="信号强度")


class NineTurnSignalResponse(BaseModel):
    """九转信号响应"""
    ts_code: str = Field(..., description="股票代码")
    signal_date: str = Field(..., description="信号日期")
    signal_type: str = Field(..., description="信号类型")
    signal_strength: float = Field(..., description="信号强度")
    signal_description: str = Field(..., description="信号描述")
    close_price: float = Field(..., description="收盘价")
    setup_buy_count: int = Field(0, description="买入设置计数")
    setup_sell_count: int = Field(0, description="卖出设置计数")
    countdown_buy_count: int = Field(0, description="买入倒计时计数")
    countdown_sell_count: int = Field(0, description="卖出倒计时计数")


class StockListResponse(BaseModel):
    """股票列表响应"""
    stocks: List[StockBasicResponse]
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")


class StockDetailResponse(BaseModel):
    """股票详情响应"""
    basic_info: StockBasicResponse
    latest_quote: Optional[DailyQuoteResponse]
    technical_indicator: Optional[TechnicalIndicatorResponse]
    nine_turn_signals: List[NineTurnSignalResponse]


class UpdateResponse(BaseModel):
    """更新响应"""
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")
    count: Optional[int] = Field(None, description="处理数量")
    total_count: Optional[int] = Field(None, description="总数量")
    failed_count: Optional[int] = Field(None, description="失败数量")
    signal_count: Optional[int] = Field(None, description="信号数量")


# API路由
@router.get("/stocks", response_model=StockListResponse, summary="获取股票列表")
async def get_stocks(
    exchange: Optional[str] = Query(None, description="交易所代码"),
    market: Optional[str] = Query(None, description="市场类型"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取股票列表
    
    - **exchange**: 交易所代码 (SSE/SZSE)
    - **market**: 市场类型 (主板/创业板/科创板)
    - **limit**: 每页数量 (1-1000)
    - **offset**: 偏移量
    """
    try:
        result = await stock_data_service.get_stock_list(
            exchange=exchange,
            market=market,
            limit=limit,
            offset=offset
        )
        return StockListResponse(**result)
    except DataServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/stocks/{ts_code}", response_model=StockDetailResponse, summary="获取股票详情")
async def get_stock_detail(
    ts_code: str = Path(..., description="股票代码", regex=r"^\d{6}\.(SH|SZ)$")
):
    """
    获取股票详情
    
    - **ts_code**: 股票代码 (如: 000001.SZ)
    """
    try:
        result = await stock_data_service.get_stock_detail(ts_code)
        return StockDetailResponse(**result)
    except DataServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取股票详情失败 {ts_code}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/stocks/{ts_code}/quotes", response_model=List[DailyQuoteResponse], summary="获取股票历史行情")
async def get_stock_quotes(
    ts_code: str = Path(..., description="股票代码", regex=r"^\d{6}\.(SH|SZ)$"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYYMMDD)"),
    limit: int = Query(100, ge=1, le=500, description="数量限制")
):
    """
    获取股票历史行情
    
    - **ts_code**: 股票代码
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **limit**: 数量限制
    """
    try:
        # 这里需要实现获取历史行情的逻辑
        # 暂时返回空列表
        return []
    except Exception as e:
        logger.error(f"获取股票历史行情失败 {ts_code}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/stocks/{ts_code}/technical", response_model=List[TechnicalIndicatorResponse], summary="获取技术指标")
async def get_technical_indicators(
    ts_code: str = Path(..., description="股票代码", regex=r"^\d{6}\.(SH|SZ)$"),
    days: int = Query(30, ge=1, le=250, description="天数")
):
    """
    获取技术指标
    
    - **ts_code**: 股票代码
    - **days**: 天数
    """
    try:
        # 这里需要实现获取技术指标的逻辑
        # 暂时返回空列表
        return []
    except Exception as e:
        logger.error(f"获取技术指标失败 {ts_code}: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/nine-turn", response_model=List[NineTurnSignalResponse], summary="获取九转信号股票")
async def get_nine_turn_stocks(
    signal_type: str = Query("all", regex="^(all|buy|sell)$", description="信号类型"),
    days: int = Query(7, ge=1, le=30, description="天数"),
    limit: int = Query(50, ge=1, le=200, description="数量限制")
):
    """
    获取九转信号股票
    
    - **signal_type**: 信号类型 (all/buy/sell)
    - **days**: 查看最近多少天的信号
    - **limit**: 数量限制
    """
    try:
        result = await stock_data_service.get_nine_turn_stocks(
            signal_type=signal_type,
            days=days,
            limit=limit
        )
        return [NineTurnSignalResponse(**signal) for signal in result]
    except DataServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取九转信号股票失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/realtime/quotes", summary="获取实时行情")
async def get_realtime_quotes(
    limit: int = Query(100, ge=1, le=1000, description="数量限制")
):
    """
    获取实时行情
    
    - **limit**: 数量限制
    """
    try:
        df = await data_source_manager.get_realtime_quotes(use_cache=True)
        
        if df.empty:
            return {"data": [], "count": 0, "message": "暂无数据"}
        
        # 转换数据格式
        data = df.head(limit).to_dict('records')
        
        return {
            "data": data,
            "count": len(data),
            "timestamp": datetime.now().isoformat(),
            "message": "获取成功"
        }
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/market/sentiment", summary="获取市场情绪")
async def get_market_sentiment():
    """
    获取市场情绪数据
    """
    try:
        sentiment_data = await data_source_manager.get_market_sentiment()
        
        # 转换DataFrame为字典
        result = {}
        for key, df in sentiment_data.items():
            if key == "timestamp":
                result[key] = df
            else:
                result[key] = df.to_dict('records') if not df.empty else []
        
        return result
    except Exception as e:
        logger.error(f"获取市场情绪失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/market/hot-stocks", summary="获取热门股票")
async def get_hot_stocks(
    rank_type: str = Query("volume", regex="^(volume|amount)$", description="排行类型"),
    limit: int = Query(50, ge=1, le=200, description="数量限制")
):
    """
    获取热门股票排行
    
    - **rank_type**: 排行类型 (volume/amount)
    - **limit**: 数量限制
    """
    try:
        df = await data_source_manager.get_hot_stocks(rank_type=rank_type)
        
        if df.empty:
            return {"data": [], "count": 0, "message": "暂无数据"}
        
        data = df.head(limit).to_dict('records')
        
        return {
            "data": data,
            "count": len(data),
            "rank_type": rank_type,
            "timestamp": datetime.now().isoformat(),
            "message": "获取成功"
        }
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


# 数据更新API
@router.post("/update/stock-basic", response_model=UpdateResponse, summary="更新股票基础信息")
async def update_stock_basic(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="强制更新")
):
    """
    更新股票基础信息
    
    - **force**: 是否强制更新
    """
    try:
        # 在后台任务中执行更新
        background_tasks.add_task(
            stock_data_service.update_stock_basic,
            force_update=force
        )
        
        return UpdateResponse(
            status="accepted",
            message="股票基础信息更新任务已启动"
        )
    except Exception as e:
        logger.error(f"启动股票基础信息更新失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/update/daily-quotes", response_model=UpdateResponse, summary="更新日线行情")
async def update_daily_quotes(
    background_tasks: BackgroundTasks,
    ts_codes: Optional[List[str]] = Query(None, description="股票代码列表"),
    trade_date: Optional[str] = Query(None, description="交易日期 (YYYYMMDD)")
):
    """
    更新日线行情
    
    - **ts_codes**: 股票代码列表
    - **trade_date**: 交易日期
    """
    try:
        # 在后台任务中执行更新
        background_tasks.add_task(
            stock_data_service.update_daily_quotes,
            ts_codes=ts_codes,
            trade_date=trade_date
        )
        
        return UpdateResponse(
            status="accepted",
            message="日线行情更新任务已启动"
        )
    except Exception as e:
        logger.error(f"启动日线行情更新失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/update/technical-indicators", response_model=UpdateResponse, summary="更新技术指标")
async def update_technical_indicators(
    background_tasks: BackgroundTasks,
    ts_codes: Optional[List[str]] = Query(None, description="股票代码列表")
):
    """
    更新技术指标
    
    - **ts_codes**: 股票代码列表
    """
    try:
        # 在后台任务中执行更新
        background_tasks.add_task(
            stock_data_service.update_technical_indicators,
            ts_codes=ts_codes
        )
        
        return UpdateResponse(
            status="accepted",
            message="技术指标更新任务已启动"
        )
    except Exception as e:
        logger.error(f"启动技术指标更新失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/update/nine-turn-signals", response_model=UpdateResponse, summary="更新九转信号")
async def update_nine_turn_signals(
    background_tasks: BackgroundTasks,
    ts_codes: Optional[List[str]] = Query(None, description="股票代码列表")
):
    """
    更新九转信号
    
    - **ts_codes**: 股票代码列表
    """
    try:
        # 在后台任务中执行更新
        background_tasks.add_task(
            stock_data_service.update_nine_turn_signals,
            ts_codes=ts_codes
        )
        
        return UpdateResponse(
            status="accepted",
            message="九转信号更新任务已启动"
        )
    except Exception as e:
        logger.error(f"启动九转信号更新失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


# 健康检查API
@router.get("/health", summary="健康检查")
async def health_check():
    """
    系统健康检查
    """
    try:
        # 检查数据源状态
        data_source_health = await data_source_manager.health_check()
        
        # 检查缓存状态
        cache_health = await StockDataCache.health_check()
        
        # 检查数据库状态
        # 这里需要实现数据库健康检查
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_sources": data_source_health,
            "cache": cache_health,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


# 导出路由器
__all__ = ["router"]