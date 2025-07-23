#!/bin/bash

# 股票交易系统 - 生产环境启动脚本
# 使用 Gunicorn + Nginx 部署

set -e

echo "🚀 启动股票交易系统生产环境..."

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "❌ 请不要使用root用户运行此脚本"
    exit 1
fi

# 设置环境变量
export ENVIRONMENT=production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

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

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 检查必要工具
log_info "检查必要工具..."
check_command python3
check_command pip3
check_command psql
check_command redis-cli

# 检查虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate

# 安装/更新依赖
log_info "安装生产环境依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]

# 检查配置文件
if [ ! -f ".env" ]; then
    log_warning ".env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    log_warning "请编辑 .env 文件设置生产环境配置"
fi

# 检查PostgreSQL服务
log_info "检查PostgreSQL服务..."
if ! pgrep -x "postgres" > /dev/null; then
    log_info "启动PostgreSQL服务..."
    if command -v brew &> /dev/null; then
        brew services start postgresql@14
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    else
        log_error "无法启动PostgreSQL服务，请手动启动"
        exit 1
    fi
    sleep 3
fi

# 检查Redis服务
log_info "检查Redis服务..."
if ! pgrep -x "redis-server" > /dev/null; then
    log_info "启动Redis服务..."
    if command -v brew &> /dev/null; then
        brew services start redis
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start redis
    else
        log_error "无法启动Redis服务，请手动启动"
        exit 1
    fi
    sleep 2
fi

# 测试数据库连接
log_info "测试数据库连接..."
python3 -c "
import asyncio
from app.database import test_connection
asyncio.run(test_connection())
" || {
    log_error "数据库连接失败"
    exit 1
}

# 运行数据库迁移
log_info "运行数据库迁移..."
alembic upgrade head

# 创建日志目录
mkdir -p logs

# 创建Gunicorn配置文件
cat > gunicorn.conf.py << 'EOF'
# Gunicorn 生产环境配置

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

# SSL (如果需要)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# 重启设置
max_requests = 1000
max_requests_jitter = 100

# 用户和组 (如果需要)
# user = "www-data"
# group = "www-data"

# 临时目录
tmp_upload_dir = None

# 环境变量
raw_env = [
    'ENVIRONMENT=production',
]
EOF

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        log_warning "端口 $port 已被占用"
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        log_info "占用进程 PID: $pid"
        read -p "是否终止占用进程? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill -9 $pid
            log_success "已终止进程 $pid"
        else
            log_error "端口冲突，无法启动服务"
            exit 1
        fi
    fi
}

check_port 8080

# 启动Gunicorn服务器
log_info "启动Gunicorn生产服务器..."
log_info "配置信息:"
log_info "  - 环境: production"
log_info "  - 端口: 8080"
log_info "  - 工作进程数: $(($(nproc) * 2 + 1))"
log_info "  - 日志目录: logs/"

# 创建启动命令
GUNICORN_CMD="gunicorn main:app -c gunicorn.conf.py"

# 检查是否需要后台运行
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    log_info "以守护进程模式启动..."
    nohup $GUNICORN_CMD > logs/gunicorn.log 2>&1 &
    GUNICORN_PID=$!
    echo $GUNICORN_PID > logs/gunicorn.pid
    log_success "Gunicorn已启动，PID: $GUNICORN_PID"
    log_info "日志文件: logs/gunicorn.log"
    log_info "PID文件: logs/gunicorn.pid"
else
    log_info "以前台模式启动..."
    exec $GUNICORN_CMD
fi

log_success "🎉 股票交易系统生产环境启动完成！"
log_info "API地址: http://localhost:8080"
log_info "API文档: http://localhost:8080/docs"
log_info "健康检查: http://localhost:8080/api/v1/health"

# 显示停止命令
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    echo
    log_info "停止服务命令:"
    log_info "  kill \$(cat logs/gunicorn.pid)"
    log_info "或者:"
    log_info "  pkill -f 'gunicorn main:app'"
fi