#!/bin/bash

# 股票交易系统Docker一键部署脚本
# 执行后所有服务自动启动，无需其他操作

set -e

echo "🐳 股票交易系统Docker一键部署开始..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"

# 配置环境变量
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📋 已创建.env文件"
fi

# 创建必要目录
mkdir -p nginx logs uploads

# 生成Nginx配置
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8080;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
EOF

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down --remove-orphans || true

# 构建并启动服务
echo "🚀 构建并启动服务..."
docker-compose up -d --build

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 10

# 初始化数据库
echo "🗄️ 初始化数据库..."
docker-compose exec -T postgres psql -U postgres -d stock_db -f /docker-entrypoint-initdb.d/init.sql || echo "⚠️ 数据库可能已初始化"

echo ""
echo "🎉 Docker部署完成！"
echo ""
echo "📖 服务访问地址:"
echo "   应用首页: http://localhost"
echo "   API文档: http://localhost/docs"
echo "   直接API: http://localhost:8080/docs"
echo ""
echo "🔧 管理命令:"
echo "   查看状态: docker-compose ps"
echo "   查看日志: docker-compose logs -f backend"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"