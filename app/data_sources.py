"""
数据源管理模块
统一管理Tushare和AKShare数据源
"""

import asyncio
import aiohttp
import tushare as ts
import akshare as ak
import pandas as pd
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from loguru import logger
import time
import random

from app.config import settings, APIConfig
from app.cache import StockDataCache


class DataSourceError(Exception):
    """数据源异常"""
    pass


class TushareDataSource:
    """Tushare数据源"""
    
    def __init__(self):
        self.token = APIConfig.TUSHARE_TOKEN
        self.base_url = APIConfig.TUSHARE_BASE_URL
        self.timeout = APIConfig.TUSHARE_TIMEOUT
        self.max_retries = APIConfig.TUSHARE_MAX_RETRIES
        
        # 初始化Tushare
        if self.token and self.token != "your_tushare_token_here":
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            logger.warning("Tushare Token未配置，相关功能将不可用")
            self.pro = None
    
    async def _retry_request(self, func, *args, **kwargs):
        """重试请求"""
        for attempt in range(self.max_retries):
            try:
                # 添加随机延迟避免频率限制
                if attempt > 0:
                    delay = random.uniform(1, 3) * attempt
                    await asyncio.sleep(delay)
                
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)
                return result
                
            except Exception as e:
                logger.warning(f"Tushare请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise DataSourceError(f"Tushare请求最终失败: {e}")
                
                # 指数退避
                await asyncio.sleep(2 ** attempt)
    
    async def get_stock_basic(self, exchange: str = None) -> pd.DataFrame:
        """获取股票基础信息"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.stock_basic(
                exchange=exchange,
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,exchange,curr_type,list_status,list_date,delist_date,is_hs'
            )
        
        return await self._retry_request(_get_data)
    
    async def get_daily_quotes(
        self, 
        ts_code: str = None, 
        start_date: str = None, 
        end_date: str = None,
        trade_date: str = None
    ) -> pd.DataFrame:
        """获取日线行情数据"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.daily(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
        
        return await self._retry_request(_get_data)
    
    async def get_daily_basic(
        self, 
        ts_code: str = None, 
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取每日基础数据"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.daily_basic(
                ts_code=ts_code,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb,ps,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
            )
        
        return await self._retry_request(_get_data)
    
    async def get_index_daily(
        self, 
        ts_code: str, 
        start_date: str = None, 
        end_date: str = None
    ) -> pd.DataFrame:
        """获取指数日线数据"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
            )
        
        return await self._retry_request(_get_data)
    
    async def get_trade_cal(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取交易日历"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.trade_cal(
                start_date=start_date,
                end_date=end_date,
                fields='exchange,cal_date,is_open,pretrade_date'
            )
        
        return await self._retry_request(_get_data)
    
    async def get_concept_detail(self, id: str = None, ts_code: str = None) -> pd.DataFrame:
        """获取概念股分类"""
        if not self.pro:
            raise DataSourceError("Tushare未初始化")
        
        def _get_data():
            return self.pro.concept_detail(
                id=id,
                ts_code=ts_code,
                fields='id,concept_name,ts_code,name,in_date,out_date'
            )
        
        return await self._retry_request(_get_data)


class AKShareDataSource:
    """AKShare数据源"""
    
    def __init__(self):
        self.timeout = APIConfig.AKSHARE_TIMEOUT
        self.max_retries = APIConfig.AKSHARE_MAX_RETRIES
    
    async def _retry_request(self, func, *args, **kwargs):
        """重试请求"""
        for attempt in range(self.max_retries):
            try:
                # 添加随机延迟
                if attempt > 0:
                    delay = random.uniform(0.5, 2) * attempt
                    await asyncio.sleep(delay)
                
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)
                return result
                
            except Exception as e:
                logger.warning(f"AKShare请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise DataSourceError(f"AKShare请求最终失败: {e}")
                
                await asyncio.sleep(1.5 ** attempt)
    
    async def get_realtime_quotes(self) -> pd.DataFrame:
        """获取A股实时行情"""
        def _get_data():
            return ak.stock_zh_a_spot_em()
        
        return await self._retry_request(_get_data)
    
    async def get_stock_realtime(self, symbol: str) -> pd.DataFrame:
        """获取单只股票实时数据"""
        def _get_data():
            return ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="")
        
        return await self._retry_request(_get_data)
    
    async def get_stock_minute_data(self, symbol: str, period: str = "1") -> pd.DataFrame:
        """获取分钟级数据"""
        def _get_data():
            return ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust="")
        
        return await self._retry_request(_get_data)
    
    async def get_index_realtime(self) -> pd.DataFrame:
        """获取指数实时数据"""
        def _get_data():
            return ak.index_zh_a_hist(symbol="000001", period="daily", start_date="20240101")
        
        return await self._retry_request(_get_data)
    
    async def get_fund_flow_individual(self, symbol: str) -> pd.DataFrame:
        """获取个股资金流向"""
        def _get_data():
            return ak.stock_individual_fund_flow_rank(symbol=symbol)
        
        return await self._retry_request(_get_data)
    
    async def get_fund_flow_concept(self) -> pd.DataFrame:
        """获取概念资金流向"""
        def _get_data():
            return ak.stock_sector_fund_flow_rank(indicator="概念资金流")
        
        return await self._retry_request(_get_data)
    
    async def get_fund_flow_industry(self) -> pd.DataFrame:
        """获取行业资金流向"""
        def _get_data():
            return ak.stock_sector_fund_flow_rank(indicator="行业资金流")
        
        return await self._retry_request(_get_data)
    
    async def get_market_fund_flow(self) -> pd.DataFrame:
        """获取大盘资金流向"""
        def _get_data():
            return ak.stock_market_fund_flow()
        
        return await self._retry_request(_get_data)
    
    async def get_hot_rank_by_volume(self) -> pd.DataFrame:
        """获取成交量排行"""
        def _get_data():
            return ak.stock_hot_rank_wc()
        
        return await self._retry_request(_get_data)
    
    async def get_hot_rank_by_amount(self) -> pd.DataFrame:
        """获取成交额排行"""
        def _get_data():
            return ak.stock_hot_rank_em()
        
        return await self._retry_request(_get_data)
    
    async def get_limit_up_stocks(self) -> pd.DataFrame:
        """获取涨停股票"""
        def _get_data():
            return ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        
        return await self._retry_request(_get_data)
    
    async def get_limit_down_stocks(self) -> pd.DataFrame:
        """获取跌停股票"""
        def _get_data():
            return ak.stock_dt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        
        return await self._retry_request(_get_data)
    
    async def get_strong_stocks(self) -> pd.DataFrame:
        """获取强势股"""
        def _get_data():
            return ak.stock_strong_pool_em(date=datetime.now().strftime("%Y%m%d"))
        
        return await self._retry_request(_get_data)
    
    async def get_new_stocks(self) -> pd.DataFrame:
        """获取次新股"""
        def _get_data():
            return ak.stock_new_a_em()
        
        return await self._retry_request(_get_data)


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.tushare = TushareDataSource()
        self.akshare = AKShareDataSource()
        self._fallback_enabled = True
        self._initialized = False
    
    async def initialize(self):
        """初始化数据源管理器"""
        try:
            logger.info("正在初始化数据源管理器...")
            
            # 检查数据源健康状态
            health_status = await self.health_check()
            logger.info(f"数据源健康状态: {health_status}")
            
            self._initialized = True
            logger.info("数据源管理器初始化完成")
            
        except Exception as e:
            logger.error(f"数据源管理器初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭数据源管理器"""
        try:
            logger.info("正在关闭数据源管理器...")
            
            # 这里可以添加清理逻辑，比如关闭连接池等
            self._initialized = False
            
            logger.info("数据源管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭数据源管理器时出错: {e}")
            raise
    
    async def get_stock_basic(self, use_cache: bool = True) -> pd.DataFrame:
        """获取股票基础信息（优先Tushare）"""
        cache_key = "stock_basic_all"
        
        if use_cache:
            cached_data = await StockDataCache.get_stock_basic(cache_key)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            # 优先使用Tushare
            df = await self.tushare.get_stock_basic()
            
            # 缓存数据
            if use_cache and not df.empty:
                await StockDataCache.set_stock_basic(
                    cache_key, 
                    df.to_dict('records'), 
                    expire=3600
                )
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            if self._fallback_enabled:
                logger.info("尝试使用备用数据源...")
                # 这里可以添加备用逻辑
            raise
    
    async def get_daily_quotes(
        self, 
        ts_code: str, 
        start_date: str = None, 
        end_date: str = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """获取日线行情（优先Tushare）"""
        
        # 如果是单日数据，检查缓存
        if use_cache and not start_date and not end_date:
            today = datetime.now().strftime("%Y%m%d")
            cached_data = await StockDataCache.get_daily_quote(ts_code, today)
            if cached_data:
                return pd.DataFrame([cached_data])
        
        try:
            df = await self.tushare.get_daily_quotes(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            # 缓存单日数据
            if use_cache and not df.empty and len(df) == 1:
                row = df.iloc[0]
                await StockDataCache.set_daily_quote(
                    ts_code,
                    row['trade_date'],
                    row.to_dict(),
                    expire=1800
                )
            
            return df
            
        except Exception as e:
            logger.error(f"获取日线行情失败 {ts_code}: {e}")
            raise
    
    async def get_realtime_quotes(self, use_cache: bool = True) -> pd.DataFrame:
        """获取实时行情（优先AKShare）"""
        cache_key = "realtime_quotes_all"
        
        if use_cache:
            cached_data = await StockDataCache.get_realtime_quote(cache_key)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            df = await self.akshare.get_realtime_quotes()
            
            # 缓存数据
            if use_cache and not df.empty:
                await StockDataCache.set_realtime_quote(
                    cache_key,
                    df.to_dict('records'),
                    expire=60
                )
            
            return df
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            if self._fallback_enabled:
                logger.info("尝试使用Tushare获取今日行情...")
                # 使用Tushare获取今日数据作为备用
                today = datetime.now().strftime("%Y%m%d")
                return await self.tushare.get_daily_quotes(trade_date=today)
            raise
    
    async def get_fund_flow_data(self, data_type: str = "market") -> pd.DataFrame:
        """获取资金流向数据（使用AKShare）"""
        try:
            if data_type == "market":
                return await self.akshare.get_market_fund_flow()
            elif data_type == "concept":
                return await self.akshare.get_fund_flow_concept()
            elif data_type == "industry":
                return await self.akshare.get_fund_flow_industry()
            else:
                raise ValueError(f"不支持的资金流向类型: {data_type}")
                
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {data_type}: {e}")
            raise
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """获取市场情绪数据（使用AKShare）"""
        try:
            # 并发获取多个情绪指标
            tasks = [
                self.akshare.get_limit_up_stocks(),
                self.akshare.get_limit_down_stocks(),
                self.akshare.get_strong_stocks(),
                self.akshare.get_new_stocks(),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            sentiment_data = {
                "limit_up": results[0] if not isinstance(results[0], Exception) else pd.DataFrame(),
                "limit_down": results[1] if not isinstance(results[1], Exception) else pd.DataFrame(),
                "strong_stocks": results[2] if not isinstance(results[2], Exception) else pd.DataFrame(),
                "new_stocks": results[3] if not isinstance(results[3], Exception) else pd.DataFrame(),
                "timestamp": datetime.now().isoformat()
            }
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"获取市场情绪数据失败: {e}")
            raise
    
    async def get_hot_stocks(self, rank_type: str = "volume") -> pd.DataFrame:
        """获取热门股票排行"""
        try:
            if rank_type == "volume":
                return await self.akshare.get_hot_rank_by_volume()
            elif rank_type == "amount":
                return await self.akshare.get_hot_rank_by_amount()
            else:
                raise ValueError(f"不支持的排行类型: {rank_type}")
                
        except Exception as e:
            logger.error(f"获取热门股票失败 {rank_type}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, bool]:
        """数据源健康检查"""
        health_status = {
            "tushare": False,
            "akshare": False
        }
        
        # 检查Tushare
        try:
            if self.tushare.pro:
                df = await self.tushare.get_trade_cal(
                    start_date=datetime.now().strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d")
                )
                health_status["tushare"] = not df.empty
        except Exception as e:
            logger.error(f"Tushare健康检查失败: {e}")
        
        # 检查AKShare
        try:
            df = await self.akshare.get_index_realtime()
            health_status["akshare"] = not df.empty
        except Exception as e:
            logger.error(f"AKShare健康检查失败: {e}")
        
        return health_status


# 全局数据源管理器实例
data_source_manager = DataSourceManager()


# 导出
__all__ = [
    "DataSourceError",
    "TushareDataSource",
    "AKShareDataSource", 
    "DataSourceManager",
    "data_source_manager",
]