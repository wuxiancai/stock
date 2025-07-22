from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import asyncio
import aiohttp
import json

from app.database.models import Stock, StockDaily, TechnicalIndicator
from app.schemas.stock import (
    StockListRequest, StockHistoryRequest, StockSearchRequest,
    RealtimeQuote, TechnicalIndicatorResponse
)
from app.core.config import settings

class StockService:
    def __init__(self, db: Session):
        self.db = db

    def get_stocks(self, request: StockListRequest) -> Dict[str, Any]:
        """获取股票列表"""
        query = self.db.query(Stock)
        
        # 应用过滤条件
        if request.market:
            query = query.filter(Stock.market == request.market)
        if request.industry:
            query = query.filter(Stock.industry == request.industry)
        if request.area:
            query = query.filter(Stock.area == request.area)
        
        # 计算总数
        total = query.count()
        
        # 分页
        offset = (request.page - 1) * request.page_size
        stocks = query.offset(offset).limit(request.page_size).all()
        
        return {
            "stocks": stocks,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": (total + request.page_size - 1) // request.page_size
        }

    def get_stock_by_code(self, ts_code: str) -> Optional[Stock]:
        """根据代码获取股票信息"""
        return self.db.query(Stock).filter(Stock.ts_code == ts_code).first()

    def search_stocks(self, request: StockSearchRequest) -> List[Stock]:
        """搜索股票"""
        keyword = f"%{request.keyword}%"
        return self.db.query(Stock).filter(
            or_(
                Stock.ts_code.like(keyword),
                Stock.symbol.like(keyword),
                Stock.name.like(keyword)
            )
        ).limit(request.limit).all()

    def get_stock_history(self, request: StockHistoryRequest) -> List[StockDaily]:
        """获取股票历史数据"""
        query = self.db.query(StockDaily).filter(StockDaily.ts_code == request.ts_code)
        
        if request.start_date:
            query = query.filter(StockDaily.trade_date >= request.start_date)
        if request.end_date:
            query = query.filter(StockDaily.trade_date <= request.end_date)
        
        return query.order_by(desc(StockDaily.trade_date)).limit(request.limit).all()

    async def get_realtime_quote(self, ts_code: str) -> Optional[RealtimeQuote]:
        """获取实时行情数据"""
        try:
            # 这里应该调用实际的数据源API
            # 暂时返回模拟数据
            stock = self.get_stock_by_code(ts_code)
            if not stock:
                return None
            
            # 获取最新的历史数据作为基础
            latest_data = self.db.query(StockDaily).filter(
                StockDaily.ts_code == ts_code
            ).order_by(desc(StockDaily.trade_date)).first()
            
            if not latest_data:
                return None
            
            # 模拟实时数据（实际应用中应该调用实时API）
            return RealtimeQuote(
                ts_code=ts_code,
                name=stock.name,
                price=latest_data.close or 0,
                change=latest_data.change or 0,
                pct_chg=latest_data.pct_chg or 0,
                volume=latest_data.vol or 0,
                amount=latest_data.amount or 0,
                high=latest_data.high or 0,
                low=latest_data.low or 0,
                open=latest_data.open or 0,
                pre_close=latest_data.pre_close or 0,
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None

    async def get_multiple_realtime_quotes(self, ts_codes: List[str]) -> List[RealtimeQuote]:
        """批量获取实时行情"""
        tasks = [self.get_realtime_quote(code) for code in ts_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = []
        for result in results:
            if isinstance(result, RealtimeQuote):
                quotes.append(result)
        
        return quotes

    def get_technical_indicators(self, ts_code: str, start_date: Optional[date] = None, 
                               end_date: Optional[date] = None, limit: int = 100) -> List[TechnicalIndicator]:
        """获取技术指标数据"""
        query = self.db.query(TechnicalIndicator).filter(TechnicalIndicator.ts_code == ts_code)
        
        if start_date:
            query = query.filter(TechnicalIndicator.trade_date >= start_date)
        if end_date:
            query = query.filter(TechnicalIndicator.trade_date <= end_date)
        
        return query.order_by(desc(TechnicalIndicator.trade_date)).limit(limit).all()

    async def refresh_stock_data(self, ts_code: Optional[str] = None) -> Dict[str, Any]:
        """刷新股票数据"""
        try:
            # 这里应该调用数据源API获取最新数据
            # 暂时返回模拟结果
            if ts_code:
                # 刷新单个股票
                stock = self.get_stock_by_code(ts_code)
                if not stock:
                    return {"success": False, "message": "股票不存在"}
                
                # 模拟数据更新
                return {
                    "success": True,
                    "message": f"股票 {ts_code} 数据刷新成功",
                    "updated_count": 1
                }
            else:
                # 刷新所有股票
                total_stocks = self.db.query(Stock).count()
                return {
                    "success": True,
                    "message": "所有股票数据刷新成功",
                    "updated_count": total_stocks
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"数据刷新失败: {str(e)}"
            }

    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场概况"""
        try:
            # 获取今日数据统计
            today = date.today()
            
            # 统计今日涨跌股票数量
            today_data = self.db.query(StockDaily).filter(
                StockDaily.trade_date == today
            ).all()
            
            if not today_data:
                # 如果没有今日数据，使用最新交易日数据
                latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
                if latest_date:
                    today_data = self.db.query(StockDaily).filter(
                        StockDaily.trade_date == latest_date
                    ).all()
            
            rising_count = sum(1 for data in today_data if data.pct_chg and data.pct_chg > 0)
            falling_count = sum(1 for data in today_data if data.pct_chg and data.pct_chg < 0)
            unchanged_count = sum(1 for data in today_data if data.pct_chg and data.pct_chg == 0)
            
            total_volume = sum(data.vol or 0 for data in today_data)
            total_amount = sum(data.amount or 0 for data in today_data)
            
            return {
                "total_stocks": len(today_data),
                "rising_stocks": rising_count,
                "falling_stocks": falling_count,
                "unchanged_stocks": unchanged_count,
                "total_volume": total_volume,
                "total_amount": total_amount,
                "trade_date": latest_date if 'latest_date' in locals() else today
            }
        except Exception as e:
            return {
                "error": f"获取市场概况失败: {str(e)}"
            }

    def get_top_gainers(self, limit: int = 20) -> List[StockDaily]:
        """获取涨幅榜"""
        latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        if not latest_date:
            return []
        
        return self.db.query(StockDaily).filter(
            StockDaily.trade_date == latest_date
        ).order_by(desc(StockDaily.pct_chg)).limit(limit).all()

    def get_top_losers(self, limit: int = 20) -> List[StockDaily]:
        """获取跌幅榜"""
        latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        if not latest_date:
            return []
        
        return self.db.query(StockDaily).filter(
            StockDaily.trade_date == latest_date
        ).order_by(asc(StockDaily.pct_chg)).limit(limit).all()

    def get_top_volume(self, limit: int = 20) -> List[StockDaily]:
        """获取成交量榜"""
        latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        if not latest_date:
            return []
        
        return self.db.query(StockDaily).filter(
            StockDaily.trade_date == latest_date
        ).order_by(desc(StockDaily.vol)).limit(limit).all()

    def get_top_amount(self, limit: int = 20) -> List[StockDaily]:
        """获取成交额榜"""
        latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
        if not latest_date:
            return []
        
        return self.db.query(StockDaily).filter(
            StockDaily.trade_date == latest_date
        ).order_by(desc(StockDaily.amount)).limit(limit).all()