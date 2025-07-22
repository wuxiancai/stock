from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database.database import get_db
from app.services.market_service import MarketService
from app.core.exceptions import DataSourceException

router = APIRouter()

@router.get("/overview")
async def get_market_overview(
    db: Session = Depends(get_db)
):
    """获取市场概览"""
    try:
        market_service = MarketService(db)
        overview = await market_service.get_market_overview()
        return overview
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=f"数据源服务不可用: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")

@router.get("/indices")
async def get_market_indices(
    db: Session = Depends(get_db)
):
    """获取主要指数"""
    try:
        market_service = MarketService(db)
        indices = await market_service.get_market_indices()
        return indices
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=f"数据源服务不可用: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指数数据失败: {str(e)}")

@router.get("/hot")
async def get_hot_stocks(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取热门股票"""
    try:
        market_service = MarketService(db)
        hot_stocks = await market_service.get_hot_stocks(limit)
        return hot_stocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门股票失败: {str(e)}")

@router.get("/gainers")
async def get_top_gainers(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取涨幅榜"""
    try:
        market_service = MarketService(db)
        gainers = await market_service.get_top_gainers(limit)
        return gainers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取涨幅榜失败: {str(e)}")

@router.get("/losers")
async def get_top_losers(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取跌幅榜"""
    try:
        market_service = MarketService(db)
        losers = await market_service.get_top_losers(limit)
        return losers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取跌幅榜失败: {str(e)}")

@router.get("/volume")
async def get_top_volume(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取成交量榜"""
    try:
        market_service = MarketService(db)
        volume_stocks = await market_service.get_top_volume(limit)
        return volume_stocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成交量榜失败: {str(e)}")

@router.get("/sectors")
async def get_sector_performance(
    db: Session = Depends(get_db)
):
    """获取行业表现"""
    try:
        market_service = MarketService(db)
        sectors = await market_service.get_sector_performance()
        return sectors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行业表现失败: {str(e)}")

@router.get("/calendar")
async def get_trading_calendar(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取交易日历"""
    try:
        market_service = MarketService(db)
        calendar = await market_service.get_trading_calendar(start_date, end_date)
        return calendar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易日历失败: {str(e)}")

@router.get("/news")
async def get_market_news(
    limit: int = Query(20, ge=1, le=100, description="新闻数量"),
    db: Session = Depends(get_db)
):
    """获取市场新闻"""
    try:
        market_service = MarketService(db)
        news = await market_service.get_market_news(limit)
        return news
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=f"数据源服务不可用: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场新闻失败: {str(e)}")