#!/bin/bash

# 股票交易系统环境设置脚本
# 适用于 macOS 开发环境

set -e

echo "🚀 开始设置股票交易系统开发环境..."

# 智能选择 Python 版本（优先使用兼容性好的版本）
echo "🔍 检测可用的 Python 版本..."

# 按优先级检查 Python 版本
PYTHON_CMD=""
PYTHON_VERSION=""

# 优先级：3.12 > 3.11 > 3.10 > 3.9 > 3.13
for version in "3.12" "3.11" "3.10" "3.9" "3.13"; do
    if command -v python$version >/dev/null 2>&1; then
        PYTHON_CMD="python$version"
        PYTHON_VERSION=$version
        echo "✅ 找到 Python $version"
        break
    fi
done

# 如果没找到特定版本，使用默认的 python3
if [[ -z "$PYTHON_CMD" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        echo "⚠️ 使用默认 Python 版本: $PYTHON_VERSION"
    else
        echo "❌ 错误：未找到 Python 3.x"
        echo "请先安装 Python 3.10 或更高版本："
        echo "  brew install python@3.12"
        exit 1
    fi
fi

echo "🐍 选择的 Python 版本: $PYTHON_VERSION (命令: $PYTHON_CMD)"

# 根据版本设置兼容性优化
case "$PYTHON_VERSION" in
    "3.13")
        echo "⚠️ Python 3.13 检测到，启用兼容性优化..."
        echo "   某些数据分析库可能存在兼容性问题"
        echo "   如遇到安装问题，可以："
        echo "   1. 使用 './install_deps_py313.sh' 脚本"
        echo "   2. 或安装 Python 3.12: brew install python@3.12"
        echo ""
        export SETUPTOOLS_USE_DISTUTILS=stdlib
        export CPPFLAGS="-I$(brew --prefix)/include"
        export LDFLAGS="-L$(brew --prefix)/lib"
        ;;
    "3.12"|"3.11"|"3.10"|"3.9")
        echo "✅ Python $PYTHON_VERSION 具有良好的包兼容性"
        ;;
    *)
        echo "⚠️ 未知 Python 版本，可能存在兼容性问题"
        ;;
esac

# 检查操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本仅适用于 macOS 系统"
    exit 1
fi

# 验证选择的 Python 版本是否满足最低要求
echo "🔍 验证 Python 版本要求..."
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo "❌ 选择的 Python $PYTHON_VERSION 版本过低，需要 3.9+ 版本"
    echo "请安装更新的 Python 版本："
    echo "  brew install python@3.12"
    exit 1
fi

echo "✅ Python 版本检查通过: $PYTHON_VERSION"

# 检查并安装 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew 已安装"
fi

# 检查并安装 PostgreSQL
echo "🔧 配置 PostgreSQL 环境..."

# 检测系统架构并设置路径
if [[ $(uname -m) == "arm64" ]]; then
    # Apple Silicon (M1/M2)
    PG_PATH="/opt/homebrew/opt/postgresql@15"
    echo "📱 检测到 Apple Silicon 架构"
else
    # Intel
    PG_PATH="/usr/local/opt/postgresql@15"
    echo "💻 检测到 Intel 架构"
fi

# 安装 PostgreSQL
if ! command -v psql &> /dev/null || ! brew list postgresql@15 &> /dev/null; then
    echo "📦 安装 PostgreSQL@15..."
    brew install postgresql@15
else
    echo "✅ PostgreSQL@15 已安装"
fi

# 强制链接 PostgreSQL 工具（解决 pg_config 问题）
echo "🔗 链接 PostgreSQL 工具..."
brew link postgresql@15 --force --overwrite 2>/dev/null || true

# 设置环境变量
echo "⚙️ 配置环境变量..."
export PATH="$PG_PATH/bin:$PATH"
export LDFLAGS="-L$PG_PATH/lib"
export CPPFLAGS="-I$PG_PATH/include"
export PKG_CONFIG_PATH="$PG_PATH/lib/pkgconfig"

