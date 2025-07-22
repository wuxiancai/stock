#!/bin/bash

# 股票交易系统一键部署脚本
# 执行后可直接运行: python3 main.py

set -e

echo "🚀 股票交易系统一键部署开始..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "当前Python版本: $python_version"

if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
    echo "❌ 需要Python 3.8+，当前: $python_version"
    exit 1
fi

# 创建并激活虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 升级pip并安装依赖
echo "📦 安装依赖..."
pip install --upgrade pip setuptools wheel

# 使用requirements.txt安装所有依赖
echo "📚 从requirements.txt安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt文件不存在"
    exit 1
fi

# 创建必要目录
mkdir -p logs uploads

# 配置环境变量
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📋 已创建.env文件，请根据需要修改配置"
fi

# 数据库服务检查和启动
echo "🗄️ 检查数据库服务..."

# 检查PostgreSQL
if ! pgrep -x "postgres" > /dev/null; then
    echo "⚠️ PostgreSQL未运行，尝试启动..."
    
    # macOS使用brew启动
    if command -v brew &> /dev/null; then
        if brew services list | grep postgresql | grep started > /dev/null; then
            echo "✅ PostgreSQL已通过brew启动"
        else
            brew services start postgresql || {
                echo "❌ 无法启动PostgreSQL，请手动启动:"
                echo "   brew services start postgresql"
                echo "   或者使用Docker: bash start_docker.sh"
            }
        fi
    # Linux使用systemctl启动
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql || {
            echo "❌ 无法启动PostgreSQL，请手动启动:"
            echo "   sudo systemctl start postgresql"
            echo "   或者使用Docker: bash start_docker.sh"
        }
    else
        echo "⚠️ 请手动启动PostgreSQL服务"
        echo "💡 建议使用Docker部署: bash start_docker.sh"
    fi
else
    echo "✅ PostgreSQL正在运行"
fi

# 检查Redis
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️ Redis未运行，尝试启动..."
    
    # macOS使用brew启动
    if command -v brew &> /dev/null; then
        if brew services list | grep redis | grep started > /dev/null; then
            echo "✅ Redis已通过brew启动"
        else
            brew services start redis || {
                echo "❌ 无法启动Redis，请手动启动:"
                echo "   brew services start redis"
                echo "   或者使用Docker: bash start_docker.sh"
            }
        fi
    # Linux使用systemctl启动
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start redis || {
            echo "❌ 无法启动Redis，请手动启动:"
            echo "   sudo systemctl start redis"
            echo "   或者使用Docker: bash start_docker.sh"
        }
    else
        echo "⚠️ 请手动启动Redis服务"
        echo "💡 建议使用Docker部署: bash start_docker.sh"
    fi
else
    echo "✅ Redis正在运行"
fi

# 等待数据库服务完全启动
echo "⏳ 等待数据库服务完全启动..."
sleep 3

# 检查核心模块
echo "🔍 检查核心模块..."
python3 -c "
modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'pydantic', 'pandas', 'numpy', 'tushare']
failed = []
for m in modules:
    try:
        __import__(m)
        print(f'✅ {m}')
    except:
        print(f'❌ {m}')
        failed.append(m)

# 特别检查 pydantic_settings
try:
    import pydantic_settings
    print('✅ pydantic_settings')
except:
    print('❌ pydantic_settings - 正在安装...')
    import subprocess
    subprocess.run(['pip', 'install', 'pydantic-settings>=2.0.0'], check=True)
    print('✅ pydantic_settings 安装完成')
        
if failed:
    print(f'\\n⚠️ 模块导入失败: {failed}')
    print('请检查依赖安装')
else:
    print('\\n🎉 所有核心模块正常')
"

echo ""
echo "🔗 测试数据库连接..."
python3 -c "
import sys
import os
sys.path.append('.')

try:
    # 测试PostgreSQL连接
    import psycopg2
    from app.core.config import settings
    
    # 从.env文件读取配置
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    db_url = os.getenv('DATABASE_URL', 'postgresql://stock_user:stock_password@localhost:5432/stock_db')
    # 解析数据库URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if match:
        user, password, host, port, dbname = match.groups()
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        conn.close()
        print('✅ PostgreSQL连接成功')
    else:
        print('⚠️ 无法解析数据库URL')
except Exception as e:
    print(f'❌ PostgreSQL连接失败: {e}')
    print('💡 请检查数据库配置或使用Docker部署')

try:
    # 测试Redis连接
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url)
    r.ping()
    print('✅ Redis连接成功')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
    print('💡 请检查Redis配置或使用Docker部署')
"

echo ""
echo "✅ 部署完成！"
echo ""
echo "🚀 启动应用:"
echo "   python3 main.py"
echo ""
echo "📖 访问地址:"
echo "   API文档: http://localhost:8080/docs"
echo "   应用首页: http://localhost:8080"
echo ""
echo "💡 提示:"
echo "   - 数据库服务已自动检查和启动"
echo "   - 如果数据库连接失败，建议使用Docker部署"
echo "   - Docker部署: bash start_docker.sh"
echo "   - 根据需要修改.env文件中的配置"