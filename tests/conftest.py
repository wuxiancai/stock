"""
测试配置模块
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

from main import app
from app.config import settings
from app.database import get_async_session, Base
from app.cache import get_redis_client
from app.models import *


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试数据库引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# 创建测试会话
TestAsyncSession = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_test_db() -> AsyncGenerator:
    """设置测试数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # 清理数据库
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with TestAsyncSession() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def redis_client() -> AsyncGenerator:
    """创建Redis客户端"""
    # 使用测试Redis数据库
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=15,  # 使用测试数据库
        decode_responses=True
    )
    
    yield client
    
    # 清理测试数据
    await client.flushdb()
    await client.close()


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """覆盖数据库依赖"""
    async def _override_get_db():
        yield db_session
    
    return _override_get_db


@pytest.fixture
def override_get_redis(redis_client):
    """覆盖Redis依赖"""
    async def _override_get_redis():
        return redis_client
    
    return _override_get_redis


@pytest.fixture
async def client(
    override_get_db,
    override_get_redis
) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    # 覆盖依赖
    app.dependency_overrides[get_async_session] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> Generator[TestClient, None]:
    """创建同步测试客户端"""
    with TestClient(app) as client:
        yield client


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_stock_basic(**kwargs):
        """创建股票基础信息"""
        default_data = {
            "ts_code": "000001.SZ",
            "symbol": "000001",
            "name": "平安银行",
            "area": "深圳",
            "industry": "银行",
            "market": "主板",
            "list_date": "19910403",
            "is_hs": "S"
        }
        default_data.update(kwargs)
        return StockBasic(**default_data)
    
    @staticmethod
    def create_daily_quote(**kwargs):
        """创建日线数据"""
        default_data = {
            "ts_code": "000001.SZ",
            "trade_date": "20240101",
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "pre_close": 10.0,
            "change": 0.5,
            "pct_chg": 5.0,
            "vol": 1000000,
            "amount": 10500000.0
        }
        default_data.update(kwargs)
        return DailyQuote(**default_data)
    
    @staticmethod
    def create_technical_indicator(**kwargs):
        """创建技术指标"""
        default_data = {
            "ts_code": "000001.SZ",
            "trade_date": "20240101",
            "ma5": 10.0,
            "ma10": 10.2,
            "ma20": 10.5,
            "ema12": 10.1,
            "ema26": 10.3,
            "macd": 0.1,
            "macd_signal": 0.05,
            "macd_hist": 0.05,
            "rsi": 55.0,
            "k": 60.0,
            "d": 55.0,
            "j": 65.0
        }
        default_data.update(kwargs)
        return TechnicalIndicator(**default_data)
    
    @staticmethod
    def create_nine_turn_signal(**kwargs):
        """创建九转信号"""
        default_data = {
            "ts_code": "000001.SZ",
            "trade_date": "20240101",
            "td_setup": 5,
            "td_countdown": 0,
            "signal_type": "buy_setup",
            "signal_strength": 0.7,
            "description": "买入设置第5天"
        }
        default_data.update(kwargs)
        return NineTurnSignal(**default_data)


@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory


# 测试配置
pytest_plugins = ["pytest_asyncio"]

# 异步测试配置
asyncio_mode = "auto"