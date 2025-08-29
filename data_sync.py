import tushare as ts
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataSync:
    def __init__(self):
        # 设置Tushare token
        self.token = '68a7f380e45182b216eb63a9666c277ee96e68e3754476976adc5019'
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        self.db_path = 'stock_data.db'
        
        # API调用频率控制
        self.last_api_call_time = 0
        self.rate_limited = False  # 是否遇到频率限制
        self.api_call_interval = 30  # 遇到频率限制时的等待间隔
        self.max_retries = 3  # 最大重试次数
    
    def get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        return conn
    
    def _api_call_with_retry(self, api_func, *args, **kwargs):
        """带重试机制的API调用包装函数"""
        for attempt in range(self.max_retries):
            try:
                # 只有在遇到频率限制时才进行时间控制
                if self.rate_limited:
                    current_time = time.time()
                    time_since_last_call = current_time - self.last_api_call_time
                    
                    if time_since_last_call < self.api_call_interval:
                        sleep_time = self.api_call_interval - time_since_last_call
                        logger.info(f"API调用频率控制，等待 {sleep_time:.1f} 秒...")
                        time.sleep(sleep_time)
                
                # 执行API调用
                result = api_func(*args, **kwargs)
                self.last_api_call_time = time.time()
                
                # 成功调用后，重置频率限制标志
                if self.rate_limited:
                    logger.info("API调用成功，解除频率限制")
                    self.rate_limited = False
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                if "每分钟最多访问该接口" in error_msg or "访问频率" in error_msg or "抱歉，您每分钟最多访问" in error_msg:
                    # 频率限制错误，启用频率控制
                    self.rate_limited = True
                    wait_time = 60 * (attempt + 1)  # 递增等待时间
                    logger.warning(f"检测到API频率限制告警，启用时间限制控制，第{attempt+1}次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                else:
                    # 其他错误，记录并重试
                    logger.error(f"API调用失败 (第{attempt+1}次尝试): {error_msg}")
                    if attempt < self.max_retries - 1:
                        time.sleep(5 * (attempt + 1))  # 递增等待时间
                        continue
                    else:
                        raise e
        
        raise Exception(f"API调用失败，已重试 {self.max_retries} 次")
    
    def check_data_integrity(self, sync_dates, expected_counts):
        """检查数据完整性"""
        try:
            conn = self.get_db_connection()
            integrity_report = {
                'is_complete': True,
                'missing_dates': [],
                'incomplete_data': [],
                'total_expected': sum(expected_counts.values()),
                'total_actual': 0,
                'details': {}
            }
            
            for sync_date in sync_dates:
                date_report = {
                    'date': sync_date,
                    'expected': expected_counts.get(sync_date, 0),
                    'actual': 0,
                    'tables': {}
                }
                
                # 检查各个数据表的记录数
                tables_to_check = [
                    ('daily_data', '日线数据'),
                    ('stock_basic_data', '基础信息'),
                    ('margin_data', '融资融券'),
                    ('moneyflow_data', '资金流向'),
                    ('top_list_data', '龙虎榜明细'),
                    ('top_inst_data', '龙虎榜机构'),
                    ('daily_basic_data', '基础指标')
                ]
                
                total_actual_for_date = 0
                for table_name, table_desc in tables_to_check:
                    try:
                        count = conn.execute(
                            f'SELECT COUNT(*) as count FROM {table_name} WHERE trade_date = ?',
                            (sync_date,)
                        ).fetchone()['count']
                        
                        date_report['tables'][table_name] = {
                            'name': table_desc,
                            'count': count
                        }
                        total_actual_for_date += count
                        
                    except Exception as e:
                        logger.error(f"检查表 {table_name} 失败: {e}")
                        date_report['tables'][table_name] = {
                            'name': table_desc,
                            'count': 0,
                            'error': str(e)
                        }
                
                date_report['actual'] = total_actual_for_date
                integrity_report['total_actual'] += total_actual_for_date
                integrity_report['details'][sync_date] = date_report
                
                # 检查是否有缺失数据
                if total_actual_for_date == 0:
                    integrity_report['missing_dates'].append(sync_date)
                    integrity_report['is_complete'] = False
                elif total_actual_for_date < expected_counts.get(sync_date, 0) * 0.8:  # 如果实际数据少于预期的80%
                    integrity_report['incomplete_data'].append({
                        'date': sync_date,
                        'expected': expected_counts.get(sync_date, 0),
                        'actual': total_actual_for_date,
                        'completion_rate': round(total_actual_for_date / expected_counts.get(sync_date, 1) * 100, 2)
                    })
                    integrity_report['is_complete'] = False
            
            conn.close()
            
            # 计算总体完成率
            if integrity_report['total_expected'] > 0:
                integrity_report['completion_rate'] = round(
                    integrity_report['total_actual'] / integrity_report['total_expected'] * 100, 2
                )
            else:
                integrity_report['completion_rate'] = 100.0
            
            logger.info(f"数据完整性检查完成，完成率: {integrity_report['completion_rate']}%")
            return integrity_report
            
        except Exception as e:
            logger.error(f"数据完整性检查失败: {e}")
            return {
                'is_complete': False,
                'error': str(e),
                'completion_rate': 0.0
            }
    
    def get_stock_list(self):
        """获取A股股票列表"""
        try:
            # 使用带重试机制的API调用
            stock_basic = self._api_call_with_retry(
                self.pro.stock_basic,
                exchange='', 
                list_status='L', 
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            logger.info(f"获取到 {len(stock_basic)} 只股票")
            return stock_basic['ts_code'].tolist()
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_daily_data(self, ts_code, start_date=None, end_date=None):
        """获取单个股票的日线数据"""
        try:
            # 如果没有指定日期，获取最近30天的数据
            if not start_date:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            # 使用带重试机制的API调用
            df = self._api_call_with_retry(
                self.pro.daily,
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"股票 {ts_code} 在 {start_date} 到 {end_date} 期间无数据")
                return pd.DataFrame()
            
            logger.info(f"获取股票 {ts_code} 数据 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {ts_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def save_daily_data(self, df):
        """保存日线数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO daily_data 
                        (ts_code, trade_date, open, high, low, close, pre_close, 
                         change, pct_chg, vol, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['ts_code'], row['trade_date'], row['open'], row['high'],
                        row['low'], row['close'], row['pre_close'], row['change'],
                        row['pct_chg'], row['vol'], row['amount']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")
            return 0
    
    def get_last_trade_date(self, ts_code):
        """获取股票在数据库中的最后交易日期"""
        try:
            conn = self.get_db_connection()
            result = conn.execute(
                'SELECT MAX(trade_date) as last_date FROM daily_data WHERE ts_code = ?',
                (ts_code,)
            ).fetchone()
            conn.close()
            
            return result[0] if result[0] else None
        except Exception as e:
            logger.error(f"获取最后交易日期失败: {e}")
            return None
    
    def sync_stock_data(self, ts_code, days=None):
        """同步单个股票数据"""
        try:
            # 获取最后交易日期
            last_date = self.get_last_trade_date(ts_code)
            
            if last_date:
                # 从最后交易日期的下一天开始同步
                start_date = (datetime.strptime(last_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
                end_date = datetime.now().strftime('%Y%m%d')
            else:
                # 如果没有历史数据，同步最近指定天数的数据
                if days:
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                else:
                    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')  # 默认一年
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 如果开始日期大于等于结束日期，说明数据已是最新
            if start_date >= end_date:
                logger.info(f"股票 {ts_code} 数据已是最新")
                return 0
            
            # 获取数据
            df = self.get_daily_data(ts_code, start_date, end_date)
            
            # 保存数据
            return self.save_daily_data(df)
            
        except Exception as e:
            logger.error(f"同步股票 {ts_code} 数据失败: {e}")
            return 0
    
    def sync_all_stocks(self, days=None):
        """同步所有股票数据"""
        logger.info("开始同步所有股票数据")
        
        # 获取股票列表
        stock_list = self.get_stock_list()
        
        if not stock_list:
            logger.error("获取股票列表失败")
            return {'total': 0, 'success': 0, 'failed': 0}
        
        total_count = 0
        success_count = 0
        failed_count = 0
        
        for i, ts_code in enumerate(stock_list):
            try:
                logger.info(f"正在同步 {ts_code} ({i+1}/{len(stock_list)})")
                
                # 同步数据
                saved_count = self.sync_stock_data(ts_code, days)
                total_count += saved_count
                
                if saved_count >= 0:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 避免API调用过于频繁，每次调用后休息0.1秒
                time.sleep(0.1)
                
                # 每100只股票输出一次进度
                if (i + 1) % 100 == 0:
                    logger.info(f"已处理 {i+1}/{len(stock_list)} 只股票，共保存 {total_count} 条数据")
                    
            except Exception as e:
                logger.error(f"处理股票 {ts_code} 时发生错误: {e}")
                failed_count += 1
                continue
        
        result = {
            'total': total_count,
            'success': success_count,
            'failed': failed_count,
            'stocks_processed': len(stock_list)
        }
        
        logger.info(f"同步完成: {result}")
        return result
    
    def get_latest_trade_date(self):
        """获取最近的交易日期"""
        try:
            # 从当前日期开始，往前查找最近的交易日
            current_date = datetime.now()
            for i in range(10):  # 最多查找10天
                check_date = (current_date - timedelta(days=i)).strftime('%Y%m%d')
                
                # 检查该日期是否有交易数据
                df = self._api_call_with_retry(self.pro.daily, trade_date=check_date)
                if not df.empty:
                    logger.info(f"找到最近交易日: {check_date}")
                    return check_date
            
            # 如果都没有找到，返回当前日期
            logger.warning("未找到最近交易日，使用当前日期")
            return datetime.now().strftime('%Y%m%d')
            
        except Exception as e:
            logger.error(f"获取最近交易日失败: {e}")
            return datetime.now().strftime('%Y%m%d')
    
    def sync_by_date(self, trade_date):
        """按交易日期同步所有股票数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的所有股票数据")
            
            # 获取指定日期的所有股票数据
            df = self._api_call_with_retry(self.pro.daily, trade_date=trade_date)
            
            if df.empty:
                logger.warning(f"日期 {trade_date} 无交易数据，尝试查找最近交易日")
                # 如果指定日期无数据，尝试获取最近的交易日
                latest_trade_date = self.get_latest_trade_date()
                if latest_trade_date != trade_date:
                    logger.info(f"使用最近交易日 {latest_trade_date} 进行同步")
                    df = self._api_call_with_retry(self.pro.daily, trade_date=latest_trade_date)
                
                if df.empty:
                    logger.warning(f"最近交易日 {latest_trade_date} 也无交易数据")
                    return 0
            
            # 保存数据
            saved_count = self.save_daily_data(df)
            logger.info(f"日期 {trade_date} 同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 数据失败: {e}")
            return 0
    
    def get_stock_basic_data(self, trade_date):
        """获取指定交易日的股票基础信息"""
        try:
            # 使用带重试机制的API调用
            df = self._api_call_with_retry(
                self.pro.bak_basic,
                trade_date=trade_date,
                fields='trade_date,ts_code,name,industry,area,pe,float_share,total_share,total_assets,liquid_assets,fixed_assets,reserved,reserved_pershare,eps,bvps,pb,list_date,undp,per_undp,rev_yoy,profit_yoy,gpr,npr,holder_num'
            )
            
            if df.empty:
                logger.warning(f"日期 {trade_date} 无股票基础信息")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条股票基础信息")
            return df
            
        except Exception as e:
            logger.error(f"获取股票基础信息失败: {e}")
            return pd.DataFrame()
    
    def get_daily_basic_data(self, trade_date):
        """获取指定交易日的每日基础指标数据（包含换手率等）"""
        try:
            # 使用带重试机制的API调用
            df = self._api_call_with_retry(
                self.pro.daily_basic,
                trade_date=trade_date,
                fields='trade_date,ts_code,close,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
            )
            
            if df.empty:
                logger.warning(f"日期 {trade_date} 无每日基础指标数据")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条每日基础指标数据")
            return df
            
        except Exception as e:
            logger.error(f"获取每日基础指标数据失败: {e}")
            return pd.DataFrame()
    
    def save_stock_basic_data(self, df):
        """保存股票基础信息到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO stock_basic 
                        (trade_date, ts_code, name, industry, area, pe, float_share, 
                         total_share, total_assets, liquid_assets, fixed_assets, 
                         reserved, reserved_pershare, eps, bvps, pb, list_date, 
                         undp, per_undp, rev_yoy, profit_yoy, gpr, npr, holder_num)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['trade_date'], row['ts_code'], row['name'], row['industry'],
                        row['area'], row['pe'], row['float_share'], row['total_share'],
                        row['total_assets'], row['liquid_assets'], row['fixed_assets'],
                        row['reserved'], row['reserved_pershare'], row['eps'], row['bvps'],
                        row['pb'], row['list_date'], row['undp'], row['per_undp'],
                        row['rev_yoy'], row['profit_yoy'], row['gpr'], row['npr'], row['holder_num']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存股票基础信息失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条股票基础信息")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存股票基础信息到数据库失败: {e}")
            return 0
    
    def save_daily_basic_data(self, df):
        """保存每日基础指标数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 创建daily_basic表（如果不存在）
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_basic (
                    trade_date TEXT,
                    ts_code TEXT,
                    close REAL,
                    turnover_rate REAL,
                    volume_ratio REAL,
                    pe REAL,
                    pe_ttm REAL,
                    pb REAL,
                    ps REAL,
                    ps_ttm REAL,
                    dv_ratio REAL,
                    dv_ttm REAL,
                    total_share REAL,
                    float_share REAL,
                    free_share REAL,
                    total_mv REAL,
                    circ_mv REAL,
                    PRIMARY KEY (trade_date, ts_code)
                )
            ''')
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO daily_basic 
                        (trade_date, ts_code, close, turnover_rate, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share, float_share, free_share, total_mv, circ_mv)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['trade_date'], row['ts_code'], row['close'], row['turnover_rate'],
                        row['volume_ratio'], row['pe'], row['pe_ttm'], row['pb'], row['ps'],
                        row['ps_ttm'], row['dv_ratio'], row['dv_ttm'], row['total_share'],
                        row['float_share'], row['free_share'], row['total_mv'], row['circ_mv']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存每日基础指标数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条每日基础指标数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存每日基础指标数据到数据库失败: {e}")
            return 0
    
    def sync_daily_basic_by_date(self, trade_date):
        """按交易日期同步每日基础指标数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的每日基础指标数据")
            
            # 获取每日基础指标数据
            df = self.get_daily_basic_data(trade_date)
            
            # 保存数据
            saved_count = self.save_daily_basic_data(df)
            logger.info(f"日期 {trade_date} 每日基础指标数据同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 每日基础指标数据失败: {e}")
            return 0
    
    def sync_stock_basic_by_date(self, trade_date):
        """按交易日期同步股票基础信息"""
        try:
            logger.info(f"开始同步 {trade_date} 的股票基础信息")
            
            # 获取股票基础信息
            df = self.get_stock_basic_data(trade_date)
            
            # 保存数据
            saved_count = self.save_stock_basic_data(df)
            logger.info(f"日期 {trade_date} 股票基础信息同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 股票基础信息失败: {e}")
            return 0
    
    def get_margin_data(self, trade_date=None, start_date=None, end_date=None, exchange_id=None):
        """获取融资融券交易汇总数据"""
        try:
            # 调用Tushare margin接口获取融资融券数据
            params = {}
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if exchange_id:
                params['exchange_id'] = exchange_id
            
            df = self._api_call_with_retry(self.pro.margin, **params)
            
            if df.empty:
                logger.warning(f"融资融券数据查询无结果")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条融资融券数据")
            return df
            
        except Exception as e:
            logger.error(f"获取融资融券数据失败: {e}")
            return pd.DataFrame()
    
    def save_margin_data(self, df):
        """保存融资融券数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO margin_data 
                        (trade_date, exchange_id, rzye, rzmre, rzche, rqye, rqmcl, rzrqye, rqyl)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['trade_date'], row['exchange_id'], row['rzye'], row['rzmre'],
                        row['rzche'], row['rqye'], row['rqmcl'], row['rzrqye'], row['rqyl']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存融资融券数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条融资融券数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存融资融券数据到数据库失败: {e}")
            return 0
    
    def sync_margin_by_date(self, trade_date):
        """按交易日期同步融资融券数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的融资融券数据")
            
            # 获取融资融券数据
            df = self.get_margin_data(trade_date=trade_date)
            
            # 保存数据
            saved_count = self.save_margin_data(df)
            logger.info(f"日期 {trade_date} 融资融券数据同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 融资融券数据失败: {e}")
            return 0
    
    def get_moneyflow_data(self, ts_code=None, trade_date=None, start_date=None, end_date=None):
        """获取个股资金流向数据"""
        try:
            # 调用Tushare moneyflow接口获取个股资金流向数据
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if trade_date:
                params['trade_date'] = trade_date
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            df = self._api_call_with_retry(self.pro.moneyflow, **params)
            
            if df.empty:
                logger.warning(f"个股资金流向数据查询无结果")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条个股资金流向数据")
            return df
            
        except Exception as e:
            logger.error(f"获取个股资金流向数据失败: {e}")
            return pd.DataFrame()
    
    def save_moneyflow_data(self, df):
        """保存个股资金流向数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO moneyflow_data 
                        (ts_code, trade_date, buy_sm_vol, buy_sm_amount, sell_sm_vol, sell_sm_amount,
                         buy_md_vol, buy_md_amount, sell_md_vol, sell_md_amount, buy_lg_vol, buy_lg_amount,
                         sell_lg_vol, sell_lg_amount, buy_elg_vol, buy_elg_amount, sell_elg_vol, sell_elg_amount,
                         net_mf_vol, net_mf_amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['ts_code'], row['trade_date'], row['buy_sm_vol'], row['buy_sm_amount'],
                        row['sell_sm_vol'], row['sell_sm_amount'], row['buy_md_vol'], row['buy_md_amount'],
                        row['sell_md_vol'], row['sell_md_amount'], row['buy_lg_vol'], row['buy_lg_amount'],
                        row['sell_lg_vol'], row['sell_lg_amount'], row['buy_elg_vol'], row['buy_elg_amount'],
                        row['sell_elg_vol'], row['sell_elg_amount'], row['net_mf_vol'], row['net_mf_amount']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存个股资金流向数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条个股资金流向数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存个股资金流向数据到数据库失败: {e}")
            return 0
    
    def sync_moneyflow_by_date(self, trade_date):
        """按交易日期同步个股资金流向数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的个股资金流向数据")
            
            # 获取个股资金流向数据
            df = self.get_moneyflow_data(trade_date=trade_date)
            
            # 保存数据
            saved_count = self.save_moneyflow_data(df)
            logger.info(f"日期 {trade_date} 个股资金流向数据同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 个股资金流向数据失败: {e}")
            return 0
    
    def get_top_list_data(self, trade_date, ts_code=None):
        """获取龙虎榜每日明细数据"""
        try:
            params = {'trade_date': trade_date}
            if ts_code:
                params['ts_code'] = ts_code
                
            df = self._api_call_with_retry(self.pro.top_list, **params)
            
            if df.empty:
                logger.warning(f"龙虎榜每日明细数据查询无结果")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条龙虎榜每日明细数据")
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜每日明细数据失败: {e}")
            return pd.DataFrame()
    
    def save_top_list_data(self, df):
        """保存龙虎榜每日明细数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO top_list_data 
                        (trade_date, ts_code, name, close, pct_change, turnover_rate, amount, 
                         l_sell, l_buy, l_amount, net_amount, net_rate, amount_rate, 
                         float_values, reason)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['trade_date'], row['ts_code'], row['name'], row['close'],
                        row['pct_change'], row['turnover_rate'], row['amount'], row['l_sell'],
                        row['l_buy'], row['l_amount'], row['net_amount'], row['net_rate'],
                        row['amount_rate'], row['float_values'], row['reason']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存龙虎榜每日明细数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条龙虎榜每日明细数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存龙虎榜每日明细数据到数据库失败: {e}")
            return 0
    
    def sync_top_list_by_date(self, trade_date, ts_code=None):
        """按交易日期同步龙虎榜每日明细数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的龙虎榜每日明细数据")
            
            # 获取龙虎榜每日明细数据
            df = self.get_top_list_data(trade_date, ts_code)
            
            # 保存数据
            saved_count = self.save_top_list_data(df)
            logger.info(f"日期 {trade_date} 龙虎榜每日明细数据同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 龙虎榜每日明细数据失败: {e}")
            return 0
    
    def get_top_inst_data(self, trade_date, ts_code=None):
        """获取龙虎榜机构明细数据"""
        try:
            params = {'trade_date': trade_date}
            if ts_code:
                params['ts_code'] = ts_code
                
            df = self._api_call_with_retry(self.pro.top_inst, **params)
            
            if df.empty:
                logger.warning(f"龙虎榜机构明细数据查询无结果")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条龙虎榜机构明细数据")
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜机构明细数据失败: {e}")
            return pd.DataFrame()
    
    def save_top_inst_data(self, df):
        """保存龙虎榜机构明细数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    # 处理NaN值，转换为None
                    buy = row['buy'] if pd.notna(row['buy']) else None
                    buy_rate = row['buy_rate'] if pd.notna(row['buy_rate']) else None
                    sell = row['sell'] if pd.notna(row['sell']) else None
                    sell_rate = row['sell_rate'] if pd.notna(row['sell_rate']) else None
                    net_buy = row['net_buy'] if pd.notna(row['net_buy']) else None
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO top_inst_data 
                        (trade_date, ts_code, exalter, buy, buy_rate, sell, sell_rate, net_buy, side, reason)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['trade_date'], row['ts_code'], row['exalter'], buy, buy_rate,
                        sell, sell_rate, net_buy, row['side'], row['reason']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存龙虎榜机构明细数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条龙虎榜机构明细数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存龙虎榜机构明细数据到数据库失败: {e}")
            return 0
    
    def sync_top_inst_by_date(self, trade_date, ts_code=None):
        """按交易日期同步龙虎榜机构明细数据"""
        try:
            logger.info(f"开始同步 {trade_date} 的龙虎榜机构明细数据")
            
            # 获取龙虎榜机构明细数据
            df = self.get_top_inst_data(trade_date, ts_code)
            
            # 保存数据
            saved_count = self.save_top_inst_data(df)
            logger.info(f"日期 {trade_date} 龙虎榜机构明细数据同步完成，共保存 {saved_count} 条数据")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"同步日期 {trade_date} 龙虎榜机构明细数据失败: {e}")
            return 0
    
    def get_index_daily_data(self, ts_code=None, start_date=None, end_date=None):
        """获取指数日线行情数据"""
        try:
            params = {}
            if ts_code:
                params['ts_code'] = ts_code
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            df = self._api_call_with_retry(self.pro.index_daily, **params)
            
            if df.empty:
                logger.warning(f"指数日线行情数据查询无结果")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条指数日线行情数据")
            return df
            
        except Exception as e:
            logger.error(f"获取指数日线行情数据失败: {e}")
            return pd.DataFrame()
    
    def save_index_daily_data(self, df):
        """保存指数日线行情数据到数据库"""
        if df.empty:
            return 0
        
        try:
            conn = self.get_db_connection()
            
            # 使用INSERT OR REPLACE避免重复数据
            saved_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO index_daily_data 
                        (ts_code, trade_date, close, open, high, low, pre_close, change, pct_chg, vol, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('ts_code'),
                        row.get('trade_date'),
                        row.get('close'),
                        row.get('open'),
                        row.get('high'),
                        row.get('low'),
                        row.get('pre_close'),
                        row.get('change'),
                        row.get('pct_chg'),
                        row.get('vol'),
                        row.get('amount')
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存指数日线行情数据失败: {e}, 数据: {row.to_dict()}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {saved_count} 条指数日线行情数据")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存指数日线行情数据到数据库失败: {e}")
            return 0
    
    def sync_index_daily_data(self, ts_code=None, start_date=None, end_date=None):
        """同步指数日线行情数据"""
        try:
            if start_date is None:
                start_date = '20100101'  # 默认从2010年开始
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            
            # 如果没有指定ts_code，使用默认的主要指数列表
            if ts_code is None:
                default_indices = [
                    '000001.SH',  # 上证指数
                    '399001.SZ',  # 深证成指
                    '000300.SH',  # 沪深300
                    '399006.SZ',  # 创业板指
                    '000688.SH',  # 科创50
                    '000905.SH',  # 中证500
                ]
                ts_codes = default_indices
            else:
                ts_codes = [ts_code] if isinstance(ts_code, str) else ts_code
            
            logger.info(f"开始同步指数日线行情数据: {start_date} - {end_date}, 指数代码: {ts_codes}")
            
            total_saved = 0
            for code in ts_codes:
                try:
                    # 获取指数日线行情数据
                    df = self.get_index_daily_data(ts_code=code, start_date=start_date, end_date=end_date)
                    
                    # 保存数据
                    saved_count = self.save_index_daily_data(df)
                    total_saved += saved_count
                    logger.info(f"指数 {code} 数据同步完成，保存 {saved_count} 条数据")
                    
                    # 避免频率限制
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"同步指数 {code} 数据失败: {e}")
                    continue
            
            logger.info(f"指数日线行情数据同步完成，共保存 {total_saved} 条数据")
            return total_saved
            
        except Exception as e:
            logger.error(f"同步指数日线行情数据失败: {e}")
            return 0
    

    

    def generate_unified_analysis_data(self, trade_date=None):
        """生成统一分析表数据"""
        try:
            conn = self.get_db_connection()
            
            # 如果没有指定日期，使用最新交易日期
            if not trade_date:
                latest_date_result = conn.execute(
                    'SELECT MAX(trade_date) as max_date FROM daily_data'
                ).fetchone()
                if not latest_date_result or not latest_date_result[0]:
                    logger.warning("没有找到交易数据")
                    return {'success': False, 'message': '没有找到交易数据'}
                trade_date = latest_date_result[0]
            
            logger.info(f"开始生成 {trade_date} 的统一分析表数据")
            
            # 清除指定日期的旧数据
            conn.execute('DELETE FROM unified_analysis_data WHERE trade_date = ?', (trade_date,))
            
            total_inserted = 0
            
            # 1. 插入股票日线数据 + 基础信息 + 计算字段
            stock_query = '''
                INSERT OR REPLACE INTO unified_analysis_data 
                (ts_code, trade_date, data_type, name, close, open, high, low, pre_close, 
                 change, pct_chg, vol, amount, industry, area, pe, pb, eps, bvps, volume_ratio, total_mv)
                SELECT 
                    d.ts_code, d.trade_date, 'stock' as data_type, b.name,
                    d.close, d.open, d.high, d.low, d.pre_close, d.change, d.pct_chg, d.vol, d.amount,
                    b.industry, b.area, b.pe, b.pb, b.eps, b.bvps,
                    -- 计算量比：当日成交量 / 前5日平均成交量
                    CASE 
                        WHEN (
                            SELECT AVG(vol) 
                            FROM daily_data d2 
                            WHERE d2.ts_code = d.ts_code 
                            AND d2.trade_date < d.trade_date 
                            AND d2.trade_date >= (
                                SELECT MIN(trade_date) 
                                FROM (
                                    SELECT trade_date 
                                    FROM daily_data d3 
                                    WHERE d3.ts_code = d.ts_code 
                                    AND d3.trade_date < d.trade_date 
                                    ORDER BY trade_date DESC 
                                    LIMIT 5
                                )
                            )
                        ) > 0 
                        THEN d.vol / (
                            SELECT AVG(vol) 
                            FROM daily_data d2 
                            WHERE d2.ts_code = d.ts_code 
                            AND d2.trade_date < d.trade_date 
                            AND d2.trade_date >= (
                                SELECT MIN(trade_date) 
                                FROM (
                                    SELECT trade_date 
                                    FROM daily_data d3 
                                    WHERE d3.ts_code = d.ts_code 
                                    AND d3.trade_date < d.trade_date 
                                    ORDER BY trade_date DESC 
                                    LIMIT 5
                                )
                            )
                        )
                        ELSE NULL 
                    END as volume_ratio,
                    -- 从daily_basic表获取总市值（万元）
                    db.total_mv
                FROM daily_data d
                LEFT JOIN stock_basic b ON d.ts_code = b.ts_code AND d.trade_date = b.trade_date
                LEFT JOIN daily_basic db ON d.ts_code = db.ts_code AND d.trade_date = db.trade_date
                WHERE d.trade_date = ?
            '''
            cursor = conn.execute(stock_query, (trade_date,))
            stock_count = cursor.rowcount
            total_inserted += stock_count
            logger.info(f"插入股票数据: {stock_count} 条")
            
            # 2. 插入指数数据
            index_query = '''
                INSERT OR REPLACE INTO unified_analysis_data 
                (ts_code, trade_date, data_type, name, close, open, high, low, pre_close, 
                 change, pct_chg, vol, amount)
                SELECT 
                    ts_code, trade_date, 'index' as data_type, ts_code as name,
                    close, open, high, low, pre_close, change, pct_chg, vol, amount
                FROM index_daily_data
                WHERE trade_date = ?
            '''
            cursor = conn.execute(index_query, (trade_date,))
            index_count = cursor.rowcount
            total_inserted += index_count
            logger.info(f"插入指数数据: {index_count} 条")
            

            
            # 4. 更新资金流向数据
            moneyflow_query = '''
                UPDATE unified_analysis_data 
                SET net_mf_amount = (
                    SELECT m.net_mf_amount 
                    FROM moneyflow_data m 
                    WHERE m.ts_code = unified_analysis_data.ts_code 
                    AND m.trade_date = unified_analysis_data.trade_date
                ),
                buy_lg_amount = (
                    SELECT m.buy_lg_amount 
                    FROM moneyflow_data m 
                    WHERE m.ts_code = unified_analysis_data.ts_code 
                    AND m.trade_date = unified_analysis_data.trade_date
                ),
                sell_lg_amount = (
                    SELECT m.sell_lg_amount 
                    FROM moneyflow_data m 
                    WHERE m.ts_code = unified_analysis_data.ts_code 
                    AND m.trade_date = unified_analysis_data.trade_date
                )
                WHERE trade_date = ? AND data_type = 'stock'
                AND EXISTS (
                    SELECT 1 FROM moneyflow_data m 
                    WHERE m.ts_code = unified_analysis_data.ts_code 
                    AND m.trade_date = unified_analysis_data.trade_date
                )
            '''
            cursor = conn.execute(moneyflow_query, (trade_date,))
            moneyflow_count = cursor.rowcount
            logger.info(f"更新资金流向数据: {moneyflow_count} 条")
            
            # 5. 更新龙虎榜数据
            toplist_query = '''
                UPDATE unified_analysis_data 
                SET net_amount = (
                    SELECT t.net_amount 
                    FROM top_list_data t 
                    WHERE t.ts_code = unified_analysis_data.ts_code 
                    AND t.trade_date = unified_analysis_data.trade_date
                ),
                turnover_rate = (
                    SELECT t.turnover_rate 
                    FROM top_list_data t 
                    WHERE t.ts_code = unified_analysis_data.ts_code 
                    AND t.trade_date = unified_analysis_data.trade_date
                ),
                reason = (
                    SELECT t.reason 
                    FROM top_list_data t 
                    WHERE t.ts_code = unified_analysis_data.ts_code 
                    AND t.trade_date = unified_analysis_data.trade_date
                )
                WHERE trade_date = ? AND data_type = 'stock'
                AND EXISTS (
                    SELECT 1 FROM top_list_data t 
                    WHERE t.ts_code = unified_analysis_data.ts_code 
                    AND t.trade_date = unified_analysis_data.trade_date
                )
            '''
            cursor = conn.execute(toplist_query, (trade_date,))
            toplist_count = cursor.rowcount
            logger.info(f"更新龙虎榜数据: {toplist_count} 条")
            
            # 6. 插入融资融券汇总数据（按交易所）
            margin_query = '''
                INSERT OR REPLACE INTO unified_analysis_data 
                (ts_code, trade_date, data_type, name, rzye, rzmre, rzrqye)
                SELECT 
                    exchange_id as ts_code, trade_date, 'margin' as data_type, 
                    exchange_id as name, rzye, rzmre, rzrqye
                FROM margin_data
                WHERE trade_date = ?
            '''
            cursor = conn.execute(margin_query, (trade_date,))
            margin_count = cursor.rowcount
            total_inserted += margin_count
            logger.info(f"插入融资融券数据: {margin_count} 条")
            
            # 更新时间戳
            conn.execute(
                'UPDATE unified_analysis_data SET updated_at = CURRENT_TIMESTAMP WHERE trade_date = ?', 
                (trade_date,)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"统一分析表生成完成，共处理 {total_inserted} 条数据")
            return {
                'success': True, 
                'message': f'统一分析表生成完成', 
                'trade_date': trade_date,
                'total_records': total_inserted,
                'details': {
                    'stock_count': stock_count,
                    'index_count': index_count,
                    'moneyflow_count': moneyflow_count,
                    'toplist_count': toplist_count,
                    'margin_count': margin_count
                }
            }
            
        except Exception as e:
            logger.error(f"生成统一分析表失败: {str(e)}")
            return {'success': False, 'message': f'生成统一分析表失败: {str(e)}'}


if __name__ == '__main__':
    # 测试数据同步
    data_sync = DataSync()
    
    # 同步单个股票数据（测试用）
    # result = data_sync.sync_stock_data('000001.SZ', days=30)
    # print(f"同步结果: {result}")
    
    # 同步所有股票数据
    result = data_sync.sync_all_stocks(days=30)
    print(f"同步结果: {result}")
    
    # 同步股票基础信息（测试用）
    # basic_result = data_sync.sync_stock_basic_by_date('20240115')
    # print(f"基础信息同步结果: {basic_result}")