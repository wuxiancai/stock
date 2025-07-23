#!/bin/bash

# 股票交易系统 - Supervisor 配置安装脚本
# 用于进程管理和监控

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

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    log_error "此脚本需要root权限运行"
    log_info "请使用: sudo $0"
    exit 1
fi

# 获取当前目录和用户
CURRENT_DIR=$(pwd)
CURRENT_USER=$(logname 2>/dev/null || echo $SUDO_USER)

if [ -z "$CURRENT_USER" ]; then
    log_error "无法确定当前用户"
    exit 1
fi

log_info "🔧 安装Supervisor配置..."

# 安装supervisor
if ! command -v supervisord &> /dev/null; then
    log_info "安装Supervisor..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y supervisor
    elif command -v yum &> /dev/null; then
        yum install -y supervisor
    elif command -v brew &> /dev/null; then
        sudo -u $CURRENT_USER brew install supervisor
    else
        log_error "无法自动安装Supervisor，请手动安装"
        exit 1
    fi
fi

# 创建supervisor配置目录
SUPERVISOR_CONF_DIR="/etc/supervisor/conf.d"
mkdir -p "$SUPERVISOR_CONF_DIR"

# 创建股票交易系统配置文件
CONF_FILE="$SUPERVISOR_CONF_DIR/stock-trading.conf"

log_info "创建Supervisor配置文件: $CONF_FILE"

cat > "$CONF_FILE" << EOF
[group:stock-trading]
programs=stock-api,stock-celery-worker,stock-celery-beat

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

[program:stock-celery-worker]
command=$CURRENT_DIR/venv/bin/celery -A app.celery_app worker --loglevel=info --concurrency=4
directory=$CURRENT_DIR
user=$CURRENT_USER
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=$CURRENT_DIR/logs/supervisor-celery-worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=ENVIRONMENT="production",PYTHONPATH="$CURRENT_DIR"
stopwaitsecs=600
killasgroup=true
priority=998

[program:stock-celery-beat]
command=$CURRENT_DIR/venv/bin/celery -A app.celery_app beat --loglevel=info
directory=$CURRENT_DIR
user=$CURRENT_USER
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=$CURRENT_DIR/logs/supervisor-celery-beat.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=ENVIRONMENT="production",PYTHONPATH="$CURRENT_DIR"
stopwaitsecs=600
killasgroup=true
priority=999
EOF

# 创建日志目录
log_info "创建日志目录..."
mkdir -p "$CURRENT_DIR/logs"
chown -R "$CURRENT_USER:$CURRENT_USER" "$CURRENT_DIR/logs"

# 确保gunicorn配置文件存在
if [ ! -f "$CURRENT_DIR/gunicorn.conf.py" ]; then
    log_info "创建Gunicorn配置文件..."
    cat > "$CURRENT_DIR/gunicorn.conf.py" << 'EOF'
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

# 进程命名
proc_name = "stock-trading-api"

# 重启设置
max_requests = 1000
max_requests_jitter = 100

# 环境变量
raw_env = [
    'ENVIRONMENT=production',
]
EOF
    chown "$CURRENT_USER:$CURRENT_USER" "$CURRENT_DIR/gunicorn.conf.py"
fi

# 重新加载supervisor配置
log_info "重新加载Supervisor配置..."
supervisorctl reread
supervisorctl update

# 启动supervisor服务
if command -v systemctl &> /dev/null; then
    systemctl enable supervisor
    systemctl start supervisor
elif command -v service &> /dev/null; then
    service supervisor start
fi

log_success "🎉 Supervisor配置安装完成！"

echo
log_info "Supervisor管理命令:"
log_info "  查看所有程序状态: sudo supervisorctl status"
log_info "  启动股票交易系统: sudo supervisorctl start stock-trading:*"
log_info "  停止股票交易系统: sudo supervisorctl stop stock-trading:*"
log_info "  重启股票交易系统: sudo supervisorctl restart stock-trading:*"
log_info "  查看API日志: sudo supervisorctl tail -f stock-api"
log_info "  查看Worker日志: sudo supervisorctl tail -f stock-celery-worker"
log_info "  查看Beat日志: sudo supervisorctl tail -f stock-celery-beat"

echo
log_info "配置文件: $CONF_FILE"
log_info "日志目录: $CURRENT_DIR/logs"

echo
read -p "是否现在启动所有服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "启动股票交易系统服务..."
    supervisorctl start stock-trading:*
    sleep 3
    
    log_info "服务状态:"
    supervisorctl status stock-trading:*
fi