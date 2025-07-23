"""
数据库连接和会话管理
支持异步和同步操作
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager, contextmanager
from loguru import logger

from app.config import settings, DatabaseConfig
from app.models import Base

# 异步数据库引擎
async_engine = None
async_session_factory = None

# 同步数据库引擎
sync_engine = None
sync_session_factory = None


async def init_db():
    """初始化数据库连接"""
    global async_engine, async_session_factory, sync_engine, sync_session_factory
    
    try:
        # 创建异步引擎
        async_engine = create_async_engine(
            DatabaseConfig.get_async_url(),
            **DatabaseConfig.get_engine_config(),
            future=True
        )
        
        # 创建异步会话工厂
        async_session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # 创建同步引擎（用于Alembic和某些同步操作）
        sync_engine = create_engine(
            DatabaseConfig.get_sync_url(),
            **DatabaseConfig.get_engine_config(),
            future=True
        )
        
        # 创建同步会话工厂
        sync_session_factory = sessionmaker(
            bind=sync_engine,
            autoflush=True,
            autocommit=False
        )
        
        # 注册数据库事件监听器
        @event.listens_for(sync_engine, "connect", once=True)
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """设置SQLite参数（如果使用SQLite）"""
            if "sqlite" in DatabaseConfig.get_sync_url():
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # 连接池事件
        @event.listens_for(sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接池检出事件"""
            logger.debug("数据库连接已检出")

        @event.listens_for(sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接池检入事件"""
            logger.debug("数据库连接已检入")
        
        # 测试连接
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
        
        logger.info("数据库连接初始化成功")
        
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    global async_engine, sync_engine
    
    try:
        if async_engine:
            await async_engine.dispose()
            logger.info("异步数据库连接已关闭")
        
        if sync_engine:
            sync_engine.dispose()
            logger.info("同步数据库连接已关闭")
            
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


async def create_tables():
    """创建数据库表"""
    if not async_engine:
        raise RuntimeError("数据库引擎未初始化")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("数据库表创建完成")


async def drop_tables():
    """删除数据库表"""
    if not async_engine:
        raise RuntimeError("数据库引擎未初始化")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("数据库表删除完成")


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    if not async_session_factory:
        raise RuntimeError("异步会话工厂未初始化")
    
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """获取同步数据库会话"""
    if not sync_session_factory:
        raise RuntimeError("同步会话工厂未初始化")
    
    session = sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库会话错误: {e}")
        raise
    finally:
        session.close()


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    async def get_async_session() -> AsyncSession:
        """获取异步会话（用于依赖注入）"""
        if not async_session_factory:
            raise RuntimeError("异步会话工厂未初始化")
        return async_session_factory()
    
    @staticmethod
    def get_sync_session() -> Session:
        """获取同步会话"""
        if not sync_session_factory:
            raise RuntimeError("同步会话工厂未初始化")
        return sync_session_factory()
    
    @staticmethod
    async def execute_raw_sql(sql: str, params: dict = None):
        """执行原生SQL"""
        async with get_async_session() as session:
            result = await session.execute(sql, params or {})
            return result.fetchall()
    
    @staticmethod
    async def check_connection():
        """检查数据库连接"""
        try:
            async with get_async_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False


# FastAPI依赖注入函数
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入：获取数据库会话"""
    async with get_async_session() as session:
        yield session


# 健康检查
class DatabaseHealthCheck:
    """数据库健康检查"""
    
    @staticmethod
    async def check_async_connection() -> bool:
        """检查异步连接"""
        try:
            async with get_async_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"异步数据库连接检查失败: {e}")
            return False
    
    @staticmethod
    def check_sync_connection() -> bool:
        """检查同步连接"""
        try:
            with get_sync_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"同步数据库连接检查失败: {e}")
            return False
    
    @staticmethod
    async def get_connection_info() -> dict:
        """获取连接信息"""
        info = {
            "async_engine_url": str(async_engine.url) if async_engine else None,
            "sync_engine_url": str(sync_engine.url) if sync_engine else None,
            "async_pool_size": async_engine.pool.size() if async_engine else 0,
            "sync_pool_size": sync_engine.pool.size() if sync_engine else 0,
            "async_checked_out": async_engine.pool.checkedout() if async_engine else 0,
            "sync_checked_out": sync_engine.pool.checkedout() if sync_engine else 0,
        }
        return info


# 导出
__all__ = [
    "init_db",
    "close_db",
    "create_tables",
    "drop_tables",
    "get_async_session",
    "get_sync_session",
    "get_db_session",
    "DatabaseManager",
    "DatabaseHealthCheck",
    "async_engine",
    "sync_engine",
]