#!/bin/bash

# 股票交易系统完整部署脚本
# 支持多种操作系统和部署方式

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            DISTRO=$(lsb_release -si 2>/dev/null || echo "Debian")
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            DISTRO=$(cat /etc/redhat-release | awk '{print $1}')
        else
            OS="linux"
            DISTRO="Unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macOS"
    else
        OS="unknown"
        DISTRO="Unknown"
    fi
    
    log_info "检测到操作系统: $DISTRO ($OS)"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    log_info "Python版本: $python_version"
    
    if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
        log_error "需要Python 3.8+，当前: $python_version"
        exit 1
    fi
    
    # 检查必要的系统工具
    local missing_tools=()
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v wget &> /dev/null; then
        missing_tools+=("wget")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "缺少系统工具: ${missing_tools[*]}"
        install_system_tools "${missing_tools[@]}"
    fi
    
    log_success "系统要求检查完成"
}

# 安装系统工具
install_system_tools() {
    local tools=("$@")
    log_info "安装系统工具: ${tools[*]}"
    
    case $OS in
        "debian")
            sudo apt-get update
            for tool in "${tools[@]}"; do
                sudo apt-get install -y "$tool"
            done
            ;;
        "redhat")
            for tool in "${tools[@]}"; do
                sudo yum install -y "$tool" || sudo dnf install -y "$tool"
            done
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_info "安装Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            for tool in "${tools[@]}"; do
                brew install "$tool"
            done
            ;;
        *)
            log_error "不支持的操作系统，请手动安装: ${tools[*]}"
            exit 1
            ;;
    esac
}

# 安装PostgreSQL
install_postgresql() {
    log_info "安装PostgreSQL..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib postgresql-client
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            ;;
        "redhat")
            if command -v dnf &> /dev/null; then
                sudo dnf install -y postgresql postgresql-server postgresql-contrib
                sudo postgresql-setup --initdb
            else
                sudo yum install -y postgresql postgresql-server postgresql-contrib
                sudo postgresql-setup initdb
            fi
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_error "需要先安装Homebrew"
                exit 1
            fi
            brew install postgresql
            brew services start postgresql
            ;;
        *)
            log_error "不支持的操作系统，请手动安装PostgreSQL"
            exit 1
            ;;
    esac
    
    # 等待PostgreSQL启动
    sleep 5
    
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log_success "PostgreSQL安装并启动成功"
    else
        log_error "PostgreSQL启动失败"
        exit 1
    fi
}

# 安装Redis
install_redis() {
    log_info "安装Redis..."
    
    case $OS in
        "debian")
            sudo apt-get update
            sudo apt-get install -y redis-server
            sudo systemctl enable redis-server
            sudo systemctl start redis-server
            ;;
        "redhat")
            if command -v dnf &> /dev/null; then
                sudo dnf install -y redis
            else
                sudo yum install -y redis
            fi
            sudo systemctl enable redis
            sudo systemctl start redis
            ;;
        "macos")
            brew install redis
            brew services start redis
            ;;
        *)
            log_error "不支持的操作系统，请手动安装Redis"
            exit 1
            ;;
    esac
    
    # 等待Redis启动
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        log_success "Redis安装并启动成功"
    else
        log_warning "Redis启动失败，应用程序可能无法正常工作"
    fi
}

# 检查并安装数据库服务
setup_databases() {
    log_info "设置数据库服务..."
    
    # 检查PostgreSQL
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL客户端未安装，正在安装..."
        install_postgresql
    elif ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log_warning "PostgreSQL服务未运行，尝试启动..."
        start_postgresql
    else
        log_success "PostgreSQL服务正在运行"
    fi
    
    # 检查Redis
    if ! command -v redis-cli &> /dev/null; then
        log_warning "Redis客户端未安装，正在安装..."
        install_redis
    elif ! redis-cli ping > /dev/null 2>&1; then
        log_warning "Redis服务未运行，尝试启动..."
        start_redis
    else
        log_success "Redis服务正在运行"
    fi
}

# 启动PostgreSQL服务
start_postgresql() {
    case $OS in
        "debian"|"redhat")
            if systemctl list-unit-files | grep -q "^postgresql.service"; then
                sudo systemctl start postgresql
            elif systemctl list-unit-files | grep -q "^postgresql-"; then
                # 查找具体的PostgreSQL服务名
                PG_SERVICE=$(systemctl list-unit-files | grep "^postgresql-" | head -1 | awk '{print $1}')
                sudo systemctl start "$PG_SERVICE"
            else
                log_error "找不到PostgreSQL服务，请手动安装"
                exit 1
            fi
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew services start postgresql
            else
                log_error "需要Homebrew来管理PostgreSQL服务"
                exit 1
            fi
            ;;
        *)
            log_error "不支持的操作系统"
            exit 1
            ;;
    esac
    
    sleep 3
}

