"""
数据服务层
统一管理数据获取、处理和存储
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, timedelta
from sqlalchemy import select, insert, update, delete, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_async_session, DatabaseManager
from app.models import (
    StockBasic, DailyQuote, TechnicalIndicator, NineTurnSignal,
    MarketData, UserWatchlist, DataUpdateLog, SystemConfig
)
from app.data_sources import data_source_manager, DataSourceError
from app.technical_analysis import technical_analyzer, TechnicalIndicatorError
from app.cache import StockDataCache
from app.config import settings


class DataServiceError(Exception):
    """数据服务异常"""
    pass


class StockDataService:
    """股票数据服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    async def update_stock_basic(self, force_update: bool = False) -> Dict[str, Any]:
        """更新股票基础信息"""
        try:
            logger.info("开始更新股票基础信息...")
            
            # 检查是否需要更新
            if not force_update:
                last_update = await self._get_last_update_time("stock_basic")
                if last_update and (datetime.now() - last_update).days < 1:
                    logger.info("股票基础信息已是最新，跳过更新")
                    return {"status": "skipped", "message": "数据已是最新"}
            
            # 获取数据
            df = await data_source_manager.get_stock_basic(use_cache=False)
            if df.empty:
                raise DataServiceError("获取股票基础信息失败")
            
            # 数据清洗和转换
            df = self._clean_stock_basic_data(df)
            
            # 保存到数据库
            async with get_async_session() as session:
                # 清空现有数据
                await session.execute(delete(StockBasic))
                
                # 批量插入新数据
                records = df.to_dict('records')
                await session.execute(insert(StockBasic), records)
                
                # 记录更新日志
                await self._log_data_update(session, "stock_basic", len(records))
                
                await session.commit()
            
            logger.info(f"股票基础信息更新完成，共 {len(df)} 条记录")
            return {
                "status": "success",
                "count": len(df),
                "message": f"更新了 {len(df)} 条股票基础信息"
            }
            
        except Exception as e:
            logger.error(f"更新股票基础信息失败: {e}")
            raise DataServiceError(f"更新股票基础信息失败: {e}")
    
    async def update_daily_quotes(
        self, 
        ts_codes: List[str] = None, 
        trade_date: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """更新日线行情数据"""
        try:
            logger.info("开始更新日线行情数据...")
            
            # 如果没有指定股票代码，获取所有股票
            if not ts_codes:
                ts_codes = await self._get_all_stock_codes()
            
            # 如果没有指定日期，使用最新交易日
            if not trade_date and not start_date:
                trade_date = datetime.now().strftime("%Y%m%d")
            
            total_count = 0
            failed_count = 0
            
            # 分批处理股票
            batch_size = 50
            for i in range(0, len(ts_codes), batch_size):
                batch_codes = ts_codes[i:i + batch_size]
                
                try:
                    # 并发获取数据
                    tasks = []
                    for ts_code in batch_codes:
                        task = data_source_manager.get_daily_quotes(
                            ts_code=ts_code,
                            trade_date=trade_date,
                            start_date=start_date,
                            end_date=end_date
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理结果
                    async with get_async_session() as session:
                        for j, result in enumerate(results):
                            if isinstance(result, Exception):
                                logger.warning(f"获取 {batch_codes[j]} 行情失败: {result}")
                                failed_count += 1
                                continue
                            
                            if result.empty:
                                continue
                            
                            # 数据清洗
                            df = self._clean_daily_quote_data(result)
                            
                            # 保存数据
                            records = df.to_dict('records')
                            
                            # 删除已存在的数据（避免重复）
                            if trade_date:
                                await session.execute(
                                    delete(DailyQuote).where(
                                        and_(
                                            DailyQuote.ts_code == batch_codes[j],
                                            DailyQuote.trade_date == trade_date
                                        )
                                    )
                                )
                            
                            await session.execute(insert(DailyQuote), records)
                            total_count += len(records)
                        
                        await session.commit()
                    
                    # 避免请求过于频繁
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"处理批次 {i//batch_size + 1} 失败: {e}")
                    failed_count += len(batch_codes)
            
            # 记录更新日志
            async with get_async_session() as session:
                await self._log_data_update(session, "daily_quotes", total_count)
                await session.commit()
            
            logger.info(f"日线行情更新完成，成功 {total_count} 条，失败 {failed_count} 条")
            return {
                "status": "success",
                "total_count": total_count,
                "failed_count": failed_count,
                "message": f"更新了 {total_count} 条日线行情数据"
            }
            
        except Exception as e:
            logger.error(f"更新日线行情失败: {e}")
            raise DataServiceError(f"更新日线行情失败: {e}")
    
    async def update_technical_indicators(self, ts_codes: List[str] = None) -> Dict[str, Any]:
        """更新技术指标"""
        try:
            logger.info("开始更新技术指标...")
            
            if not ts_codes:
                ts_codes = await self._get_all_stock_codes()
            
            total_count = 0
            failed_count = 0
            
            async with get_async_session() as session:
                for ts_code in ts_codes:
                    try:
                        # 获取历史数据
                        historical_data = await self._get_historical_data(ts_code, days=250)
                        if historical_data.empty:
                            continue
                        
                        # 计算技术指标
                        df_with_indicators = await technical_analyzer.calculate_all_indicators(
                            historical_data, ts_code
                        )
                        
                        # 保存技术指标
                        await self._save_technical_indicators(session, ts_code, df_with_indicators)
                        total_count += 1
                        
                    except Exception as e:
                        logger.warning(f"更新 {ts_code} 技术指标失败: {e}")
                        failed_count += 1
                
                # 记录更新日志
                await self._log_data_update(session, "technical_indicators", total_count)
                await session.commit()
            
            logger.info(f"技术指标更新完成，成功 {total_count} 条，失败 {failed_count} 条")
            return {
                "status": "success",
                "total_count": total_count,
                "failed_count": failed_count,
                "message": f"更新了 {total_count} 只股票的技术指标"
            }
            
        except Exception as e:
            logger.error(f"更新技术指标失败: {e}")
            raise DataServiceError(f"更新技术指标失败: {e}")
    
    async def update_nine_turn_signals(self, ts_codes: List[str] = None) -> Dict[str, Any]:
        """更新九转信号"""
        try:
            logger.info("开始更新九转信号...")
            
            if not ts_codes:
                ts_codes = await self._get_all_stock_codes()
            
            total_count = 0
            signal_count = 0
            
            async with get_async_session() as session:
                for ts_code in ts_codes:
                    try:
                        # 获取历史数据
                        historical_data = await self._get_historical_data(ts_code, days=100)
                        if len(historical_data) < 13:  # 九转至少需要13个数据点
                            continue
                        
                        # 计算九转信号
                        df_with_signals = await technical_analyzer.nine_turn.calculate_nine_turn_signals(
                            historical_data
                        )
                        
                        # 获取最新信号
                        recent_signals = await technical_analyzer.nine_turn.get_current_signals(
                            df_with_signals, days=30
                        )
                        
                        # 保存九转信号
                        if recent_signals:
                            await self._save_nine_turn_signals(session, ts_code, recent_signals)
                            signal_count += len(recent_signals)
                        
                        total_count += 1
                        
                    except Exception as e:
                        logger.warning(f"更新 {ts_code} 九转信号失败: {e}")
                
                # 记录更新日志
                await self._log_data_update(session, "nine_turn_signals", signal_count)
                await session.commit()
            
            logger.info(f"九转信号更新完成，处理 {total_count} 只股票，发现 {signal_count} 个信号")
            return {
                "status": "success",
                "total_count": total_count,
                "signal_count": signal_count,
                "message": f"处理了 {total_count} 只股票，发现 {signal_count} 个九转信号"
            }
            
        except Exception as e:
            logger.error(f"更新九转信号失败: {e}")
            raise DataServiceError(f"更新九转信号失败: {e}")
    
    async def get_stock_list(
        self, 
        exchange: str = None, 
        market: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """获取股票列表"""
        try:
            async with get_async_session() as session:
                query = select(StockBasic)
                
                # 添加筛选条件
                if exchange:
                    query = query.where(StockBasic.exchange == exchange)
                if market:
                    query = query.where(StockBasic.market == market)
                
                # 分页
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                stocks = result.scalars().all()
                
                # 获取总数
                count_query = select(StockBasic)
                if exchange:
                    count_query = count_query.where(StockBasic.exchange == exchange)
                if market:
                    count_query = count_query.where(StockBasic.market == market)
                
                total_result = await session.execute(count_query)
                total = len(total_result.scalars().all())
                
                return {
                    "stocks": [self._stock_to_dict(stock) for stock in stocks],
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise DataServiceError(f"获取股票列表失败: {e}")
    
    async def get_stock_detail(self, ts_code: str) -> Dict[str, Any]:
        """获取股票详情"""
        try:
            async with get_async_session() as session:
                # 获取基础信息
                stock_result = await session.execute(
                    select(StockBasic).where(StockBasic.ts_code == ts_code)
                )
                stock = stock_result.scalar_one_or_none()
                
                if not stock:
                    raise DataServiceError(f"股票 {ts_code} 不存在")
                
                # 获取最新行情
                quote_result = await session.execute(
                    select(DailyQuote)
                    .where(DailyQuote.ts_code == ts_code)
                    .order_by(desc(DailyQuote.trade_date))
                    .limit(1)
                )
                latest_quote = quote_result.scalar_one_or_none()
                
                # 获取技术指标
                indicator_result = await session.execute(
                    select(TechnicalIndicator)
                    .where(TechnicalIndicator.ts_code == ts_code)
                    .order_by(desc(TechnicalIndicator.trade_date))
                    .limit(1)
                )
                latest_indicator = indicator_result.scalar_one_or_none()
                
                # 获取九转信号
                signal_result = await session.execute(
                    select(NineTurnSignal)
                    .where(NineTurnSignal.ts_code == ts_code)
                    .order_by(desc(NineTurnSignal.signal_date))
                    .limit(5)
                )
                signals = signal_result.scalars().all()
                
                return {
                    "basic_info": self._stock_to_dict(stock),
                    "latest_quote": self._quote_to_dict(latest_quote) if latest_quote else None,
                    "technical_indicator": self._indicator_to_dict(latest_indicator) if latest_indicator else None,
                    "nine_turn_signals": [self._signal_to_dict(signal) for signal in signals]
                }
                
        except Exception as e:
            logger.error(f"获取股票详情失败 {ts_code}: {e}")
            raise DataServiceError(f"获取股票详情失败: {e}")
    
    async def get_nine_turn_stocks(
        self, 
        signal_type: str = "all",
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取九转信号股票"""
        try:
            async with get_async_session() as session:
                query = select(NineTurnSignal).join(StockBasic)
                
                # 时间筛选
                start_date = (datetime.now() - timedelta(days=days)).date()
                query = query.where(NineTurnSignal.signal_date >= start_date)
                
                # 信号类型筛选
                if signal_type == "buy":
                    query = query.where(NineTurnSignal.signal_type == "buy")
                elif signal_type == "sell":
                    query = query.where(NineTurnSignal.signal_type == "sell")
                
                # 按信号强度排序
                query = query.order_by(desc(NineTurnSignal.signal_strength)).limit(limit)
                
                result = await session.execute(query)
                signals = result.scalars().all()
                
                return [self._signal_to_dict(signal) for signal in signals]
                
        except Exception as e:
            logger.error(f"获取九转信号股票失败: {e}")
            raise DataServiceError(f"获取九转信号股票失败: {e}")
    
    # 私有方法
    async def _get_last_update_time(self, data_type: str) -> Optional[datetime]:
        """获取最后更新时间"""
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(DataUpdateLog.update_time)
                    .where(DataUpdateLog.data_type == data_type)
                    .order_by(desc(DataUpdateLog.update_time))
                    .limit(1)
                )
                return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def _get_all_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        try:
            async with get_async_session() as session:
                result = await session.execute(select(StockBasic.ts_code))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取股票代码列表失败: {e}")
            return []
    
    async def _get_historical_data(self, ts_code: str, days: int = 250) -> pd.DataFrame:
        """获取历史数据"""
        try:
            async with get_async_session() as session:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
                
                result = await session.execute(
                    select(DailyQuote)
                    .where(
                        and_(
                            DailyQuote.ts_code == ts_code,
                            DailyQuote.trade_date >= start_date,
                            DailyQuote.trade_date <= end_date
                        )
                    )
                    .order_by(asc(DailyQuote.trade_date))
                )
                
                quotes = result.scalars().all()
                
                if not quotes:
                    return pd.DataFrame()
                
                data = []
                for quote in quotes:
                    data.append({
                        'trade_date': quote.trade_date.strftime("%Y%m%d"),
                        'open': float(quote.open_price),
                        'high': float(quote.high_price),
                        'low': float(quote.low_price),
                        'close': float(quote.close_price),
                        'vol': float(quote.volume) if quote.volume else 0,
                        'amount': float(quote.amount) if quote.amount else 0
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"获取历史数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    async def _log_data_update(self, session: AsyncSession, data_type: str, record_count: int):
        """记录数据更新日志"""
        try:
            log_entry = DataUpdateLog(
                data_type=data_type,
                record_count=record_count,
                update_time=datetime.now(),
                status="success"
            )
            session.add(log_entry)
        except Exception as e:
            logger.error(f"记录更新日志失败: {e}")
    
    async def _save_technical_indicators(
        self, 
        session: AsyncSession, 
        ts_code: str, 
        df: pd.DataFrame
    ):
        """保存技术指标"""
        try:
            # 删除现有数据
            await session.execute(
                delete(TechnicalIndicator).where(TechnicalIndicator.ts_code == ts_code)
            )
            
            # 准备新数据
            records = []
            for _, row in df.tail(30).iterrows():  # 只保存最近30天的数据
                record = {
                    'ts_code': ts_code,
                    'trade_date': datetime.strptime(row['trade_date'], "%Y%m%d").date(),
                    'ma5': float(row.get('ma5', 0)) if pd.notna(row.get('ma5')) else None,
                    'ma10': float(row.get('ma10', 0)) if pd.notna(row.get('ma10')) else None,
                    'ma20': float(row.get('ma20', 0)) if pd.notna(row.get('ma20')) else None,
                    'ma60': float(row.get('ma60', 0)) if pd.notna(row.get('ma60')) else None,
                    'ema12': float(row.get('ema12', 0)) if pd.notna(row.get('ema12')) else None,
                    'ema26': float(row.get('ema26', 0)) if pd.notna(row.get('ema26')) else None,
                    'macd': float(row.get('macd', 0)) if pd.notna(row.get('macd')) else None,
                    'macd_signal': float(row.get('macd_signal', 0)) if pd.notna(row.get('macd_signal')) else None,
                    'macd_histogram': float(row.get('macd_histogram', 0)) if pd.notna(row.get('macd_histogram')) else None,
                    'rsi': float(row.get('rsi', 0)) if pd.notna(row.get('rsi')) else None,
                    'kdj_k': float(row.get('kdj_k', 0)) if pd.notna(row.get('kdj_k')) else None,
                    'kdj_d': float(row.get('kdj_d', 0)) if pd.notna(row.get('kdj_d')) else None,
                    'kdj_j': float(row.get('kdj_j', 0)) if pd.notna(row.get('kdj_j')) else None,
                    'bb_upper': float(row.get('bb_upper', 0)) if pd.notna(row.get('bb_upper')) else None,
                    'bb_middle': float(row.get('bb_middle', 0)) if pd.notna(row.get('bb_middle')) else None,
                    'bb_lower': float(row.get('bb_lower', 0)) if pd.notna(row.get('bb_lower')) else None,
                    'obv': float(row.get('obv', 0)) if pd.notna(row.get('obv')) else None,
                    'ad': float(row.get('ad', 0)) if pd.notna(row.get('ad')) else None,
                    'td_setup_buy': int(row.get('td_setup_buy', 0)),
                    'td_setup_sell': int(row.get('td_setup_sell', 0)),
                    'td_countdown_buy': int(row.get('td_countdown_buy', 0)),
                    'td_countdown_sell': int(row.get('td_countdown_sell', 0)),
                    'nine_turn_signal': int(row.get('nine_turn_signal', 0)),
                    'signal_strength': float(row.get('signal_strength', 0))
                }
                records.append(record)
            
            if records:
                await session.execute(insert(TechnicalIndicator), records)
                
        except Exception as e:
            logger.error(f"保存技术指标失败 {ts_code}: {e}")
    
    async def _save_nine_turn_signals(
        self, 
        session: AsyncSession, 
        ts_code: str, 
        signals: List[Dict[str, Any]]
    ):
        """保存九转信号"""
        try:
            # 删除现有信号
            await session.execute(
                delete(NineTurnSignal).where(NineTurnSignal.ts_code == ts_code)
            )
            
            # 保存新信号
            records = []
            for signal in signals:
                record = {
                    'ts_code': ts_code,
                    'signal_date': datetime.strptime(signal['date'], "%Y%m%d").date(),
                    'signal_type': signal['signal_type'],
                    'signal_strength': signal['strength'],
                    'signal_description': signal['description'],
                    'close_price': signal['close_price'],
                    'setup_buy_count': signal['setup_buy_count'],
                    'setup_sell_count': signal['setup_sell_count'],
                    'countdown_buy_count': signal['countdown_buy_count'],
                    'countdown_sell_count': signal['countdown_sell_count']
                }
                records.append(record)
            
            if records:
                await session.execute(insert(NineTurnSignal), records)
                
        except Exception as e:
            logger.error(f"保存九转信号失败 {ts_code}: {e}")
    
    def _clean_stock_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗股票基础数据"""
        try:
            df = df.copy()
            
            # 处理空值
            df = df.fillna({
                'area': '未知',
                'industry': '未知',
                'market': '主板',
                'curr_type': 'CNY',
                'is_hs': 'N'
            })
            
            # 处理日期
            if 'list_date' in df.columns:
                df['list_date'] = pd.to_datetime(df['list_date'], format='%Y%m%d', errors='coerce')
            
            if 'delist_date' in df.columns:
                df['delist_date'] = pd.to_datetime(df['delist_date'], format='%Y%m%d', errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"清洗股票基础数据失败: {e}")
            return df
    
    def _clean_daily_quote_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗日线行情数据"""
        try:
            df = df.copy()
            
            # 处理日期
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            
            # 处理数值
            numeric_columns = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 重命名列以匹配数据库字段
            column_mapping = {
                'open': 'open_price',
                'high': 'high_price',
                'low': 'low_price',
                'close': 'close_price',
                'vol': 'volume'
            }
            df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception as e:
            logger.error(f"清洗日线行情数据失败: {e}")
            return df
    
    def _stock_to_dict(self, stock: StockBasic) -> Dict[str, Any]:
        """股票对象转字典"""
        return {
            'ts_code': stock.ts_code,
            'symbol': stock.symbol,
            'name': stock.name,
            'area': stock.area,
            'industry': stock.industry,
            'market': stock.market,
            'exchange': stock.exchange,
            'curr_type': stock.curr_type,
            'list_status': stock.list_status,
            'list_date': stock.list_date.isoformat() if stock.list_date else None,
            'delist_date': stock.delist_date.isoformat() if stock.delist_date else None,
            'is_hs': stock.is_hs
        }
    
    def _quote_to_dict(self, quote: DailyQuote) -> Dict[str, Any]:
        """行情对象转字典"""
        return {
            'ts_code': quote.ts_code,
            'trade_date': quote.trade_date.isoformat(),
            'open_price': float(quote.open_price),
            'high_price': float(quote.high_price),
            'low_price': float(quote.low_price),
            'close_price': float(quote.close_price),
            'pre_close': float(quote.pre_close) if quote.pre_close else None,
            'change': float(quote.change) if quote.change else None,
            'pct_chg': float(quote.pct_chg) if quote.pct_chg else None,
            'volume': float(quote.volume) if quote.volume else None,
            'amount': float(quote.amount) if quote.amount else None
        }
    
    def _indicator_to_dict(self, indicator: TechnicalIndicator) -> Dict[str, Any]:
        """技术指标对象转字典"""
        return {
            'ts_code': indicator.ts_code,
            'trade_date': indicator.trade_date.isoformat(),
            'ma5': float(indicator.ma5) if indicator.ma5 else None,
            'ma10': float(indicator.ma10) if indicator.ma10 else None,
            'ma20': float(indicator.ma20) if indicator.ma20 else None,
            'ma60': float(indicator.ma60) if indicator.ma60 else None,
            'ema12': float(indicator.ema12) if indicator.ema12 else None,
            'ema26': float(indicator.ema26) if indicator.ema26 else None,
            'macd': float(indicator.macd) if indicator.macd else None,
            'macd_signal': float(indicator.macd_signal) if indicator.macd_signal else None,
            'macd_histogram': float(indicator.macd_histogram) if indicator.macd_histogram else None,
            'rsi': float(indicator.rsi) if indicator.rsi else None,
            'kdj_k': float(indicator.kdj_k) if indicator.kdj_k else None,
            'kdj_d': float(indicator.kdj_d) if indicator.kdj_d else None,
            'kdj_j': float(indicator.kdj_j) if indicator.kdj_j else None,
            'bb_upper': float(indicator.bb_upper) if indicator.bb_upper else None,
            'bb_middle': float(indicator.bb_middle) if indicator.bb_middle else None,
            'bb_lower': float(indicator.bb_lower) if indicator.bb_lower else None,
            'obv': float(indicator.obv) if indicator.obv else None,
            'ad': float(indicator.ad) if indicator.ad else None,
            'td_setup_buy': indicator.td_setup_buy,
            'td_setup_sell': indicator.td_setup_sell,
            'td_countdown_buy': indicator.td_countdown_buy,
            'td_countdown_sell': indicator.td_countdown_sell,
            'nine_turn_signal': indicator.nine_turn_signal,
            'signal_strength': float(indicator.signal_strength)
        }
    
    def _signal_to_dict(self, signal: NineTurnSignal) -> Dict[str, Any]:
        """九转信号对象转字典"""
        return {
            'ts_code': signal.ts_code,
            'signal_date': signal.signal_date.isoformat(),
            'signal_type': signal.signal_type,
            'signal_strength': float(signal.signal_strength),
            'signal_description': signal.signal_description,
            'close_price': float(signal.close_price),
            'setup_buy_count': signal.setup_buy_count,
            'setup_sell_count': signal.setup_sell_count,
            'countdown_buy_count': signal.countdown_buy_count,
            'countdown_sell_count': signal.countdown_sell_count
        }


# 全局数据服务实例
stock_data_service = StockDataService()


# 导出
__all__ = [
    "DataServiceError",
    "StockDataService",
    "stock_data_service",
]