#!/usr/bin/env python3
"""
测试Tushare历史股票数据获取
"""

import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data_sources import data_source_manager


async def test_tushare_data():
    """测试Tushare数据获取"""
    try:
        # 初始化数据源
        logger.info("初始化数据源管理器...")
        await data_source_manager.initialize()
        
        # 测试获取股票基础信息
        logger.info("获取股票基础信息...")
        stock_basic = await data_source_manager.get_stock_basic()
        logger.info(f"获取到 {len(stock_basic)} 只股票的基础信息")
        
        # 显示前5只股票
        print("\n=== 股票基础信息示例 ===")
        print(stock_basic.head().to_string())
        
        # 测试获取历史行情数据
        # 选择平安银行 (000001.SZ) 作为示例
        ts_code = "000001.SZ"
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        logger.info(f"获取 {ts_code} 最近30天的历史行情...")
        daily_data = await data_source_manager.get_daily_quotes(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        
        if not daily_data.empty:
            print(f"\n=== {ts_code} 历史行情数据 ===")
            print(f"数据范围: {start_date} 到 {end_date}")
            print(f"数据条数: {len(daily_data)}")
            print(daily_data.to_string())
        else:
            logger.warning("未获取到历史行情数据")
        
        # 测试获取实时行情
        logger.info("获取实时行情数据...")
        realtime_data = await data_source_manager.get_realtime_quotes()
        
        if not realtime_data.empty:
            print(f"\n=== 实时行情数据示例 ===")
            print(f"数据条数: {len(realtime_data)}")
            print(realtime_data.head(10).to_string())
        else:
            logger.warning("未获取到实时行情数据")
        
        # 测试获取市场情绪数据
        logger.info("获取市场情绪数据...")
        sentiment_data = await data_source_manager.get_market_sentiment()
        
        print(f"\n=== 市场情绪数据 ===")
        for key, value in sentiment_data.items():
            if key == "timestamp":
                print(f"{key}: {value}")
            else:
                print(f"{key}: {len(value) if hasattr(value, '__len__') else value} 条数据")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据源
        await data_source_manager.close()


async def test_specific_stock_data():
    """测试特定股票的详细数据获取"""
    try:
        await data_source_manager.initialize()
        
        # 测试多只股票的数据
        test_stocks = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH"]
        
        for ts_code in test_stocks:
            logger.info(f"获取 {ts_code} 的数据...")
            
            # 获取最近10天的数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
            daily_data = await data_source_manager.get_daily_quotes(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not daily_data.empty:
                latest = daily_data.iloc[0]  # 最新数据
                print(f"\n{ts_code} 最新行情:")
                print(f"  交易日期: {latest['trade_date']}")
                print(f"  收盘价: {latest['close']:.2f}")
                print(f"  涨跌幅: {latest.get('pct_chg', 'N/A')}%")
                print(f"  成交量: {latest.get('vol', 'N/A')}")
                print(f"  成交额: {latest.get('amount', 'N/A')}")
            else:
                print(f"{ts_code}: 无数据")
    
    except Exception as e:
        logger.error(f"测试失败: {e}")
    
    finally:
        await data_source_manager.close()


if __name__ == "__main__":
    print("=== Tushare历史股票数据获取测试 ===\n")
    
    # 选择测试模式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "specific":
        asyncio.run(test_specific_stock_data())
    else:
        asyncio.run(test_tushare_data())