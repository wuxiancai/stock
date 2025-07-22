#!/bin/bash

# 一键部署脚本 - 包含完整的数据库初始化

set -e  # 遇到错误立即退出

echo "🚀 开始一键部署股票交易系统..."

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

# 安装psycopg2依赖
echo "🔧 安装数据库驱动..."
pip install psycopg2-binary

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

# 检查PostgreSQL服务
echo "🗄️ 检查PostgreSQL服务..."

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL客户端未安装"
    echo "💡 安装方法:"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql-client"
    echo "   或使用Docker: bash start_docker.sh"
    exit 1
fi

if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL服务未运行，尝试启动..."
    
    # macOS使用brew启动
    if command -v brew &> /dev/null; then
        if brew services list | grep postgresql | grep started > /dev/null; then
            echo "✅ PostgreSQL已通过brew启动"
        else
            echo "🔧 启动PostgreSQL..."
            brew services start postgresql
            sleep 3
        fi
    # Linux使用systemctl启动
    elif command -v systemctl &> /dev/null; then
        echo "🔧 启动PostgreSQL..."
        sudo systemctl start postgresql
        sleep 3
    else
        echo "❌ 无法自动启动PostgreSQL"
        echo "💡 请手动启动PostgreSQL或使用Docker部署"
        echo "   Docker部署: bash start_docker.sh"
        exit 1
    fi
fi

# 检查PostgreSQL是否成功启动
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL服务正在运行"
else
    echo "❌ PostgreSQL服务启动失败"
    echo "💡 建议使用Docker部署: bash start_docker.sh"
    exit 1
fi

# 初始化数据库
echo "🗄️ 初始化数据库..."
chmod +x init_database.sh
./init_database.sh

if [ $? -ne 0 ]; then
    echo "❌ 数据库初始化失败"
    exit 1
fi

# 检查Redis
echo "🔧 检查Redis服务..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️ Redis客户端未安装，尝试安装..."
    if command -v brew &> /dev/null; then
        brew install redis
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y redis-tools redis-server
    else
        echo "⚠️ 请手动安装Redis"
    fi
fi

if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️ Redis未运行，尝试启动..."
    
    # macOS使用brew启动
    if command -v brew &> /dev/null; then
        brew services start redis
    # Linux使用systemctl启动
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start redis
    else
        echo "⚠️ 请手动启动Redis服务"
    fi
    
    sleep 2
fi

# 检查Redis连接
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis服务正在运行"
else
    echo "⚠️ Redis服务未运行，应用程序可能无法正常工作"
fi

# 检查核心模块
echo "🔍 检查核心模块..."
python3 -c "
modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2', 'pydantic', 'pandas', 'numpy']
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
    exit(1)
else:
    print('\\n🎉 所有核心模块正常')
"

# 最终测试
echo "🔗 最终测试..."
python3 -c "
import sys
sys.path.append('.')

try:
    from app.core.config import settings
    print(f'✅ 配置加载成功')
    print(f'   数据库URL: {settings.DATABASE_URL}')
    
    from app.database.database import test_connection
    import asyncio
    
    async def test():
        result = await test_connection()
        if result:
            print('✅ 数据库连接测试成功')
        else:
            print('❌ 数据库连接测试失败')
            return False
        return True
    
    if not asyncio.run(test()):
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 测试失败: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "🚀 启动应用:"
    echo "   python3 main.py"
    echo ""
    echo "📖 访问地址:"
    echo "   API文档: http://localhost:8080/docs"
    echo "   应用首页: http://localhost:8080"
    echo ""
    echo "💡 提示:"
    echo "   - 数据库已初始化完成"
    echo "   - 如需重置数据库，运行: ./init_database.sh"
    echo "   - 根据需要修改.env文件中的配置"
    echo "   - 如果使用Tushare，请在.env中设置TUSHARE_TOKEN"
else
    echo "❌ 部署失败，请检查错误信息"
    exit 1
fi