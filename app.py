from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime, timedelta
import sqlite3
import os
import subprocess
import signal
import psutil
from data_sync import DataSync
from scheduler import start_scheduler
import random
import json
import time
import threading
from queue import Queue

# 技术指标计算函数
def calculate_rsi(closes, period=14):
    """计算RSI指标"""
    rsi = []
    for i in range(len(closes)):
        if i < period:
            rsi.append(50)
            continue
        gains = 0
        losses = 0
        for j in range(i - period + 1, i + 1):
            change = closes[j] - closes[j - 1]
            if change > 0:
                gains += change
            else:
                losses -= change
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
    return rsi

def calculate_kdj(highs, lows, closes, period=9):
    """计算KDJ指标"""
    k = []
    d = []
    j = []
    
    for i in range(len(closes)):
        start = max(0, i - period + 1)
        period_highs = highs[start:i + 1]
        period_lows = lows[start:i + 1]
        highest_high = max(period_highs)
        lowest_low = min(period_lows)
        
        if highest_high == lowest_low:
            rsv = 50
        else:
            rsv = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
        
        if i == 0:
            k.append(50)
            d.append(50)
        else:
            k_val = (2/3) * k[i-1] + (1/3) * rsv
            d_val = (2/3) * d[i-1] + (1/3) * k_val
            k.append(k_val)
            d.append(d_val)
        
        j_val = 3 * k[i] - 2 * d[i]
        j.append(j_val)
    
    return {'k': k, 'd': d, 'j': j}

def calculate_td_sequential(closes):
    """计算九转序列法 - 与前端JavaScript版本保持一致"""
    if len(closes) < 5:
        return None
    
    buy_sequence = []
    sell_sequence = []
    buy_count = 0
    sell_count = 0
    
    # 为每个数据点计算九转序列
    for i in range(len(closes)):
        if i < 4:
            buy_sequence.append(None)
            sell_sequence.append(None)
            continue
        
        # 买入序列：当前收盘价 > 4天前收盘价
        if closes[i] > closes[i - 4]:
            buy_count += 1
            sell_count = 0
            buy_sequence.append(buy_count if buy_count <= 9 else None)
            sell_sequence.append(None)
        # 卖出序列：当前收盘价 < 4天前收盘价
        elif closes[i] < closes[i - 4]:
            sell_count += 1
            buy_count = 0
            sell_sequence.append(sell_count if sell_count <= 9 else None)
            buy_sequence.append(None)
        # 既不满足买入也不满足卖出条件
        else:
            buy_count = 0
            sell_count = 0
            buy_sequence.append(None)
            sell_sequence.append(None)
    
    # 返回最后一个数据点的九转序列状态
    last_buy = buy_sequence[-1] if buy_sequence else None
    last_sell = sell_sequence[-1] if sell_sequence else None
    
    if last_buy is not None:
        return last_buy
    elif last_sell is not None:
        return -last_sell  # 负数表示卖出序列
    else:
        return None


def filter_td_sequential_stocks():
    """筛选九转数值大于红2的股票"""
    conn = get_db_connection()
    
    # 获取最新交易日期
    latest_date = conn.execute(
        'SELECT MAX(trade_date) as max_date FROM daily_data'
    ).fetchone()['max_date']
    
    if not latest_date:
        conn.close()
        return []
    
    # 获取最新交易日的所有股票数据，包含新增字段
    stocks = conn.execute('''
        SELECT d.ts_code, d.trade_date, d.open, d.high, d.low, d.close, d.pre_close, 
               d.change, d.pct_chg, d.vol, d.amount, 
               sb.name, sb.industry, sb.area,
               db.turnover_rate, db.volume_ratio, db.pe, db.pb, db.total_mv,
               mf.net_mf_amount
        FROM daily_data d
        LEFT JOIN stock_basic_info sb ON d.ts_code = sb.ts_code
        LEFT JOIN (
            SELECT ts_code, turnover_rate, volume_ratio, pe, pb, total_mv,
                   ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
            FROM daily_basic
        ) db ON d.ts_code = db.ts_code AND db.rn = 1
        LEFT JOIN (
            SELECT ts_code, net_mf_amount,
                   ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
            FROM moneyflow_data
        ) mf ON d.ts_code = mf.ts_code AND mf.rn = 1
        WHERE d.trade_date = ?
        ORDER BY d.pct_chg DESC
    ''', (latest_date,)).fetchall()
    
    # 筛选九转数值大于红2的股票
    filtered_stocks = []
    for stock in stocks:
        # 获取该股票最近90天的收盘价用于计算九转序列
        closes_data = conn.execute('''
            SELECT close FROM daily_data 
            WHERE ts_code = ? 
            ORDER BY trade_date DESC 
            LIMIT 90
        ''', (stock['ts_code'],)).fetchall()
        
        if len(closes_data) >= 5:
            closes = [row['close'] for row in reversed(closes_data)]
            td_sequential = calculate_td_sequential(closes)
            
            # 筛选条件：九转数值大于红2（即大于2的正数）
            if td_sequential is not None and td_sequential > 2:
                stock_dict = dict(stock)
                stock_dict['td_sequential'] = td_sequential
                filtered_stocks.append(stock_dict)
    
    conn.close()
    
    # 按九转序列值降序排序
    filtered_stocks.sort(key=lambda x: x['td_sequential'], reverse=True)
    
    return filtered_stocks