# 验证 pg_config 是否可用
if command -v pg_config &> /dev/null; then
    echo "✅ pg_config 配置成功: $(pg_config --version)"
else
    echo "⚠️ pg_config 仍未找到，尝试手动配置..."
    if [ -f "$PG_PATH/bin/pg_config" ]; then
        export PATH="$PG_PATH/bin:$PATH"
        echo "✅ 手动添加 pg_config 路径成功"
    else
        echo "❌ 无法找到 pg_config，PostgreSQL 安装可能有问题"
        echo "🔧 尝试重新安装 PostgreSQL..."
        brew uninstall postgresql@15 --ignore-dependencies 2>/dev/null || true
        brew install postgresql@15
        brew link postgresql@15 --force --overwrite
        export PATH="$PG_PATH/bin:$PATH"
    fi
fi

# 启动 PostgreSQL 服务
echo "🚀 启动 PostgreSQL 服务..."
brew services start postgresql@15
sleep 3

# 检查并安装 Redis
if ! command -v redis-server &> /dev/null; then
    echo "📦 安装 Redis..."
    brew install redis
    brew services start redis
else
    echo "✅ Redis 已安装"
fi

# 检查并安装 TA-Lib
if ! brew list ta-lib &> /dev/null; then
    echo "📦 安装 TA-Lib..."
    brew install ta-lib
else
    echo "✅ TA-Lib 已安装"
fi

# 创建虚拟环境（强制重新创建以确保使用正确的 Python 版本）
echo "🔧 创建 Python 虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️ 删除现有虚拟环境（可能使用了错误的 Python 版本）..."
    rm -rf venv
fi

echo "📦 使用 $PYTHON_CMD 创建新的虚拟环境..."
$PYTHON_CMD -m venv venv

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 验证虚拟环境中的 Python 版本
VENV_PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ 虚拟环境 Python 版本: $VENV_PYTHON_VERSION"

# 确保虚拟环境使用了正确的 Python 版本
if [[ "$VENV_PYTHON_VERSION" != "$PYTHON_VERSION" ]]; then
    echo "❌ 虚拟环境 Python 版本不匹配！"
    echo "   期望: $PYTHON_VERSION"
    echo "   实际: $VENV_PYTHON_VERSION"
    echo "🔧 重新创建虚拟环境..."
    deactivate 2>/dev/null || true
    rm -rf venv
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    VENV_PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "✅ 重新创建后的虚拟环境 Python 版本: $VENV_PYTHON_VERSION"
fi

# 升级 pip
echo "📦 升级 pip..."
pip install --upgrade pip setuptools wheel

# 安装 Python 依赖
echo "📦 安装 Python 依赖包..."

# 智能 psycopg2 安装策略（集成修复逻辑）
echo "🔧 智能安装 psycopg2-binary..."

# 清理之前的安装缓存
pip cache purge

# 第一次尝试：安装指定版本
if pip install psycopg2-binary==2.9.10; then
    echo "✅ psycopg2-binary 2.9.10 安装成功"
