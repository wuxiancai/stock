#!/bin/bash

# 股票交易系统完整部署脚本 v2.0
# 支持 macOS 和 Linux 系统，包含完整的错误处理和依赖检查

set -euo pipefail  # 严格模式

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deploy.log"
OS_TYPE=""
DISTRO=""
PYTHON_CMD=""
PIP_CMD=""

# 日志函数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$LOG_FILE" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        "DEBUG") echo -e "${PURPLE}[DEBUG]${NC} $message" | tee -a "$LOG_FILE" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# 错误处理
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log "ERROR" "部署失败，退出码: $exit_code"
        log "ERROR" "详细日志请查看: $LOG_FILE"
        log "ERROR" "如需帮助，请提供日志文件内容"
    fi
    exit $exit_code
}

trap cleanup EXIT

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测操作系统
detect_os() {
    log "INFO" "检测操作系统..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS_TYPE="linux"
        log "SUCCESS" "检测到Linux系统"
        
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            case "$ID" in
                ubuntu|debian)
                    DISTRO="debian"
                    log "SUCCESS" "检测到 $PRETTY_NAME"
                    ;;
                centos|rhel|fedora|rocky|almalinux)
                    DISTRO="redhat"
                    log "SUCCESS" "检测到 $PRETTY_NAME"
                    ;;
                *)
                    DISTRO="unknown"
                    log "WARNING" "未知的Linux发行版: $PRETTY_NAME"
                    ;;
            esac
        else
            log "WARNING" "无法检测Linux发行版"
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        local macos_version=$(sw_vers -productVersion)
        log "SUCCESS" "检测到macOS系统，版本: $macos_version"
    else
        log "ERROR" "不支持的操作系统: $OSTYPE"
        log "ERROR" "支持的系统: Linux (Ubuntu/Debian, CentOS/RHEL/Fedora), macOS"
        exit 1
    fi
}

# 安装系统包管理器
install_package_manager() {
    if [[ "$OS_TYPE" == "macos" ]]; then
        if ! command_exists brew; then
            log "INFO" "安装Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # 添加到PATH
            if [[ -f "/opt/homebrew/bin/brew" ]]; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [[ -f "/usr/local/bin/brew" ]]; then
                echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
                eval "$(/usr/local/bin/brew shellenv)"
            fi
            
            log "SUCCESS" "Homebrew安装完成"
        else
            log "SUCCESS" "Homebrew已安装"
        fi
    fi
}

# 安装系统依赖
install_system_dependencies() {
    log "INFO" "安装系统依赖..."
    
    local packages=()
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        if [[ "$DISTRO" == "debian" ]]; then
            # 更新包列表
            sudo apt-get update
            
            packages=(
                "curl" "git" "wget" "build-essential"
                "python3" "python3-pip" "python3-venv" "python3-dev"
                "libpq-dev" "postgresql-client"
                "redis-tools"
            )
            
            for package in "${packages[@]}"; do
                if ! dpkg -l | grep -q "^ii  $package "; then
                    log "INFO" "安装 $package..."
                    sudo apt-get install -y "$package"
                else
                    log "SUCCESS" "$package 已安装"
                fi
            done
            
        elif [[ "$DISTRO" == "redhat" ]]; then
            local pkg_manager="yum"
            if command_exists dnf; then
                pkg_manager="dnf"
            fi
            
            packages=(
                "curl" "git" "wget" "gcc" "gcc-c++" "make"
                "python3" "python3-pip" "python3-devel"
                "postgresql-devel" "postgresql"
                "redis"
            )
            
            for package in "${packages[@]}"; do
                if ! rpm -q "$package" >/dev/null 2>&1; then
                    log "INFO" "安装 $package..."
                    sudo $pkg_manager install -y "$package"
                else
                    log "SUCCESS" "$package 已安装"
                fi
            done
        fi
        
    elif [[ "$OS_TYPE" == "macos" ]]; then
        packages=("python@3.11" "postgresql@14" "redis" "git")
        
        for package in "${packages[@]}"; do
            if ! brew list "$package" >/dev/null 2>&1; then
                log "INFO" "安装 $package..."
                brew install "$package"
            else
                log "SUCCESS" "$package 已安装"
            fi
        done
    fi
}

# 检查Python版本
check_python() {
    log "INFO" "检查Python环境..."
    
    # 查找可用的Python命令
    for cmd in python3.11 python3.10 python3.9 python3.8 python3; do
        if command_exists "$cmd"; then
            PYTHON_CMD="$cmd"
            break
        fi
    done
    
    if [[ -z "$PYTHON_CMD" ]]; then
        log "ERROR" "未找到Python3"
        exit 1
    fi
    
    local python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log "ERROR" "Python版本过低，需要 $required_version+，当前: $python_version"
        exit 1
    fi
    
    log "SUCCESS" "Python版本检查通过: $python_version ($PYTHON_CMD)"
    
    # 设置pip命令
    PIP_CMD="$PYTHON_CMD -m pip"
}

