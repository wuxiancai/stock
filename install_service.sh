#!/bin/bash

# 股票交易系统 - Systemd 服务安装脚本
# 用于将系统注册为系统服务，实现开机自启和服务管理

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

log_info "🔧 安装股票交易系统为系统服务..."
log_info "安装目录: $CURRENT_DIR"
log_info "运行用户: $CURRENT_USER"

# 检查必要文件
if [ ! -f "$CURRENT_DIR/start_prod.sh" ]; then
    log_error "未找到 start_prod.sh 文件"
    exit 1
fi

if [ ! -f "$CURRENT_DIR/stop_prod.sh" ]; then
    log_error "未找到 stop_prod.sh 文件"
    exit 1
fi

# 确保脚本可执行
chmod +x "$CURRENT_DIR/start_prod.sh"
chmod +x "$CURRENT_DIR/stop_prod.sh"

# 确保虚拟环境存在
if [ ! -d "$CURRENT_DIR/venv" ]; then
    log_error "虚拟环境不存在，请先运行 python3 -m venv venv"
    exit 1
fi

# 确保gunicorn配置文件存在
if [ ! -f "$CURRENT_DIR/gunicorn.conf.py" ]; then
    log_info "创建Gunicorn配置文件..."
    cat > "$CURRENT_DIR/gunicorn.conf.py" << 'GUNICORN_EOF'
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
GUNICORN_EOF
    chown "$CURRENT_USER:$CURRENT_USER" "$CURRENT_DIR/gunicorn.conf.py"
fi

# 创建systemd服务文件
SERVICE_FILE="/etc/systemd/system/stock-trading.service"

log_info "创建systemd服务文件: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Stock Trading System API Server
Documentation=https://github.com/your-repo/stock-trading-system
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=ENVIRONMENT=production
Environment=PYTHONPATH=$CURRENT_DIR

# 启动前准备
ExecStartPre=/bin/bash -c 'source $CURRENT_DIR/venv/bin/activate && alembic upgrade head'

# 启动命令 - 直接使用gunicorn而不是脚本
ExecStart=$CURRENT_DIR/venv/bin/gunicorn main:app -c $CURRENT_DIR/gunicorn.conf.py

# 停止命令
ExecStop=/bin/kill -TERM \$MAINPID

# 重载命令
ExecReload=/bin/kill -HUP \$MAINPID

# 进程管理
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CURRENT_DIR

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stock-trading

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
log_info "创建日志目录..."
mkdir -p "$CURRENT_DIR/logs"
chown -R "$CURRENT_USER:$CURRENT_USER" "$CURRENT_DIR/logs"

# 重新加载systemd配置
log_info "重新加载systemd配置..."
systemctl daemon-reload

# 启用服务
log_info "启用股票交易系统服务..."
systemctl enable stock-trading.service

log_success "🎉 股票交易系统服务安装完成！"

echo
log_info "服务管理命令:"
log_info "  启动服务: sudo systemctl start stock-trading"
log_info "  停止服务: sudo systemctl stop stock-trading"
log_info "  重启服务: sudo systemctl restart stock-trading"
log_info "  查看状态: sudo systemctl status stock-trading"
log_info "  查看日志: sudo journalctl -u stock-trading -f"
log_info "  禁用服务: sudo systemctl disable stock-trading"

echo
log_info "服务配置文件: $SERVICE_FILE"
log_info "工作目录: $CURRENT_DIR"
log_info "运行用户: $CURRENT_USER"

echo
read -p "是否现在启动服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "启动股票交易系统服务..."
    systemctl start stock-trading.service
    sleep 3
    
    if systemctl is-active --quiet stock-trading.service; then
        log_success "服务启动成功！"
        log_info "服务状态:"
        systemctl status stock-trading.service --no-pager -l
    else
        log_error "服务启动失败"
        log_info "查看错误日志:"
        journalctl -u stock-trading.service --no-pager -l
    fi
fi