else
    echo "⚠️ psycopg2-binary 2.9.10 安装失败，开始智能修复..."
    
    # 修复步骤1：重新配置环境变量
    echo "🔧 重新配置 PostgreSQL 环境变量..."
    export PATH="$PG_PATH/bin:$PATH"
    export LDFLAGS="-L$PG_PATH/lib"
    export CPPFLAGS="-I$PG_PATH/include"
    export PKG_CONFIG_PATH="$PG_PATH/lib/pkgconfig"
    
    # 修复步骤2：验证 pg_config
    if ! command -v pg_config &> /dev/null; then
        echo "🔧 pg_config 不可用，尝试强制链接 PostgreSQL..."
        brew link postgresql@15 --force --overwrite
        export PATH="$PG_PATH/bin:$PATH"
    fi
    
    # 修复步骤3：再次验证 pg_config
    if command -v pg_config &> /dev/null; then
        echo "✅ pg_config 可用: $(which pg_config)"
        echo "✅ PostgreSQL 版本: $(pg_config --version)"
    else
        echo "⚠️ pg_config 仍然不可用，尝试手动添加路径..."
        export PATH="$PG_PATH/bin:$PATH"
    fi
    
    # 修复步骤4：尝试安装最新版本
    if pip install psycopg2-binary; then
        echo "✅ psycopg2-binary 最新版本安装成功"
    else
        echo "⚠️ psycopg2-binary 仍然失败，尝试从源码编译..."
        
        # 修复步骤5：尝试源码编译（作为最后手段）
        if pip install psycopg2; then
            echo "✅ psycopg2 源码编译成功"
        else
            echo "❌ 所有 psycopg2 安装方法都失败"
            echo ""
            echo "🔧 自动修复建议："
            echo "   这可能是 Python 3.13 兼容性问题"
            echo "   1. 尝试安装 Python 3.12: brew install python@3.12"
            echo "   2. 或者重新安装 PostgreSQL: brew reinstall postgresql@15"
            echo "   3. 或者手动运行: pip install psycopg2-binary"
            echo ""
            echo "⚠️ 继续安装其他依赖，但数据库功能可能不可用..."
            PSYCOPG2_FAILED=true
        fi
    fi
fi

# 验证 psycopg2 安装（如果成功安装）
if [ "$PSYCOPG2_FAILED" != "true" ]; then
    echo "🔍 验证 psycopg2 安装..."
    if python -c "import psycopg2; print('✅ psycopg2 版本:', psycopg2.__version__)" 2>/dev/null; then
        echo "✅ psycopg2 验证成功"
    else
        echo "⚠️ psycopg2 导入失败，但继续安装其他依赖..."
        PSYCOPG2_FAILED=true
    fi
fi

# 智能依赖安装策略
echo "📦 安装其他 Python 依赖..."

# Python 3.13 兼容性检查和优化
if [[ "$VENV_PYTHON_VERSION" == "3.13" ]]; then
    echo "⚠️ Python 3.13 检测到，启用兼容性优化..."
    
    # 设置编译优化选项
    export CFLAGS="-O2"
    export CXXFLAGS="-O2"
    export PIP_NO_BUILD_ISOLATION=false
    export PIP_USE_PEP517=true
    
    # 优先使用预编译包
    pip install --upgrade pip setuptools wheel
    
    echo "🔧 Python 3.13 优化配置完成"
fi

# 核心依赖优先安装（使用最新版本，确保兼容性）
CORE_DEPS=(
    "fastapi"
    "uvicorn[standard]"
    "sqlalchemy"
    "alembic"
    "redis"
    "python-dotenv"
)

# 可选依赖（如果安装失败不影响核心功能）
OPTIONAL_DEPS=(
    "talib-binary"  # 如果失败，会尝试 TA-Lib
    "pandas"
    "numpy"
    "matplotlib"
    "plotly"
    "yfinance"
    "tushare"
)

# Python 3.13 问题包列表（需要特殊处理）
PROBLEMATIC_PACKAGES=(
    "pydantic"
    "pandas"
    "numpy"
    "scipy"
    "talib"
    "matplotlib"
)

