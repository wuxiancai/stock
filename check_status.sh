#!/bin/bash
# 集成的系统状态检查脚本

echo "🔍 股票交易系统状态检查"
echo "=========================="

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 检查 Python 版本
echo ""
echo "🐍 Python 环境："
python --version
echo "虚拟环境路径: $(which python)"

# 检查核心依赖
echo ""
echo "📦 核心依赖检查："
python -c "
import sys
dependencies = {
    'psycopg2': 'PostgreSQL 数据库连接',
    'fastapi': 'Web 框架',
    'uvicorn': 'ASGI 服务器',
    'sqlalchemy': 'ORM 框架',
    'redis': 'Redis 客户端',
    'alembic': '数据库迁移工具'
}

for dep, desc in dependencies.items():
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', '未知版本')
        print(f'✅ {dep} ({desc}): {version}')
    except ImportError:
        print(f'❌ {dep} ({desc}): 未安装')
"

# 检查数据库连接
echo ""
echo "🗄️ 数据库连接检查："
python -c "
import psycopg2
from psycopg2 import OperationalError

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='stock_trading_db',
        user='stock_user',
        password='stock_password'
    )
    conn.close()
    print('✅ PostgreSQL 数据库连接成功')
except OperationalError as e:
    if 'role \"stock_user\" does not exist' in str(e):
        print('⚠️ 数据库用户不存在，请运行完整安装')
    elif 'database \"stock_trading_db\" does not exist' in str(e):
        print('⚠️ 数据库不存在，请运行完整安装')
    else:
        print(f'❌ 数据库连接失败: {e}')
except Exception as e:
    print(f'❌ 数据库连接错误: {e}')
"

# 检查 Redis 连接
echo ""
echo "🔴 Redis 连接检查："
python -c "
import redis

try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis 连接成功')
except Exception as e:
    print(f'❌ Redis 连接失败: {e}')
"

# 检查服务状态
echo ""
echo "🔧 系统服务状态："

# 检查 PostgreSQL
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "✅ PostgreSQL 服务运行中"
else
    echo "❌ PostgreSQL 服务未运行"
fi

# 检查 Redis
if redis-cli ping &> /dev/null; then
    echo "✅ Redis 服务运行中"
else
    echo "❌ Redis 服务未运行"
fi

# 检查端口占用
echo ""
echo "🌐 端口状态检查："
if lsof -i :8080 &> /dev/null; then
    echo "⚠️ 端口 8080 已被占用"
    lsof -i :8080
else
    echo "✅ 端口 8080 可用"
fi

# 检查环境变量
echo ""
echo "🔧 环境变量检查："
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    if grep -q "TUSHARE_TOKEN" .env && ! grep -q "your_tushare_token_here" .env; then
        echo "✅ TUSHARE_TOKEN 已配置"
    else
        echo "⚠️ TUSHARE_TOKEN 需要配置"
    fi
else
    echo "❌ .env 文件不存在"
fi

echo ""
echo "📋 状态检查完成"
echo "=========================="
