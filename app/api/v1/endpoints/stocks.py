from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database.database import get_db
from app.schemas.stock import StockResponse, StockDailyResponse, StockListResponse
from app.services.stock_service import StockService
from app.core.exceptions import DataSourceException

router = APIRouter()

@router.get("/list", response_model=StockListResponse)
async def get_stock_list(
    market: Optional[str] = Query(None, description="市场代码 (SH/SZ/HK/US)"),
    industry: Optional[str] = Query(None, description="行业"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    try:
        stock_service = StockService(db)
        result = await stock_service.get_stock_list(
            market=market,
            industry=industry,
            page=page,
            size=size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")

@router.get("/{stock_code}", response_model=StockResponse)
async def get_stock_info(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取股票基本信息"""
    try:
        stock_service = StockService(db)
        stock = await stock_service.get_stock_by_code(stock_code)
        if not stock:
            raise HTTPException(status_code=404, detail="股票不存在")
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")

@router.get("/{stock_code}/daily", response_model=List[StockDailyResponse])
async def get_stock_daily_data(
    stock_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="数据条数"),
    db: Session = Depends(get_db)
):
    """获取股票历史行情数据"""
    try:
        stock_service = StockService(db)
        data = await stock_service.get_stock_daily_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")

@router.post("/{stock_code}/refresh")
async def refresh_stock_data(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """刷新股票数据"""
    try:
        stock_service = StockService(db)
        result = await stock_service.refresh_stock_data(stock_code)
        return {"message": "数据刷新成功", "updated_records": result}
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=f"数据源服务不可用: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据刷新失败: {str(e)}")

@router.get("/{stock_code}/realtime")
async def get_realtime_data(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取实时行情数据"""
    try:
        stock_service = StockService(db)
        data = await stock_service.get_realtime_data(stock_code)
        return data
    except DataSourceException as e:
        raise HTTPException(status_code=503, detail=f"实时数据获取失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实时数据失败: {str(e)}")

@router.get("/search/{keyword}")
async def search_stocks(
    keyword: str,
    limit: int = Query(10, ge=1, le=50, description="搜索结果数量"),
    db: Session = Depends(get_db)
):
    """搜索股票"""
    try:
        stock_service = StockService(db)
        results = await stock_service.search_stocks(keyword, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.get("/{stock_code}/technical")
async def get_technical_indicators(
    stock_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="数据条数"),
    db: Session = Depends(get_db)
):
    """获取技术指标数据"""
    try:
        stock_service = StockService(db)
        data = await stock_service.get_technical_indicators(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")