# 安装函数：带超时和重试机制（macOS 兼容）
install_with_timeout() {
    local package="$1"
    local is_optional="$2"  # 是否为可选依赖
    local timeout_seconds=300  # 5分钟超时
    
    echo "📦 安装: $package (超时: ${timeout_seconds}秒)"
    
    # 检查是否是问题包
    local is_problematic=false
    for prob_pkg in "${PROBLEMATIC_PACKAGES[@]}"; do
        if [[ $package =~ $prob_pkg ]]; then
            is_problematic=true
            break
        fi
    done
    
    # macOS 兼容的超时函数
    run_with_timeout() {
        local cmd="$1"
        local timeout="$2"
        
        # 在后台运行命令
        eval "$cmd" &
        local pid=$!
        
        # 等待指定时间
        local count=0
        while [ $count -lt $timeout ]; do
            if ! kill -0 $pid 2>/dev/null; then
                # 进程已结束
                wait $pid
                return $?
            fi
            sleep 1
            count=$((count + 1))
        done
        
        # 超时，杀死进程
        kill $pid 2>/dev/null
        wait $pid 2>/dev/null
        echo "⚠️ 命令超时"
        return 124
    }
    
    # 特殊处理 talib-binary
    if [[ $package =~ "talib-binary" ]]; then
        echo "🔧 尝试安装 talib-binary..."
        if ! run_with_timeout "pip install talib-binary" $timeout_seconds; then
            echo "⚠️ talib-binary 安装失败，尝试使用系统 TA-Lib..."
            if ! run_with_timeout "pip install TA-Lib" $timeout_seconds; then
                echo "⚠️ TA-Lib 也安装失败，跳过技术分析功能..."
                return 1
            fi
        fi
        return 0
    fi
    
    if [[ "$is_problematic" == "true" && "$VENV_PYTHON_VERSION" == "3.13" ]]; then
        echo "⚠️ 检测到问题包 $package，尝试安装最新兼容版本..."
        
        # 尝试安装最新版本（可能有 Python 3.13 支持）
        if ! run_with_timeout "pip install --no-cache-dir '$package'" $timeout_seconds; then
            if [[ "$is_optional" == "true" ]]; then
                echo "⚠️ 可选依赖 $package 安装失败，跳过..."
            else
                echo "⚠️ 核心依赖 $package 安装失败，跳过..."
            fi
            return 1
        fi
    else
        # 正常安装
        if ! run_with_timeout "pip install '$package'" $timeout_seconds; then
            if [[ "$is_optional" == "true" ]]; then
                echo "⚠️ 可选依赖 $package 安装失败，跳过..."
            else
                echo "⚠️ 核心依赖 $package 安装失败，跳过..."
            fi
            return 1
        fi
    fi
}

echo "🔧 优先安装核心依赖..."
for dep in "${CORE_DEPS[@]}"; do
    install_with_timeout "$dep" "false"  # false 表示核心依赖
done

echo "🔧 安装可选依赖..."
for dep in "${OPTIONAL_DEPS[@]}"; do
    install_with_timeout "$dep" "true"  # true 表示可选依赖
done

# Python 3.13 特殊修复：升级 SQLAlchemy 到最新版本
if [[ "$VENV_PYTHON_VERSION" == "3.13" ]]; then
    echo "🔧 Python 3.13 特殊修复：升级 SQLAlchemy..."
    pip install --upgrade sqlalchemy || echo "⚠️ SQLAlchemy 升级失败"
fi

# 尝试安装 requirements.txt 中的其他依赖（跳过已处理的）
echo "📦 安装 requirements.txt 中的其他依赖..."
echo "⏱️ 批量安装超时设置: 10分钟"

