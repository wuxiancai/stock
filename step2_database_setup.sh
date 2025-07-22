#!/bin/bash

# 股票交易系统 - 第二步：数据库安装和初始化
# 用户名: wuxiancai, 密码: noneboy780308
# 特别处理PostgreSQL认证和用户权限问题

set -euo pipefail

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

# 数据库配置
readonly DB_USER="wuxiancai"
readonly DB_PASSWORD="noneboy780308"
readonly DB_NAME="stock_trading"
readonly DB_HOST="localhost"
readonly DB_PORT="5432"

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 错误处理
handle_error() {
    log_error "第二步部署失败，退出码: $1"
    log_error "请检查错误信息并重新运行"
    exit 1
}

trap 'handle_error $?' ERR

echo "🗄️  股票交易系统部署 - 第二步：数据库安装和初始化"
echo "=================================================="
echo "数据库用户: $DB_USER"
echo "数据库名称: $DB_NAME"
echo "=================================================="

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_TYPE="linux"
        case "$ID" in
            ubuntu|debian)
                DISTRO="debian"
                PKG_MANAGER="apt-get"
                ;;
            centos|rhel|fedora|rocky|almalinux)
                DISTRO="redhat"
                if command -v dnf >/dev/null 2>&1; then
                    PKG_MANAGER="dnf"
                else
                    PKG_MANAGER="yum"
                fi
                ;;
        esac
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    PKG_MANAGER="brew"
fi

# 安装PostgreSQL服务器
log_step "安装PostgreSQL服务器"
if [[ "$DISTRO" == "debian" ]]; then
    if ! dpkg -l | grep -q "^ii  postgresql "; then
        log_info "安装PostgreSQL服务器..."
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        log_success "PostgreSQL服务器安装完成"
    else
        log_success "PostgreSQL服务器已安装"
    fi
elif [[ "$DISTRO" == "redhat" ]]; then
    if ! rpm -q postgresql-server >/dev/null 2>&1; then
        log_info "安装PostgreSQL服务器..."
        sudo $PKG_MANAGER install -y postgresql-server postgresql-contrib
        
        # 初始化数据库（仅RedHat系需要）
        log_info "初始化PostgreSQL数据库..."
        sudo postgresql-setup initdb
        log_success "PostgreSQL服务器安装完成"
    else
        log_success "PostgreSQL服务器已安装"
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! brew list postgresql@14 >/dev/null 2>&1; then
        log_info "安装PostgreSQL服务器..."
        brew install postgresql@14
        log_success "PostgreSQL服务器安装完成"
    else
        log_success "PostgreSQL服务器已安装"
    fi
fi

# 启动PostgreSQL服务
log_step "启动PostgreSQL服务"
if [[ "$OS_TYPE" == "linux" ]]; then
    # 检查不同的服务名称
    service_names=("postgresql" "postgresql-14" "postgresql-13" "postgresql-12")
    service_started=false
    
    for service in "${service_names[@]}"; do
        if systemctl list-unit-files | grep -q "^${service}.service"; then
            log_info "找到PostgreSQL服务: $service"
            
            if ! systemctl is-active --quiet "$service"; then
                log_info "启动 $service..."
                sudo systemctl enable "$service"
                sudo systemctl start "$service"
            fi
            
            if systemctl is-active --quiet "$service"; then
                log_success "PostgreSQL服务已启动: $service"
                service_started=true
                break
            fi
        fi
    done
    
    if ! $service_started; then
        log_error "无法启动PostgreSQL服务"
        exit 1
    fi
    
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! brew services list | grep postgresql@14 | grep -q started; then
        log_info "启动PostgreSQL服务..."
        brew services start postgresql@14
        sleep 3
    fi
    log_success "PostgreSQL服务已启动"
fi

# 等待PostgreSQL完全启动
log_info "等待PostgreSQL服务完全启动..."
sleep 5

# 配置PostgreSQL认证
log_step "配置PostgreSQL认证"

