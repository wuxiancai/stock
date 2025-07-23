"""
服务层测试
"""

import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import StockDataService
from tests.conftest import TestDataFactory


class TestStockDataService:
    """股票数据服务测试"""
    
    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """创建服务实例"""
        return StockDataService()
    
    async def test_get_stock_list_empty(
        self, 
        service: StockDataService,
        db_session: AsyncSession
    ):
        """测试获取空股票列表"""
        result = await service.get_stock_list()
        
        assert result["total"] == 0
        assert result["stocks"] == []
        assert result["page"] == 1
        assert result["page_size"] == 20
    
    async def test_get_stock_list_with_data(
        self,
        service: StockDataService,
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
        result = await service.get_stock_list()
        
        assert result["total"] == 2
        assert len(result["stocks"]) == 2
        
        # 验证数据
        stock_codes = [stock["ts_code"] for stock in result["stocks"]]
        assert "000001.SZ" in stock_codes
        assert "000002.SZ" in stock_codes
    
    async def test_get_stock_list_with_search(
        self,
        service: StockDataService,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试搜索股票"""
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
        
        # 测试搜索
        result = await service.get_stock_list(search="平安")
        
        assert result["total"] == 1
        assert result["stocks"][0]["name"] == "平安银行"
    
    async def test_get_stock_detail_not_found(
        self,
        service: StockDataService
    ):
        """测试获取不存在的股票详情"""
        result = await service.get_stock_detail("999999.SZ")
        assert result is None
    
    async def test_get_stock_detail_success(
        self,
        service: StockDataService,
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
        result = await service.get_stock_detail("000001.SZ")
        
        assert result is not None
        assert result["ts_code"] == "000001.SZ"
        assert result["name"] == "平安银行"
        assert "latest_quote" in result
    
    @patch('app.data_sources.data_source_manager.get_stock_basic')
    async def test_update_stock_basic_success(
        self,
        mock_get_stock_basic,
        service: StockDataService,
        db_session: AsyncSession
    ):
        """测试更新股票基础信息成功"""
        # 模拟数据源返回
        mock_data = pd.DataFrame([
            {
                "ts_code": "000001.SZ",
                "symbol": "000001",
                "name": "平安银行",
                "area": "深圳",
                "industry": "银行",
                "market": "主板",
                "list_date": "19910403",
                "is_hs": "S"
            }
        ])
        mock_get_stock_basic.return_value = mock_data
        
        # 执行更新
        result = await service.update_stock_basic()
        
        assert result["success"] is True
        assert result["updated_count"] == 1
        assert "平安银行" in result["message"]
    
    @patch('app.data_sources.data_source_manager.get_stock_basic')
    async def test_update_stock_basic_failure(
        self,
        mock_get_stock_basic,
        service: StockDataService
    ):
        """测试更新股票基础信息失败"""
        # 模拟数据源异常
        mock_get_stock_basic.side_effect = Exception("数据源异常")
        
        # 执行更新
        result = await service.update_stock_basic()
        
        assert result["success"] is False
        assert "数据源异常" in result["message"]
    
    @patch('app.data_sources.data_source_manager.get_daily_quotes')
    async def test_update_daily_quotes_success(
        self,
        mock_get_daily_quotes,
        service: StockDataService,
        db_session: AsyncSession,
        test_data_factory: TestDataFactory
    ):
        """测试更新日线数据成功"""
        # 创建股票基础信息
        stock = test_data_factory.create_stock_basic()
        db_session.add(stock)
        await db_session.commit()
        
        # 模拟数据源返回
        mock_data = pd.DataFrame([
            {
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
        ])
        mock_get_daily_quotes.return_value = mock_data
        
        # 执行更新
        result = await service.update_daily_quotes(ts_codes=["000001.SZ"])
        
        assert result["success"] is True
        assert result["updated_count"] == 1
    
    async def test_get_nine_turn_stocks_empty(
        self,
        service: StockDataService
    ):
        """测试获取空九转信号"""
        result = await service.get_nine_turn_stocks()
        assert result == []
    
    async def test_get_nine_turn_stocks_with_data(
        self,
        service: StockDataService,
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
        result = await service.get_nine_turn_stocks()
        
        assert len(result) == 1
        assert result[0]["ts_code"] == "000001.SZ"
        assert result[0]["signal_type"] == "buy_setup"
    
    async def test_get_nine_turn_stocks_filter_by_type(
        self,
        service: StockDataService,
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
        result = await service.get_nine_turn_stocks(signal_type="buy")
        
        assert len(result) == 1
        assert result[0]["signal_type"] == "buy_setup"
    
    async def test_update_technical_indicators_no_data(
        self,
        service: StockDataService
    ):
        """测试更新技术指标但无数据"""
        result = await service.update_technical_indicators(ts_codes=["999999.SZ"])
        
        assert result["success"] is True
        assert result["updated_count"] == 0
    
    async def test_update_nine_turn_signals_no_data(
        self,
        service: StockDataService
    ):
        """测试更新九转信号但无数据"""
        result = await service.update_nine_turn_signals(ts_codes=["999999.SZ"])
        
        assert result["success"] is True
        assert result["updated_count"] == 0


class TestDataCleaning:
    """数据清洗测试"""
    
    def test_clean_stock_basic_data(self):
        """测试股票基础信息数据清洗"""
        from app.services import StockDataService
        
        # 创建包含异常数据的DataFrame
        df = pd.DataFrame([
            {
                "ts_code": "000001.SZ",
                "symbol": "000001",
                "name": "平安银行",
                "area": "深圳",
                "industry": "银行",
                "market": "主板",
                "list_date": "19910403",
                "is_hs": "S"
            },
            {
                "ts_code": None,  # 空值
                "symbol": "000002",
                "name": "万科A",
                "area": "深圳",
                "industry": "房地产",
                "market": "主板",
                "list_date": "19910129",
                "is_hs": "S"
            },
            {
                "ts_code": "000003.SZ",
                "symbol": "000003",
                "name": "",  # 空名称
                "area": "深圳",
                "industry": "房地产",
                "market": "主板",
                "list_date": "19910403",
                "is_hs": "S"
            }
        ])
        
        service = StockDataService()
        cleaned_df = service._clean_stock_basic_data(df)
        
        # 验证清洗结果
        assert len(cleaned_df) == 1  # 只保留有效数据
        assert cleaned_df.iloc[0]["ts_code"] == "000001.SZ"
    
    def test_clean_daily_quote_data(self):
        """测试日线数据清洗"""
        from app.services import StockDataService
        
        # 创建包含异常数据的DataFrame
        df = pd.DataFrame([
            {
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
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240102",
                "open": None,  # 空值
                "high": 11.0,
                "low": 9.5,
                "close": 10.5,
                "pre_close": 10.0,
                "change": 0.5,
                "pct_chg": 5.0,
                "vol": 1000000,
                "amount": 10500000.0
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240103",
                "open": 10.0,
                "high": 8.0,  # 最高价小于最低价（异常）
                "low": 9.5,
                "close": 10.5,
                "pre_close": 10.0,
                "change": 0.5,
                "pct_chg": 5.0,
                "vol": 1000000,
                "amount": 10500000.0
            }
        ])
        
        service = StockDataService()
        cleaned_df = service._clean_daily_quote_data(df)
        
        # 验证清洗结果
        assert len(cleaned_df) == 1  # 只保留有效数据
        assert cleaned_df.iloc[0]["trade_date"] == "20240101"