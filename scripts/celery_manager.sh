#!/bin/bash

# Celery 管理脚本

set -e

# 激活虚拟环境
source venv/bin/activate

CELERY_APP="app.tasks.celery_app"
WORKER_CONCURRENCY=4
BEAT_SCHEDULER="celery.beat:PersistentScheduler"

case "$1" in
    worker)
        echo "🚀 启动 Celery Worker..."
        celery -A $CELERY_APP worker --loglevel=info --concurrency=$WORKER_CONCURRENCY
        ;;
    beat)
        echo "⏰ 启动 Celery Beat..."
        celery -A $CELERY_APP beat --loglevel=info --scheduler=$BEAT_SCHEDULER
        ;;
    flower)
        echo "🌸 启动 Flower 监控..."
        celery -A $CELERY_APP flower --port=5555
        ;;
    status)
        echo "📊 检查 Celery 状态..."
        celery -A $CELERY_APP status
        ;;
    inspect)
        echo "🔍 检查 Celery 任务..."
        celery -A $CELERY_APP inspect active
        ;;
    purge)
        echo "🗑️ 清空任务队列..."
        celery -A $CELERY_APP purge -f
        ;;
    stop)
        echo "🛑 停止 Celery 进程..."
        pkill -f "celery.*worker" 2>/dev/null || echo "Worker 未运行"
        pkill -f "celery.*beat" 2>/dev/null || echo "Beat 未运行"
        pkill -f "celery.*flower" 2>/dev/null || echo "Flower 未运行"
        ;;
    restart)
        echo "🔄 重启 Celery 服务..."
        $0 stop
        sleep 2
        $0 worker &
        $0 beat &
        echo "✅ Celery 服务已重启"
        ;;
    *)
        echo "用法: $0 {worker|beat|flower|status|inspect|purge|stop|restart}"
        echo ""
        echo "命令说明:"
        echo "  worker   - 启动 Celery Worker"
        echo "  beat     - 启动 Celery Beat 调度器"
        echo "  flower   - 启动 Flower 监控界面"
        echo "  status   - 检查 Celery 状态"
        echo "  inspect  - 检查活跃任务"
        echo "  purge    - 清空任务队列"
        echo "  stop     - 停止所有 Celery 进程"
        echo "  restart  - 重启 Celery 服务"
        exit 1
        ;;
esac