# macOS 兼容的批量安装超时函数
bulk_install_with_timeout() {
    local timeout_seconds=600  # 10分钟
    
    # 创建临时 requirements 文件，排除已处理的依赖
    temp_req=$(mktemp)
    
    # 构建已处理依赖的模式
    processed_patterns=""
    for dep in "${CORE_DEPS[@]}" "${OPTIONAL_DEPS[@]}"; do
        # 提取包名（去掉版本号）
        pkg_name=$(echo "$dep" | sed 's/\[.*\]//' | sed 's/==.*//' | sed 's/>=.*//' | sed 's/<=.*//')
        if [ -n "$processed_patterns" ]; then
            processed_patterns="$processed_patterns|$pkg_name"
        else
            processed_patterns="$pkg_name"
        fi
    done
    
    # 过滤 requirements.txt
    if [ -f requirements.txt ]; then
        grep -v -E "^[[:space:]]*($processed_patterns)" requirements.txt > "$temp_req" || true
        # 移除空行和注释
        sed -i '' '/^[[:space:]]*$/d' "$temp_req" 2>/dev/null || sed -i '/^[[:space:]]*$/d' "$temp_req"
        sed -i '' '/^[[:space:]]*#/d' "$temp_req" 2>/dev/null || sed -i '/^[[:space:]]*#/d' "$temp_req"
    fi
    
    # 如果临时文件为空，跳过安装
    if [ ! -s "$temp_req" ]; then
        echo "✅ 所有依赖已处理完成"
        rm -f "$temp_req"
        return 0
    fi
    
    echo "📋 剩余待安装的依赖："
    cat "$temp_req"
    
    # 在后台运行批量安装
    pip install -r "$temp_req" &
    local pid=$!
    
    # 等待指定时间
    local count=0
    while [ $count -lt $timeout_seconds ]; do
        if ! kill -0 $pid 2>/dev/null; then
            # 进程已结束
            wait $pid
            local exit_code=$?
            rm -f "$temp_req"
            return $exit_code
        fi
        sleep 1
        count=$((count + 1))
        
        # 每30秒显示一次进度
        if [ $((count % 30)) -eq 0 ]; then
            echo "⏳ 批量安装进行中... (已用时: ${count}秒)"
        fi
    done
    
    # 超时，杀死进程
    echo "⚠️ 批量安装超时，切换到逐个安装模式..."
    kill $pid 2>/dev/null
    wait $pid 2>/dev/null
    rm -f "$temp_req"
    return 124
}

if bulk_install_with_timeout; then
    echo "✅ 剩余依赖批量安装成功"
