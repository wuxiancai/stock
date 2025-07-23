# Tushare历史股票数据获取指南

## 概述

股票交易系统已经成功启动，现在可以通过多种方式获取Tushare的历史股票数据。

## 服务状态

✅ 服务器运行在: http://localhost:8080
✅ Tushare数据源: 已连接
✅ AKShare数据源: 已连接
✅ 数据库: PostgreSQL 已连接
✅ 缓存: Redis 已连接

## 获取历史股票数据的方法

### 1. 通过API接口获取

#### 1.1 更新股票基础信息
```bash
curl -X POST "http://localhost:8080/api/v1/update/stock-basic"
```

#### 1.2 更新日线行情数据
```bash
# 更新所有股票的日线行情
curl -X POST "http://localhost:8080/api/v1/update/daily-quotes"

# 更新特定股票的日线行情
curl -X POST "http://localhost:8080/api/v1/update/daily-quotes?ts_codes=000001.SZ,000002.SZ"

# 更新特定日期的行情
curl -X POST "http://localhost:8080/api/v1/update/daily-quotes?trade_date=20250722"
```

#### 1.3 获取股票列表
```bash
# 获取所有股票
curl "http://localhost:8080/api/v1/stocks"

# 获取深交所股票
curl "http://localhost:8080/api/v1/stocks?exchange=SZSE"

# 获取上交所股票
curl "http://localhost:8080/api/v1/stocks?exchange=SSE"
```

#### 1.4 获取股票详情
```bash
# 获取平安银行详情
curl "http://localhost:8080/api/v1/stocks/000001.SZ"
```

#### 1.5 获取历史行情
```bash
# 获取股票历史行情
curl "http://localhost:8080/api/v1/stocks/000001.SZ/quotes?start_date=20250101&end_date=20250722&limit=100"
```

#### 1.6 获取实时行情
```bash
curl "http://localhost:8080/api/v1/realtime/quotes?limit=50"
```

#### 1.7 获取九转信号
```bash
# 获取所有九转信号
curl "http://localhost:8080/api/v1/nine-turn"

# 获取买入信号
curl "http://localhost:8080/api/v1/nine-turn?signal_type=buy"

# 获取卖出信号
curl "http://localhost:8080/api/v1/nine-turn?signal_type=sell"
```

### 2. 通过Python脚本获取

#### 2.1 基础数据获取示例
```python
import asyncio
from app.data_sources import data_source_manager

async def get_stock_data():
    # 初始化数据源
    await data_source_manager.initialize()
    
    try:
        # 获取股票基础信息
        stock_basic = await data_source_manager.get_stock_basic()
        print(f"获取到 {len(stock_basic)} 只股票")
        
        # 获取历史行情
        daily_data = await data_source_manager.get_daily_quotes(
            ts_code="000001.SZ",
            start_date="20250101",
            end_date="20250722"
        )
        print(f"获取到 {len(daily_data)} 条历史数据")
        
        # 获取实时行情
        realtime_data = await data_source_manager.get_realtime_quotes()
        print(f"获取到 {len(realtime_data)} 条实时数据")
        
    finally:
        await data_source_manager.close()

# 运行
asyncio.run(get_stock_data())
```

#### 2.2 批量数据更新示例
```python
import asyncio
from app.services import stock_data_service

async def update_all_data():
    try:
        # 更新股票基础信息
        await stock_data_service.update_stock_basic()
        
        # 更新日线行情
        await stock_data_service.update_daily_quotes()
        
        # 更新技术指标
        await stock_data_service.update_technical_indicators()
        
        # 更新九转信号
        await stock_data_service.update_nine_turn_signals()
        
        print("所有数据更新完成")
        
    except Exception as e:
        print(f"更新失败: {e}")

# 运行
asyncio.run(update_all_data())
```

### 3. 通过Web界面获取

访问 http://localhost:8080 可以看到系统的Web界面，包含：
- 系统状态监控
- API文档链接
- 健康检查接口

### 4. 数据存储位置

所有获取的历史数据都存储在PostgreSQL数据库中：

- **stock_basic**: 股票基础信息表
- **daily_quotes**: 日线行情数据表
- **technical_indicators**: 技术指标表
- **nine_turn_signals**: 九转信号表
- **data_update_logs**: 数据更新日志表

### 5. 常用股票代码示例

- 平安银行: 000001.SZ
- 万科A: 000002.SZ
- 浦发银行: 600000.SH
- 招商银行: 600036.SH
- 中国平安: 601318.SH
- 贵州茅台: 600519.SH

### 6. 数据更新频率

系统支持以下更新策略：
- **实时数据**: 通过WebSocket实时推送
- **日线数据**: 每日收盘后更新
- **技术指标**: 基于最新行情数据计算
- **九转信号**: 基于技术分析实时计算

### 7. 错误处理

如果遇到数据获取问题：

1. 检查Tushare Token是否正确配置
2. 检查网络连接
3. 查看服务器日志: `tail -f logs/app.log`
4. 检查API限制和配额

### 8. 性能优化

- 使用Redis缓存提高查询速度
- 支持批量数据更新
- 异步处理提高并发性能
- 数据库索引优化查询效率

## 测试验证

运行测试脚本验证数据获取功能：
```bash
# 基础测试
python3 test_tushare_data.py

# 特定股票测试
python3 test_tushare_data.py specific
```

## 注意事项

1. **API限制**: Tushare有调用频率限制，请合理使用
2. **数据延迟**: 免费版本可能有数据延迟
3. **存储空间**: 历史数据会占用较多存储空间
4. **网络稳定**: 确保网络连接稳定以获取实时数据

现在你可以开始使用这些方法获取Tushare的历史股票数据了！