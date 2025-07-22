#!/bin/bash

# 数据库初始化脚本
# 用于创建数据库、用户和初始化表结构

set -e  # 遇到错误立即退出

echo "🗄️ 开始初始化数据库..."

# 读取环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 默认数据库配置
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-stock_db}
DB_USER=${DB_USER:-stock_user}
DB_PASSWORD=${DB_PASSWORD:-stock_password}
POSTGRES_USER=${POSTGRES_USER:-postgres}

echo "📋 数据库配置:"
echo "   主机: $DB_HOST"
echo "   端口: $DB_PORT"
echo "   数据库: $DB_NAME"
echo "   用户: $DB_USER"

# 检查PostgreSQL是否运行
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER > /dev/null 2>&1; then
    echo "❌ PostgreSQL服务未运行，请先启动PostgreSQL"
    echo "💡 启动方法:"
    echo "   macOS: brew services start postgresql"
    echo "   Linux: sudo systemctl start postgresql"
    echo "   Docker: docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:13"
    exit 1
fi

echo "✅ PostgreSQL服务正在运行"

# 创建数据库和用户
echo "🔧 创建数据库和用户..."

# 使用postgres用户连接并创建数据库和用户
PGPASSWORD=${POSTGRES_PASSWORD:-postgres} psql -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d postgres << EOF
-- 创建用户（如果不存在）
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        RAISE NOTICE '用户 $DB_USER 创建成功';
    ELSE
        RAISE NOTICE '用户 $DB_USER 已存在';
    END IF;
END
\$\$;

-- 创建数据库（如果不存在）
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- 授权
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ 数据库和用户创建成功"
else
    echo "❌ 数据库和用户创建失败"
    exit 1
fi

# 连接到新创建的数据库并执行初始化脚本
echo "📋 执行数据库初始化脚本..."

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 执行init.sql中的内容
\i init.sql

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ 数据库初始化脚本执行成功"
else
    echo "⚠️ 数据库初始化脚本执行可能有问题，但继续进行..."
fi

# 测试数据库连接
echo "🔗 测试数据库连接..."

python3 << EOF
import sys
import os
sys.path.append('.')

try:
    import psycopg2
    
    # 测试连接
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME'
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'✅ 数据库连接成功: {version[0][:50]}...')
    
    # 检查表是否存在
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    if tables:
        print(f'✅ 发现 {len(tables)} 个表:')
        for table in tables[:5]:  # 只显示前5个
            print(f'   - {table[0]}')
        if len(tables) > 5:
            print(f'   ... 还有 {len(tables) - 5} 个表')
    else:
        print('⚠️ 未发现任何表，可能需要运行应用程序来创建表')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 数据库初始化完成！"
    echo ""
    echo "📋 连接信息:"
    echo "   数据库URL: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    echo ""
    echo "🚀 现在可以启动应用程序:"
    echo "   python3 main.py"
    echo ""
    echo "💡 如果仍有问题，请检查 .env 文件中的数据库配置"
else
    echo "❌ 数据库初始化失败"
    exit 1
fi