else
    echo "⚠️ 批量安装失败或超时，切换到逐个安装模式..."
    
    # 逐行读取 requirements.txt 并安装
    if [ -f requirements.txt ]; then
        while IFS= read -r line; do
            # 跳过注释和空行
            if [[ $line =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
                continue
            fi
            
            # 跳过已安装的 psycopg2-binary
            if [[ $line =~ psycopg2 ]]; then
                continue
            fi
            
            # 跳过已处理的核心依赖和可选依赖
            skip_line=false
            for dep in "${CORE_DEPS[@]}" "${OPTIONAL_DEPS[@]}"; do
                pkg_name=$(echo "$dep" | sed 's/\[.*\]//' | sed 's/==.*//' | sed 's/>=.*//' | sed 's/<=.*//')
                if [[ $line =~ $pkg_name ]]; then
                    skip_line=true
                    break
                fi
            done
            
            if [ "$skip_line" = false ]; then
                install_with_timeout "$line" "true"  # 其他依赖视为可选
            fi
        done < requirements.txt
    fi
fi

# 安装总结
echo ""
echo "📋 Python 依赖安装总结："
if [ "$PSYCOPG2_FAILED" = "true" ]; then
    echo "⚠️ psycopg2 安装失败 - 数据库功能可能受限"
else
    echo "✅ psycopg2 安装成功 - 数据库功能可用"
fi

# 验证核心依赖
echo "🔍 验证核心依赖..."
python -c "
import sys
failed_core = []
optional_available = []
optional_failed = []

# 检查核心依赖
core_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'alembic']
for pkg in core_packages:
    try:
        __import__(pkg)
    except ImportError:
        failed_core.append(pkg)

if not failed_core:
    print('✅ 所有核心依赖可用')
else:
    print('❌ 以下核心依赖不可用:', ', '.join(failed_core))

# 检查可选依赖
optional_packages = {
    'pandas': '数据处理',
    'numpy': '数值计算', 
    'matplotlib': '图表绘制',
    'plotly': '交互式图表',
    'yfinance': '股票数据获取',
    'tushare': '中国股票数据',
}

# 检查 talib
try:
    import talib
    optional_available.append('talib (技术分析)')
except ImportError:
    try:
        import talib_binary
        optional_available.append('talib-binary (技术分析)')
    except ImportError:
        optional_failed.append('talib/talib-binary (技术分析)')

for pkg, desc in optional_packages.items():
    try:
        __import__(pkg)
        optional_available.append(f'{pkg} ({desc})')
    except ImportError:
        optional_failed.append(f'{pkg} ({desc})')

if optional_available:
    print('✅ 可用的可选功能:')
    for pkg in optional_available:
        print(f'   - {pkg}')

if optional_failed:
    print('⚠️ 不可用的可选功能:')
    for pkg in optional_failed:
        print(f'   - {pkg}')
    print('   注意：这些功能不影响系统核心运行')
"

echo "✅ Python 依赖安装完成"

# 创建必要的目录
echo "📁 创建项目目录结构..."
mkdir -p logs
mkdir -p uploads
mkdir -p data
mkdir -p tests
mkdir -p scripts

# 设置数据库
echo "🗄️ 设置数据库..."

# 检查 PostgreSQL 是否运行
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "🔄 启动 PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# 创建数据库用户和数据库
psql postgres -c "CREATE USER stock_user WITH PASSWORD 'stock_password';" 2>/dev/null || echo "用户 stock_user 已存在"
psql postgres -c "CREATE DATABASE stock_trading_db OWNER stock_user;" 2>/dev/null || echo "数据库 stock_trading_db 已存在"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_trading_db TO stock_user;" 2>/dev/null

echo "✅ 数据库设置完成"

# 检查 Redis 是否运行
if ! redis-cli ping &> /dev/null; then
    echo "🔄 启动 Redis..."
    brew services start redis
    sleep 2
fi

echo "✅ Redis 服务已启动"

# 创建启动脚本
echo "📝 创建启动脚本..."

cat > start_dev.sh << 'EOF'
#!/bin/bash
# 开发环境启动脚本

set -e

echo "🚀 启动股票交易系统开发环境..."

# 激活虚拟环境
source venv/bin/activate

# 检查服务状态
echo "🔍 检查服务状态..."

# 检查 PostgreSQL
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "🔄 启动 PostgreSQL..."
    brew services start postgresql@15
    sleep 3
fi

# 检查 Redis
if ! redis-cli ping &> /dev/null; then
    echo "🔄 启动 Redis..."
    brew services start redis
    sleep 2
fi

echo "✅ 所有服务已就绪"

# 运行数据库迁移
echo "🗄️ 运行数据库迁移..."
python -m alembic upgrade head

# 启动后端服务
echo "🚀 启动后端服务..."
python main.py
EOF

chmod +x start_dev.sh

# 创建停止脚本
cat > stop_dev.sh << 'EOF'
#!/bin/bash
# 开发环境停止脚本

echo "🛑 停止股票交易系统开发环境..."

# 停止后端进程
pkill -f "python main.py" 2>/dev/null || echo "后端服务未运行"
pkill -f "uvicorn" 2>/dev/null || echo "Uvicorn 未运行"
pkill -f "celery" 2>/dev/null || echo "Celery 未运行"

echo "✅ 开发环境已停止"
EOF

chmod +x stop_dev.sh

# 创建测试脚本
cat > run_tests.sh << 'EOF'
#!/bin/bash
# 测试运行脚本

set -e

echo "🧪 运行测试..."

# 激活虚拟环境
source venv/bin/activate

# 运行测试
python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo "✅ 测试完成"
EOF

chmod +x run_tests.sh

# 保存环境变量到 shell 配置文件
echo "💾 保存环境变量配置..."
ENV_CONFIG="
# PostgreSQL 环境变量 (由 setup_macos.sh 添加)
export PATH=\"$PG_PATH/bin:\$PATH\"
export LDFLAGS=\"-L$PG_PATH/lib\"
export CPPFLAGS=\"-I$PG_PATH/include\"
export PKG_CONFIG_PATH=\"$PG_PATH/lib/pkgconfig\"
"

# 检查并添加到 shell 配置文件
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "PostgreSQL 环境变量" "$HOME/.zshrc"; then
        echo "$ENV_CONFIG" >> "$HOME/.zshrc"
        echo "✅ 环境变量已添加到 ~/.zshrc"
    else
        echo "✅ 环境变量已存在于 ~/.zshrc"
    fi
elif [ -f "$HOME/.bash_profile" ]; then
    if ! grep -q "PostgreSQL 环境变量" "$HOME/.bash_profile"; then
        echo "$ENV_CONFIG" >> "$HOME/.bash_profile"
        echo "✅ 环境变量已添加到 ~/.bash_profile"
    else
        echo "✅ 环境变量已存在于 ~/.bash_profile"
    fi
fi

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "⚠️ 请编辑 .env 文件，设置您的 TUSHARE_TOKEN"
else
    echo "✅ .env 文件已存在"
fi

# 创建集成的系统状态检查脚本
echo "📝 创建系统状态检查脚本..."

cat > check_status.sh << 'EOF'
#!/bin/bash
# 集成的系统状态检查脚本

echo "🔍 股票交易系统状态检查"
echo "=========================="

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 检查 Python 版本
echo ""
echo "🐍 Python 环境："
python --version
echo "虚拟环境路径: $(which python)"

# 检查核心依赖
echo ""
echo "📦 核心依赖检查："
python -c "
import sys
dependencies = {
    'psycopg2': 'PostgreSQL 数据库连接',
    'fastapi': 'Web 框架',
    'uvicorn': 'ASGI 服务器',
    'sqlalchemy': 'ORM 框架',
    'redis': 'Redis 客户端',
    'alembic': '数据库迁移工具'
}

for dep, desc in dependencies.items():
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', '未知版本')
        print(f'✅ {dep} ({desc}): {version}')
    except ImportError:
        print(f'❌ {dep} ({desc}): 未安装')
"

# 检查数据库连接
echo ""
echo "🗄️ 数据库连接检查："
python -c "
import psycopg2
from psycopg2 import OperationalError

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='stock_trading_db',
        user='stock_user',
        password='stock_password'
    )
    conn.close()
    print('✅ PostgreSQL 数据库连接成功')
