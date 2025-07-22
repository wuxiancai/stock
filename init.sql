-- 初始化数据库脚本

-- 创建数据库（如果不存在）
-- CREATE DATABASE stock_db;

-- 使用数据库
-- \c stock_db;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建索引函数
CREATE OR REPLACE FUNCTION create_indexes() RETURNS void AS $$
BEGIN
    -- 为股票表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_stocks_ts_code') THEN
        CREATE INDEX idx_stocks_ts_code ON stocks(ts_code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_stocks_symbol') THEN
        CREATE INDEX idx_stocks_symbol ON stocks(symbol);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_stocks_name') THEN
        CREATE INDEX idx_stocks_name ON stocks(name);
    END IF;
    
    -- 为股票日线数据表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_stock_daily_ts_code_date') THEN
        CREATE INDEX idx_stock_daily_ts_code_date ON stock_daily(ts_code, trade_date);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_stock_daily_trade_date') THEN
        CREATE INDEX idx_stock_daily_trade_date ON stock_daily(trade_date);
    END IF;
    
    -- 为技术指标表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_technical_indicators_ts_code_date') THEN
        CREATE INDEX idx_technical_indicators_ts_code_date ON technical_indicators(ts_code, trade_date);
    END IF;
    
    -- 为九转信号表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_nine_turn_signals_ts_code_date') THEN
        CREATE INDEX idx_nine_turn_signals_ts_code_date ON nine_turn_signals(ts_code, trade_date);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_nine_turn_signals_signal_type') THEN
        CREATE INDEX idx_nine_turn_signals_signal_type ON nine_turn_signals(signal_type);
    END IF;
    
    -- 为用户自选股表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_favorites_user_id') THEN
        CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_favorites_ts_code') THEN
        CREATE INDEX idx_user_favorites_ts_code ON user_favorites(ts_code);
    END IF;
    
    -- 为每日基本面数据表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_daily_basic_ts_code_date') THEN
        CREATE INDEX idx_daily_basic_ts_code_date ON daily_basic(ts_code, trade_date);
    END IF;
    
    -- 为资金流向表创建索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_money_flow_ts_code_date') THEN
        CREATE INDEX idx_money_flow_ts_code_date ON money_flow(ts_code, trade_date);
    END IF;
    
    RAISE NOTICE '数据库索引创建完成';
END;
$$ LANGUAGE plpgsql;

-- 执行索引创建
-- SELECT create_indexes();

-- 插入一些初始数据
INSERT INTO users (username, email, hashed_password, is_active, is_superuser, created_at, updated_at)
VALUES 
    ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6QJSm2/K.W', true, true, NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- 创建一些示例股票数据
INSERT INTO stocks (ts_code, symbol, name, area, industry, market, list_date, is_active, created_at, updated_at)
VALUES 
    ('000001.SZ', '000001', '平安银行', '深圳', '银行', '主板', '19910403', true, NOW(), NOW()),
    ('000002.SZ', '000002', '万科A', '深圳', '房地产开发', '主板', '19910129', true, NOW(), NOW()),
    ('600000.SH', '600000', '浦发银行', '上海', '银行', '主板', '19990810', true, NOW(), NOW()),
    ('600036.SH', '600036', '招商银行', '深圳', '银行', '主板', '20020409', true, NOW(), NOW()),
    ('600519.SH', '600519', '贵州茅台', '贵州', '白酒', '主板', '20010827', true, NOW(), NOW())
ON CONFLICT (ts_code) DO NOTHING;

COMMIT;