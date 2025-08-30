#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 设置环境变量以确保正确处理UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
if 'LANG' not in os.environ:
    os.environ['LANG'] = 'en_US.UTF-8'
if 'LC_ALL' not in os.environ:
    os.environ['LC_ALL'] = 'en_US.UTF-8'

import tushare as ts
import pandas as pd
import sqlite3
import logging
from data_sync import DataSync

# 配置日志为DEBUG级别
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_info():
    """测试环境信息"""
    print("=== 环境信息 ===")
    print(f"Python版本: {sys.version}")
    print(f"系统编码: {sys.getdefaultencoding()}")
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print(f"LANG: {os.environ.get('LANG', 'Not Set')}")
    print(f"LC_ALL: {os.environ.get('LC_ALL', 'Not Set')}")
    print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'Not Set')}")
    print()

def test_tushare_api():
    """测试Tushare API返回的数据编码"""
    print("=== Tushare API测试 ===")
    
    try:
        # 初始化DataSync
        data_sync = DataSync()
        
        # 获取少量股票基础信息进行测试
        print("正在获取股票基础信息...")
        stock_basic = data_sync._api_call_with_retry(
            data_sync.pro.stock_basic,
            exchange='', 
            list_status='L', 
            fields='ts_code,symbol,name,area,industry',
            limit=10  # 只获取10条数据进行测试
        )
        
        if stock_basic is not None and not stock_basic.empty:
            print(f"成功获取 {len(stock_basic)} 条数据")
            
            # 检查每条数据的编码
            for idx, row in stock_basic.iterrows():
                ts_code = row.get('ts_code')
                name = row.get('name')
                area = row.get('area')
                industry = row.get('industry')
                
                print(f"\n股票 {idx + 1}:")
                print(f"  代码: {ts_code}")
                print(f"  名称: {name} (类型: {type(name)})")
                print(f"  地域: {area} (类型: {type(area)})")
                print(f"  行业: {industry} (类型: {type(industry)})")
                
                # 检查中文字符编码
                if name and isinstance(name, str):
                    try:
                        name_utf8 = name.encode('utf-8')
                        print(f"  名称UTF-8编码: {name_utf8}")
                        print(f"  名称UTF-8长度: {len(name_utf8)} 字节")
                        print(f"  名称字符长度: {len(name)} 字符")
                    except Exception as e:
                        print(f"  名称编码错误: {e}")
                
                if area and isinstance(area, str):
                    try:
                        area_utf8 = area.encode('utf-8')
                        print(f"  地域UTF-8编码: {area_utf8}")
                    except Exception as e:
                        print(f"  地域编码错误: {e}")
                
                if industry and isinstance(industry, str):
                    try:
                        industry_utf8 = industry.encode('utf-8')
                        print(f"  行业UTF-8编码: {industry_utf8}")
                    except Exception as e:
                        print(f"  行业编码错误: {e}")
        else:
            print("未获取到数据")
            
    except Exception as e:
        print(f"API测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_database_encoding():
    """测试数据库编码"""
    print("\n=== 数据库编码测试 ===")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('stock_data.db')
        conn.text_factory = str  # 确保返回字符串而不是字节
        
        # 查询股票基础信息
        cursor = conn.execute(
            "SELECT ts_code, name, area, industry FROM stock_basic_info LIMIT 5"
        )
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"数据库中有 {len(rows)} 条测试数据:")
            for i, (ts_code, name, area, industry) in enumerate(rows):
                print(f"\n数据库记录 {i + 1}:")
                print(f"  代码: {ts_code} (类型: {type(ts_code)})")
                print(f"  名称: {name} (类型: {type(name)})")
                print(f"  地域: {area} (类型: {type(area)})")
                print(f"  行业: {industry} (类型: {type(industry)})")
                
                # 检查是否为中文
                if name:
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(name))
                    print(f"  名称包含中文: {has_chinese}")
        else:
            print("数据库中没有股票基础信息数据")
        
        conn.close()
        
    except Exception as e:
        print(f"数据库测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("股票系统编码测试工具")
    print("=" * 50)
    
    test_environment_info()
    test_tushare_api()
    test_database_encoding()
    
    print("\n=== 测试完成 ===")
    print("请将此输出结果与其他环境进行对比")

if __name__ == '__main__':
    main()