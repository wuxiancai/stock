#!/bin/bash

# 股票交易系统 - macOS 虚拟环境设置脚本
# 此脚本将创建Python虚拟环境并安装所有必要的依赖

set -e  # 遇到错误时退出

echo "🚀 开始设置股票交易系统开发环境..."
echo "📍 当前目录: $(pwd)"

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    echo "💡 建议使用 Homebrew 安装: brew install python@3.11"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查pip是否可用
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip 不可用，请检查Python安装"
    exit 1
fi

echo "✅ pip 已安装: $(python3 -m pip --version)"

# 创建虚拟环境目录
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "⚠️  虚拟环境目录已存在，是否删除重建？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  删除现有虚拟环境..."
        rm -rf "$VENV_DIR"
    else
        echo "📦 使用现有虚拟环境..."
    fi
fi

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
echo "⬆️  升级pip..."
python -m pip install --upgrade pip

# 安装wheel和setuptools
echo "🛠️  安装基础工具..."
python -m pip install wheel setuptools

# 检查requirements.txt是否存在
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 安装项目依赖
echo "📚 安装项目依赖..."
echo "📄 从 requirements.txt 安装依赖包..."

# 分批安装依赖，避免某些包安装失败影响整体
echo "🔧 安装核心Web框架..."
python -m pip install fastapi>=0.100.0 uvicorn[standard]>=0.20.0

echo "🗄️  安装数据库相关..."
python -m pip install sqlalchemy>=2.0.0 alembic>=1.12.0 psycopg2-binary>=2.9.0 asyncpg>=0.28.0

echo "⚡ 安装缓存相关..."
python -m pip install redis>=4.5.0 aioredis>=2.0.0

echo "✅ 安装数据验证..."
python -m pip install "pydantic[email]>=2.0.0" pydantic-settings>=2.0.0

echo "🔐 安装认证相关..."
python -m pip install "passlib[bcrypt]>=1.7.0" PyJWT>=2.8.0

echo "🌐 安装HTTP客户端..."
python -m pip install httpx>=0.24.0 aiohttp>=3.8.0 requests>=2.28.0

echo "📁 安装文件处理..."
python -m pip install python-multipart>=0.0.6 aiofiles>=23.0.0

echo "📊 安装数据分析..."
python -m pip install pandas>=2.0.0 numpy>=1.24.0

echo "⚙️  安装配置和工具..."
python -m pip install python-dotenv>=1.0.0 loguru>=0.7.0 APScheduler>=3.10.0

echo "📈 安装数据源..."
python -m pip install tushare>=1.2.0 akshare>=1.17.0

echo "🔧 安装其他工具..."
python -m pip install python-dateutil>=2.8.0 websockets>=11.0.0 psutil>=5.9.0

echo "✅ 所有依赖安装完成！"

# 验证关键包是否安装成功
echo "🔍 验证关键包安装..."
python -c "import fastapi; print(f'✅ FastAPI: {fastapi.__version__}')" || echo "❌ FastAPI 安装失败"
python -c "import uvicorn; print(f'✅ Uvicorn: {uvicorn.__version__}')" || echo "❌ Uvicorn 安装失败"
python -c "import sqlalchemy; print(f'✅ SQLAlchemy: {sqlalchemy.__version__}')" || echo "❌ SQLAlchemy 安装失败"
python -c "import pandas; print(f'✅ Pandas: {pandas.__version__}')" || echo "❌ Pandas 安装失败"

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# 应用配置
APP_NAME=股票交易系统
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
BACKEND_PORT=8080
FRONTEND_PORT=3000

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stock_db
DB_USER=stock_user
DB_PASSWORD=stock_password
DATABASE_URL=postgresql://stock_user:stock_password@localhost:5432/stock_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 数据源配置
TUSHARE_TOKEN=your-tushare-token-here
AKSHARE_TIMEOUT=30

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080
EOF
    echo "✅ 环境变量文件创建完成"
fi

# 创建日志目录
mkdir -p logs

# 创建启动脚本
echo "📝 创建启动脚本..."
cat > start_dev.sh << 'EOF'
#!/bin/bash

# 开发环境启动脚本

echo "🚀 启动股票交易系统开发环境..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行 ./setup_env.sh"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    exit 1
fi

# 启动后端服务
echo "🔧 启动后端API服务器..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务
echo "🌐 启动前端开发服务器..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ 服务启动完成！"
echo "🔧 后端API: http://localhost:8080"
echo "🌐 前端页面: http://localhost:3000"
echo "📚 API文档: http://localhost:8080/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ 所有服务已停止'; exit 0" INT

wait
EOF

chmod +x start_dev.sh

# 创建快速测试脚本
cat > test_env.sh << 'EOF'
#!/bin/bash

# 环境测试脚本

echo "🧪 测试开发环境..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 测试Python包导入
echo "📦 测试关键包导入..."
python -c "
import sys
print(f'Python版本: {sys.version}')

try:
    import fastapi
    print('✅ FastAPI 可用')
except ImportError:
    print('❌ FastAPI 不可用')

try:
    import uvicorn
    print('✅ Uvicorn 可用')
except ImportError:
    print('❌ Uvicorn 不可用')

try:
    import sqlalchemy
    print('✅ SQLAlchemy 可用')
except ImportError:
    print('❌ SQLAlchemy 不可用')

try:
    import pandas
    print('✅ Pandas 可用')
except ImportError:
    print('❌ Pandas 不可用')

try:
    import redis
    print('✅ Redis 可用')
except ImportError:
    print('❌ Redis 不可用')
"

echo "🔍 测试应用导入..."
python -c "
try:
    from app.main import app
    print('✅ 应用主模块可用')
except ImportError as e:
    print(f'❌ 应用主模块导入失败: {e}')

try:
    from app.core.config import settings
    print('✅ 配置模块可用')
except ImportError as e:
    print(f'❌ 配置模块导入失败: {e}')
"

echo "✅ 环境测试完成"
EOF

chmod +x test_env.sh

echo ""
echo "🎉 开发环境设置完成！"
echo ""
echo "📋 接下来的步骤："
echo "1. 运行测试: ./test_env.sh"
echo "2. 启动开发服务: ./start_dev.sh"
echo "3. 访问前端: http://localhost:3000"
echo "4. 访问API文档: http://localhost:8080/docs"
echo ""
echo "💡 提示："
echo "- 虚拟环境位置: ./venv"
echo "- 手动激活虚拟环境: source venv/bin/activate"
echo "- 退出虚拟环境: deactivate"
echo ""
echo "🔧 如需重新设置环境，删除 venv 目录后重新运行此脚本"