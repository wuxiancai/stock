#!/bin/bash

# 数据库管理脚本

set -e

# 激活虚拟环境
source venv/bin/activate

DB_NAME="stock_trading_db"
DB_USER="stock_user"
DB_PASSWORD="stock_password"
DB_HOST="localhost"
DB_PORT="5432"

case "$1" in
    init)
        echo "🗄️ 初始化数据库..."
        
        # 检查 PostgreSQL 是否运行
        if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
            echo "🔄 启动 PostgreSQL..."
            brew services start postgresql@15
            sleep 3
        fi
        
        # 创建数据库和用户
        psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "用户 $DB_USER 已存在"
        psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "数据库 $DB_NAME 已存在"
        psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null
        
        echo "✅ 数据库初始化完成"
        ;;
    migrate)
        echo "🔄 运行数据库迁移..."
        alembic upgrade head
        echo "✅ 数据库迁移完成"
        ;;
    reset)
        echo "⚠️ 重置数据库（将删除所有数据）..."
        read -p "确认要重置数据库吗？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            psql postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
            psql postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
            alembic upgrade head
            echo "✅ 数据库重置完成"
        else
            echo "❌ 操作已取消"
        fi
        ;;
    backup)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        echo "💾 备份数据库到 $BACKUP_FILE..."
        pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > "data/$BACKUP_FILE"
        echo "✅ 数据库备份完成: data/$BACKUP_FILE"
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "❌ 请指定备份文件路径"
            echo "用法: $0 restore <backup_file>"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            echo "❌ 备份文件不存在: $2"
            exit 1
        fi
        
        echo "📥 从 $2 恢复数据库..."
        read -p "确认要恢复数据库吗？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < "$2"
            echo "✅ 数据库恢复完成"
        else
            echo "❌ 操作已取消"
        fi
        ;;
    status)
        echo "📊 检查数据库状态..."
        if pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
            echo "✅ PostgreSQL 服务正常"
            
            # 检查数据库连接
            if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
                echo "✅ 数据库连接正常"
                
                # 显示表信息
                echo ""
                echo "📋 数据库表信息:"
                psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                "
            else
                echo "❌ 数据库连接失败"
            fi
        else
            echo "❌ PostgreSQL 服务未运行"
        fi
        ;;
    clean)
        echo "🧹 清理旧数据..."
        python -c "
from app.database import get_sync_session
from app.models import DailyQuote, TechnicalIndicator, NineTurnSignal, DataUpdateLog
from datetime import datetime, timedelta
from sqlalchemy import delete

with get_sync_session() as session:
    # 删除一年前的数据
    cutoff_date = datetime.now() - timedelta(days=365)
    
    # 删除旧的日线数据
    result1 = session.execute(delete(DailyQuote).where(DailyQuote.trade_date < cutoff_date.date()))
    print(f'删除了 {result1.rowcount} 条日线数据')
    
    # 删除旧的技术指标数据
    result2 = session.execute(delete(TechnicalIndicator).where(TechnicalIndicator.trade_date < cutoff_date.date()))
    print(f'删除了 {result2.rowcount} 条技术指标数据')
    
    # 删除旧的九转信号数据
    result3 = session.execute(delete(NineTurnSignal).where(NineTurnSignal.trade_date < cutoff_date.date()))
    print(f'删除了 {result3.rowcount} 条九转信号数据')
    
    # 删除三个月前的更新日志
    log_cutoff_date = datetime.now() - timedelta(days=90)
    result4 = session.execute(delete(DataUpdateLog).where(DataUpdateLog.created_at < log_cutoff_date))
    print(f'删除了 {result4.rowcount} 条更新日志')
    
    session.commit()
    print('✅ 数据清理完成')
"
        ;;
    *)
        echo "用法: $0 {init|migrate|reset|backup|restore|status|clean}"
        echo ""
        echo "命令说明:"
        echo "  init     - 初始化数据库和用户"
        echo "  migrate  - 运行数据库迁移"
        echo "  reset    - 重置数据库（删除所有数据）"
        echo "  backup   - 备份数据库"
        echo "  restore  - 恢复数据库"
        echo "  status   - 检查数据库状态"
        echo "  clean    - 清理旧数据"
        exit 1
        ;;
esac