import logging
from sqlalchemy import text
from app.database.database import async_engine, Base, test_connection
# 明确导入所有模型，确保SQLAlchemy能正确识别表的依赖关系
from app.database.models import (
    Stock, StockDaily, TechnicalIndicator, User, UserFavorite, 
    NineTurnSignal, DailyBasic, MoneyFlow
)

logger = logging.getLogger(__name__)

async def init_database():
    """初始化数据库"""
    try:
        # 测试数据库连接
        logger.info("🔍 测试数据库连接...")
        if not await test_connection():
            raise Exception("数据库连接失败")
        
        logger.info("✅ 数据库连接成功")
        
        # 先删除所有现有表，确保表结构的完整性
        logger.info("🗑️ 清理现有数据库表...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("✅ 现有表清理完成")
        
        # 手动控制表创建顺序
        logger.info("📋 按顺序创建数据库表...")
        await create_tables_in_order()
        
        logger.info("✅ 数据库表创建完成")
        
        # 创建索引（如果需要额外的索引）
        await create_additional_indexes()
        
        logger.info("✅ 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

async def create_tables_in_order():
    """按正确顺序创建表"""
    async with async_engine.begin() as conn:
        # 1. 首先创建基础表（没有外键依赖的表）
        logger.info("创建基础表: users, stocks")
        await conn.run_sync(User.__table__.create, checkfirst=True)
        await conn.run_sync(Stock.__table__.create, checkfirst=True)
        
        # 2. 然后创建依赖基础表的表
        logger.info("创建依赖表: stock_daily, technical_indicators, nine_turn_signals, daily_basic, money_flow, user_favorites")
        await conn.run_sync(StockDaily.__table__.create, checkfirst=True)
        await conn.run_sync(TechnicalIndicator.__table__.create, checkfirst=True)
        await conn.run_sync(NineTurnSignal.__table__.create, checkfirst=True)
        await conn.run_sync(DailyBasic.__table__.create, checkfirst=True)
        await conn.run_sync(MoneyFlow.__table__.create, checkfirst=True)
        await conn.run_sync(UserFavorite.__table__.create, checkfirst=True)

async def create_additional_indexes():
    """创建额外的索引"""
    indexes = [
        # 股票代码索引
        "CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);",
        "CREATE INDEX IF NOT EXISTS idx_stocks_industry ON stocks(industry);",
        
        # 行情数据复合索引
        "CREATE INDEX IF NOT EXISTS idx_stock_daily_code_date_desc ON stock_daily(stock_code, trade_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_stock_daily_date_desc ON stock_daily(trade_date DESC);",
        
        # 技术指标索引
        "CREATE INDEX IF NOT EXISTS idx_technical_code_date_desc ON technical_indicators(stock_code, trade_date DESC);",
        
        # 九转信号索引
        "CREATE INDEX IF NOT EXISTS idx_nine_turn_date_desc ON nine_turn_signals(signal_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_nine_turn_type_date ON nine_turn_signals(signal_type, signal_date DESC);",
        
        # 用户相关索引
        "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_user_favorites_created ON user_favorites(created_at DESC);",
    ]
    
    try:
        async with async_engine.begin() as conn:
            for index_sql in indexes:
                await conn.execute(text(index_sql))
        logger.info("✅ 额外索引创建完成")
    except Exception as e:
        logger.warning(f"⚠️ 创建额外索引时出现警告: {e}")

async def drop_all_tables():
    """删除所有表（谨慎使用）"""
    logger.warning("⚠️ 正在删除所有数据库表...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("✅ 所有表已删除")

async def reset_database():
    """重置数据库（删除并重新创建所有表）"""
    logger.warning("⚠️ 正在重置数据库...")
    await drop_all_tables()
    await init_database()
    logger.info("✅ 数据库重置完成")