#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票选股系统启动脚本

使用方法:
    python run.py                    # 启动Web服务
    python run.py --sync             # 执行一次数据同步
    python run.py --init             # 初始化数据库
    python run.py --help             # 显示帮助信息
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_database
from data_sync import DataSync
from scheduler import start_scheduler

def init_db():
    """初始化数据库"""
    print("正在初始化数据库...")
    try:
        init_database()
        print("✓ 数据库初始化成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False
    return True

def sync_data():
    """执行数据同步"""
    print("开始同步股票数据...")
    try:
        data_sync = DataSync()
        result = data_sync.sync_all_stocks(days=30)
        print(f"✓ 数据同步完成")
        print(f"  - 处理股票数量: {result.get('stocks_processed', 0)}")
        print(f"  - 成功同步: {result.get('success', 0)}")
        print(f"  - 失败数量: {result.get('failed', 0)}")
        print(f"  - 总数据量: {result.get('total', 0)}")
    except Exception as e:
        print(f"✗ 数据同步失败: {e}")
        return False
    return True

def start_web_server(host='0.0.0.0', port=5000, debug=False):
    """启动Web服务器"""
    print(f"正在启动股票选股系统...")
    print(f"服务地址: http://{host}:{port}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        # 初始化数据库
        init_database()
        
        # 启动定时任务
        start_scheduler()
        
        # 启动Flask应用
        app.run(host=host, port=port, debug=debug, threaded=True)
        
    except KeyboardInterrupt:
        print("\n正在停止服务...")
    except Exception as e:
        print(f"启动失败: {e}")

def check_dependencies():
    """检查依赖包"""
    print("检查依赖包...")
    required_packages = [
        'flask',
        'tushare',
        'pandas',
        'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✓ 所有依赖包已安装")
    return True

def show_system_info():
    """显示系统信息"""
    print("=" * 60)
    print("股票选股系统 v1.0")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print("-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description='股票选股系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py                    # 启动Web服务
  python run.py --sync             # 执行数据同步
  python run.py --init             # 初始化数据库
  python run.py --check            # 检查依赖
  python run.py --host 127.0.0.1   # 指定主机地址
  python run.py --port 8080        # 指定端口
  python run.py --debug            # 开启调试模式
        """
    )
    
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--sync', action='store_true', help='执行数据同步')
    parser.add_argument('--check', action='store_true', help='检查依赖包')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    parser.add_argument('--info', action='store_true', help='显示系统信息')
    
    args = parser.parse_args()
    
    # 显示系统信息
    if args.info:
        show_system_info()
        return
    
    # 检查依赖
    if args.check:
        show_system_info()
        if not check_dependencies():
            sys.exit(1)
        return
    
    # 初始化数据库
    if args.init:
        show_system_info()
        if not init_db():
            sys.exit(1)
        return
    
    # 执行数据同步
    if args.sync:
        show_system_info()
        if not check_dependencies():
            sys.exit(1)
        if not sync_data():
            sys.exit(1)
        return
    
    # 默认启动Web服务
    show_system_info()
    if not check_dependencies():
        sys.exit(1)
    
    start_web_server(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()