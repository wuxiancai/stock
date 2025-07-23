#!/usr/bin/env python3
"""
最小化的股票指数API服务器
用于快速测试前端页面
"""

import json
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class StockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 路由处理
        if parsed_path.path == '/api/v1/market/indices':
            self.handle_indices()
        elif parsed_path.path == '/health':
            self.handle_health()
        else:
            self.handle_404()
    
    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_indices(self):
        """返回A股主要指数数据"""
        indices = [
            {
                "code": "000001",
                "name": "上证指数",
                "current_price": round(3000 + random.uniform(-100, 100), 2),
                "change": round(random.uniform(-50, 50), 2),
                "change_percent": round(random.uniform(-2, 2), 2),
                "volume": random.randint(100000000, 500000000),
                "turnover": round(random.uniform(200, 400), 2),
                "high": round(3000 + random.uniform(0, 50), 2),
                "low": round(3000 - random.uniform(0, 50), 2),
                "open": round(3000 + random.uniform(-20, 20), 2),
                "prev_close": 3000.0
            },
            {
                "code": "399001",
                "name": "深证成指",
                "current_price": round(10000 + random.uniform(-500, 500), 2),
                "change": round(random.uniform(-100, 100), 2),
                "change_percent": round(random.uniform(-2, 2), 2),
                "volume": random.randint(80000000, 300000000),
                "turnover": round(random.uniform(150, 300), 2),
                "high": round(10000 + random.uniform(0, 200), 2),
                "low": round(10000 - random.uniform(0, 200), 2),
                "open": round(10000 + random.uniform(-100, 100), 2),
                "prev_close": 10000.0
            },
            {
                "code": "399006",
                "name": "创业板指",
                "current_price": round(2000 + random.uniform(-100, 100), 2),
                "change": round(random.uniform(-30, 30), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": random.randint(50000000, 200000000),
                "turnover": round(random.uniform(100, 250), 2),
                "high": round(2000 + random.uniform(0, 50), 2),
                "low": round(2000 - random.uniform(0, 50), 2),
                "open": round(2000 + random.uniform(-20, 20), 2),
                "prev_close": 2000.0
            },
            {
                "code": "000300",
                "name": "沪深300",
                "current_price": round(4000 + random.uniform(-200, 200), 2),
                "change": round(random.uniform(-80, 80), 2),
                "change_percent": round(random.uniform(-2.5, 2.5), 2),
                "volume": random.randint(60000000, 250000000),
                "turnover": round(random.uniform(120, 280), 2),
                "high": round(4000 + random.uniform(0, 100), 2),
                "low": round(4000 - random.uniform(0, 100), 2),
                "open": round(4000 + random.uniform(-50, 50), 2),
                "prev_close": 4000.0
            },
            {
                "code": "000905",
                "name": "中证500",
                "current_price": round(6000 + random.uniform(-300, 300), 2),
                "change": round(random.uniform(-120, 120), 2),
                "change_percent": round(random.uniform(-2.8, 2.8), 2),
                "volume": random.randint(40000000, 180000000),
                "turnover": round(random.uniform(80, 200), 2),
                "high": round(6000 + random.uniform(0, 150), 2),
                "low": round(6000 - random.uniform(0, 150), 2),
                "open": round(6000 + random.uniform(-80, 80), 2),
                "prev_close": 6000.0
            },
            {
                "code": "000016",
                "name": "上证50",
                "current_price": round(2500 + random.uniform(-100, 100), 2),
                "change": round(random.uniform(-40, 40), 2),
                "change_percent": round(random.uniform(-2, 2), 2),
                "volume": random.randint(30000000, 120000000),
                "turnover": round(random.uniform(60, 150), 2),
                "high": round(2500 + random.uniform(0, 50), 2),
                "low": round(2500 - random.uniform(0, 50), 2),
                "open": round(2500 + random.uniform(-25, 25), 2),
                "prev_close": 2500.0
            }
        ]
        
        response = {
            "success": True,
            "data": indices,
            "timestamp": datetime.now().isoformat(),
            "message": "获取指数数据成功"
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_health(self):
        """健康检查"""
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "股票指数API"
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_404(self):
        """404处理"""
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "success": False,
            "message": "API端点不存在",
            "timestamp": datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def start_api_server(port=8080):
    """启动API服务器"""
    server = HTTPServer(('localhost', port), StockAPIHandler)
    print(f"🚀 股票指数API服务器启动在 http://localhost:{port}")
    print(f"📊 指数数据API: http://localhost:{port}/api/v1/market/indices")
    print(f"💚 健康检查: http://localhost:{port}/health")
    print("按 Ctrl+C 停止服务器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 正在停止API服务器...")
        server.shutdown()
        print("✅ API服务器已停止")

if __name__ == "__main__":
    start_api_server()