# 查找PostgreSQL配置文件
if [[ "$OS_TYPE" == "linux" ]]; then
    # 查找pg_hba.conf文件
    PG_HBA_CONF=""
    possible_paths=(
        "/etc/postgresql/*/main/pg_hba.conf"
        "/var/lib/pgsql/*/data/pg_hba.conf"
        "/var/lib/postgresql/*/main/pg_hba.conf"
    )
    
    for path_pattern in "${possible_paths[@]}"; do
        for file in $path_pattern; do
            if [ -f "$file" ]; then
                PG_HBA_CONF="$file"
                break 2
            fi
        done
    done
    
    if [ -n "$PG_HBA_CONF" ]; then
        log_info "找到PostgreSQL配置文件: $PG_HBA_CONF"
        
        # 备份原配置
        sudo cp "$PG_HBA_CONF" "${PG_HBA_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 修改认证方式
        log_info "修改PostgreSQL认证配置..."
        sudo sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' "$PG_HBA_CONF"
        sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' "$PG_HBA_CONF"
        
        # 添加新用户的认证规则
        if ! sudo grep -q "local   all             $DB_USER" "$PG_HBA_CONF"; then
            echo "local   all             $DB_USER                                md5" | sudo tee -a "$PG_HBA_CONF" >/dev/null
        fi
        
        # 重启PostgreSQL服务
        log_info "重启PostgreSQL服务以应用配置..."
        for service in "${service_names[@]}"; do
            if systemctl list-unit-files | grep -q "^${service}.service"; then
                if systemctl is-active --quiet "$service"; then
                    sudo systemctl restart "$service"
                    sleep 3
                    break
                fi
            fi
        done
        
        log_success "PostgreSQL认证配置完成"
    else
        log_warning "未找到PostgreSQL配置文件，使用默认配置"
    fi
fi

# 设置postgres用户密码（临时用于创建新用户）
log_step "配置PostgreSQL超级用户"
if [[ "$OS_TYPE" == "linux" ]]; then
    # 在Linux上，通常需要切换到postgres用户
    log_info "设置postgres用户密码..."
    sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || {
        log_warning "postgres用户密码设置可能已存在"
    }
elif [[ "$OS_TYPE" == "macos" ]]; then
    # 在macOS上，当前用户通常有权限
    log_info "配置PostgreSQL超级用户..."
    psql postgres -c "ALTER USER $(whoami) WITH SUPERUSER;" 2>/dev/null || {
        log_warning "当前用户可能已有超级用户权限"
    }
fi

# 创建数据库用户
log_step "创建数据库用户: $DB_USER"

# 检查用户是否已存在
user_exists=false
if [[ "$OS_TYPE" == "linux" ]]; then
    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        user_exists=true
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        user_exists=true
    fi
fi

if [ "$user_exists" = true ]; then
    log_warning "用户 $DB_USER 已存在，更新密码..."
    if [[ "$OS_TYPE" == "linux" ]]; then
        sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        psql postgres -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    fi
else
    log_info "创建新用户 $DB_USER..."
    if [[ "$OS_TYPE" == "linux" ]]; then
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    fi
fi

# 授予用户权限
log_info "授予用户权限..."
if [[ "$OS_TYPE" == "linux" ]]; then
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;"
elif [[ "$OS_TYPE" == "macos" ]]; then
    psql postgres -c "ALTER USER $DB_USER CREATEDB;"
    psql postgres -c "ALTER USER $DB_USER WITH SUPERUSER;"
fi

log_success "数据库用户 $DB_USER 配置完成"

# 创建数据库
log_step "创建数据库: $DB_NAME"

# 检查数据库是否已存在
db_exists=false
if [[ "$OS_TYPE" == "linux" ]]; then
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        db_exists=true
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    if psql postgres -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        db_exists=true
    fi
fi

if [ "$db_exists" = true ]; then
    log_warning "数据库 $DB_NAME 已存在"
else
    log_info "创建数据库 $DB_NAME..."
    if [[ "$OS_TYPE" == "linux" ]]; then
        sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
    elif [[ "$OS_TYPE" == "macos" ]]; then
        createdb -O "$DB_USER" "$DB_NAME"
    fi
    log_success "数据库 $DB_NAME 创建完成"
fi

