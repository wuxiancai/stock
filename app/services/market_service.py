from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncio

from app.database.models import Stock, StockDaily, DailyBasic, MoneyFlow
from app.schemas.market import (
    MarketOverview, IndexData, HotStock, RankingStock,
    IndustryPerformance, TradingCalendar, MarketNews
)
from app.services.data_source_service import DataSourceService

class MarketService:
    """市场服务"""
    
    def __init__(self, db: Session):
        self.db = db

    async def get_market_overview(self) -> MarketOverview:
        """获取市场概览"""
        try:
            # 获取最新交易日
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                latest_date = date.today()
            
            # 获取当日所有股票数据
            daily_data = self.db.query(StockDaily).filter(
                StockDaily.trade_date == latest_date
            ).all()
            
            if not daily_data:
                return MarketOverview(
                    total_stocks=0,
                    rising_stocks=0,
                    falling_stocks=0,
                    unchanged_stocks=0,
                    total_volume=Decimal('0'),
                    total_amount=Decimal('0'),
                    avg_pct_chg=Decimal('0')
                )
            
            # 统计涨跌股票数量
            rising_stocks = sum(1 for d in daily_data if d.pct_chg and d.pct_chg > 0)
            falling_stocks = sum(1 for d in daily_data if d.pct_chg and d.pct_chg < 0)
            unchanged_stocks = sum(1 for d in daily_data if d.pct_chg and d.pct_chg == 0)
            
            # 计算总成交量和成交额
            total_volume = sum(d.vol or Decimal('0') for d in daily_data)
            total_amount = sum(d.amount or Decimal('0') for d in daily_data)
            
            # 计算平均涨跌幅
            valid_pct_chg = [d.pct_chg for d in daily_data if d.pct_chg is not None]
            avg_pct_chg = sum(valid_pct_chg) / len(valid_pct_chg) if valid_pct_chg else Decimal('0')
            
            return MarketOverview(
                total_stocks=len(daily_data),
                rising_stocks=rising_stocks,
                falling_stocks=falling_stocks,
                unchanged_stocks=unchanged_stocks,
                total_volume=total_volume,
                total_amount=total_amount,
                avg_pct_chg=round(avg_pct_chg, 2)
            )
            
        except Exception as e:
            print(f"获取市场概览失败: {e}")
            return MarketOverview(
                total_stocks=0,
                rising_stocks=0,
                falling_stocks=0,
                unchanged_stocks=0,
                total_volume=Decimal('0'),
                total_amount=Decimal('0'),
                avg_pct_chg=Decimal('0')
            )

    async def get_major_indices(self) -> List[IndexData]:
        """获取主要指数"""
        try:
            async with DataSourceService() as data_service:
                # 获取主要指数数据
                indices = ["000001.SH", "399001.SZ", "399006.SZ"]  # 上证指数、深证成指、创业板指
                index_data = []
                
                for index_code in indices:
                    data = await data_service.get_index_data(index_code)
                    if data:
                        index_data.append(IndexData(
                            code=data['code'],
                            name=data['name'],
                            current=Decimal(str(data['current'])),
                            change=Decimal(str(data['change'])),
                            pct_chg=Decimal(str(data['pct_chg'])),
                            volume=Decimal(str(data['volume'])),
                            amount=Decimal(str(data['amount'])),
                            timestamp=datetime.fromisoformat(data['timestamp'])
                        ))
                
                return index_data
                
        except Exception as e:
            print(f"获取主要指数失败: {e}")
            return []

    async def get_hot_stocks(self, limit: int = 20) -> List[HotStock]:
        """获取热门股票"""
        try:
            # 获取最新交易日
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            # 获取成交额最大的股票作为热门股票
            hot_stocks_data = self.db.query(StockDaily, Stock).join(
                Stock, StockDaily.ts_code == Stock.ts_code
            ).filter(
                StockDaily.trade_date == latest_date
            ).order_by(desc(StockDaily.amount)).limit(limit).all()
            
            hot_stocks = []
            for daily, stock in hot_stocks_data:
                hot_stocks.append(HotStock(
                    ts_code=daily.ts_code,
                    name=stock.name,
                    price=daily.close or Decimal('0'),
                    change=daily.change or Decimal('0'),
                    pct_chg=daily.pct_chg or Decimal('0'),
                    volume=daily.vol or Decimal('0'),
                    amount=daily.amount or Decimal('0'),
                    reason="成交活跃"
                ))
            
            return hot_stocks
            
        except Exception as e:
            print(f"获取热门股票失败: {e}")
            return []

    async def get_top_gainers(self, limit: int = 20) -> List[RankingStock]:
        """获取涨幅榜"""
        try:
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            gainers_data = self.db.query(StockDaily, Stock).join(
                Stock, StockDaily.ts_code == Stock.ts_code
            ).filter(
                StockDaily.trade_date == latest_date
            ).order_by(desc(StockDaily.pct_chg)).limit(limit).all()
            
            gainers = []
            for rank, (daily, stock) in enumerate(gainers_data, 1):
                gainers.append(RankingStock(
                    ts_code=daily.ts_code,
                    name=stock.name,
                    price=daily.close or Decimal('0'),
                    change=daily.change or Decimal('0'),
                    pct_chg=daily.pct_chg or Decimal('0'),
                    volume=daily.vol or Decimal('0'),
                    amount=daily.amount or Decimal('0'),
                    rank=rank
                ))
            
            return gainers
            
        except Exception as e:
            print(f"获取涨幅榜失败: {e}")
            return []

    async def get_top_losers(self, limit: int = 20) -> List[RankingStock]:
        """获取跌幅榜"""
        try:
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            losers_data = self.db.query(StockDaily, Stock).join(
                Stock, StockDaily.ts_code == Stock.ts_code
            ).filter(
                StockDaily.trade_date == latest_date
            ).order_by(StockDaily.pct_chg).limit(limit).all()
            
            losers = []
            for rank, (daily, stock) in enumerate(losers_data, 1):
                losers.append(RankingStock(
                    ts_code=daily.ts_code,
                    name=stock.name,
                    price=daily.close or Decimal('0'),
                    change=daily.change or Decimal('0'),
                    pct_chg=daily.pct_chg or Decimal('0'),
                    volume=daily.vol or Decimal('0'),
                    amount=daily.amount or Decimal('0'),
                    rank=rank
                ))
            
            return losers
            
        except Exception as e:
            print(f"获取跌幅榜失败: {e}")
            return []

    async def get_volume_leaders(self, limit: int = 20) -> List[RankingStock]:
        """获取成交量榜"""
        try:
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            volume_data = self.db.query(StockDaily, Stock).join(
                Stock, StockDaily.ts_code == Stock.ts_code
            ).filter(
                StockDaily.trade_date == latest_date
            ).order_by(desc(StockDaily.vol)).limit(limit).all()
            
            volume_leaders = []
            for rank, (daily, stock) in enumerate(volume_data, 1):
                volume_leaders.append(RankingStock(
                    ts_code=daily.ts_code,
                    name=stock.name,
                    price=daily.close or Decimal('0'),
                    change=daily.change or Decimal('0'),
                    pct_chg=daily.pct_chg or Decimal('0'),
                    volume=daily.vol or Decimal('0'),
                    amount=daily.amount or Decimal('0'),
                    rank=rank
                ))
            
            return volume_leaders
            
        except Exception as e:
            print(f"获取成交量榜失败: {e}")
            return []

    async def get_amount_leaders(self, limit: int = 20) -> List[RankingStock]:
        """获取成交额榜"""
        try:
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            amount_data = self.db.query(StockDaily, Stock).join(
                Stock, StockDaily.ts_code == Stock.ts_code
            ).filter(
                StockDaily.trade_date == latest_date
            ).order_by(desc(StockDaily.amount)).limit(limit).all()
            
            amount_leaders = []
            for rank, (daily, stock) in enumerate(amount_data, 1):
                amount_leaders.append(RankingStock(
                    ts_code=daily.ts_code,
                    name=stock.name,
                    price=daily.close or Decimal('0'),
                    change=daily.change or Decimal('0'),
                    pct_chg=daily.pct_chg or Decimal('0'),
                    volume=daily.vol or Decimal('0'),
                    amount=daily.amount or Decimal('0'),
                    rank=rank
                ))
            
            return amount_leaders
            
        except Exception as e:
            print(f"获取成交额榜失败: {e}")
            return []

    async def get_industry_performance(self) -> List[IndustryPerformance]:
        """获取行业表现"""
        try:
            latest_date = self.db.query(func.max(StockDaily.trade_date)).scalar()
            if not latest_date:
                return []
            
            # 按行业统计涨跌情况
            industry_stats = self.db.query(
                Stock.industry,
                func.avg(StockDaily.pct_chg).label('avg_pct_chg'),
                func.count().label('total_count'),
                func.sum(func.case([(StockDaily.pct_chg > 0, 1)], else_=0)).label('rising_count'),
                func.sum(func.case([(StockDaily.pct_chg < 0, 1)], else_=0)).label('falling_count')
            ).join(
                StockDaily, Stock.ts_code == StockDaily.ts_code
            ).filter(
                and_(
                    StockDaily.trade_date == latest_date,
                    Stock.industry.isnot(None)
                )
            ).group_by(Stock.industry).order_by(desc('avg_pct_chg')).limit(20).all()
            
            industry_performance = []
            for stat in industry_stats:
                # 找出该行业的领涨股
                leading_stock_data = self.db.query(StockDaily, Stock).join(
                    Stock, StockDaily.ts_code == Stock.ts_code
                ).filter(
                    and_(
                        StockDaily.trade_date == latest_date,
                        Stock.industry == stat.industry
                    )
                ).order_by(desc(StockDaily.pct_chg)).first()
                
                leading_stock = None
                leading_stock_pct_chg = None
                if leading_stock_data:
                    leading_stock = leading_stock_data[1].name
                    leading_stock_pct_chg = leading_stock_data[0].pct_chg
                
                industry_performance.append(IndustryPerformance(
                    industry=stat.industry,
                    avg_pct_chg=round(Decimal(str(stat.avg_pct_chg or 0)), 2),
                    rising_count=int(stat.rising_count or 0),
                    falling_count=int(stat.falling_count or 0),
                    total_count=int(stat.total_count or 0),
                    leading_stock=leading_stock,
                    leading_stock_pct_chg=leading_stock_pct_chg
                ))
            
            return industry_performance
            
        except Exception as e:
            print(f"获取行业表现失败: {e}")
            return []

    async def get_trading_calendar(self, start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None) -> List[TradingCalendar]:
        """获取交易日历"""
        try:
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            # 简化的交易日历（实际应用中应该从专门的交易日历API获取）
            calendar = []
            current_date = start_date
            
            while current_date <= end_date:
                # 简单判断：周一到周五为交易日
                is_trading_day = current_date.weekday() < 5
                
                calendar.append(TradingCalendar(
                    date=current_date,
                    is_trading_day=is_trading_day,
                    description="正常交易日" if is_trading_day else "休市"
                ))
                
                current_date += timedelta(days=1)
            
            return calendar
            
        except Exception as e:
            print(f"获取交易日历失败: {e}")
            return []

    async def get_market_news(self, limit: int = 20) -> List[MarketNews]:
        """获取市场新闻"""
        try:
            async with DataSourceService() as data_service:
                news_data = await data_service.get_market_news(limit)
                
                market_news = []
                for news in news_data:
                    market_news.append(MarketNews(
                        id=news['id'],
                        title=news['title'],
                        summary=news.get('summary'),
                        source=news['source'],
                        publish_time=datetime.fromisoformat(news['publish_time']),
                        url=news.get('url'),
                        category=news.get('category')
                    ))
                
                return market_news
                
        except Exception as e:
            print(f"获取市场新闻失败: {e}")
            return []

    async def get_money_flow_ranking(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取资金流向排行"""
        try:
            latest_date = self.db.query(func.max(MoneyFlow.trade_date)).scalar()
            if not latest_date:
                return []
            
            money_flow_data = self.db.query(MoneyFlow, Stock).join(
                Stock, MoneyFlow.ts_code == Stock.ts_code
            ).filter(
                MoneyFlow.trade_date == latest_date
            ).order_by(desc(MoneyFlow.net_mf_amount)).limit(limit).all()
            
            ranking = []
            for rank, (flow, stock) in enumerate(money_flow_data, 1):
                ranking.append({
                    "rank": rank,
                    "ts_code": flow.ts_code,
                    "name": stock.name,
                    "net_inflow": flow.net_mf_amount or Decimal('0'),
                    "buy_amount": (flow.buy_elg_amount or Decimal('0')) + (flow.buy_lg_amount or Decimal('0')),
                    "sell_amount": (flow.sell_elg_amount or Decimal('0')) + (flow.sell_lg_amount or Decimal('0')),
                    "trade_date": flow.trade_date
                })
            
            return ranking
            
        except Exception as e:
            print(f"获取资金流向排行失败: {e}")
            return []