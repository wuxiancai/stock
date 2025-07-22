#!/bin/bash

# 股票交易系统一键部署脚本
# 支持 macOS 和 Linux 系统

set -e  # 遇到错误立即退出

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

# 错误处理函数
handle_error() {
    log_error "部署过程中发生错误，退出码: $1"
    log_error "错误发生在第 $2 行"
    log_error "请检查上述错误信息并重新运行脚本"
    exit 1
}

# 设置错误陷阱
trap 'handle_error $? $LINENO' ERR

echo "🚀 开始一键部署股票交易系统..."

# 检查系统要求
log_info "检查系统要求..."

# 检查操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_success "检测到Linux系统"
    OS_TYPE="linux"
    
    # 检测Linux发行版
    if [ -f /etc/debian_version ]; then
        DISTRO="debian"
        log_success "检测到Debian/Ubuntu系统"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="redhat"
        log_success "检测到RedHat/CentOS/Fedora系统"
    else
        DISTRO="unknown"
        log_warning "未知的Linux发行版"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_success "检测到macOS系统"
    OS_TYPE="macos"
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        log_warning "未检测到Homebrew，正在安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        log_success "Homebrew已安装"
    fi
else
    log_error "不支持的操作系统: $OSTYPE"
    log_error "支持的系统: Linux (Debian/Ubuntu, RedHat/CentOS/Fedora), macOS"
    exit 1
fi

# 检查基本工具
log_info "检查基本工具..."
REQUIRED_TOOLS=("curl" "git")

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        log_warning "$tool 未安装，正在安装..."
        
        if [[ "$OS_TYPE" == "linux" ]]; then
            if [[ "$DISTRO" == "debian" ]]; then
                sudo apt-get update
                sudo apt-get install -y "$tool"
            elif [[ "$DISTRO" == "redhat" ]]; then
                if command -v dnf &> /dev/null; then
                    sudo dnf install -y "$tool"
                else
                    sudo yum install -y "$tool"
                fi
            fi
        elif [[ "$OS_TYPE" == "macos" ]]; then
            brew install "$tool"
        fi
    else
        log_success "$tool 已安装"
    fi
done

# 检查Python版本
echo "🐍 检查Python版本..."

if ! command -v python3 &> /dev/null; then
    echo "⚠️ Python3未安装，正在安装..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        if [[ "$DISTRO" == "debian" ]]; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev
        elif [[ "$DISTRO" == "redhat" ]]; then
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3 python3-pip python3-devel
            else
                sudo yum install -y python3 python3-pip python3-devel
            fi
        fi
    elif [[ "$OS_TYPE" == "macos" ]]; then
        brew install python@3.11
    fi
    
    # 再次检查
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3安装失败，请手动安装"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python版本过低，需要Python $REQUIRED_VERSION+，当前版本: $PYTHON_VERSION"
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "💡 尝试安装更新的Python版本..."
        brew install python@3.11
        # 创建符号链接
        brew link --overwrite python@3.11
    fi
    
    # 再次检查版本
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo "❌ Python版本仍然过低: $PYTHON_VERSION"
        exit 1
    fi
fi

echo "✅ Python版本检查通过: $PYTHON_VERSION"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "⚠️ pip3未安装，正在安装..."
    
    if [[ "$OS_TYPE" == "linux" ]]; then
        if [[ "$DISTRO" == "debian" ]]; then
            sudo apt-get install -y python3-pip
        elif [[ "$DISTRO" == "redhat" ]]; then
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3-pip
            else
                sudo yum install -y python3-pip
            fi
        fi
    elif [[ "$OS_TYPE" == "macos" ]]; then
        python3 -m ensurepip --upgrade
    fi
fi

echo "✅ pip3已安装"

# 创建并激活虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 安装依赖
echo "📦 安装Python依赖..."

# 升级pip
pip install --upgrade pip

# 安装PostgreSQL开发库（psycopg2需要）
echo "🔧 安装PostgreSQL开发库..."
if [[ "$OS_TYPE" == "linux" ]]; then
    if [[ "$DISTRO" == "debian" ]]; then
        sudo apt-get install -y libpq-dev build-essential
    elif [[ "$DISTRO" == "redhat" ]]; then
        if command -v dnf &> /dev/null; then
            sudo dnf install -y postgresql-devel gcc
        else
            sudo yum install -y postgresql-devel gcc
        fi
    fi
elif [[ "$OS_TYPE" == "macos" ]]; then
    # macOS通过brew安装的PostgreSQL已包含开发库
    echo "✅ macOS PostgreSQL开发库已包含"
fi

# 安装psycopg2-binary（更简单的选择）
echo "📦 安装psycopg2-binary..."
pip install psycopg2-binary

# 安装其他依赖
if [ -f "requirements.txt" ]; then
    echo "📦 安装requirements.txt中的依赖..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt文件不存在，安装基本依赖..."
    pip install fastapi uvicorn sqlalchemy alembic redis python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv
fi

# 创建必要目录
mkdir -p logs uploads
sudo apt install postgresql-client
# 配置环境变量
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📋 已创建.env文件，请根据需要修改配置"
fi