# 安装Redis服务器
log_step "安装Redis服务器"
if [[ "$DISTRO" == "debian" ]]; then
    if ! dpkg -l | grep -q "^ii  redis-server "; then
        log_info "安装Redis服务器..."
        sudo apt-get install -y redis-server
        log_success "Redis服务器安装完成"
    else
        log_success "Redis服务器已安装"
    fi
elif [[ "$DISTRO" == "redhat" ]]; then
    if ! rpm -q redis >/dev/null 2>&1; then
        log_info "安装Redis服务器..."
        sudo $PKG_MANAGER install -y redis
        log_success "Redis服务器安装完成"
    else
        log_success "Redis服务器已安装"
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! brew list redis >/dev/null 2>&1; then
        log_info "安装Redis服务器..."
        brew install redis
        log_success "Redis服务器安装完成"
    else
        log_success "Redis服务器已安装"
    fi
fi

# 启动Redis服务
log_step "启动Redis服务"
if [[ "$OS_TYPE" == "linux" ]]; then
    redis_services=("redis-server" "redis")
    for service in "${redis_services[@]}"; do
        if systemctl list-unit-files | grep -q "^${service}.service"; then
            if ! systemctl is-active --quiet "$service"; then
                sudo systemctl enable "$service"
                sudo systemctl start "$service"
            fi
            if systemctl is-active --quiet "$service"; then
                log_success "Redis服务已启动: $service"
                break
            fi
        fi
    done
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! brew services list | grep redis | grep -q started; then
        brew services start redis
    fi
    log_success "Redis服务已启动"
fi

# 创建环境配置文件
log_step "创建环境配置文件"
cat > .env << EOF
# 数据库配置
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# CORS配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://127.0.0.1:8000"]

# 数据库连接池配置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# 缓存配置
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# 日志配置
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
EOF

log_success "环境配置文件创建完成"

# 测试数据库连接
log_step "测试数据库连接"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    log_error "虚拟环境不存在，请先运行 step1_environment_setup.sh"
    exit 1
fi

# 测试PostgreSQL连接
log_info "测试PostgreSQL连接..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        database='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'✅ PostgreSQL连接成功: {version[0][:50]}...')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL连接失败: {e}')
    exit(1)
"

# 测试Redis连接
log_info "测试Redis连接..."
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    info = r.info()
    print(f'✅ Redis连接成功: Redis {info[\"redis_version\"]}')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
"

# 初始化数据库表结构
log_step "初始化数据库表结构"
if [ -f "app/init_db.py" ]; then
    log_info "运行数据库初始化脚本..."
    python app/init_db.py
    log_success "数据库表结构初始化完成"
elif [ -f "init_db.py" ]; then
    log_info "运行数据库初始化脚本..."
    python init_db.py
    log_success "数据库表结构初始化完成"
else
    log_warning "未找到数据库初始化脚本"
    log_info "手动创建基本表结构..."
    
    # 创建基本的用户表
    python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='$DB_HOST',
    port='$DB_PORT',
    database='$DB_NAME',
    user='$DB_USER',
    password='$DB_PASSWORD'
)
cursor = conn.cursor()

# 创建用户表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

# 创建股票表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        market VARCHAR(20) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

conn.commit()
cursor.close()
conn.close()
print('✅ 基本表结构创建完成')
"
fi

echo ""
echo "✅ 第二步部署完成！"
echo "=================================================="
echo "已完成："
echo "  ✓ PostgreSQL服务器安装和启动"
echo "  ✓ PostgreSQL认证配置"
echo "  ✓ 数据库用户创建: $DB_USER"
echo "  ✓ 数据库创建: $DB_NAME"
echo "  ✓ Redis服务器安装和启动"
echo "  ✓ 环境配置文件创建"
echo "  ✓ 数据库连接测试"
echo "  ✓ 数据库表结构初始化"
echo ""
echo "数据库信息："
echo "  主机: $DB_HOST:$DB_PORT"
echo "  数据库: $DB_NAME"
echo "  用户: $DB_USER"
echo "  连接URL: postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "下一步："
echo "  运行 'source venv/bin/activate && uvicorn app.main:app --reload' 启动应用"
echo "  或运行 './start.sh' 启动应用"