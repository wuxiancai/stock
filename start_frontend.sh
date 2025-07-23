#!/bin/bash

# 股票交易系统前端启动脚本

echo "🚀 启动股票交易系统前端..."

# 检查前端目录
if [ ! -d "frontend" ]; then
    echo "❌ 前端目录不存在"
    exit 1
fi

cd frontend

echo "📊 启动模拟API服务器 (端口 8080)..."
python3 mock_api.py &
API_PID=$!

# 等待API服务器启动
sleep 2

echo "🌐 启动前端HTTP服务器 (端口 3001)..."
python3 -m http.server 3001 &
WEB_PID=$!

# 等待服务器启动
sleep 2

echo ""
echo "✅ 服务启动完成！"
echo "📊 API服务器: http://localhost:8080"
echo "🌐 前端页面: http://localhost:3001"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $API_PID $WEB_PID 2>/dev/null; echo '✅ 所有服务已停止'; exit 0" INT

# 保持脚本运行
wait