# 指数名称映射字典
INDEX_NAME_MAP = {
    '000001.SH': '上证指数',
    '399001.SZ': '深证成指',
    '399006.SZ': '创业板指',
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '399905.SZ': '中证500',
    '000016.SH': '上证50',
    '000688.SH': '科创50',
    '000009.SH': '上证380',
    '000010.SH': '上证180',
    '000015.SH': '红利指数',
    '000043.SH': '超大盘',
    '000045.SH': '基金指数',
    '000046.SH': '债券指数',
    '000047.SH': '企债指数',
    '000048.SH': '国债指数',
    '000132.SH': '上证100',
    '000133.SH': '上证150',
    '000134.SH': '上证200',
    '000135.SH': '上证380',
    '000136.SH': '上证消费',
    '000137.SH': '上证医药',
    '000138.SH': '上证能源',
    '000139.SH': '上证信息',
    '000140.SH': '上证金融',
    '000141.SH': '上证材料',
    '000142.SH': '上证工业',
    '000143.SH': '上证可选',
    '000144.SH': '上证公用',
    '000145.SH': '上证电信',
    '000146.SH': '上证地产',
    '000147.SH': '上证运输',
    '000148.SH': '上证环保',
    '000149.SH': '上证农业',
    '000150.SH': '上证银行',
    '000151.SH': '上证保险',
    '000152.SH': '上证证券',
    '000153.SH': '上证软件',
    '000154.SH': '上证传媒',
    '000155.SH': '上证汽车',
    '000156.SH': '上证机械',
    '000157.SH': '上证化工',
    '000158.SH': '上证钢铁',
    '000159.SH': '上证有色',
    '000160.SH': '上证煤炭',
    '000161.SH': '上证石油',
    '000162.SH': '上证电力',
    '000163.SH': '上证建筑',
    '000164.SH': '上证建材',
    '000165.SH': '上证家电',
    '000166.SH': '上证食品',
    '000167.SH': '上证纺织',
    '000168.SH': '上证轻工',
    '000169.SH': '上证商贸',
    '000170.SH': '上证休闲',
    '000171.SH': '上证综合',
    '000172.SH': '上证国防',
    '000173.SH': '上证计算',
    '000174.SH': '上证通信',
    '000175.SH': '上证电子',
    '000176.SH': '上证医疗',
    '000177.SH': '上证生物',
    '000178.SH': '上证农林',
    '000179.SH': '上证采掘',
    '000180.SH': '上证化学',
    '000181.SH': '上证钢铁',
    '000182.SH': '上证有色',
    '000183.SH': '上证建筑',
    '000184.SH': '上证机械',
    '000185.SH': '上证国防',
    '000186.SH': '上证汽车',
    '000187.SH': '上证家电',
    '000188.SH': '上证食品',
    '000189.SH': '上证纺织',
    '000190.SH': '上证轻工',
    '000191.SH': '上证医药',
    '000192.SH': '上证公用',
    '000193.SH': '上证交运',
    '000194.SH': '上证商贸',
    '000195.SH': '上证休闲',
    '000196.SH': '上证综合',
    '000197.SH': '上证银行',
    '000198.SH': '上证非银',
    '000199.SH': '上证地产',
    '000200.SH': '上证TMT',
    '399002.SZ': '深成指R',
    '399003.SZ': '成份B指',
    '399004.SZ': '深证100R',
    '399005.SZ': '中小板指',
    '399007.SZ': '深证300',
    '399008.SZ': '中小300',
    '399009.SZ': '深证200',
    '399010.SZ': '深证700',
    '399011.SZ': '深证1000',
    '399012.SZ': '创业300',
    '399013.SZ': '深市精选',
    '399015.SZ': '中小创新',
    '399016.SZ': '深证创新',
    '399100.SZ': '新指数',
    '399101.SZ': '中小板综',
    '399106.SZ': '深证综指',
    '399107.SZ': '深证A指',
    '399108.SZ': '深证B指',
    '399330.SZ': '深证100',
    '399333.SZ': '中小板R',
    '399606.SZ': '创业板R',
    '399678.SZ': '深次新股'
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 全局变量用于管理同步进度
sync_progress = {
    'is_syncing': False,
    'current_step': '',
    'progress': 0,
    'total_steps': 7,
    'details': [],
    'start_time': None,
    'estimated_remaining': 0
}

# 数据库配置
DATABASE_PATH = 'stock_data.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    
    # 创建日线数据表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code, trade_date)
        )
    ''')
    

    
    # 创建股票基础信息表（基于stock_basic接口）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_basic_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            area TEXT,
            industry TEXT,
            fullname TEXT,
            enname TEXT,
            cnspell TEXT,
            market TEXT,
            exchange TEXT,
            curr_type TEXT,
            list_status TEXT,
            list_date TEXT,
            delist_date TEXT,
            is_hs TEXT,
            act_name TEXT,
            act_ent_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code)
        )
    ''')
    

    
    # 创建个股资金流向表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS moneyflow_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            buy_sm_vol INTEGER,
            buy_sm_amount REAL,
            sell_sm_vol INTEGER,
            sell_sm_amount REAL,
            buy_md_vol INTEGER,
            buy_md_amount REAL,
            sell_md_vol INTEGER,
            sell_md_amount REAL,
            buy_lg_vol INTEGER,
            buy_lg_amount REAL,
            sell_lg_vol INTEGER,
            sell_lg_amount REAL,
            buy_elg_vol INTEGER,
            buy_elg_amount REAL,
            sell_elg_vol INTEGER,
            sell_elg_amount REAL,
            net_mf_vol INTEGER,
            net_mf_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code, trade_date)
        )
    ''')
    

    

    

    

    
    # 创建指数日线行情数据表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS index_daily_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            close REAL,
            open REAL,
            high REAL,
            low REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code, trade_date)
        )
    ''')
    
    # 创建每日基础指标数据表
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
    
    # 创建自选股表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorite_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            name TEXT,
            added_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code)
        )
    ''')
    
    # 创建索引提高查询性能
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ts_code ON daily_data(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_trade_date ON daily_data(trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ts_code_date ON daily_data(ts_code, trade_date)')
    

    
    # 为stock_basic_info表创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_ts_code ON stock_basic_info(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_symbol ON stock_basic_info(symbol)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_industry ON stock_basic_info(industry)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_area ON stock_basic_info(area)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_market ON stock_basic_info(market)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_list_status ON stock_basic_info(list_status)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_basic_info_exchange ON stock_basic_info(exchange)')
    

    
    conn.execute('CREATE INDEX IF NOT EXISTS idx_moneyflow_ts_code ON moneyflow_data(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_moneyflow_trade_date ON moneyflow_data(trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_moneyflow_ts_code_date ON moneyflow_data(ts_code, trade_date)')
    

    

    
    # 为美国利率数据表创建索引
    
    # 为指数日线行情数据表创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_index_ts_code ON index_daily_data(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_index_trade_date ON index_daily_data(trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_index_ts_code_date ON index_daily_data(ts_code, trade_date)')
    
    # 为每日基础指标数据表创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_basic_ts_code ON daily_basic(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_basic_trade_date ON daily_basic(trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_basic_ts_code_date ON daily_basic(ts_code, trade_date)')
    
    # 为自选股表创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_favorite_ts_code ON favorite_stocks(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_favorite_added_date ON favorite_stocks(added_date)')
    
    # 创建统一分析表（用于快速数据分析）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS unified_analysis_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            data_type TEXT NOT NULL,  -- 'stock', 'index', 'gold', 'margin', 'moneyflow', 'toplist'
            name TEXT,
            close REAL,
            open REAL,
            high REAL,
            low REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            -- 股票基础信息字段
            industry TEXT,
            area TEXT,
            pe REAL,
            pb REAL,
            eps REAL,
            bvps REAL,
            -- 计算字段
            volume_ratio REAL,  -- 量比
            total_mv REAL,      -- 总市值（万元）
            -- 资金流向字段
            net_mf_amount REAL,
            buy_lg_amount REAL,
            sell_lg_amount REAL,
            turnover_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ts_code, trade_date, data_type)
        )
    ''')
    
    # 为统一分析表创建索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_ts_code ON unified_analysis_data(ts_code)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_trade_date ON unified_analysis_data(trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_data_type ON unified_analysis_data(data_type)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_ts_code_date ON unified_analysis_data(ts_code, trade_date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_industry ON unified_analysis_data(industry)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_area ON unified_analysis_data(area)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_pct_chg ON unified_analysis_data(pct_chg)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_vol ON unified_analysis_data(vol)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_amount ON unified_analysis_data(amount)')
    # 检查字段是否存在后再创建索引
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_volume_ratio ON unified_analysis_data(volume_ratio)')
    except sqlite3.OperationalError:
        pass  # 字段不存在，跳过索引创建
    
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_unified_total_mv ON unified_analysis_data(total_mv)')
    except sqlite3.OperationalError:
        pass  # 字段不存在，跳过索引创建
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/stock/<ts_code>')
def stock_detail(ts_code):
    """股票详情页面"""
    conn = get_db_connection()
    
    # 获取股票基础信息（从stock_basic_info表获取股票名称）
    stock_info = conn.execute(
        'SELECT name FROM stock_basic_info WHERE ts_code = ?',
        (ts_code,)
    ).fetchone()
    
    stock_name = stock_info['name'] if stock_info else None
    
    # 获取最新数据
    latest_data = conn.execute(
        'SELECT * FROM daily_data WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
        (ts_code,)
    ).fetchone()
    
    # 获取最新的换手率数据（从daily_basic表）
    turnover_data = conn.execute(
        'SELECT turnover_rate FROM daily_basic WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
        (ts_code,)
    ).fetchone()
    
    # 获取前一交易日数据用于计算量比
    prev_data = conn.execute(
        'SELECT vol FROM daily_data WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1 OFFSET 1',
        (ts_code,)
    ).fetchone()
    
    # 计算额外指标
    additional_metrics = {}
    if latest_data and stock_info:
        # 成交额（原始数据单位：千元）
        amount_qian = latest_data['amount'] or 0
        amount_wan = amount_qian / 10  # 千元转万元
        if amount_wan >= 10000:  # 超过1亿（10000万）
            additional_metrics['amount'] = f"{amount_wan / 10000:.1f} 亿"
        else:
            additional_metrics['amount'] = f"{amount_wan:.0f} 万"
        
        # 量比（当日成交量/前一日成交量）
        if prev_data and prev_data['vol'] and prev_data['vol'] > 0:
            additional_metrics['volume_ratio'] = round((latest_data['vol'] or 0) / prev_data['vol'], 2)
        else:
            additional_metrics['volume_ratio'] = 0
        
        # 换手率（从daily_basic表获取正确的turnover_rate数据）
        if turnover_data and turnover_data['turnover_rate'] is not None:
            turnover_rate = turnover_data['turnover_rate']
            additional_metrics['turnover_rate'] = f"{turnover_rate:.2f}%"
        else:
            additional_metrics['turnover_rate'] = "--"
        
        # 市盈率（从daily_basic表获取）
        pe_data = conn.execute(
            'SELECT pe FROM daily_basic WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
            (ts_code,)
        ).fetchone()
        additional_metrics['pe'] = pe_data['pe'] if pe_data and pe_data['pe'] else 0
        
        # 市净率（从daily_basic表获取）
        pb_data = conn.execute(
            'SELECT pb FROM daily_basic WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
            (ts_code,)
        ).fetchone()
        additional_metrics['pb'] = pb_data['pb'] if pb_data and pb_data['pb'] else 0
        
        # 总市值（从daily_basic表获取）
        total_mv_data = conn.execute(
            'SELECT total_mv FROM daily_basic WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
            (ts_code,)
        ).fetchone()
        if total_mv_data and total_mv_data['total_mv']:
            total_mv_wan = total_mv_data['total_mv']  # 单位已经是万元
            if total_mv_wan >= 10000:  # 超过1亿（10000万）
                additional_metrics['total_market_value'] = f"{total_mv_wan / 10000:.1f} 亿"
            else:
                additional_metrics['total_market_value'] = f"{total_mv_wan:.0f} 万"
        else:
            additional_metrics['total_market_value'] = "--"
    
    # 获取历史数据（最近120天用于显示）
    history_rows = conn.execute(
        'SELECT * FROM daily_data WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 120',
        (ts_code,)
    ).fetchall()
    
    # 获取资金流向数据（最新一天）
    moneyflow_rows = conn.execute(
        'SELECT * FROM moneyflow_data WHERE ts_code = ? ORDER BY trade_date DESC LIMIT 1',
        (ts_code,)
    ).fetchall()
    
    conn.close()
    
    # 将Row对象转换为字典
    history = [dict(row) for row in history_rows] if history_rows else []
    moneyflow = [dict(row) for row in moneyflow_rows] if moneyflow_rows else []
    
    return render_template('stock_detail.html', 
                         stock_code=ts_code,
                         stock_name=stock_name,
                         latest_data=latest_data,
                         additional_metrics=additional_metrics,
                         history=history,
                         moneyflow=moneyflow)

