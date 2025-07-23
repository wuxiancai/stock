"""
API接口测试
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import TestDataFactory


class TestStockAPI:
    """股票API测试"""
    
    async def test_get_stocks_empty(self, client: AsyncClient):
        """测试获取空股票列表"""
        response = await client.get("/api/v1/stocks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["stocks"] == []
    
    async def test_get_stocks_with_data(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试获取股票列表"""
        # 创建测试数据
        stock1 = test_data_factory.create_stock_basic(
            ts_code="000001.SZ",
            name="平安银行"
        )
        stock2 = test_data_factory.create_stock_basic(
            ts_code="000002.SZ", 
            name="万科A"
        )
        
        db_session.add(stock1)
        db_session.add(stock2)
        await db_session.commit()
        
        # 测试获取列表
        response = await client.get("/api/v1/stocks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["stocks"]) == 2
        
        # 验证数据
        stock_codes = [stock["ts_code"] for stock in data["stocks"]]
        assert "000001.SZ" in stock_codes
        assert "000002.SZ" in stock_codes
    
    async def test_get_stocks_with_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试分页"""
        # 创建多个股票
        for i in range(15):
            stock = test_data_factory.create_stock_basic(
                ts_code=f"00000{i:02d}.SZ",
                name=f"测试股票{i}"
            )
            db_session.add(stock)
        
        await db_session.commit()
        
        # 测试第一页
        response = await client.get("/api/v1/stocks?page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 15
        assert len(data["stocks"]) == 10
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 2
        
        # 测试第二页
        response = await client.get("/api/v1/stocks?page=2&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["stocks"]) == 5
    
    async def test_get_stock_detail_not_found(self, client: AsyncClient):
        """测试获取不存在的股票详情"""
        response = await client.get("/api/v1/stocks/999999.SZ")
        assert response.status_code == 404
    
    async def test_get_stock_detail_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试获取股票详情"""
        # 创建测试数据
        stock = test_data_factory.create_stock_basic()
        daily_quote = test_data_factory.create_daily_quote()
        
        db_session.add(stock)
        db_session.add(daily_quote)
        await db_session.commit()
        
        # 测试获取详情
        response = await client.get("/api/v1/stocks/000001.SZ")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ts_code"] == "000001.SZ"
        assert data["name"] == "平安银行"
        assert "latest_quote" in data
    
    async def test_get_stock_quotes(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试获取股票历史行情"""
        # 创建测试数据
        stock = test_data_factory.create_stock_basic()
        
        # 创建多天的行情数据
        for i in range(5):
            quote = test_data_factory.create_daily_quote(
                trade_date=f"2024010{i+1}",
                close=10.0 + i * 0.5
            )
            db_session.add(quote)
        
        db_session.add(stock)
        await db_session.commit()
        
        # 测试获取行情
        response = await client.get("/api/v1/stocks/000001.SZ/quotes")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 5
        
        # 验证数据按日期降序排列
        dates = [quote["trade_date"] for quote in data]
        assert dates == sorted(dates, reverse=True)
    
    async def test_get_stock_technical(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试获取技术指标"""
        # 创建测试数据
        stock = test_data_factory.create_stock_basic()
        tech_indicator = test_data_factory.create_technical_indicator()
        
        db_session.add(stock)
        db_session.add(tech_indicator)
        await db_session.commit()
        
        # 测试获取技术指标
        response = await client.get("/api/v1/stocks/000001.SZ/technical")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["ts_code"] == "000001.SZ"
        assert "ma5" in data[0]
        assert "rsi" in data[0]


class TestNineTurnAPI:
    """九转信号API测试"""
    
    async def test_get_nine_turn_signals_empty(self, client: AsyncClient):
        """测试获取空九转信号"""
        response = await client.get("/api/v1/nine-turn")
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    async def test_get_nine_turn_signals_with_data(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试获取九转信号"""
        # 创建测试数据
        stock = test_data_factory.create_stock_basic()
        signal = test_data_factory.create_nine_turn_signal()
        
        db_session.add(stock)
        db_session.add(signal)
        await db_session.commit()
        
        # 测试获取信号
        response = await client.get("/api/v1/nine-turn")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["ts_code"] == "000001.SZ"
        assert data[0]["signal_type"] == "buy_setup"
    
    async def test_get_nine_turn_signals_filter_by_type(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试按类型过滤九转信号"""
        # 创建测试数据
        stock = test_data_factory.create_stock_basic()
        
        buy_signal = test_data_factory.create_nine_turn_signal(
            signal_type="buy_setup"
        )
        sell_signal = test_data_factory.create_nine_turn_signal(
            ts_code="000002.SZ",
            signal_type="sell_setup"
        )
        
        db_session.add(stock)
        db_session.add(buy_signal)
        db_session.add(sell_signal)
        await db_session.commit()
        
        # 测试过滤买入信号
        response = await client.get("/api/v1/nine-turn?signal_type=buy")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["signal_type"] == "buy_setup"


class TestMarketAPI:
    """市场数据API测试"""
    
    async def test_get_realtime_quotes(self, client: AsyncClient):
        """测试获取实时行情"""
        response = await client.get("/api/v1/realtime/quotes")
        assert response.status_code == 200
        # 注意：这里可能返回空数据，因为依赖外部数据源
    
    async def test_get_market_sentiment(self, client: AsyncClient):
        """测试获取市场情绪"""
        response = await client.get("/api/v1/market/sentiment")
        assert response.status_code == 200
        # 注意：这里可能返回空数据，因为依赖外部数据源
    
    async def test_get_hot_stocks(self, client: AsyncClient):
        """测试获取热门股票"""
        response = await client.get("/api/v1/market/hot-stocks")
        assert response.status_code == 200
        # 注意：这里可能返回空数据，因为依赖外部数据源


class TestUpdateAPI:
    """数据更新API测试"""
    
    async def test_update_stock_basic(self, client: AsyncClient):
        """测试更新股票基础信息"""
        response = await client.post("/api/v1/update/stock-basic")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "message" in data
    
    async def test_update_daily_quotes(self, client: AsyncClient):
        """测试更新日线数据"""
        response = await client.post("/api/v1/update/daily-quotes")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "message" in data
    
    async def test_update_technical_indicators(self, client: AsyncClient):
        """测试更新技术指标"""
        response = await client.post("/api/v1/update/technical-indicators")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "message" in data
    
    async def test_update_nine_turn_signals(self, client: AsyncClient):
        """测试更新九转信号"""
        response = await client.post("/api/v1/update/nine-turn-signals")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "message" in data


class TestHealthAPI:
    """健康检查API测试"""
    
    async def test_health_check(self, client: AsyncClient):
        """测试健康检查"""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "cache" in data
        assert "data_sources" in data


class TestErrorHandling:
    """错误处理测试"""
    
    async def test_invalid_stock_code(self, client: AsyncClient):
        """测试无效股票代码"""
        response = await client.get("/api/v1/stocks/INVALID")
        assert response.status_code == 404
    
    async def test_invalid_pagination(self, client: AsyncClient):
        """测试无效分页参数"""
        response = await client.get("/api/v1/stocks?page=0")
        assert response.status_code == 422
        
        response = await client.get("/api/v1/stocks?page_size=0")
        assert response.status_code == 422
    
    async def test_invalid_date_range(self, client: AsyncClient):
        """测试无效日期范围"""
        response = await client.get("/api/v1/stocks/000001.SZ/quotes?start_date=invalid")
        assert response.status_code == 422