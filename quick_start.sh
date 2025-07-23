#!/bin/bash

# 简化的开发环境启动脚本

echo "🚀 启动股票交易系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查并安装基础依赖
echo "📚 检查依赖..."
python -c "import fastapi" 2>/dev/null || {
    echo "🔧 安装FastAPI..."
    pip install fastapi uvicorn[standard]
}

python -c "import sqlalchemy" 2>/dev/null || {
    echo "🗄️ 安装SQLAlchemy..."
    pip install sqlalchemy
}

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    cat > .env << 'EOF'
APP_NAME=股票交易系统
DEBUG=true
HOST=0.0.0.0
BACKEND_PORT=8080
FRONTEND_PORT=3000
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./stock.db
REDIS_URL=redis://localhost:6379/0
EOF
fi

echo "✅ 环境准备完成！"
echo ""
echo "🔧 后端服务将在: http://localhost:8080"
echo "🌐 前端页面将在: http://localhost:3000"
echo "📚 API文档将在: http://localhost:8080/docs"
echo ""
echo "请在两个终端窗口中分别运行："
echo "1. 后端: source venv/bin/activate && python -m uvicorn app.main:app --reload --port 8080"
echo "2. 前端: cd frontend && python3 -m http.server 3000"