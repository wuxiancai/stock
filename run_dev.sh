#!/bin/bash

# 股票交易系统 - 快速启动脚本
# 使用Python内置服务器，无需额外依赖

echo "🚀 启动股票交易系统..."

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查前端目录
if [ ! -d "frontend" ]; then
    echo "❌ frontend 目录不存在"
    exit 1
fi

# 检查前端文件
if [ ! -f "frontend/index.html" ]; then
    echo "❌ frontend/index.html 不存在"
    exit 1
fi

# 检查API服务器文件
if [ ! -f "simple_api.py" ]; then
    echo "❌ simple_api.py 不存在"
    exit 1
fi

echo "📁 检查文件完成"

# 启动后端API服务器
echo "🔧 启动后端API服务器..."
python3 simple_api.py &
API_PID=$!

# 等待API服务器启动
sleep 2

# 启动前端服务器
echo "🌐 启动前端服务器..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "🔧 后端API: http://localhost:8080"
echo "📊 指数数据: http://localhost:8080/api/v1/market/indices"
echo "🌐 前端页面: http://localhost:3000"
echo ""
echo "🎯 请在浏览器中访问: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获中断信号
trap "echo ''; echo '🛑 正在停止服务...'; kill $API_PID $FRONTEND_PID 2>/dev/null; echo '✅ 所有服务已停止'; exit 0" INT

# 等待用户中断
wait