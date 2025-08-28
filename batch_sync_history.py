#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量同步所有A股股票120个交易日历史数据
"""

import time
import logging
from datetime import datetime
from data_sync import DataSync

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_sync_history.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def batch_sync_all_stocks_history(start_date='20240101'):
    """
    批量同步所有A股股票的历史数据
    
    Args:
        start_date: 开始日期，格式YYYYMMDD，默认从2024年1月1日开始
    """
    logger.info("开始批量同步所有A股股票历史数据")
    logger.info(f"同步起始日期: {start_date}")
    
    data_sync = DataSync()
    
    # 获取所有A股股票列表
    logger.info("正在获取A股股票列表...")
    stock_list = data_sync.get_stock_list()
    
    if not stock_list:
        logger.error("获取股票列表失败")
        return False
    
    total_stocks = len(stock_list)
    logger.info(f"获取到 {total_stocks} 只A股股票")
    
    # 统计信息
    success_count = 0
    failed_count = 0
    total_data_count = 0
    
    # 开始批量同步
    start_time = datetime.now()
    
    for i, ts_code in enumerate(stock_list, 1):
        try:
            logger.info(f"正在处理 {ts_code} ({i}/{total_stocks})")
            
            # 获取历史数据
            df = data_sync.get_daily_data(ts_code, start_date=start_date)
            
            if not df.empty:
                # 保存数据
                saved_count = data_sync.save_daily_data(df)
                total_data_count += saved_count
                success_count += 1
                logger.info(f"✓ {ts_code} 成功保存 {saved_count} 条数据")
            else:
                logger.warning(f"⚠ {ts_code} 没有获取到数据")
                failed_count += 1
            
            # API限制：每次调用后休息0.2秒
            time.sleep(0.2)
            
            # 每100只股票输出进度统计
            if i % 100 == 0:
                elapsed_time = datetime.now() - start_time
                avg_time_per_stock = elapsed_time.total_seconds() / i
                remaining_stocks = total_stocks - i
                estimated_remaining_time = remaining_stocks * avg_time_per_stock
                
                logger.info(f"进度报告 ({i}/{total_stocks}):")
                logger.info(f"  - 成功: {success_count}, 失败: {failed_count}")
                logger.info(f"  - 已保存数据: {total_data_count} 条")
                logger.info(f"  - 已用时: {elapsed_time}")
                logger.info(f"  - 预计剩余时间: {estimated_remaining_time:.0f} 秒")
                
        except Exception as e:
            logger.error(f"✗ 处理股票 {ts_code} 时发生错误: {e}")
            failed_count += 1
            continue
    
    # 最终统计
    end_time = datetime.now()
    total_time = end_time - start_time
    
    logger.info("=" * 60)
    logger.info("批量同步完成！")
    logger.info(f"总股票数: {total_stocks}")
    logger.info(f"成功同步: {success_count}")
    logger.info(f"失败数量: {failed_count}")
    logger.info(f"总数据量: {total_data_count} 条")
    logger.info(f"总用时: {total_time}")
    logger.info(f"平均每只股票用时: {total_time.total_seconds() / total_stocks:.2f} 秒")
    logger.info("=" * 60)
    
    return {
        'total_stocks': total_stocks,
        'success_count': success_count,
        'failed_count': failed_count,
        'total_data_count': total_data_count,
        'total_time': total_time
    }

def main():
    """
    主函数
    """
    print("A股历史数据批量同步工具")
    print("=" * 40)
    
    # 确认操作
    confirm = input("此操作将为所有A股股票同步历史数据，可能需要较长时间。是否继续？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 询问起始日期
    start_date = input("请输入起始日期 (格式: YYYYMMDD, 默认: 20240101): ").strip()
    if not start_date:
        start_date = '20240101'
    
    # 验证日期格式
    try:
        datetime.strptime(start_date, '%Y%m%d')
    except ValueError:
        print("日期格式错误，请使用 YYYYMMDD 格式")
        return
    
    print(f"开始同步，起始日期: {start_date}")
    print("请耐心等待，过程中会显示进度信息...")
    print()
    
    # 执行批量同步
    result = batch_sync_all_stocks_history(start_date)
    
    if result:
        print("\n同步完成！详细日志已保存到 batch_sync_history.log")
    else:
        print("\n同步失败，请检查日志文件")

if __name__ == '__main__':
    main()