# 检查PostgreSQL服务
echo "🗄️ 检查PostgreSQL服务..."

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL客户端未安装，正在安装..."
    
    # 检测操作系统并安装PostgreSQL
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib postgresql-client
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
        elif [ -f /etc/redhat-release ]; then
            # RedHat/CentOS/Fedora
            if command -v dnf &> /dev/null; then
                sudo dnf install -y postgresql postgresql-server postgresql-contrib
                sudo postgresql-setup --initdb
            else
                sudo yum install -y postgresql postgresql-server postgresql-contrib
                sudo postgresql-setup initdb
            fi
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
        else
            echo "❌ 不支持的Linux发行版，请手动安装PostgreSQL"
            echo "💡 或使用Docker部署: bash start_docker.sh"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "❌ 需要先安装Homebrew"
            echo "💡 安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        brew install postgresql
        brew services start postgresql
    else
        echo "❌ 不支持的操作系统，请手动安装PostgreSQL"
        echo "💡 或使用Docker部署: bash start_docker.sh"
        exit 1
    fi
    
    # 等待PostgreSQL启动
    sleep 5
fi

# 检查PostgreSQL服务状态
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL服务未运行，尝试启动..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux系统
        if systemctl list-unit-files | grep -q "^postgresql.service"; then
            sudo systemctl start postgresql
        elif systemctl list-unit-files | grep -q "^postgresql-"; then
            # 查找具体的PostgreSQL服务名（如postgresql-13.service）
            PG_SERVICE=$(systemctl list-unit-files | grep "^postgresql-" | head -1 | awk '{print $1}')
            echo "🔧 启动PostgreSQL服务: $PG_SERVICE"
            sudo systemctl start "$PG_SERVICE"
        else
            echo "❌ 找不到PostgreSQL服务"
            echo "💡 请检查PostgreSQL是否正确安装，或使用Docker部署"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS系统
        if command -v brew &> /dev/null; then
            brew services start postgresql
        else
            echo "❌ 需要Homebrew来管理PostgreSQL服务"
            exit 1
        fi
    fi
    
    # 等待服务启动
    sleep 3
fi

# 检查PostgreSQL是否成功启动
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL服务正在运行"
else
    echo "❌ PostgreSQL服务启动失败"
    echo "💡 建议使用Docker部署: bash start_docker.sh"
    exit 1
fi

# 初始化数据库
echo "🗄️ 初始化数据库..."
chmod +x init_database.sh
./init_database.sh

if [ $? -ne 0 ]; then
    echo "❌ 数据库初始化失败"
    exit 1
fi

# 检查Redis
echo "🔧 检查Redis服务..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️ Redis客户端未安装，正在安装..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y redis-server
            sudo systemctl enable redis-server
            sudo systemctl start redis-server
        elif [ -f /etc/redhat-release ]; then
            # RedHat/CentOS/Fedora
            if command -v dnf &> /dev/null; then
                sudo dnf install -y redis
            else
                sudo yum install -y redis
            fi
            sudo systemctl enable redis
            sudo systemctl start redis
        else
            echo "⚠️ 不支持的Linux发行版，请手动安装Redis"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
            brew services start redis
        else
            echo "⚠️ 需要Homebrew来安装Redis"
        fi
    else
        echo "⚠️ 不支持的操作系统，请手动安装Redis"
    fi
    
    sleep 2
fi

if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️ Redis未运行，尝试启动..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux系统
        if systemctl list-unit-files | grep -q "^redis-server.service"; then
            sudo systemctl start redis-server
        elif systemctl list-unit-files | grep -q "^redis.service"; then
            sudo systemctl start redis
        else
            echo "⚠️ 找不到Redis服务，请手动启动"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS系统
        if command -v brew &> /dev/null; then
            brew services start redis
        else
            echo "⚠️ 需要Homebrew来管理Redis服务"
        fi
    fi
    
    sleep 2
fi

# 检查Redis连接
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis服务正在运行"
else
    echo "⚠️ Redis服务未运行，应用程序可能无法正常工作"
fi

# 检查核心模块
echo "🔍 检查核心模块..."
python3 -c "
modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2', 'pydantic', 'pandas', 'numpy']
failed = []
for m in modules:
    try:
        __import__(m)
        print(f'✅ {m}')
    except:
        print(f'❌ {m}')
        failed.append(m)

# 特别检查 pydantic_settings
try:
    import pydantic_settings
    print('✅ pydantic_settings')
except:
    print('❌ pydantic_settings - 正在安装...')
    import subprocess
    subprocess.run(['pip', 'install', 'pydantic-settings>=2.0.0'], check=True)
    print('✅ pydantic_settings 安装完成')
        
if failed:
    print(f'\\n⚠️ 模块导入失败: {failed}')
    print('请检查依赖安装')
    exit(1)
else:
    print('\\n🎉 所有核心模块正常')
"

# 最终测试
echo "🔗 最终测试..."
python3 -c "
import sys
sys.path.append('.')

try:
    from app.core.config import settings
    print(f'✅ 配置加载成功')
    print(f'   数据库URL: {settings.DATABASE_URL}')
    
    from app.database.database import test_connection
    import asyncio
    
    async def test():
        result = await test_connection()
        if result:
            print('✅ 数据库连接测试成功')
        else:
            print('❌ 数据库连接测试失败')
            return False
        return True
    
    if not asyncio.run(test()):
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 测试失败: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "🚀 启动应用:"
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
else
    echo "❌ 部署失败，请检查错误信息"
    exit 1
fi