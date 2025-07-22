#!/bin/bash

# 股票交易系统 - 第三步：应用启动脚本
# 启动Web应用和相关服务

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

echo "🚀 股票交易系统部署 - 第三步：启动应用"
echo "=================================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    log_error "虚拟环境不存在，请先运行 step1_environment_setup.sh"
    exit 1
fi

# 检查环境配置文件
if [ ! -f ".env" ]; then
    log_error "环境配置文件不存在，请先运行 step2_database_setup.sh"
    exit 1
fi

# 激活虚拟环境
log_step "激活Python虚拟环境"
source venv/bin/activate
log_success "虚拟环境已激活"

# 加载环境变量
log_step "加载环境变量"
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    log_success "环境变量已加载"
fi

# 检查服务状态
log_step "检查服务状态"

# 检查PostgreSQL
log_info "检查PostgreSQL连接..."
python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'stock_trading'),
        user=os.getenv('DB_USER', 'wuxiancai'),
        password=os.getenv('DB_PASSWORD', 'noneboy780308')
    )
    conn.close()
    print('✅ PostgreSQL连接正常')
except Exception as e:
    print(f'❌ PostgreSQL连接失败: {e}')
    exit(1)
"

# 检查Redis
log_info "检查Redis连接..."
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis连接正常')
except Exception as e:
    print(f'❌ Redis连接失败: {e}')
    print('请确保Redis服务已启动')
"

# 检查应用文件
log_step "检查应用文件"
app_files=("app/main.py" "main.py")
app_file=""

for file in "${app_files[@]}"; do
    if [ -f "$file" ]; then
        app_file="$file"
        break
    fi
done

if [ -z "$app_file" ]; then
    log_error "未找到应用主文件 (app/main.py 或 main.py)"
    log_info "请确保应用代码已正确部署"
    exit 1
fi

log_success "找到应用文件: $app_file"

# 运行数据库迁移（如果存在）
log_step "检查数据库迁移"
if [ -f "alembic.ini" ] && [ -d "alembic" ]; then
    log_info "运行数据库迁移..."
    alembic upgrade head
    log_success "数据库迁移完成"
elif [ -f "app/database/migrations.py" ]; then
    log_info "运行数据库迁移脚本..."
    python app/database/migrations.py
    log_success "数据库迁移完成"
else
    log_info "未找到数据库迁移文件，跳过迁移"
fi

# 创建启动脚本
log_step "创建启动脚本"
cat > start.sh << 'EOF'
#!/bin/bash

# 股票交易系统启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 启动股票交易系统...${NC}"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ 环境变量已加载${NC}"
fi

# 检查应用文件并启动
if [ -f "app/main.py" ]; then
    echo -e "${BLUE}📡 启动FastAPI应用...${NC}"
    echo "访问地址: http://localhost:${PORT:-8080}"
    echo "API文档: http://localhost:${PORT:-8080}/docs"
    echo "按 Ctrl+C 停止服务"
    echo ""
    uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080} --reload
elif [ -f "main.py" ]; then
    echo -e "${BLUE}📡 启动FastAPI应用...${NC}"
    echo "访问地址: http://localhost:${PORT:-8080}"
    echo "API文档: http://localhost:${PORT:-8080}/docs"
    echo "按 Ctrl+C 停止服务"
    echo ""
    uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080} --reload
else
    echo "❌ 未找到应用主文件"
    exit 1
fi
EOF

chmod +x start.sh
log_success "启动脚本创建完成: start.sh"

# 创建开发启动脚本
cat > start_dev.sh << 'EOF'
#!/bin/bash

# 股票交易系统开发模式启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔧 启动股票交易系统 (开发模式)...${NC}"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    # 开发模式设置
    export DEBUG=true
    export LOG_LEVEL=DEBUG
    echo -e "${GREEN}✅ 环境变量已加载 (开发模式)${NC}"
fi

# 检查应用文件并启动
if [ -f "app/main.py" ]; then
    echo -e "${BLUE}📡 启动FastAPI应用 (开发模式)...${NC}"
    echo -e "${YELLOW}开发模式特性:${NC}"
    echo "  • 自动重载代码变更"
    echo "  • 详细调试日志"
    echo "  • 错误堆栈跟踪"
    echo ""
    echo "访问地址: http://localhost:${PORT:-8080}"
    echo "API文档: http://localhost:${PORT:-8080}/docs"
    echo "ReDoc文档: http://localhost:${PORT:-8080}/redoc"
    echo "按 Ctrl+C 停止服务"
    echo ""
    uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080} --reload --log-level debug