except OperationalError as e:
    if 'role \"stock_user\" does not exist' in str(e):
        print('⚠️ 数据库用户不存在，请运行完整安装')
    elif 'database \"stock_trading_db\" does not exist' in str(e):
        print('⚠️ 数据库不存在，请运行完整安装')
    else:
        print(f'❌ 数据库连接失败: {e}')
except Exception as e:
    print(f'❌ 数据库连接错误: {e}')
"

# 检查 Redis 连接
echo ""
echo "🔴 Redis 连接检查："
python -c "
import redis

try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis 连接成功')
except Exception as e:
    print(f'❌ Redis 连接失败: {e}')
"

# 检查服务状态
echo ""
echo "🔧 系统服务状态："

# 检查 PostgreSQL
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "✅ PostgreSQL 服务运行中"
else
    echo "❌ PostgreSQL 服务未运行"
fi

# 检查 Redis
if redis-cli ping &> /dev/null; then
    echo "✅ Redis 服务运行中"
else
    echo "❌ Redis 服务未运行"
fi

# 检查端口占用
echo ""
echo "🌐 端口状态检查："
if lsof -i :8080 &> /dev/null; then
    echo "⚠️ 端口 8080 已被占用"
    lsof -i :8080
else
    echo "✅ 端口 8080 可用"
fi