# 删除了九转序列法相关路由

@app.route('/api/stocks')
def get_stocks():
    """获取股票列表"""
    conn = get_db_connection()
    
    # 获取最新交易日期
    latest_date = conn.execute(
        'SELECT MAX(trade_date) as max_date FROM daily_data'
    ).fetchone()['max_date']
    
    if not latest_date:
        conn.close()
        return jsonify({'stocks': [], 'message': '暂无数据'})
    
    # 获取最新交易日的所有股票数据，包含新增字段
    stocks = conn.execute('''
        SELECT d.ts_code, d.trade_date, d.open, d.high, d.low, d.close, d.pre_close, 
               d.change, d.pct_chg, d.vol, d.amount, 
               sb.name, sb.industry, sb.area,
               db.turnover_rate, db.volume_ratio, db.pe, db.pb, db.total_mv,
               mf.net_mf_amount
        FROM daily_data d
        LEFT JOIN stock_basic_info sb ON d.ts_code = sb.ts_code
        LEFT JOIN (
            SELECT ts_code, turnover_rate, volume_ratio, pe, pb, total_mv,
                   ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
            FROM daily_basic
        ) db ON d.ts_code = db.ts_code AND db.rn = 1
        LEFT JOIN (
            SELECT ts_code, net_mf_amount,
                   ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
            FROM moneyflow_data
        ) mf ON d.ts_code = mf.ts_code AND mf.rn = 1
        WHERE d.trade_date = ?
        ORDER BY d.pct_chg DESC
    ''', (latest_date,)).fetchall()
    
    # 转换为字典列表并计算九转序列
    stocks_list = []
    for stock in stocks:
        stock_dict = dict(stock)
        
        # 获取该股票最近90天的收盘价用于计算九转序列
        closes_data = conn.execute('''
            SELECT close FROM daily_data 
            WHERE ts_code = ? 
            ORDER BY trade_date DESC 
            LIMIT 90
        ''', (stock['ts_code'],)).fetchall()
        
        if len(closes_data) >= 5:
            closes = [row['close'] for row in reversed(closes_data)]
            td_sequential = calculate_td_sequential(closes)
            stock_dict['td_sequential'] = td_sequential
        else:
            stock_dict['td_sequential'] = None
            
        stocks_list.append(stock_dict)
    
    conn.close()
    
    return jsonify({
        'stocks': stocks_list,
        'trade_date': latest_date,
        'total': len(stocks_list)
    })

