import schedule
import time
import threading
from datetime import datetime
import logging
from data_sync import DataSync

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockScheduler:
    def __init__(self):
        self.data_sync = DataSync()
        self.is_running = False
    
    def daily_sync_job(self):
        """每日数据同步任务"""
        try:
            logger.info("开始执行每日数据同步任务")
            start_time = datetime.now()
            
            # 执行数据同步
            result = self.data_sync.sync_all_stocks()
            
            sync_end_time = datetime.now()
            sync_duration = (sync_end_time - start_time).total_seconds()
            
            logger.info(f"数据同步完成，耗时 {sync_duration:.2f} 秒")
            logger.info(f"同步结果: {result}")
            
            # 生成统一分析表
            logger.info("开始生成统一分析表")
            analysis_start_time = datetime.now()
            
            analysis_result = self.data_sync.generate_unified_analysis_data()
            
            analysis_end_time = datetime.now()
            analysis_duration = (analysis_end_time - analysis_start_time).total_seconds()
            
            if analysis_result.get('success'):
                logger.info(f"统一分析表生成完成，耗时 {analysis_duration:.2f} 秒")
                logger.info(f"分析表结果: {analysis_result}")
            else:
                logger.error(f"统一分析表生成失败: {analysis_result.get('message')}")
            
            total_duration = (analysis_end_time - start_time).total_seconds()
            logger.info(f"每日数据同步任务全部完成，总耗时 {total_duration:.2f} 秒")
            
        except Exception as e:
            logger.error(f"每日数据同步失败: {e}")
    
    def sync_latest_trading_day(self):
        """同步最新交易日数据"""
        try:
            logger.info("开始同步最新交易日数据")
            
            # 获取昨天的日期（因为股市数据通常有延迟）
            yesterday = datetime.now().strftime('%Y%m%d')
            
            # 尝试同步昨天的数据
            result = self.data_sync.sync_by_date(yesterday)
            
            if result > 0:
                logger.info(f"成功同步最新交易日 {yesterday} 的数据，共 {result} 条")
            else:
                logger.info(f"日期 {yesterday} 可能不是交易日或数据尚未更新")
                
        except Exception as e:
            logger.error(f"同步最新交易日数据失败: {e}")
    
    def td_sequential_filter_job(self):
        """九转序列筛选任务"""
        try:
            logger.info("开始执行九转序列筛选任务")
            start_time = datetime.now()
            
            # 导入filter_td_sequential_stocks函数
            from app import filter_td_sequential_stocks
            
            # 执行九转序列筛选
            filtered_stocks = filter_td_sequential_stocks()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"九转序列筛选完成，找到 {len(filtered_stocks)} 只符合条件的股票，耗时 {duration:.2f} 秒")
            
            # 可以在这里添加更多处理逻辑，比如发送通知等
            
        except Exception as e:
            logger.error(f"九转序列筛选任务失败: {e}")
    
    def limit_up_filter_job(self):
        """打板股票筛选任务"""
        try:
            logger.info("开始执行打板股票筛选任务")
            start_time = datetime.now()
            
            # 导入filter_limit_up_stocks函数
            from app import filter_limit_up_stocks
            
            # 执行打板股票筛选
            filtered_stocks = filter_limit_up_stocks()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"打板股票筛选完成，找到 {len(filtered_stocks)} 只涨停且成交额大于10亿的股票，耗时 {duration:.2f} 秒")
            
            # 可以在这里添加更多处理逻辑，比如发送通知等
            
        except Exception as e:
            logger.error(f"打板股票筛选任务失败: {e}")
    
    def start_scheduler(self):
        """启动定时任务"""
        if self.is_running:
            logger.warning("定时任务已在运行中")
            return
        
        # 设置工作日晚上18:00执行交易数据同步（周一到周五）
        schedule.every().monday.at("18:00").do(self.daily_sync_job)
        schedule.every().tuesday.at("18:00").do(self.daily_sync_job)
        schedule.every().wednesday.at("18:00").do(self.daily_sync_job)
        schedule.every().thursday.at("18:00").do(self.daily_sync_job)
        schedule.every().friday.at("18:00").do(self.daily_sync_job)
        
        # 设置工作日晚上21:00执行九转序列筛选（周一到周五）
        schedule.every().monday.at("19:00").do(self.td_sequential_filter_job)
        schedule.every().tuesday.at("19:00").do(self.td_sequential_filter_job)
        schedule.every().wednesday.at("19:00").do(self.td_sequential_filter_job)
        schedule.every().thursday.at("19:00").do(self.td_sequential_filter_job)
        schedule.every().friday.at("19:00").do(self.td_sequential_filter_job)
        
        # 设置工作日下午17:00执行打板股票筛选（周一到周五）
        schedule.every().monday.at("17:00").do(self.limit_up_filter_job)
        schedule.every().tuesday.at("17:00").do(self.limit_up_filter_job)
        schedule.every().wednesday.at("17:00").do(self.limit_up_filter_job)
        schedule.every().thursday.at("17:00").do(self.limit_up_filter_job)
        schedule.every().friday.at("17:00").do(self.limit_up_filter_job)
        
        self.is_running = True
        logger.info("定时任务已启动")
        logger.info("任务计划:")
        logger.info("- 工作日 17:00: 打板股票筛选（周一至周五）")
        logger.info("- 工作日 18:00: 交易数据同步（周一至周五）")
        logger.info("- 工作日 19:00: 九转序列筛选（周一至周五）")
        logger.info("- 周六周日为非交易时间，不执行任务")
        
        # 在后台线程中运行定时任务
        def run_scheduler():
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # 每分钟检查一次
                except Exception as e:
                    logger.error(f"定时任务执行出错: {e}")
                    time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def stop_scheduler(self):
        """停止定时任务"""
        self.is_running = False
        schedule.clear()
        logger.info("定时任务已停止")
    
    def get_next_run_time(self):
        """获取下次运行时间"""
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        
        next_run = min(job.next_run for job in jobs)
        return next_run
    
    def manual_sync(self):
        """手动触发同步"""
        logger.info("手动触发数据同步")
        return self.daily_sync_job()

# 全局调度器实例
_scheduler_instance = None

def start_scheduler():
    """启动全局定时任务"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = StockScheduler()
    
    return _scheduler_instance.start_scheduler()

def stop_scheduler():
    """停止全局定时任务"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop_scheduler()

def get_scheduler():
    """获取调度器实例"""
    global _scheduler_instance
    return _scheduler_instance

def manual_sync():
    """手动同步"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = StockScheduler()
    
    return _scheduler_instance.manual_sync()

if __name__ == '__main__':
    # 测试定时任务
    scheduler = StockScheduler()
    
    # 启动定时任务
    thread = scheduler.start_scheduler()
    
    try:
        # 保持程序运行
        while True:
            next_run = scheduler.get_next_run_time()
            if next_run:
                logger.info(f"下次运行时间: {next_run}")
            time.sleep(300)  # 每5分钟输出一次状态
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止定时任务...")
        scheduler.stop_scheduler()
        logger.info("定时任务已停止")