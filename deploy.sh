#!/bin/bash

# 股票交易系统后端部署脚本

set -e

echo "🚀 开始部署股票交易系统后端..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本需要 >= 3.8，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装Python依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p uploads
mkdir -p data

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f "../.env.example" ]; then
        echo "📋 复制环境变量配置文件..."
        cp ../.env.example .env
        echo "⚠️ 请编辑 .env 文件配置正确的环境变量"
    else
        echo "❌ 未找到环境变量配置文件"
        exit 1
    fi
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv('DATABASE_URL')
if not database_url or 'your' in database_url.lower():
    print('❌ 请在 .env 文件中配置正确的数据库连接')
    exit(1)
print('✅ 数据库配置检查通过')
"

# 初始化数据库
echo "🗄️ 初始化数据库..."
python3 -c "
try:
    from app.database.init_db import init_database
    init_database()
    print('✅ 数据库初始化完成')
except Exception as e:
    print(f'❌ 数据库初始化失败: {e}')
    exit(1)
"

echo "🎉 后端部署完成！"
echo ""
echo "启动命令:"
echo "  开发模式: python3 start.py"
echo "  生产模式: python3 main.py"
echo ""
echo "API文档地址:"
echo "  Swagger UI: http://localhost:8000/docs"
echo "  ReDoc: http://localhost:8000/redoc"