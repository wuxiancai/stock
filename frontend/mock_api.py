#!/usr/bin/env python3
"""
简单的模拟API服务器，用于演示前端页面
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import random

# 模拟的A股指数数据
MOCK_INDICES = [
    {
        "name": "上证指数",
        "ts_code": "000001.SH",
        "current_price": 3245.67,
        "change": 15.23,
        "change_percent": 0.47,
        "open": 3230.44,
        "high": 3250.89,
        "low": 3225.12,
        "pre_close": 3230.44,
        "volume": 245678900,
        "amount": 298765432100
    },
    {
        "name": "深证成指",
        "ts_code": "399001.SZ",
        "current_price": 10567.89,
        "change": -23.45,
        "change_percent": -0.22,
        "open": 10591.34,
        "high": 10598.76,
        "low": 10545.23,
        "pre_close": 10591.34,
        "volume": 189234567,
        "amount": 234567890123
    },
    {
        "name": "创业板指",
        "ts_code": "399006.SZ",
        "current_price": 2234.56,
        "change": 8.91,
        "change_percent": 0.40,
        "open": 2225.65,
        "high": 2238.90,
        "low": 2220.34,
        "pre_close": 2225.65,
        "volume": 156789012,
        "amount": 187654321098
    },
    {
        "name": "科创50",
        "ts_code": "000688.SH",
        "current_price": 1123.45,
        "change": -5.67,
        "change_percent": -0.50,
        "open": 1129.12,
        "high": 1132.89,
        "low": 1118.90,
        "pre_close": 1129.12,
        "volume": 98765432,
        "amount": 123456789012
    },
    {
        "name": "中证500",
        "ts_code": "000905.SH",
        "current_price": 6789.12,
        "change": 12.34,
        "change_percent": 0.18,
        "open": 6776.78,
        "high": 6795.67,
        "low": 6770.45,
        "pre_close": 6776.78,
        "volume": 134567890,
        "amount": 167890123456
    },
    {
        "name": "沪深300",
        "ts_code": "000300.SH",
        "current_price": 4567.89,
        "change": -8.90,
        "change_percent": -0.19,
        "open": 4576.79,
        "high": 4580.12,
        "low": 4560.34,
        "pre_close": 4576.79,
        "volume": 178901234,
        "amount": 201234567890
    }
]

class MockAPIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 处理API路由
        if parsed_path.path == '/api/v1/market/indices':
            # 添加一些随机波动来模拟实时数据
            mock_data = []
            for index in MOCK_INDICES:
                # 复制数据并添加小幅随机波动
                index_copy = index.copy()
                
                # 随机波动 -1% 到 +1%
                volatility = random.uniform(-0.01, 0.01)
                base_price = index['current_price']
                
                index_copy['current_price'] = round(base_price * (1 + volatility), 2)
                index_copy['change'] = round(index_copy['current_price'] - index['pre_close'], 2)
                index_copy['change_percent'] = round((index_copy['change'] / index['pre_close']) * 100, 2)
                
                mock_data.append(index_copy)
            
            response = json.dumps(mock_data, ensure_ascii=False, indent=2)
            self.wfile.write(response.encode('utf-8'))
        
        elif parsed_path.path == '/':
            # 返回API信息
            response = json.dumps({
                "message": "股票交易系统模拟API",
                "version": "1.0.0",
                "endpoints": [
                    "/api/v1/market/indices"
                ],
                "status": "running"
            }, ensure_ascii=False, indent=2)
            self.wfile.write(response.encode('utf-8'))
        
        else:
            # 404
            self.send_response(404)
            self.end_headers()
            response = json.dumps({"error": "Not Found"}, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    PORT = 8080
    
    with socketserver.TCPServer(("", PORT), MockAPIHandler) as httpd:
        print(f"🚀 模拟API服务器启动在端口 {PORT}")
        print(f"📊 指数数据API: http://localhost:{PORT}/api/v1/market/indices")
        print("按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")
            httpd.shutdown()