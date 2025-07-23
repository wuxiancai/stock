#!/bin/bash

# 股票交易系统 - 生产环境停止脚本

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

log_info "🛑 停止股票交易系统生产环境..."

# 停止Gunicorn进程
if [ -f "logs/gunicorn.pid" ]; then
    PID=$(cat logs/gunicorn.pid)
    if ps -p $PID > /dev/null 2>&1; then
        log_info "停止Gunicorn进程 (PID: $PID)..."
        kill -TERM $PID
        
        # 等待进程优雅关闭
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                log_success "Gunicorn进程已优雅关闭"
                break
            fi
            sleep 1
        done
        
        # 如果进程仍在运行，强制终止
        if ps -p $PID > /dev/null 2>&1; then
            log_warning "强制终止Gunicorn进程..."
            kill -KILL $PID
        fi
        
        rm -f logs/gunicorn.pid
    else
        log_warning "PID文件存在但进程不在运行"
        rm -f logs/gunicorn.pid
    fi
else
    log_info "未找到PID文件，尝试通过进程名停止..."
    
    # 通过进程名查找并停止
    PIDS=$(pgrep -f "gunicorn main:app" || true)
    if [ -n "$PIDS" ]; then
        log_info "找到Gunicorn进程: $PIDS"
        for PID in $PIDS; do
            log_info "停止进程 $PID..."
            kill -TERM $PID
        done
        
        # 等待进程关闭
        sleep 3
        
        # 检查是否还有残留进程
        REMAINING=$(pgrep -f "gunicorn main:app" || true)
        if [ -n "$REMAINING" ]; then
            log_warning "强制终止残留进程: $REMAINING"
            pkill -KILL -f "gunicorn main:app"
        fi
    else
        log_info "未找到运行中的Gunicorn进程"
    fi
fi

# 停止Celery worker (如果在运行)
CELERY_PIDS=$(pgrep -f "celery.*worker" || true)
if [ -n "$CELERY_PIDS" ]; then
    log_info "停止Celery worker进程..."
    for PID in $CELERY_PIDS; do
        kill -TERM $PID
    done
    sleep 2
fi

# 停止Celery beat (如果在运行)
BEAT_PIDS=$(pgrep -f "celery.*beat" || true)
if [ -n "$BEAT_PIDS" ]; then
    log_info "停止Celery beat进程..."
    for PID in $BEAT_PIDS; do
        kill -TERM $PID
    done
fi

# 检查端口占用
PORT_USAGE=$(lsof -Pi :8080 -sTCP:LISTEN -t 2>/dev/null || true)
if [ -n "$PORT_USAGE" ]; then
    log_warning "端口8080仍被占用，进程PID: $PORT_USAGE"
    log_info "强制释放端口..."
    kill -KILL $PORT_USAGE
fi

log_success "🎉 股票交易系统生产环境已停止！"

# 显示状态
log_info "当前状态检查:"
REMAINING_PROCESSES=$(pgrep -f "gunicorn\|celery.*stock" || true)
if [ -n "$REMAINING_PROCESSES" ]; then
    log_warning "仍有相关进程在运行: $REMAINING_PROCESSES"
else
    log_success "所有相关进程已停止"
fi

PORT_CHECK=$(lsof -Pi :8080 -sTCP:LISTEN 2>/dev/null || true)
if [ -n "$PORT_CHECK" ]; then
    log_warning "端口8080仍被占用"
else
    log_success "端口8080已释放"
fi