elif [ -f "main.py" ]; then
    echo -e "${BLUE}📡 启动FastAPI应用 (开发模式)...${NC}"
    echo -e "${YELLOW}开发模式特性:${NC}"
    echo "  • 自动重载代码变更"
    echo "  • 详细调试日志"
    echo "  • 错误堆栈跟踪"
    echo ""
    echo "访问地址: http://localhost:${PORT:-8080}"
    echo "API文档: http://localhost:${PORT:-8080}/docs"
    echo "ReDoc文档: http://localhost:${PORT:-8080}/redoc"
    echo "按 Ctrl+C 停止服务"
    echo ""
    uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8080} --reload --log-level debug
else
    echo "❌ 未找到应用主文件"
    exit 1
fi
EOF

chmod +x start_dev.sh
log_success "开发启动脚本创建完成: start_dev.sh"

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash

# 股票交易系统停止脚本

echo "🛑 停止股票交易系统..."

# 查找并停止uvicorn进程
pids=$(pgrep -f "uvicorn.*app" 2>/dev/null || true)
if [ -n "$pids" ]; then
    echo "停止应用进程: $pids"
    kill $pids
    sleep 2
    
    # 强制停止仍在运行的进程
    pids=$(pgrep -f "uvicorn.*app" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "强制停止进程: $pids"
        kill -9 $pids
    fi
    echo "✅ 应用已停止"
else
    echo "ℹ️  未找到运行中的应用进程"
fi
EOF

chmod +x stop.sh
log_success "停止脚本创建完成: stop.sh"

# 创建状态检查脚本
cat > status.sh << 'EOF'
#!/bin/bash

# 股票交易系统状态检查脚本

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 股票交易系统状态检查${NC}"
echo "=================================================="

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ 虚拟环境存在${NC}"
else
    echo -e "${RED}❌ 虚拟环境不存在${NC}"
fi

# 检查环境配置
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 环境配置文件存在${NC}"
else
    echo -e "${RED}❌ 环境配置文件不存在${NC}"
fi

# 检查应用进程
pids=$(pgrep -f "uvicorn.*app" 2>/dev/null || true)
if [ -n "$pids" ]; then
    echo -e "${GREEN}✅ 应用正在运行 (PID: $pids)${NC}"
else
    echo -e "${YELLOW}⚠️  应用未运行${NC}"
fi

# 激活虚拟环境并检查服务
if [ -f "venv/bin/activate" ] && [ -f ".env" ]; then
    source venv/bin/activate
    export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
    
    # 检查PostgreSQL
    echo -n "PostgreSQL: "
    python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'stock_trading'),
        user=os.getenv('DB_USER', 'wuxiancai'),
        password=os.getenv('DB_PASSWORD', 'noneboy780308')
    )
    conn.close()
    print('\033[0;32m✅ 连接正常\033[0m')
except Exception as e:
    print(f'\033[0;31m❌ 连接失败: {e}\033[0m')
" 2>/dev/null || echo -e "${RED}❌ 检查失败${NC}"
    
    # 检查Redis
    echo -n "Redis: "
    python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('\033[0;32m✅ 连接正常\033[0m')
except Exception as e:
    print(f'\033[0;31m❌ 连接失败: {e}\033[0m')
" 2>/dev/null || echo -e "${RED}❌ 检查失败${NC}"
fi

echo ""
echo "可用命令："
echo "  ./start.sh      - 启动应用"
echo "  ./start_dev.sh  - 启动应用 (开发模式)"
echo "  ./stop.sh       - 停止应用"
echo "  ./status.sh     - 检查状态"
EOF

chmod +x status.sh
log_success "状态检查脚本创建完成: status.sh"

echo ""
echo "✅ 第三步部署完成！"
echo "=================================================="
echo "已创建的脚本："
echo "  ✓ start.sh      - 生产模式启动脚本"
echo "  ✓ start_dev.sh  - 开发模式启动脚本"
echo "  ✓ stop.sh       - 停止脚本"
echo "  ✓ status.sh     - 状态检查脚本"
echo ""
echo "🚀 现在可以启动应用："
echo ""
echo "生产模式："
echo "  ./start.sh"
echo ""
echo "开发模式（推荐）："
echo "  ./start_dev.sh"
echo ""
echo "检查状态："
echo "  ./status.sh"
echo ""
echo "停止应用："
echo "  ./stop.sh"
echo ""
echo "访问地址："
echo "  应用: http://localhost:8080"
echo "  API文档: http://localhost:8080/docs"
echo "  ReDoc文档: http://localhost:8080/redoc"