# 启动Redis服务
start_redis() {
    case $OS in
        "debian")
            sudo systemctl start redis-server
            ;;
        "redhat")
            sudo systemctl start redis
            ;;
        "macos")
            brew services start redis
            ;;
        *)
            log_error "不支持的操作系统"
            exit 1
            ;;
    esac
    
    sleep 2
}

# 设置Python环境
setup_python_env() {
    log_info "设置Python环境..."
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    log_success "虚拟环境已激活"
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip setuptools wheel
    
    # 安装数据库驱动
    log_info "安装数据库驱动..."
    pip install psycopg2-binary redis
    
    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装项目依赖..."
        pip install -r requirements.txt
        log_success "依赖安装完成"
    else
        log_error "requirements.txt文件不存在"
        exit 1
    fi
}

# 配置环境变量
setup_config() {
    log_info "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "已创建.env文件"
        else
            log_error ".env.example文件不存在"
            exit 1
        fi
    else
        log_info ".env文件已存在"
    fi
    
    # 创建必要目录
    mkdir -p logs uploads
    log_success "创建必要目录完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    if [ -f "init_database.sh" ]; then
        chmod +x init_database.sh
        ./init_database.sh
        
        if [ $? -eq 0 ]; then
            log_success "数据库初始化完成"
        else
            log_error "数据库初始化失败"
            exit 1
        fi
    else
        log_error "init_database.sh文件不存在"
        exit 1
    fi
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 检查Python模块
    python3 -c "
import sys
sys.path.append('.')

modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2', 'pydantic', 'pandas', 'numpy']
failed = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module}')
        failed.append(module)

if failed:
    print(f'\\n⚠️ 模块导入失败: {failed}')
    sys.exit(1)
else:
    print('\\n🎉 所有核心模块正常')
"
    
    if [ $? -ne 0 ]; then
        log_error "模块验证失败"
        exit 1
    fi
    
    # 测试数据库连接
    python3 -c "
import sys
sys.path.append('.')

try:
    from app.core.config import settings
    print(f'✅ 配置加载成功')
    
    from app.database.database import test_connection
    import asyncio
    
    async def test():
        result = await test_connection()
        if result:
            print('✅ 数据库连接测试成功')
            return True
        else:
            print('❌ 数据库连接测试失败')
            return False
    
    if not asyncio.run(test()):
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 测试失败: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "安装验证完成"
    else
        log_error "安装验证失败"
        exit 1
    fi
}

# Docker部署选项
deploy_with_docker() {
    log_info "使用Docker部署..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        log_success "Docker部署完成"
    else
        log_error "docker-compose.yml文件不存在"
        exit 1
    fi
}

# 主函数
main() {
    echo "🚀 开始部署股票交易系统..."
    echo "=================================="
    
    # 检查是否使用Docker部署
    if [ "$1" = "--docker" ]; then
        deploy_with_docker
        return
    fi
    
    # 检测操作系统
    detect_os
    
    # 检查系统要求
    check_requirements
    
    # 设置数据库服务
    setup_databases
    
    # 设置Python环境
    setup_python_env
    
    # 配置环境变量
    setup_config
    
    # 初始化数据库
    init_database
    
    # 验证安装
    verify_installation
    
    echo ""
    echo "🎉 部署完成！"
    echo "=================================="
    echo ""
    echo "🚀 启动应用:"
    echo "   source venv/bin/activate"
    echo "   python3 main.py"
    echo ""
    echo "📖 访问地址:"
    echo "   API文档: http://localhost:8080/docs"
    echo "   应用首页: http://localhost:8080"
    echo ""
    echo "💡 提示:"
    echo "   - 数据库已初始化完成"
    echo "   - 如需重置数据库，运行: ./init_database.sh"
    echo "   - 根据需要修改.env文件中的配置"
    echo "   - 如果使用Tushare，请在.env中设置TUSHARE_TOKEN"
    echo ""
    echo "🐳 Docker部署:"
    echo "   bash $0 --docker"
}

# 运行主函数
main "$@"