#!/bin/bash

# 股票交易系统 - 第一步：环境和依赖部署
# 自动安装所有必需的环境和依赖

set -euo pipefail

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

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
    log_error "第一步部署失败，退出码: $1"
    log_error "请检查错误信息并重新运行"
    exit 1
}

trap 'handle_error $?' ERR

echo "🚀 股票交易系统部署 - 第一步：环境和依赖安装"
echo "=================================================="

# 检测操作系统
log_step "检测操作系统环境"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        log_success "检测到 $PRETTY_NAME"
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
            *)
                log_error "不支持的Linux发行版: $ID"
                exit 1
                ;;
        esac
    else
        log_error "无法检测Linux发行版"
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    PKG_MANAGER="brew"
    log_success "检测到macOS系统"
else
    log_error "不支持的操作系统: $OSTYPE"
    exit 1
fi

# 安装包管理器（macOS需要Homebrew）
if [[ "$OS_TYPE" == "macos" ]]; then
    log_step "检查Homebrew"
    if ! command -v brew >/dev/null 2>&1; then
        log_info "安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加到PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        log_success "Homebrew安装完成"
    else
        log_success "Homebrew已安装"
    fi
fi

# 更新包管理器
log_step "更新包管理器"
if [[ "$DISTRO" == "debian" ]]; then
    sudo apt-get update
elif [[ "$DISTRO" == "redhat" ]]; then
    sudo $PKG_MANAGER update -y
elif [[ "$OS_TYPE" == "macos" ]]; then
    brew update
fi

# 安装基本工具
log_step "安装基本工具"
basic_tools=()

if [[ "$DISTRO" == "debian" ]]; then
    basic_tools=(
        "curl" "wget" "git" "build-essential" "software-properties-common"
        "apt-transport-https" "ca-certificates" "gnupg" "lsb-release"
    )
elif [[ "$DISTRO" == "redhat" ]]; then
    basic_tools=(
        "curl" "wget" "git" "gcc" "gcc-c++" "make" "which"
    )
elif [[ "$OS_TYPE" == "macos" ]]; then
    basic_tools=(
        "curl" "wget" "git"
    )
fi

for tool in "${basic_tools[@]}"; do
    if [[ "$OS_TYPE" == "linux" ]]; then
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_info "安装 $tool..."
            sudo $PKG_MANAGER install -y "$tool"
        else
            log_success "$tool 已安装"
        fi
    elif [[ "$OS_TYPE" == "macos" ]]; then
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_info "安装 $tool..."
            brew install "$tool"
        else
            log_success "$tool 已安装"
        fi
    fi
done

# 安装Python环境
log_step "安装Python环境"
if [[ "$DISTRO" == "debian" ]]; then
    python_packages=(
        "python3" "python3-pip" "python3-venv" "python3-dev"
        "python3-setuptools" "python3-wheel"
    )
    for pkg in "${python_packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            log_info "安装 $pkg..."
            sudo apt-get install -y "$pkg"
        else
            log_success "$pkg 已安装"
        fi
    done
elif [[ "$DISTRO" == "redhat" ]]; then
    python_packages=(
        "python3" "python3-pip" "python3-devel" "python3-setuptools"
    )
    for pkg in "${python_packages[@]}"; do
        if ! rpm -q "$pkg" >/dev/null 2>&1; then
            log_info "安装 $pkg..."
            sudo $PKG_MANAGER install -y "$pkg"
        else
            log_success "$pkg 已安装"
        fi
    done
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! command -v python3 >/dev/null 2>&1; then
        log_info "安装Python3..."
        brew install python@3.11
    else
        log_success "Python3已安装"
    fi
fi

# 检查Python版本
log_step "验证Python版本"
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    log_error "未找到Python3"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
    log_error "Python版本过低，需要3.8+，当前: $PYTHON_VERSION"
    exit 1
fi

log_success "Python版本检查通过: $PYTHON_VERSION ($PYTHON_CMD)"

# 安装PostgreSQL客户端和开发库
log_step "安装PostgreSQL客户端和开发库"
if [[ "$DISTRO" == "debian" ]]; then
    pg_packages=("postgresql-client" "libpq-dev")
    for pkg in "${pg_packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            log_info "安装 $pkg..."
            sudo apt-get install -y "$pkg"
        else
            log_success "$pkg 已安装"
        fi
    done
elif [[ "$DISTRO" == "redhat" ]]; then
    pg_packages=("postgresql" "postgresql-devel")
    for pkg in "${pg_packages[@]}"; do
        if ! rpm -q "$pkg" >/dev/null 2>&1; then
            log_info "安装 $pkg..."
            sudo $PKG_MANAGER install -y "$pkg"
        else
            log_success "$pkg 已安装"
        fi
    done
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! command -v psql >/dev/null 2>&1; then
        log_info "安装PostgreSQL客户端..."
        brew install postgresql@14
    else
        log_success "PostgreSQL客户端已安装"
    fi
fi

# 安装Redis客户端
log_step "安装Redis客户端"
if [[ "$DISTRO" == "debian" ]]; then
    if ! dpkg -l | grep -q "^ii  redis-tools "; then
        log_info "安装redis-tools..."
        sudo apt-get install -y redis-tools
    else
        log_success "redis-tools已安装"
    fi
elif [[ "$DISTRO" == "redhat" ]]; then
    if ! rpm -q redis >/dev/null 2>&1; then
        log_info "安装redis..."
        sudo $PKG_MANAGER install -y redis
    else
        log_success "redis已安装"
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    if ! command -v redis-cli >/dev/null 2>&1; then
        log_info "安装Redis..."
        brew install redis
    else
        log_success "Redis已安装"
    fi
fi

# 创建Python虚拟环境
log_step "创建Python虚拟环境"
if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    $PYTHON_CMD -m venv venv
    log_success "虚拟环境创建完成"
else
    log_success "虚拟环境已存在"
fi

# 激活虚拟环境并安装Python依赖
log_step "安装Python依赖"
source venv/bin/activate

# 升级pip
log_info "升级pip..."
python -m pip install --upgrade pip setuptools wheel

# 安装psycopg2-binary
log_info "安装数据库驱动..."
python -m pip install psycopg2-binary

# 安装Redis客户端
log_info "安装Redis客户端..."
python -m pip install redis

# 安装项目依赖
if [ -f "requirements.txt" ]; then
    log_info "安装项目依赖..."
    python -m pip install -r requirements.txt
else
    log_warning "requirements.txt不存在，安装基本依赖..."
    python -m pip install \
        fastapi \
        uvicorn[standard] \
        sqlalchemy \
        alembic \
        python-multipart \
        python-jose[cryptography] \
        passlib[bcrypt] \
        python-dotenv \
        pydantic[email] \
        httpx \
        aiofiles
fi

log_success "Python依赖安装完成"

# 创建必要的目录
log_step "创建项目目录"
directories=("logs" "uploads" "data" "backups")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    else
        log_success "目录已存在: $dir"
    fi
done

# 设置目录权限
chmod 755 logs uploads data backups

echo ""
echo "✅ 第一步部署完成！"
echo "=================================================="
echo "已完成："
echo "  ✓ 操作系统环境检测"
echo "  ✓ 基本工具安装"
echo "  ✓ Python环境配置"
echo "  ✓ PostgreSQL客户端安装"
echo "  ✓ Redis客户端安装"
echo "  ✓ Python虚拟环境创建"
echo "  ✓ 项目依赖安装"
echo "  ✓ 必要目录创建"
echo ""
echo "下一步："
echo "  运行 ./step2_database_setup.sh 进行数据库安装和初始化"