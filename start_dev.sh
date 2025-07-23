#!/bin/bash
# 开发环境启动脚本

set -e

echo "🚀 启动股票交易系统开发环境..."

# 激活虚拟环境
source venv/bin/activate

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查 PostgreSQL
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "🔄 启动 PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# 检查 Redis
if ! redis-cli ping &> /dev/null; then
    echo "🔄 启动 Redis..."
    brew services start redis
    sleep 2
fi

echo "✅ 所有服务已就绪"

# 运行数据库迁移
echo "🗄️ 运行数据库迁移..."
python -m alembic upgrade head

# 启动后端服务
echo "🚀 启动后端服务..."
python main.py
