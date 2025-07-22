#!/bin/bash

# Ubuntu专用快速修复脚本
# 针对部署日志中发现的问题进行修复

set -e

echo "🔧 开始修复部署问题..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 1. 修复PostgreSQL
log_info "修复PostgreSQL配置..."

# 确保PostgreSQL服务运行
if ! systemctl is-active --quiet postgresql; then
    log_info "启动PostgreSQL服务..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    sleep 3
fi

# 设置postgres用户密码
log_info "配置PostgreSQL认证..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || {
    log_warning "PostgreSQL密码设置可能已存在"
}

# 修改认证方式
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/${PG_VERSION}/main"

if [ -d "$PG_CONFIG_DIR" ]; then
    log_info "修改PostgreSQL认证配置..."
    
    # 备份原配置
    sudo cp "${PG_CONFIG_DIR}/pg_hba.conf" "${PG_CONFIG_DIR}/pg_hba.conf.backup" 2>/dev/null || true
    
    # 修改认证方式
    sudo sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' "${PG_CONFIG_DIR}/pg_hba.conf"
    sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "${PG_CONFIG_DIR}/pg_hba.conf"
    
    # 重启PostgreSQL
    log_info "重启PostgreSQL服务..."
    sudo systemctl restart postgresql
    sleep 3
else
    log_warning "未找到PostgreSQL配置目录，跳过认证配置"
fi

# 测试PostgreSQL连接
log_info "测试PostgreSQL连接..."
if PGPASSWORD=postgres psql -h localhost -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
    log_success "PostgreSQL连接测试成功"
else
    log_error "PostgreSQL连接测试失败"
    exit 1
fi

# 2. 修复Redis
log_info "修复Redis配置..."

# 安装Redis（如果未安装）
if ! command -v redis-server >/dev/null 2>&1; then
    log_info "安装Redis服务器..."
    sudo apt-get update
    sudo apt-get install -y redis-server
fi

# 启动Redis服务
if ! systemctl is-active --quiet redis-server; then
    log_info "启动Redis服务..."
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    sleep 2
fi

# 测试Redis连接
log_info "测试Redis连接..."
if redis-cli ping >/dev/null 2>&1; then
    log_success "Redis连接测试成功"
else
    log_error "Redis连接测试失败"
    exit 1
fi

# 3. 创建数据库
log_info "创建数据库..."
if ! PGPASSWORD=postgres psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw stock_trading; then
    log_info "创建stock_trading数据库..."
    PGPASSWORD=postgres createdb -h localhost -U postgres stock_trading
    log_success "数据库创建成功"
else
    log_success "数据库已存在"
fi

# 4. 验证虚拟环境
log_info "检查Python虚拟环境..."
if [ ! -d "venv" ]; then
    log_info "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
log_info "激活虚拟环境并安装依赖..."
source venv/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装psycopg2-binary
python -m pip install psycopg2-binary

# 安装项目依赖
if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
    log_success "项目依赖安装完成"
else
    log_warning "requirements.txt不存在，安装基本依赖"
    python -m pip install fastapi uvicorn sqlalchemy alembic redis python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv
fi

# 5. 配置环境变量
log_info "配置环境变量..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "从.env.example创建.env文件"
    else
        log_info "创建基本.env文件..."
        cat > .env << EOF
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stock_trading
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_trading

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
EOF
        log_success "创建基本.env文件"
    fi
else
    log_success ".env文件已存在"
fi

# 6. 初始化数据库
log_info "初始化数据库..."
if [ -f "app/init_db.py" ]; then
    python app/init_db.py
    log_success "数据库初始化完成"
elif [ -f "init_db.py" ]; then
    python init_db.py
    log_success "数据库初始化完成"
else
    log_warning "未找到数据库初始化脚本"
fi

# 7. 最终测试
log_info "进行最终连接测试..."

# 测试数据库连接
python -c "
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv('DATABASE_URL')
try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

# 测试Redis连接
python -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
try:
    r = redis.from_url(redis_url)
    r.ping()
    print('✅ Redis连接成功')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
"

log_success "修复完成！"
echo ""
echo "🎉 部署修复成功！"
echo ""
echo "启动应用："
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "访问地址："
echo "  应用: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"