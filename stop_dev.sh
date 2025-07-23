#!/bin/bash
# 开发环境停止脚本

echo "🛑 停止股票交易系统开发环境..."

# 停止后端进程
pkill -f "python main.py" 2>/dev/null || echo "后端服务未运行"
pkill -f "uvicorn" 2>/dev/null || echo "Uvicorn 未运行"
pkill -f "celery" 2>/dev/null || echo "Celery 未运行"

echo "✅ 开发环境已停止"