# 检查环境变量
echo ""
echo "🔧 环境变量检查："
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    if grep -q "TUSHARE_TOKEN" .env && ! grep -q "your_tushare_token_here" .env; then
        echo "✅ TUSHARE_TOKEN 已配置"
    else
        echo "⚠️ TUSHARE_TOKEN 需要配置"
    fi
else
    echo "❌ .env 文件不存在"
fi

echo ""
echo "📋 状态检查完成"
echo "=========================="
EOF

chmod +x check_status.sh

# 运行集成的系统验证
echo ""
echo "🔍 运行系统验证..."
echo "=========================="

# 最终验证 - 检查关键组件
echo "📋 最终系统验证："

# 验证虚拟环境
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "✅ 虚拟环境创建成功"
else
    echo "❌ 虚拟环境创建失败"
fi

# 验证核心依赖（在虚拟环境中）
source venv/bin/activate
echo "🔍 验证核心依赖安装..."
python -c "
import sys
success_count = 0
total_count = 0

dependencies = ['psycopg2', 'fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'alembic']

for dep in dependencies:
    total_count += 1
    try:
        __import__(dep)
        success_count += 1
        print(f'✅ {dep}')
    except ImportError:
        print(f'❌ {dep}')

print(f'\\n📊 依赖安装成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)')

if success_count >= 4:  # 至少4个核心依赖成功
    print('✅ 核心功能可用')
    sys.exit(0)
else:
    print('⚠️ 部分核心功能可能不可用')
    sys.exit(1)
"

DEPS_STATUS=$?

# 验证服务状态
echo ""
echo "🔍 验证系统服务..."
SERVICES_OK=true

if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "⚠️ PostgreSQL 未运行，尝试启动..."
    brew services start postgresql@15
    sleep 3
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo "✅ PostgreSQL 启动成功"
    else
        echo "❌ PostgreSQL 启动失败"
        SERVICES_OK=false
    fi
else
    echo "✅ PostgreSQL 运行正常"
fi

if ! redis-cli ping &> /dev/null; then
    echo "⚠️ Redis 未运行，尝试启动..."
    brew services start redis
    sleep 2
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis 启动成功"
    else
        echo "❌ Redis 启动失败"
        SERVICES_OK=false
    fi
else
    echo "✅ Redis 运行正常"
fi

echo ""
echo "🎉 环境设置完成！"
echo ""
echo "📋 安装总结："
if [ $DEPS_STATUS -eq 0 ]; then
    echo "✅ Python 依赖安装成功"
else
    echo "⚠️ 部分 Python 依赖安装失败"
fi

if [ "$SERVICES_OK" = true ]; then
    echo "✅ 系统服务运行正常"
else
    echo "⚠️ 部分系统服务需要手动检查"
fi

if [ "$PSYCOPG2_FAILED" = "true" ]; then
    echo "⚠️ psycopg2 安装失败 - 数据库功能受限"
    echo "   建议运行: pip install psycopg2-binary"
fi

echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件，设置您的 TUSHARE_TOKEN"
echo "2. 运行 './start_dev.sh' 启动开发环境"
echo "3. 运行 './run_tests.sh' 执行测试"
echo "4. 运行 './stop_dev.sh' 停止开发环境"
echo "5. 运行 './check_status.sh' 检查系统状态"
echo ""
echo "🔗 服务地址："
echo "- 后端 API: http://localhost:8080"
echo "- API 文档: http://localhost:8080/docs"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo ""
echo "📝 重要提示："
echo "- 环境变量已保存到 shell 配置文件"
echo "- 请重新启动终端或运行 'source ~/.zshrc' 使环境变量生效"
echo "- 首次运行前请确保网络连接正常"
echo "- 开发时请使用虚拟环境: source venv/bin/activate"
echo ""
echo "🔍 故障排除："
echo "- 如遇到依赖问题，运行 './check_status.sh' 诊断"
echo "- 如遇到 psycopg2 问题，检查 PostgreSQL 安装"
echo "- 如遇到权限问题，确保 Homebrew 权限正确"
echo ""