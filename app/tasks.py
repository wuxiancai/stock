"""
Celery任务队列模块
处理后台数据更新任务
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from celery import Celery, Task
from celery.schedules import crontab
from loguru import logger
import pandas as pd

from app.config import settings
from app.database import get_async_session, DatabaseManager
from app.services import stock_data_service
from app.data_sources import data_source_manager
from app.cache import StockDataCache
from app.models import DataUpdateLog


# 创建Celery应用
celery_app = Celery(
    "stock_trading_system",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"]
)

# Celery配置
celery_app.conf.update(
    # 时区设置
    timezone=settings.timezone,
    enable_utc=True,
    
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 任务路由
    task_routes={
        "app.tasks.update_stock_basic": {"queue": "data_update"},
        "app.tasks.update_daily_quotes": {"queue": "data_update"},
        "app.tasks.update_technical_indicators": {"queue": "calculation"},
        "app.tasks.update_nine_turn_signals": {"queue": "calculation"},
        "app.tasks.cleanup_old_data": {"queue": "maintenance"},
        "app.tasks.health_check": {"queue": "monitoring"},
    },
    
    # 任务优先级
    task_default_priority=5,
    worker_prefetch_multiplier=1,
    
    # 任务超时
    task_soft_time_limit=300,  # 5分钟软超时
    task_time_limit=600,       # 10分钟硬超时
    
    # 任务重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 结果过期时间
    result_expires=3600,  # 1小时
    
    # 定时任务
    beat_schedule={
        # 更新股票基础信息 - 每天早上6点
        "update-stock-basic": {
            "task": "app.tasks.update_stock_basic",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": "data_update", "priority": 9}
        },
        
        # 更新日线数据 - 交易日下午4点
        "update-daily-quotes": {
            "task": "app.tasks.update_daily_quotes",
            "schedule": crontab(hour=16, minute=0, day_of_week="1-5"),
            "options": {"queue": "data_update", "priority": 8}
        },
        
        # 更新技术指标 - 交易日下午4点30分
        "update-technical-indicators": {
            "task": "app.tasks.update_technical_indicators",
            "schedule": crontab(hour=16, minute=30, day_of_week="1-5"),
            "options": {"queue": "calculation", "priority": 7}
        },
        
        # 更新九转信号 - 交易日下午5点
        "update-nine-turn-signals": {
            "task": "app.tasks.update_nine_turn_signals",
            "schedule": crontab(hour=17, minute=0, day_of_week="1-5"),
            "options": {"queue": "calculation", "priority": 7}
        },
        
        # 清理旧数据 - 每天凌晨2点
        "cleanup-old-data": {
            "task": "app.tasks.cleanup_old_data",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "maintenance", "priority": 3}
        },
        
        # 健康检查 - 每5分钟
        "health-check": {
            "task": "app.tasks.health_check",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "monitoring", "priority": 1}
        },
    }
)


class AsyncTask(Task):
    """异步任务基类"""
    
    def __call__(self, *args, **kwargs):
        """执行任务"""
        try:
            # 在新的事件循环中运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.run_async(*args, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"任务执行失败 {self.name}: {e}")
            raise
    
    async def run_async(self, *args, **kwargs):
        """异步任务执行方法，子类需要重写"""
        raise NotImplementedError


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.update_stock_basic")
async def update_stock_basic(self, force: bool = False) -> Dict[str, Any]:
    """更新股票基础信息"""
    task_id = self.request.id
    logger.info(f"开始更新股票基础信息 [任务ID: {task_id}]")
    
    start_time = datetime.now()
    
    try:
        # 记录任务开始
        await _log_task_start("update_stock_basic", task_id)
        
        # 执行更新
        result = await stock_data_service.update_stock_basic(force=force)
        
        # 记录任务完成
        await _log_task_completion(
            "update_stock_basic", 
            task_id, 
            start_time, 
            result.get("updated_count", 0)
        )
        
        logger.info(f"股票基础信息更新完成: {result}")
        return result
        
    except Exception as e:
        # 记录任务失败
        await _log_task_failure("update_stock_basic", task_id, start_time, str(e))
        logger.error(f"更新股票基础信息失败: {e}")
        raise


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.update_daily_quotes")
async def update_daily_quotes(self, ts_codes: Optional[List[str]] = None, days: int = 30) -> Dict[str, Any]:
    """更新日线数据"""
    task_id = self.request.id
    logger.info(f"开始更新日线数据 [任务ID: {task_id}]")
    
    start_time = datetime.now()
    
    try:
        # 记录任务开始
        await _log_task_start("update_daily_quotes", task_id)
        
        # 执行更新
        result = await stock_data_service.update_daily_quotes(ts_codes=ts_codes, days=days)
        
        # 记录任务完成
        await _log_task_completion(
            "update_daily_quotes", 
            task_id, 
            start_time, 
            result.get("updated_count", 0)
        )
        
        logger.info(f"日线数据更新完成: {result}")
        return result
        
    except Exception as e:
        # 记录任务失败
        await _log_task_failure("update_daily_quotes", task_id, start_time, str(e))
        logger.error(f"更新日线数据失败: {e}")
        raise


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.update_technical_indicators")
async def update_technical_indicators(self, ts_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """更新技术指标"""
    task_id = self.request.id
    logger.info(f"开始更新技术指标 [任务ID: {task_id}]")
    
    start_time = datetime.now()
    
    try:
        # 记录任务开始
        await _log_task_start("update_technical_indicators", task_id)
        
        # 执行更新
        result = await stock_data_service.update_technical_indicators(ts_codes=ts_codes)
        
        # 记录任务完成
        await _log_task_completion(
            "update_technical_indicators", 
            task_id, 
            start_time, 
            result.get("updated_count", 0)
        )
        
        logger.info(f"技术指标更新完成: {result}")
        return result
        
    except Exception as e:
        # 记录任务失败
        await _log_task_failure("update_technical_indicators", task_id, start_time, str(e))
        logger.error(f"更新技术指标失败: {e}")
        raise


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.update_nine_turn_signals")
async def update_nine_turn_signals(self, ts_codes: Optional[List[str]] = None) -> Dict[str, Any]:
    """更新九转信号"""
    task_id = self.request.id
    logger.info(f"开始更新九转信号 [任务ID: {task_id}]")
    
    start_time = datetime.now()
    
    try:
        # 记录任务开始
        await _log_task_start("update_nine_turn_signals", task_id)
        
        # 执行更新
        result = await stock_data_service.update_nine_turn_signals(ts_codes=ts_codes)
        
        # 记录任务完成
        await _log_task_completion(
            "update_nine_turn_signals", 
            task_id, 
            start_time, 
            result.get("updated_count", 0)
        )
        
        logger.info(f"九转信号更新完成: {result}")
        return result
        
    except Exception as e:
        # 记录任务失败
        await _log_task_failure("update_nine_turn_signals", task_id, start_time, str(e))
        logger.error(f"更新九转信号失败: {e}")
        raise


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.cleanup_old_data")
async def cleanup_old_data(self, days: int = 365) -> Dict[str, Any]:
    """清理旧数据"""
    task_id = self.request.id
    logger.info(f"开始清理旧数据 [任务ID: {task_id}]")
    
    start_time = datetime.now()
    cutoff_date = start_time - timedelta(days=days)
    
    try:
        # 记录任务开始
        await _log_task_start("cleanup_old_data", task_id)
        
        async with get_async_session() as session:
            db_manager = DatabaseManager(session)
            
            # 清理旧的日线数据（保留最近1年）
            daily_count = await db_manager.execute_sql(
                "DELETE FROM daily_quotes WHERE trade_date < :cutoff_date",
                {"cutoff_date": cutoff_date.strftime("%Y%m%d")}
            )
            
            # 清理旧的技术指标数据
            tech_count = await db_manager.execute_sql(
                "DELETE FROM technical_indicators WHERE trade_date < :cutoff_date",
                {"cutoff_date": cutoff_date.strftime("%Y%m%d")}
            )
            
            # 清理旧的九转信号数据
            signal_count = await db_manager.execute_sql(
                "DELETE FROM nine_turn_signals WHERE trade_date < :cutoff_date",
                {"cutoff_date": cutoff_date.strftime("%Y%m%d")}
            )
            
            # 清理旧的更新日志（保留最近3个月）
            log_cutoff = start_time - timedelta(days=90)
            log_count = await db_manager.execute_sql(
                "DELETE FROM data_update_logs WHERE created_at < :cutoff_date",
                {"cutoff_date": log_cutoff}
            )
            
            await session.commit()
        
        result = {
            "daily_quotes_deleted": daily_count,
            "technical_indicators_deleted": tech_count,
            "nine_turn_signals_deleted": signal_count,
            "update_logs_deleted": log_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
        # 记录任务完成
        await _log_task_completion(
            "cleanup_old_data", 
            task_id, 
            start_time, 
            sum([daily_count, tech_count, signal_count, log_count])
        )
        
        logger.info(f"旧数据清理完成: {result}")
        return result
        
    except Exception as e:
        # 记录任务失败
        await _log_task_failure("cleanup_old_data", task_id, start_time, str(e))
        logger.error(f"清理旧数据失败: {e}")
        raise


@celery_app.task(bind=True, base=AsyncTask, name="app.tasks.health_check")
async def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    task_id = self.request.id
    
    try:
        # 检查数据源连接
        data_source_health = await data_source_manager.health_check()
        
        # 检查数据库连接
        async with get_async_session() as session:
            db_manager = DatabaseManager(session)
            db_health = await db_manager.check_connection()
        
        # 检查缓存连接
        cache = StockDataCache()
        cache_health = await cache.health_check()
        
        # 检查最近的数据更新
        async with get_async_session() as session:
            db_manager = DatabaseManager(session)
            
            # 检查最近的股票基础信息更新
            stock_basic_check = await db_manager.execute_sql(
                "SELECT COUNT(*) as count FROM stock_basic WHERE updated_at > :cutoff",
                {"cutoff": datetime.now() - timedelta(days=7)}
            )
            
            # 检查最近的日线数据更新
            daily_quotes_check = await db_manager.execute_sql(
                "SELECT COUNT(*) as count FROM daily_quotes WHERE updated_at > :cutoff",
                {"cutoff": datetime.now() - timedelta(days=1)}
            )
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "data_sources": data_source_health,
            "database": db_health,
            "cache": cache_health,
            "data_freshness": {
                "stock_basic_recent_updates": stock_basic_check,
                "daily_quotes_recent_updates": daily_quotes_check
            },
            "overall_status": "healthy" if all([
                data_source_health.get("status") == "healthy",
                db_health.get("status") == "connected",
                cache_health.get("status") == "connected"
            ]) else "unhealthy"
        }
        
        if result["overall_status"] == "unhealthy":
            logger.warning(f"健康检查发现问题: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "overall_status": "error",
            "error": str(e)
        }


# 手动触发任务的函数
async def trigger_update_stock_basic(force: bool = False) -> str:
    """手动触发更新股票基础信息"""
    task = update_stock_basic.delay(force=force)
    logger.info(f"触发更新股票基础信息任务: {task.id}")
    return task.id


async def trigger_update_daily_quotes(ts_codes: Optional[List[str]] = None, days: int = 30) -> str:
    """手动触发更新日线数据"""
    task = update_daily_quotes.delay(ts_codes=ts_codes, days=days)
    logger.info(f"触发更新日线数据任务: {task.id}")
    return task.id


async def trigger_update_technical_indicators(ts_codes: Optional[List[str]] = None) -> str:
    """手动触发更新技术指标"""
    task = update_technical_indicators.delay(ts_codes=ts_codes)
    logger.info(f"触发更新技术指标任务: {task.id}")
    return task.id


async def trigger_update_nine_turn_signals(ts_codes: Optional[List[str]] = None) -> str:
    """手动触发更新九转信号"""
    task = update_nine_turn_signals.delay(ts_codes=ts_codes)
    logger.info(f"触发更新九转信号任务: {task.id}")
    return task.id


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """获取任务状态"""
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
        "traceback": task_result.traceback if task_result.failed() else None,
        "date_done": task_result.date_done.isoformat() if task_result.date_done else None
    }


# 辅助函数
async def _log_task_start(task_type: str, task_id: str):
    """记录任务开始"""
    try:
        async with get_async_session() as session:
            log = DataUpdateLog(
                task_type=task_type,
                task_id=task_id,
                status="running",
                started_at=datetime.now()
            )
            session.add(log)
            await session.commit()
    except Exception as e:
        logger.error(f"记录任务开始失败: {e}")


async def _log_task_completion(task_type: str, task_id: str, start_time: datetime, records_processed: int):
    """记录任务完成"""
    try:
        async with get_async_session() as session:
            # 查找现有记录
            result = await session.execute(
                "SELECT id FROM data_update_logs WHERE task_id = :task_id",
                {"task_id": task_id}
            )
            log_id = result.scalar()
            
            if log_id:
                # 更新现有记录
                await session.execute(
                    """UPDATE data_update_logs 
                       SET status = 'completed', 
                           completed_at = :completed_at,
                           records_processed = :records_processed,
                           duration_seconds = :duration
                       WHERE id = :log_id""",
                    {
                        "completed_at": datetime.now(),
                        "records_processed": records_processed,
                        "duration": (datetime.now() - start_time).total_seconds(),
                        "log_id": log_id
                    }
                )
            else:
                # 创建新记录
                log = DataUpdateLog(
                    task_type=task_type,
                    task_id=task_id,
                    status="completed",
                    started_at=start_time,
                    completed_at=datetime.now(),
                    records_processed=records_processed,
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
                session.add(log)
            
            await session.commit()
    except Exception as e:
        logger.error(f"记录任务完成失败: {e}")


async def _log_task_failure(task_type: str, task_id: str, start_time: datetime, error_message: str):
    """记录任务失败"""
    try:
        async with get_async_session() as session:
            # 查找现有记录
            result = await session.execute(
                "SELECT id FROM data_update_logs WHERE task_id = :task_id",
                {"task_id": task_id}
            )
            log_id = result.scalar()
            
            if log_id:
                # 更新现有记录
                await session.execute(
                    """UPDATE data_update_logs 
                       SET status = 'failed', 
                           completed_at = :completed_at,
                           error_message = :error_message,
                           duration_seconds = :duration
                       WHERE id = :log_id""",
                    {
                        "completed_at": datetime.now(),
                        "error_message": error_message,
                        "duration": (datetime.now() - start_time).total_seconds(),
                        "log_id": log_id
                    }
                )
            else:
                # 创建新记录
                log = DataUpdateLog(
                    task_type=task_type,
                    task_id=task_id,
                    status="failed",
                    started_at=start_time,
                    completed_at=datetime.now(),
                    error_message=error_message,
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
                session.add(log)
            
            await session.commit()
    except Exception as e:
        logger.error(f"记录任务失败失败: {e}")


# 导出
__all__ = [
    "celery_app",
    "update_stock_basic",
    "update_daily_quotes", 
    "update_technical_indicators",
    "update_nine_turn_signals",
    "cleanup_old_data",
    "health_check",
    "trigger_update_stock_basic",
    "trigger_update_daily_quotes",
    "trigger_update_technical_indicators", 
    "trigger_update_nine_turn_signals",
    "get_task_status",
]