from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database.database import get_db
from app.services.analysis_service import AnalysisService
from app.api.v1.endpoints.auth import oauth2_scheme
from app.services.auth_service import AuthService

router = APIRouter()

@router.get("/{stock_code}/nine-turn")
async def get_nine_turn_signals(
    stock_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    signal_type: Optional[str] = Query(None, description="信号类型"),
    db: Session = Depends(get_db)
):
    """获取九转信号"""
    try:
        analysis_service = AnalysisService(db)
        signals = await analysis_service.get_nine_turn_signals(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            signal_type=signal_type
        )
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取九转信号失败: {str(e)}")

@router.post("/{stock_code}/nine-turn/calculate")
async def calculate_nine_turn_signals(
    stock_code: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """计算九转信号"""
    try:
        auth_service = AuthService(db)
        await auth_service.get_current_user(token)
        
        analysis_service = AnalysisService(db)
        result = await analysis_service.calculate_nine_turn_signals(stock_code)
        return {"message": "九转信号计算完成", "signals_count": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算九转信号失败: {str(e)}")

@router.get("/nine-turn/screening")
async def nine_turn_screening(
    signal_type: str = Query(..., description="信号类型"),
    min_signal_value: Optional[int] = Query(None, description="最小信号值"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(get_db)
):
    """九转选股"""
    try:
        analysis_service = AnalysisService(db)
        results = await analysis_service.nine_turn_screening(
            signal_type=signal_type,
            min_signal_value=min_signal_value,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"九转选股失败: {str(e)}")

@router.get("/{stock_code}/technical-analysis")
async def get_technical_analysis(
    stock_code: str,
    period: str = Query("daily", description="周期 (daily/weekly/monthly)"),
    indicators: Optional[str] = Query(None, description="指标列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """获取技术分析"""
    try:
        analysis_service = AnalysisService(db)
        analysis = await analysis_service.get_technical_analysis(
            stock_code=stock_code,
            period=period,
            indicators=indicators.split(",") if indicators else None
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技术分析失败: {str(e)}")

@router.get("/{stock_code}/support-resistance")
async def get_support_resistance(
    stock_code: str,
    period: int = Query(20, ge=5, le=100, description="计算周期"),
    db: Session = Depends(get_db)
):
    """获取支撑阻力位"""
    try:
        analysis_service = AnalysisService(db)
        levels = await analysis_service.get_support_resistance_levels(
            stock_code=stock_code,
            period=period
        )
        return levels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取支撑阻力位失败: {str(e)}")

@router.get("/screening/custom")
async def custom_screening(
    conditions: str = Query(..., description="筛选条件JSON"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """自定义选股"""
    try:
        auth_service = AuthService(db)
        await auth_service.get_current_user(token)
        
        analysis_service = AnalysisService(db)
        results = await analysis_service.custom_screening(conditions, limit)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自定义选股失败: {str(e)}")

@router.get("/{stock_code}/pattern-recognition")
async def pattern_recognition(
    stock_code: str,
    pattern_type: Optional[str] = Query(None, description="形态类型"),
    db: Session = Depends(get_db)
):
    """形态识别"""
    try:
        analysis_service = AnalysisService(db)
        patterns = await analysis_service.pattern_recognition(
            stock_code=stock_code,
            pattern_type=pattern_type
        )
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"形态识别失败: {str(e)}")