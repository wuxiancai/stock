#!/bin/bash

# 股票交易系统 - Ubuntu 系统快速部署脚本
# 专门为Ubuntu系统优化的一键部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为Ubuntu系统
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    log_warning "此脚本专为Ubuntu系统优化，其他系统可能需要调整"
fi

# 获取当前目录和用户
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

log_info "🚀 Ubuntu系统股票交易系统快速部署..."
log_info "部署目录: $CURRENT_DIR"
log_info "运行用户: $CURRENT_USER"

# 1. 更新系统包
log_info "更新系统包..."
sudo apt-get update

# 2. 安装必要的系统依赖
log_info "安装系统依赖..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    build-essential \
    libpq-dev \
    libta-lib-dev \
    pkg-config \
    curl \
    git \
    wget

# 3. 创建虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 4. 激活虚拟环境并修复依赖问题
log_info "激活虚拟环境并处理依赖..."
source venv/bin/activate
pip install --upgrade pip

# 清理可能有问题的包
log_info "清理可能冲突的包..."
pip uninstall -y talib-binary talib TA-Lib 2>/dev/null || true

# 安装TA-Lib（技术分析库）
log_info "安装TA-Lib技术分析库..."
if ! pip install TA-Lib; then
    log_warning "pip安装TA-Lib失败，尝试从源码编译..."
    # 尝试从源码编译安装
    cd /tmp
    if [ ! -f "ta-lib-0.4.0-src.tar.gz" ]; then
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    fi
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
    sudo ldconfig  # 更新库路径
    cd $CURRENT_DIR
    pip install TA-Lib
fi

# 创建Ubuntu专用requirements文件（如果不存在）
if [ ! -f "requirements.ubuntu.txt" ]; then
    log_info "创建Ubuntu专用依赖文件..."
    cat > requirements.ubuntu.txt << 'EOF'
# Ubuntu系统专用依赖文件
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg2-binary
asyncpg
redis
aioredis
celery
flower
pandas
numpy
tushare
akshare
httpx
aiohttp
requests
python-dotenv
python-multipart
python-jose[cryptography]
passlib[bcrypt]
email-validator
loguru
prometheus-client
pytest
pytest-asyncio
pytest-cov
black
isort
flake8
mypy
websockets
python-socketio
pytz
python-dateutil
marshmallow
dynaconf
cryptography
bcrypt
click
rich
typer
gunicorn
EOF
fi

# 安装Python依赖
log_info "安装Python依赖..."
pip install -r requirements.ubuntu.txt

# 验证关键包安装
log_info "验证关键包安装..."
python3 -c "
import sys
failed = []
success = []

packages = [
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('fastapi', 'fastapi'),
    ('sqlalchemy', 'sqlalchemy'),
    ('redis', 'redis'),
    ('tushare', 'tushare'),
    ('akshare', 'akshare'),
    ('talib', 'TA-Lib')
]

for module, name in packages:
    try:
        __import__(module)
        success.append(name)
    except ImportError:
        failed.append(name)

print('✅ 成功安装:', ', '.join(success))
if failed:
    print('⚠️ 可选包未安装:', ', '.join(failed))
"

# 5. 配置PostgreSQL
log_info "配置PostgreSQL数据库..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库用户和数据库
sudo -u postgres psql << 'PSQL_EOF'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'stock_user') THEN
        CREATE USER stock_user WITH PASSWORD 'stock_password';
    END IF;
END
$$;

SELECT 'User stock_user created or already exists';

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stock_trading_db') THEN
        CREATE DATABASE stock_trading_db OWNER stock_user;
    END IF;
END
$$;

SELECT 'Database stock_trading_db created or already exists';

GRANT ALL PRIVILEGES ON DATABASE stock_trading_db TO stock_user;
PSQL_EOF

# 6. 配置Redis
log_info "配置Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 7. 创建配置文件
if [ ! -f ".env" ]; then
    log_info "创建环境配置文件..."
    cp .env.example .env
    
    # 更新配置文件
    sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env
    sed -i 's/DEBUG=true/DEBUG=false/' .env
    
    log_warning "请编辑 .env 文件设置正确的API密钥和其他配置"
fi

# 8. 创建Gunicorn配置
if [ ! -f "gunicorn.conf.py" ]; then
    log_info "创建Gunicorn配置文件..."
    cat > gunicorn.conf.py << 'EOF'
import multiprocessing
import os

# 服务器套接字
bind = "0.0.0.0:8080"
backlog = 2048

# 工作进程
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 超时设置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "stock-trading-api"

# 安全
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 重启设置
max_requests = 1000
max_requests_jitter = 100

# 环境变量
raw_env = [
    'ENVIRONMENT=production',
]
EOF
fi

# 9. 创建日志目录
mkdir -p logs
chmod 755 logs

# 10. 运行数据库迁移
log_info "运行数据库迁移..."
source venv/bin/activate
alembic upgrade head

# 11. 创建Supervisor配置
log_info "配置Supervisor进程管理..."
sudo tee /etc/supervisor/conf.d/stock-trading.conf > /dev/null << EOF
[program:stock-api]
command=$CURRENT_DIR/venv/bin/gunicorn main:app -c $CURRENT_DIR/gunicorn.conf.py
directory=$CURRENT_DIR
user=$CURRENT_USER
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=$CURRENT_DIR/logs/supervisor-api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=ENVIRONMENT="production",PYTHONPATH="$CURRENT_DIR"
EOF

# 12. 配置Nginx
log_info "配置Nginx反向代理..."
sudo tee /etc/nginx/sites-available/stock-trading > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # API 代理
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 特殊设置
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8080;
        access_log off;
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/stock-trading /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
sudo nginx -t

# 13. 启动所有服务
log_info "启动所有服务..."

# 重新加载Supervisor配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo systemctl restart nginx
sudo systemctl enable nginx

sudo systemctl restart supervisor
sudo systemctl enable supervisor

# 启动股票交易API
sudo supervisorctl start stock-api

# 14. 配置防火墙
log_info "配置防火墙..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

log_success "🎉 Ubuntu系统股票交易系统部署完成！"

echo
log_info "服务状态检查:"
echo "Nginx状态: $(sudo systemctl is-active nginx)"
echo "Supervisor状态: $(sudo systemctl is-active supervisor)"
echo "股票API状态: $(sudo supervisorctl status stock-api | awk '{print $2}')"

echo
log_info "访问地址:"
log_info "  API文档: http://$(hostname -I | awk '{print $1}')/docs"
log_info "  健康检查: http://$(hostname -I | awk '{print $1}')/api/v1/health"

echo
log_info "管理命令:"
log_info "  查看API日志: sudo supervisorctl tail -f stock-api"
log_info "  重启API: sudo supervisorctl restart stock-api"
log_info "  查看Nginx日志: sudo tail -f /var/log/nginx/access.log"
log_info "  查看系统日志: sudo journalctl -f"

echo
log_info "下一步:"
log_info "1. 编辑 .env 文件设置API密钥"
log_info "2. 重启服务: sudo supervisorctl restart stock-api"
log_info "3. 访问API文档测试功能"

# 最后测试
sleep 5
if curl -s http://localhost/api/v1/health > /dev/null; then
    log_success "✅ 系统部署成功，API正常运行！"
else
    log_warning "⚠️  API可能还在启动中，请稍后检查"
fi