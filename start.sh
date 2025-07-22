#!/bin/bash

# 股票交易系统快速启动脚本

set -e

echo "🚀 股票交易系统快速启动"
echo "========================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 复制环境变量配置文件..."
        cp .env.example .env
        echo "⚠️ 请编辑 .env 文件配置正确的环境变量"
        echo "📝 特别注意配置数据源API Token（如Tushare）"
    else
        echo "❌ 未找到环境变量配置文件"
        exit 1
    fi
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p nginx

# 创建Nginx配置（如果不存在）
if [ ! -f "nginx/nginx.conf" ]; then
    echo "🔧 创建Nginx配置..."
    mkdir -p nginx
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /redoc {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            return 404;
        }
    }
}
EOF
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
until docker-compose exec postgres pg_isready -U stock_user -d stock_db; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

echo "✅ 数据库已就绪"

# 初始化数据库
echo "🗄️ 初始化数据库..."
docker-compose exec backend python -c "
try:
    from app.database.init_db import init_database
    init_database()
    print('✅ 数据库初始化完成')
except Exception as e:
    print(f'❌ 数据库初始化失败: {e}')
"

echo ""
echo "🎉 股票交易系统启动完成！"
echo ""
echo "📍 服务地址:"
echo "  - API服务: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - ReDoc文档: http://localhost:8000/redoc"
echo ""
echo "🔧 管理命令:"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo "  - 重启服务: docker-compose restart"
echo ""
echo "📊 默认管理员账户:"
echo "  - 用户名: admin"
echo "  - 密码: admin123"
echo ""
echo "⚠️ 注意事项:"
echo "  1. 请在 .env 文件中配置正确的数据源API Token"
echo "  2. 生产环境请修改默认密码和密钥"
echo "  3. 确保防火墙允许相应端口访问"