# 启动PostgreSQL服务
start_postgresql() {
    log "INFO" "启动PostgreSQL服务..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        # 检查不同的服务名称
        local service_names=("postgresql" "postgresql-14" "postgresql-13" "postgresql-12")
        local service_started=false
        
        for service in "${service_names[@]}"; do
            if systemctl list-unit-files | grep -q "^${service}.service"; then
                log "INFO" "找到PostgreSQL服务: $service"
                
                if ! systemctl is-active --quiet "$service"; then
                    log "INFO" "启动 $service..."
                    sudo systemctl enable "$service"
                    sudo systemctl start "$service"
                fi
                
                if systemctl is-active --quiet "$service"; then
                    log "SUCCESS" "PostgreSQL服务已启动: $service"
                    service_started=true
                    break
                fi
            fi
        done
        
        if ! $service_started; then
            log "WARNING" "未找到PostgreSQL服务，尝试安装..."
            if [[ "$DISTRO" == "debian" ]]; then
                sudo apt-get install -y postgresql postgresql-contrib
                sudo systemctl enable postgresql
                sudo systemctl start postgresql
            elif [[ "$DISTRO" == "redhat" ]]; then
                local pkg_manager="yum"
                if command_exists dnf; then
                    pkg_manager="dnf"
                fi
                sudo $pkg_manager install -y postgresql-server postgresql-contrib
                sudo postgresql-setup initdb
                sudo systemctl enable postgresql
                sudo systemctl start postgresql
            fi
        fi
        
    elif [[ "$OS_TYPE" == "macos" ]]; then
        if ! brew services list | grep postgresql | grep -q started; then
            log "INFO" "启动PostgreSQL服务..."
            brew services start postgresql@14
        else
            log "SUCCESS" "PostgreSQL服务已运行"
        fi
    fi
    
    # 验证PostgreSQL是否可连接
    sleep 3
    if command_exists psql; then
        if psql -h localhost -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
            log "SUCCESS" "PostgreSQL连接测试成功"
        else
            log "WARNING" "PostgreSQL连接测试失败，可能需要配置认证"
        fi
    fi
}

# 启动Redis服务
start_redis() {
    log "INFO" "启动Redis服务..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        local service_names=("redis-server" "redis")
        local service_started=false
        
        for service in "${service_names[@]}"; do
            if systemctl list-unit-files | grep -q "^${service}.service"; then
                if ! systemctl is-active --quiet "$service"; then
                    sudo systemctl enable "$service"
                    sudo systemctl start "$service"
                fi
                
                if systemctl is-active --quiet "$service"; then
                    log "SUCCESS" "Redis服务已启动: $service"
                    service_started=true
                    break
                fi
            fi
        done
        
        if ! $service_started; then
            log "WARNING" "未找到Redis服务"
        fi
        
    elif [[ "$OS_TYPE" == "macos" ]]; then
        if ! brew services list | grep redis | grep -q started; then
            brew services start redis
        else
            log "SUCCESS" "Redis服务已运行"
        fi
    fi
    
    # 验证Redis连接
    sleep 2
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            log "SUCCESS" "Redis连接测试成功"
        else
            log "WARNING" "Redis连接测试失败"
        fi
    fi
}

# 设置Python虚拟环境
setup_python_env() {
    log "INFO" "设置Python虚拟环境..."
    
    if [ ! -d "venv" ]; then
        log "INFO" "创建虚拟环境..."
        $PYTHON_CMD -m venv venv
    else
        log "SUCCESS" "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log "SUCCESS" "虚拟环境已激活"
    
    # 升级pip
    log "INFO" "升级pip..."
    python -m pip install --upgrade pip setuptools wheel
    
    # 安装psycopg2-binary
    log "INFO" "安装数据库驱动..."
    python -m pip install psycopg2-binary
    
    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        log "INFO" "安装项目依赖..."
        python -m pip install -r requirements.txt
    else
        log "WARNING" "requirements.txt不存在，安装基本依赖..."
        python -m pip install fastapi uvicorn sqlalchemy alembic redis python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv
    fi
    
    log "SUCCESS" "Python环境设置完成"
}

# 配置环境变量
setup_environment() {
    log "INFO" "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log "SUCCESS" "从.env.example创建.env文件"
        else
            log "WARNING" ".env.example不存在，创建基本.env文件"
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
        fi
    else
        log "SUCCESS" ".env文件已存在"
    fi
}

# 初始化数据库
init_database() {
    log "INFO" "初始化数据库..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 创建数据库
    if command_exists createdb; then
        if ! psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw stock_trading; then
            log "INFO" "创建数据库..."
            createdb -h localhost -U postgres stock_trading
            log "SUCCESS" "数据库创建成功"
        else
            log "SUCCESS" "数据库已存在"
        fi
    fi
    
    # 运行数据库初始化脚本
    if [ -f "init_db.py" ]; then
        log "INFO" "运行数据库初始化脚本..."
        python init_db.py
    elif [ -f "app/init_db.py" ]; then
        log "INFO" "运行数据库初始化脚本..."
        python app/init_db.py
    else
        log "WARNING" "未找到数据库初始化脚本"
    fi
}

# 测试连接
test_connections() {
    log "INFO" "测试服务连接..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
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
}

# 主函数
main() {
    log "INFO" "开始部署股票交易系统..."
    log "INFO" "日志文件: $LOG_FILE"
    
    # 检查是否在项目根目录
    if [ ! -f "app/main.py" ] && [ ! -f "main.py" ]; then
        log "ERROR" "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行部署步骤
    detect_os
    install_package_manager
    install_system_dependencies
    check_python
    start_postgresql
    start_redis
    setup_python_env
    setup_environment
    init_database
    test_connections
    
    log "SUCCESS" "部署完成！"
    log "INFO" "启动应用: source venv/bin/activate && uvicorn app.main:app --reload"
    log "INFO" "访问地址: http://localhost:8000"
    log "INFO" "API文档: http://localhost:8000/docs"
}

# 运行主函数
main "$@"