@app.route('/api/stock/<ts_code>')
def get_stock_history(ts_code):
    """获取单个股票历史数据"""
    days = request.args.get('days', 30, type=int)
    
    conn = get_db_connection()
    
    history = conn.execute('''
        SELECT ts_code, trade_date, open, high, low, close, pre_close,
               change, pct_chg, vol, amount
        FROM daily_data 
        WHERE ts_code = ?
        ORDER BY trade_date DESC
        LIMIT ?
    ''', (ts_code, days)).fetchall()
    
    conn.close()
    
    # 转换为字典列表
    history_list = [dict(row) for row in history]
    
    return jsonify({
        'ts_code': ts_code,
        'history': history_list,
        'total': len(history_list)
    })

@app.route('/api/sync')
def manual_sync():
    """手动同步数据"""
    try:
        data_sync = DataSync()
        result = data_sync.sync_all_stocks()
        return jsonify({
            'success': True,
            'message': f'同步完成，共处理 {result.get("total", 0)} 条数据'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500



@app.route('/api/sync_stock_basic_info', methods=['POST'])
def sync_stock_basic_info():
    """手动同步股票基础信息（基于stock_basic接口）"""
    try:
        data_sync = DataSync()
        saved_count = data_sync.sync_stock_basic_info()
        
        return jsonify({
            'success': True,
            'message': f'股票基础信息同步完成，共保存 {saved_count} 条记录',
            'saved_count': saved_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步失败: {str(e)}'
        }), 500

@app.route('/api/stock_basic_info')
def get_stock_basic_info():
    """获取股票基础信息列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        market = request.args.get('market', '')
        industry = request.args.get('industry', '')
        list_status = request.args.get('list_status', 'L')
        
        conn = get_db_connection()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append('(ts_code LIKE ? OR name LIKE ? OR symbol LIKE ?)')
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if market:
            where_conditions.append('market = ?')
            params.append(market)
        
        if industry:
            where_conditions.append('industry = ?')
            params.append(industry)
        
        if list_status:
            where_conditions.append('list_status = ?')
            params.append(list_status)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        # 获取总数
        count_query = f'SELECT COUNT(*) as total FROM stock_basic_info WHERE {where_clause}'
        total = conn.execute(count_query, params).fetchone()['total']
        
        # 获取分页数据
        offset = (page - 1) * per_page
        data_query = f'''
            SELECT ts_code, symbol, name, area, industry, market, exchange, 
                   list_status, list_date, delist_date, is_hs, created_at, updated_at
            FROM stock_basic_info 
            WHERE {where_clause}
            ORDER BY ts_code
            LIMIT ? OFFSET ?
        '''
        params.extend([per_page, offset])
        
        stocks = conn.execute(data_query, params).fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(stock) for stock in stocks],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取股票基础信息失败: {str(e)}'
        }), 500

@app.route('/api/sync_moneyflow')
def manual_sync_moneyflow():
    """手动同步个股资金流向数据"""
    trade_date = request.args.get('trade_date')
    
    if not trade_date:
        # 如果没有指定日期，使用最新交易日期
        conn = get_db_connection()
        latest_date = conn.execute(
            'SELECT MAX(trade_date) as max_date FROM daily_data'
        ).fetchone()['max_date']
        conn.close()
        
        if not latest_date:
            return jsonify({
                'success': False,
                'message': '无法获取最新交易日期，请先同步日线数据'
            }), 400
        
        trade_date = latest_date
    
    try:
        data_sync = DataSync()
        result = data_sync.sync_moneyflow_by_date(trade_date)
        return jsonify({
            'success': True,
            'message': f'个股资金流向数据同步完成，共处理 {result} 条数据',
            'trade_date': trade_date
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'个股资金流向数据同步失败: {str(e)}'
        }), 500









def update_sync_progress(step, progress, details=None):
    """更新同步进度"""
    global sync_progress
    sync_progress['current_step'] = step
    sync_progress['progress'] = progress
    if details:
        sync_progress['details'].append(details)
    
    # 计算预计剩余时间
    if sync_progress['start_time'] and progress > 0:
        elapsed = time.time() - sync_progress['start_time']
        estimated_total = elapsed * sync_progress['total_steps'] / progress
        sync_progress['estimated_remaining'] = max(0, estimated_total - elapsed)

@app.route('/api/sync_progress')
def sync_progress_stream():
    """SSE接口，推送同步进度"""
    def generate():
        while True:
            data = json.dumps(sync_progress)
            yield f"data: {data}\n\n"
            time.sleep(1)
            if not sync_progress['is_syncing']:
                break
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

def sync_all_a_stock_data_background(start_date=None, end_date=None):
    """后台同步所有A股数据"""
    global sync_progress
    try:
        sync_progress['is_syncing'] = True
        sync_progress['start_time'] = time.time()
        sync_progress['progress'] = 0
        sync_progress['details'] = []
        
        # 确保数据库已初始化
        update_sync_progress('检查数据库', 0, '正在检查数据库和表结构...')
        init_database()
        
        data_sync = DataSync()
        total_count = 0
        results = []
        
        # 确定同步日期范围
        if start_date and end_date:
            # 用户指定了日期范围
            sync_dates = []
            current_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            while current_date <= end_date_obj:
                sync_dates.append(current_date.strftime('%Y%m%d'))
                current_date += timedelta(days=1)
            
            update_sync_progress('准备同步日期范围', 5, f'同步日期: {start_date} 到 {end_date} ({len(sync_dates)}天)')
        else:
            # 获取最新交易日期
            update_sync_progress('获取最新交易日期', 5, '正在查询数据库...')
            conn = get_db_connection()
            latest_date = conn.execute(
                'SELECT MAX(trade_date) as max_date FROM daily_data'
            ).fetchone()['max_date']
            conn.close()
            
            if not latest_date:
                # 如果没有历史数据，使用当前日期
                latest_date = datetime.now().strftime('%Y%m%d')
            
            sync_dates = [latest_date]
            update_sync_progress(f'开始同步 {latest_date} 数据', 5, f'目标日期: {latest_date}')
        
        # 按日期同步数据
        total_dates = len(sync_dates)
        # 更新总步骤数为实际的日期数量 + 初始化步骤
        sync_progress['total_steps'] = total_dates * 7 + 5  # 每个日期7个同步步骤 + 5个初始化步骤
        
        for i, sync_date in enumerate(sync_dates):
            base_progress = 5 + i * 7  # 基础进度 = 初始化步骤 + 已完成日期的步骤数
            
            # 同步日线数据
            update_sync_progress(f'同步 {sync_date} 日线数据', base_progress + 1, f'进度: {i+1}/{total_dates} 日期')
            count1 = data_sync.sync_by_date(sync_date)
            total_count += count1
            
            # 基础信息已通过stock_basic_info表同步，跳过
            count2 = 0
            
            # 同步资金流向数据
            update_sync_progress(f'同步 {sync_date} 资金流向', base_progress + 3, f'已完成基础信息')
            count3 = data_sync.sync_moneyflow_by_date(sync_date)
            total_count += count3
            
            # 同步每日基础指标数据
            update_sync_progress(f'同步 {sync_date} 基础指标', base_progress + 4, f'已完成资金流向')
            count4 = data_sync.sync_daily_basic_by_date(sync_date)
            total_count += count4
            
            date_total = count1 + count2 + count3 + count4
            results.append(f'{sync_date}: {date_total}条')
        
        update_sync_progress('检查数据完整性', sync_progress['total_steps'], f'正在验证同步数据...')
        
        # 进行数据完整性检查
        expected_counts = {}
        for i, sync_date in enumerate(sync_dates):
            # 根据results计算每个日期的预期数据量
            if i < len(results):
                try:
                    count_str = results[i].split(': ')[1].replace('条', '')
                    expected_counts[sync_date] = int(count_str)
                except:
                    expected_counts[sync_date] = 0
            else:
                expected_counts[sync_date] = 0
        
        integrity_report = data_sync.check_data_integrity(sync_dates, expected_counts)
        
        update_sync_progress('同步完成', sync_progress['total_steps'], f'成功同步 {total_count} 条数据')
        
        sync_progress['success'] = True
        sync_progress['message'] = f'成功同步 {total_count} 条A股数据'
        sync_progress['total_count'] = total_count
        sync_progress['results'] = results
        sync_progress['integrity_report'] = integrity_report
        
    except Exception as e:
        sync_progress['success'] = False
        sync_progress['message'] = f'同步失败: {str(e)}'
        update_sync_progress('同步失败', sync_progress['progress'], str(e))
    finally:
        sync_progress['is_syncing'] = False

@app.route('/api/sync_all_a_stock_data', methods=['POST'])
def sync_all_a_stock_data():
    """一键同步所有A股数据"""
    global sync_progress
    
    if sync_progress['is_syncing']:
        return jsonify({
            'success': False,
            'message': '同步正在进行中，请稍后再试'
        }), 400
    
    # 获取请求参数
    data = request.get_json() or {}
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # 启动后台同步任务
    thread = threading.Thread(target=sync_all_a_stock_data_background, args=(start_date, end_date))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '同步任务已启动，请查看进度'
    })





@app.route('/api/sync_index_daily', methods=['POST'])
def sync_index_daily():
    """同步指数日线行情数据"""
    ts_code = request.args.get('ts_code')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        data_sync = DataSync()
        result = data_sync.sync_index_daily_data(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return jsonify({
            'success': True,
            'message': f'指数日线行情数据同步完成，共处理 {result} 条数据'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'指数日线行情数据同步失败: {str(e)}'
        }), 500

@app.route('/api/sync_daily_basic', methods=['POST'])
def sync_daily_basic():
    """同步每日基础指标数据"""
    trade_date = request.args.get('trade_date')
    
    try:
        data_sync = DataSync()
        
        if trade_date:
            # 同步指定日期的数据
            result = data_sync.sync_daily_basic_by_date(trade_date)
            return jsonify({
                'success': True,
                'message': f'每日基础指标数据同步完成，共处理 {result} 条数据',
                'trade_date': trade_date,
                'count': result
            })
        else:
            # 同步最新交易日的数据
            conn = get_db_connection()
            latest_date = conn.execute(
                'SELECT MAX(trade_date) as max_date FROM daily_data'
            ).fetchone()['max_date']
            conn.close()
            
            if not latest_date:
                latest_date = datetime.now().strftime('%Y%m%d')
            
            result = data_sync.sync_daily_basic_by_date(latest_date)
            return jsonify({
                'success': True,
                'message': f'每日基础指标数据同步完成，共处理 {result} 条数据',
                'trade_date': latest_date,
                'count': result
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'每日基础指标数据同步失败: {str(e)}'
        }), 500

@app.route('/api/generate_analysis_data', methods=['POST'])
def generate_analysis_data():
    """生成统一分析表数据"""
    trade_date = request.args.get('trade_date')
    
    try:
        data_sync = DataSync()
        result = data_sync.generate_unified_analysis_data(trade_date=trade_date)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'trade_date': result.get('trade_date'),
                'total_records': result.get('total_records'),
                'details': result.get('details')
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成统一分析表失败: {str(e)}'
        }), 500

@app.route('/api/analysis_data')
def get_analysis_data():
    """获取统一分析表数据"""
    trade_date = request.args.get('trade_date')
    data_type = request.args.get('data_type')  # stock, index, gold, margin
    ts_code = request.args.get('ts_code')
    industry = request.args.get('industry')
    area = request.args.get('area')
    min_pct_chg = request.args.get('min_pct_chg', type=float)
    max_pct_chg = request.args.get('max_pct_chg', type=float)
    min_vol = request.args.get('min_vol', type=float)
    max_vol = request.args.get('max_vol', type=float)
    sort_by = request.args.get('sort_by', 'pct_chg')
    sort_order = request.args.get('sort_order', 'desc')
    limit = request.args.get('limit', 1000, type=int)
    
    conn = get_db_connection()
    
    where_conditions = []
    params = []
    
    if trade_date:
        where_conditions.append('trade_date = ?')
        params.append(trade_date)
    
    if data_type:
        where_conditions.append('data_type = ?')
        params.append(data_type)
    
    if ts_code:
        where_conditions.append('ts_code LIKE ?')
        params.append(f'%{ts_code}%')
    
    if industry:
        where_conditions.append('industry = ?')
        params.append(industry)
    
    if area:
        where_conditions.append('area = ?')
        params.append(area)
    
    if min_pct_chg is not None:
        where_conditions.append('pct_chg >= ?')
        params.append(min_pct_chg)
    
    if max_pct_chg is not None:
        where_conditions.append('pct_chg <= ?')
        params.append(max_pct_chg)
    
    if min_vol is not None:
        where_conditions.append('vol >= ?')
        params.append(min_vol)
    
    if max_vol is not None:
        where_conditions.append('vol <= ?')
        params.append(max_vol)
    
    where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
    
    # 验证排序字段
    valid_sort_fields = ['ts_code', 'trade_date', 'close', 'pct_chg', 'vol', 'amount', 'pe', 'pb']
    if sort_by not in valid_sort_fields:
        sort_by = 'pct_chg'
    
    sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    query = f'''
        SELECT ts_code, trade_date, data_type, name, close, open, high, low, pre_close,
               change, pct_chg, vol, amount, industry, area, pe, pb, eps, bvps,
               net_mf_amount, buy_lg_amount, sell_lg_amount, net_amount, turnover_rate,
               reason, rzye, rzmre, rzrqye, updated_at
        FROM unified_analysis_data
        WHERE {where_clause}
        ORDER BY {sort_by} {sort_direction}
        LIMIT ?
    '''
    
    params.append(limit)
    
    try:
        cursor = conn.execute(query, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data),
            'filters': {
                'trade_date': trade_date,
                'data_type': data_type,
                'ts_code': ts_code,
                'industry': industry,
                'area': area,
                'min_pct_chg': min_pct_chg,
                'max_pct_chg': max_pct_chg,
                'min_vol': min_vol,
                'max_vol': max_vol,
                'sort_by': sort_by,
                'sort_order': sort_order,
                'limit': limit
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'查询统一分析表数据失败: {str(e)}'
        }), 500



@app.route('/api/index_daily')
def get_index_daily():
    """获取指数日线行情数据"""
    ts_code = request.args.get('ts_code')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 100, type=int)
    
    conn = get_db_connection()
    
    # 构建查询条件
    where_conditions = []
    params = []
    
    if ts_code:
        where_conditions.append('ts_code = ?')
        params.append(ts_code)
    
    if start_date:
        where_conditions.append('trade_date >= ?')
        params.append(start_date)
    
    if end_date:
        where_conditions.append('trade_date <= ?')
        params.append(end_date)
    
    where_clause = ''
    if where_conditions:
        where_clause = 'WHERE ' + ' AND '.join(where_conditions)
    
    # 查询指数日线行情数据 - 每个指数只显示最新的一条数据
    query = f'''
        SELECT ts_code, trade_date, close, open, high, low, pre_close, change, pct_chg, vol, amount
        FROM index_daily_data i1
        WHERE i1.trade_date = (
            SELECT MAX(i2.trade_date) 
            FROM index_daily_data i2 
            WHERE i2.ts_code = i1.ts_code
        )
        {('AND ' + ' AND '.join(where_conditions)) if where_conditions else ''}
        ORDER BY ts_code
        LIMIT ?
    '''
    
    params.append(limit)
    index_daily = conn.execute(query, params).fetchall()
    
    conn.close()
    
    # 转换为字典列表并添加指数名称
    index_daily_data = []
    for row in index_daily:
        row_dict = dict(row)
        # 从指数名称映射字典中获取指数名称
        row_dict['name'] = INDEX_NAME_MAP.get(row_dict['ts_code'], row_dict['ts_code'])
        index_daily_data.append(row_dict)
    
    return jsonify({
        'index_daily': index_daily_data,
        'total': len(index_daily_data)
    })











@app.route('/api/sync_td_sequential', methods=['POST'])
def sync_td_sequential():
    """手动触发九转序列筛选"""
    try:
        filtered_stocks = filter_td_sequential_stocks()
        return jsonify({
            'success': True,
            'message': f'九转序列筛选完成，找到 {len(filtered_stocks)} 只符合条件的股票',
            'count': len(filtered_stocks)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'九转序列筛选失败: {str(e)}'
        }), 500


@app.route('/api/td_sequential_stocks')
def get_td_sequential_stocks():
    """获取九转序列筛选结果"""
    try:
        filtered_stocks = filter_td_sequential_stocks()
        return jsonify({
            'stocks': filtered_stocks,
            'total': len(filtered_stocks),
            'message': f'找到 {len(filtered_stocks)} 只九转数值大于红2的股票'
        })
    except Exception as e:
        return jsonify({
            'stocks': [],
            'total': 0,
            'message': f'获取数据失败: {str(e)}'
        }), 500


@app.route('/td_sequential_result')
def td_sequential_result_page():
    """九转序列筛选结果页面"""
    return render_template('td_sequential_result.html')


@app.route('/api/status')
def get_status():
    """获取系统状态"""
    conn = get_db_connection()
    
    # 获取日线数据统计
    daily_stats = conn.execute('''
        SELECT 
            COUNT(DISTINCT ts_code) as stock_count,
            COUNT(*) as total_records,
            MAX(trade_date) as latest_date,
            MIN(trade_date) as earliest_date
        FROM daily_data
    ''').fetchone()
    
    # 获取股票基础信息统计
    basic_stats = conn.execute('''
        SELECT 
            COUNT(DISTINCT ts_code) as basic_stock_count,
            COUNT(*) as basic_total_records,
            MAX(updated_at) as basic_latest_date,
            MIN(created_at) as basic_earliest_date
        FROM stock_basic_info
    ''').fetchone()
    

    
    # 获取个股资金流向数据统计
    moneyflow_stats = conn.execute('''
        SELECT 
            COUNT(DISTINCT ts_code) as moneyflow_stock_count,
            COUNT(*) as moneyflow_total_records,
            MAX(trade_date) as moneyflow_latest_date,
            MIN(trade_date) as moneyflow_earliest_date
        FROM moneyflow_data
    ''').fetchone()
    

    

    
    # 获取指数日线行情数据统计
    index_stats = conn.execute('''
        SELECT 
            COUNT(DISTINCT ts_code) as index_count,
            COUNT(*) as index_total_records,
            MAX(trade_date) as index_latest_date,
            MIN(trade_date) as index_earliest_date
        FROM index_daily_data
    ''').fetchone()
    
    conn.close()
    
    return jsonify({
        'daily_data': {
            'stock_count': daily_stats['stock_count'] or 0,
            'total_records': daily_stats['total_records'] or 0,
            'latest_date': daily_stats['latest_date'],
            'earliest_date': daily_stats['earliest_date']
        },
        'basic_data': {
            'stock_count': basic_stats['basic_stock_count'] or 0,
            'total_records': basic_stats['basic_total_records'] or 0,
            'latest_date': basic_stats['basic_latest_date'],
            'earliest_date': basic_stats['basic_earliest_date']
        },

        'moneyflow_data': {
            'stock_count': moneyflow_stats['moneyflow_stock_count'] or 0,
            'total_records': moneyflow_stats['moneyflow_total_records'] or 0,
            'latest_date': moneyflow_stats['moneyflow_latest_date'],
            'earliest_date': moneyflow_stats['moneyflow_earliest_date']
        },

        'index_data': {
            'index_count': index_stats['index_count'] or 0,
            'total_records': index_stats['index_total_records'] or 0,
            'latest_date': index_stats['index_latest_date'],
            'earliest_date': index_stats['index_earliest_date']
        }
    })

# 自选股相关API
@app.route('/favorites')
def favorites_page():
    """自选股页面"""
    return render_template('favorites.html')

@app.route('/api/favorites')
def get_favorites():
    """获取自选股列表"""
    try:
        conn = get_db_connection()
        
        # 获取自选股及其最新数据
        query = '''
            SELECT 
                f.ts_code,
                f.name,
                f.added_date,
                d.close,
                d.pre_close,
                d.change,
                d.pct_chg,
                d.vol,
                d.amount,
                d.trade_date,
                b.industry,
                b.area,
                db.total_mv,
                db.pe,
                db.pb,
                mf.net_mf_amount
            FROM favorite_stocks f
            LEFT JOIN (
                SELECT ts_code, close, pre_close, change, pct_chg, vol, amount, trade_date,
                       ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
                FROM daily_data
            ) d ON f.ts_code = d.ts_code AND d.rn = 1
            LEFT JOIN stock_basic_info b ON f.ts_code = b.ts_code
            LEFT JOIN (
                SELECT ts_code, total_mv, pe, pb, trade_date,
                       ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
                FROM daily_basic
            ) db ON f.ts_code = db.ts_code AND db.rn = 1
            LEFT JOIN (
                SELECT ts_code, net_mf_amount, trade_date,
                       ROW_NUMBER() OVER (PARTITION BY ts_code ORDER BY trade_date DESC) as rn
                FROM moneyflow_data
            ) mf ON f.ts_code = mf.ts_code AND mf.rn = 1
            ORDER BY f.added_date DESC
        '''
        
        cursor = conn.execute(query)
        favorites = []
        
        for row in cursor.fetchall():
            # 格式化总市值
            total_mv_formatted = ""
            if row['total_mv']:
                if row['total_mv'] >= 10000:
                    total_mv_formatted = f"{row['total_mv'] / 10000:.2f} 亿"
                else:
                    total_mv_formatted = f"{row['total_mv']:.2f} 万"
            
            # 格式化净流入额
            net_mf_formatted = ""
            if row['net_mf_amount']:
                if abs(row['net_mf_amount']) >= 10000:
                    net_mf_formatted = f"{row['net_mf_amount'] / 10000:.2f} 亿"
                else:
                    net_mf_formatted = f"{row['net_mf_amount']:.2f} 万"
            
            # 计算九转序列
            td_sequential = None
            closes_data = conn.execute('''
                SELECT close FROM daily_data 
                WHERE ts_code = ? 
                ORDER BY trade_date DESC 
                LIMIT 90
            ''', (row['ts_code'],)).fetchall()
            
            if len(closes_data) >= 5:
                closes = [close_row['close'] for close_row in reversed(closes_data)]
                td_sequential = calculate_td_sequential(closes)
            
            favorites.append({
                'ts_code': row['ts_code'],
                'name': row['name'],
                'added_date': row['added_date'],
                'close': row['close'],
                'pre_close': row['pre_close'],
                'change': row['change'],
                'pct_chg': row['pct_chg'],
                'vol': row['vol'],
                'amount': row['amount'],
                'trade_date': row['trade_date'],
                'industry': row['industry'],
                'area': row['area'],
                'total_mv': total_mv_formatted,
                'pe': row['pe'],
                'pb': row['pb'],
                'net_mf_amount': net_mf_formatted,
                'td_sequential': td_sequential
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': favorites,
            'total': len(favorites)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取自选股失败: {str(e)}'
        }), 500

@app.route('/api/favorites/add', methods=['POST'])
def add_favorite():
    """添加自选股"""
    try:
        data = request.get_json()
        ts_code = data.get('ts_code')
        
        if not ts_code:
            return jsonify({
                'success': False,
                'message': '股票代码不能为空'
            }), 400
        
        conn = get_db_connection()
        
        # 获取股票名称
        stock_info = conn.execute(
            'SELECT name FROM stock_basic_info WHERE ts_code = ?',
            (ts_code,)
        ).fetchone()
        
        if not stock_info:
            conn.close()
            return jsonify({
                'success': False,
                'message': '股票不存在'
            }), 404
        
        # 检查是否已经添加
        existing = conn.execute(
            'SELECT id FROM favorite_stocks WHERE ts_code = ?',
            (ts_code,)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'message': '该股票已在自选股中'
            }), 409
        
        # 添加到自选股
        today = datetime.now().strftime('%Y-%m-%d')
        conn.execute(
            'INSERT INTO favorite_stocks (ts_code, name, added_date) VALUES (?, ?, ?)',
            (ts_code, stock_info['name'], today)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '添加自选股成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加自选股失败: {str(e)}'
        }), 500

@app.route('/api/favorites/remove', methods=['POST'])
def remove_favorite():
    """移除自选股"""
    try:
        data = request.get_json()
        ts_code = data.get('ts_code')
        
        if not ts_code:
            return jsonify({
                'success': False,
                'message': '股票代码不能为空'
            }), 400
        
        conn = get_db_connection()
        
        # 检查是否存在
        existing = conn.execute(
            'SELECT id FROM favorite_stocks WHERE ts_code = ?',
            (ts_code,)
        ).fetchone()
        
        if not existing:
            conn.close()
            return jsonify({
                'success': False,
                'message': '该股票不在自选股中'
            }), 404
        
        # 从自选股中移除
        conn.execute(
            'DELETE FROM favorite_stocks WHERE ts_code = ?',
            (ts_code,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '移除自选股成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'移除自选股失败: {str(e)}'
        }), 500

def check_and_kill_port(port):
    """检查端口是否被占用，如果被占用则强制杀死占用的进程"""
    try:
        current_pid = os.getpid()  # 获取当前进程ID
        found_port_occupied = False
        
        # 查找占用指定端口的进程
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                found_port_occupied = True
                
                # 如果是当前进程占用的端口，跳过
                if conn.pid == current_pid:
                    print(f"端口 {port} 被当前进程占用 (PID={current_pid})，跳过")
                    continue
                    
                try:
                    # 获取进程对象
                    process = psutil.Process(conn.pid)
                    print(f"发现端口 {port} 被其他进程占用: PID={conn.pid}, 进程名={process.name()}")
                    
                    # 强制杀死进程
                    process.terminate()
                    process.wait(timeout=3)  # 等待进程正常终止
                    print(f"已终止进程 PID={conn.pid}")
                    
                except psutil.NoSuchProcess:
                    print(f"进程 PID={conn.pid} 已不存在")
                except psutil.AccessDenied:
                    print(f"无权限访问进程 PID={conn.pid}，跳过")
                except psutil.TimeoutExpired:
                    # 如果进程没有正常终止，强制杀死
                    try:
                        process.kill()
                        print(f"已强制杀死进程 PID={conn.pid}")
                    except psutil.NoSuchProcess:
                        print(f"进程 PID={conn.pid} 已不存在")
                    except psutil.AccessDenied:
                        print(f"无权限杀死进程 PID={conn.pid}")
                except Exception as e:
                    print(f"处理进程 PID={conn.pid} 时出错: {e}")
        
        if not found_port_occupied:
            print(f"端口 {port} 未被占用")
                    
    except Exception as e:
        print(f"检查端口占用时出错: {e}")

if __name__ == '__main__':
    # 设置端口
    PORT = 8888
    
    # 检查并杀死占用端口的进程
    print(f"检查端口 {PORT} 是否被占用...")
    check_and_kill_port(PORT)
    
    # 初始化数据库
    init_database()
    
    # 启动定时任务
    start_scheduler()
    
    # 启动Flask应用
    # Production mode is enabled via APP_ENV=production environment variable
    is_production = os.environ.get('APP_ENV') == 'production'
    print(f"启动Flask应用，端口: {PORT}, 生产模式: {is_production}")
    app.run(debug=not is_production, host='0.0.0.0', port=PORT)