import aiohttp
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import json
import time

from app.core.config import settings

class DataSourceService:
    """数据源服务 - 负责从外部API获取股票数据"""
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 0.1  # API调用间隔
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_stock_list(self, market: str = "SSE") -> List[Dict[str, Any]]:
        """获取股票列表"""
        try:
            # 模拟API调用 - 实际应用中应该调用真实的数据源API
            await asyncio.sleep(self.rate_limit_delay)
            
            # 这里应该调用实际的API，比如tushare、东方财富等
            # 暂时返回模拟数据
            mock_stocks = [
                {
                    "ts_code": "000001.SZ",
                    "symbol": "000001",
                    "name": "平安银行",
                    "area": "深圳",
                    "industry": "银行",
                    "market": "主板",
                    "list_date": "1991-04-03"
                },
                {
                    "ts_code": "000002.SZ",
                    "symbol": "000002",
                    "name": "万科A",
                    "area": "深圳",
                    "industry": "房地产开发",
                    "market": "主板",
                    "list_date": "1991-01-29"
                }
            ]
            
            return mock_stocks
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

    async def get_daily_data(self, ts_code: str, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """获取日线数据"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟API调用
            # 实际应用中应该调用真实的数据源API
            if not start_date:
                start_date = date.today() - timedelta(days=365)
            if not end_date:
                end_date = date.today()
            
            # 生成模拟数据
            mock_data = []
            current_date = start_date
            base_price = 10.0
            
            while current_date <= end_date:
                # 跳过周末
                if current_date.weekday() < 5:
                    # 模拟价格波动
                    import random
                    change_pct = random.uniform(-0.1, 0.1)
                    new_price = base_price * (1 + change_pct)
                    
                    mock_data.append({
                        "ts_code": ts_code,
                        "trade_date": current_date.strftime("%Y%m%d"),
                        "open": round(base_price * random.uniform(0.99, 1.01), 2),
                        "high": round(max(base_price, new_price) * random.uniform(1.0, 1.05), 2),
                        "low": round(min(base_price, new_price) * random.uniform(0.95, 1.0), 2),
                        "close": round(new_price, 2),
                        "pre_close": round(base_price, 2),
                        "change": round(new_price - base_price, 2),
                        "pct_chg": round(change_pct * 100, 2),
                        "vol": random.randint(1000000, 10000000),
                        "amount": random.randint(10000000, 100000000)
                    })
                    
                    base_price = new_price
                
                current_date += timedelta(days=1)
            
            return mock_data[-100:]  # 返回最近100条数据
            
        except Exception as e:
            print(f"获取日线数据失败: {e}")
            return []

    async def get_realtime_data(self, ts_codes: List[str]) -> List[Dict[str, Any]]:
        """获取实时数据"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟实时数据
            realtime_data = []
            for ts_code in ts_codes:
                import random
                base_price = random.uniform(5, 50)
                change_pct = random.uniform(-0.1, 0.1)
                
                realtime_data.append({
                    "ts_code": ts_code,
                    "name": f"股票{ts_code[:6]}",
                    "price": round(base_price, 2),
                    "change": round(base_price * change_pct, 2),
                    "pct_chg": round(change_pct * 100, 2),
                    "volume": random.randint(1000000, 10000000),
                    "amount": random.randint(10000000, 100000000),
                    "high": round(base_price * 1.05, 2),
                    "low": round(base_price * 0.95, 2),
                    "open": round(base_price * random.uniform(0.98, 1.02), 2),
                    "pre_close": round(base_price / (1 + change_pct), 2),
                    "timestamp": datetime.now().isoformat()
                })
            
            return realtime_data
            
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return []

    async def get_basic_data(self, ts_code: str, trade_date: Optional[date] = None) -> Dict[str, Any]:
        """获取基本面数据"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟基本面数据
            import random
            return {
                "ts_code": ts_code,
                "trade_date": (trade_date or date.today()).strftime("%Y%m%d"),
                "pe": round(random.uniform(10, 50), 2),
                "pb": round(random.uniform(1, 10), 2),
                "ps": round(random.uniform(1, 20), 2),
                "dv_ratio": round(random.uniform(0, 5), 2),
                "dv_ttm": round(random.uniform(0, 5), 2),
                "total_share": random.randint(1000000, 10000000),
                "float_share": random.randint(500000, 8000000),
                "free_share": random.randint(300000, 6000000),
                "total_mv": random.randint(1000000, 100000000),
                "circ_mv": random.randint(500000, 80000000)
            }
            
        except Exception as e:
            print(f"获取基本面数据失败: {e}")
            return {}

    async def get_money_flow(self, ts_code: str, trade_date: Optional[date] = None) -> Dict[str, Any]:
        """获取资金流向数据"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟资金流向数据
            import random
            return {
                "ts_code": ts_code,
                "trade_date": (trade_date or date.today()).strftime("%Y%m%d"),
                "buy_sm_vol": random.randint(100000, 1000000),
                "buy_sm_amount": random.randint(1000000, 10000000),
                "sell_sm_vol": random.randint(100000, 1000000),
                "sell_sm_amount": random.randint(1000000, 10000000),
                "buy_md_vol": random.randint(200000, 2000000),
                "buy_md_amount": random.randint(2000000, 20000000),
                "sell_md_vol": random.randint(200000, 2000000),
                "sell_md_amount": random.randint(2000000, 20000000),
                "buy_lg_vol": random.randint(500000, 5000000),
                "buy_lg_amount": random.randint(5000000, 50000000),
                "sell_lg_vol": random.randint(500000, 5000000),
                "sell_lg_amount": random.randint(5000000, 50000000),
                "buy_elg_vol": random.randint(1000000, 10000000),
                "buy_elg_amount": random.randint(10000000, 100000000),
                "sell_elg_vol": random.randint(1000000, 10000000),
                "sell_elg_amount": random.randint(10000000, 100000000),
                "net_mf_vol": random.randint(-1000000, 1000000),
                "net_mf_amount": random.randint(-10000000, 10000000)
            }
            
        except Exception as e:
            print(f"获取资金流向数据失败: {e}")
            return {}

    async def get_index_data(self, index_code: str = "000001.SH") -> Dict[str, Any]:
        """获取指数数据"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟指数数据
            import random
            base_value = 3000 if index_code == "000001.SH" else 2000
            change_pct = random.uniform(-0.03, 0.03)
            
            return {
                "code": index_code,
                "name": "上证指数" if index_code == "000001.SH" else "深证成指",
                "current": round(base_value * (1 + change_pct), 2),
                "change": round(base_value * change_pct, 2),
                "pct_chg": round(change_pct * 100, 2),
                "volume": random.randint(100000000, 1000000000),
                "amount": random.randint(1000000000, 10000000000),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return {}

    async def get_market_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取市场新闻"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            # 模拟新闻数据
            mock_news = []
            for i in range(limit):
                mock_news.append({
                    "id": f"news_{i}",
                    "title": f"市场新闻标题 {i+1}",
                    "summary": f"这是第{i+1}条市场新闻的摘要内容...",
                    "source": "财经网站",
                    "publish_time": (datetime.now() - timedelta(hours=i)).isoformat(),
                    "url": f"https://example.com/news/{i}",
                    "category": "市场动态"
                })
            
            return mock_news
            
        except Exception as e:
            print(f"获取市场新闻失败: {e}")
            return []

    async def batch_update_stocks(self, ts_codes: List[str]) -> Dict[str, Any]:
        """批量更新股票数据"""
        try:
            success_count = 0
            failed_codes = []
            
            for ts_code in ts_codes:
                try:
                    # 获取日线数据
                    daily_data = await self.get_daily_data(ts_code)
                    if daily_data:
                        success_count += 1
                    else:
                        failed_codes.append(ts_code)
                except Exception as e:
                    failed_codes.append(ts_code)
                    print(f"更新股票 {ts_code} 失败: {e}")
            
            return {
                "success_count": success_count,
                "failed_count": len(failed_codes),
                "failed_codes": failed_codes,
                "total": len(ts_codes)
            }
            
        except Exception as e:
            print(f"批量更新股票数据失败: {e}")
            return {
                "success_count": 0,
                "failed_count": len(ts_codes),
                "failed_codes": ts_codes,
                "total": len(ts_codes)
            }