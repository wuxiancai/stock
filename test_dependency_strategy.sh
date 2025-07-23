#!/bin/bash
# 测试新的依赖安装策略

echo "🧪 测试新的依赖安装策略"
echo "================================"

# 1. 测试 Python 版本选择
echo "🔍 1. Python 版本选择测试"
echo "可用的 Python 版本："
for version in 3.12 3.11 3.10 3.9 3.13; do
    if command -v python$version &> /dev/null; then
        actual_version=$(python$version --version 2>&1 | cut -d" " -f2)
        echo "  ✅ python$version -> $actual_version"
    else
        echo "  ❌ python$version 不可用"
    fi
done

# 2. 测试核心依赖列表
echo ""
echo "🔍 2. 核心依赖列表测试"
CORE_DEPS=(
    "fastapi"
    "uvicorn[standard]"
    "sqlalchemy"
    "alembic"
    "redis"
    "python-dotenv"
)

echo "核心依赖（无版本限制）："
for dep in "${CORE_DEPS[@]}"; do
    echo "  📦 $dep"
done

# 3. 测试可选依赖列表
echo ""
echo "🔍 3. 可选依赖列表测试"
OPTIONAL_DEPS=(
    "talib-binary"
    "pandas"
    "numpy"
    "matplotlib"
    "plotly"
    "yfinance"
    "tushare"
)

echo "可选依赖（安装失败不影响核心功能）："
for dep in "${OPTIONAL_DEPS[@]}"; do
    echo "  📦 $dep"
done

# 4. 测试 talib 安装策略
echo ""
echo "🔍 4. talib 安装策略测试"
echo "安装顺序："
echo "  1️⃣ 尝试 talib-binary（预编译，快速）"
echo "  2️⃣ 失败时尝试 TA-Lib（需要编译）"
echo "  3️⃣ 都失败时跳过技术分析功能"

# 5. 显示优势
echo ""
echo "✅ 新策略优势："
echo "  🎯 使用最新版本，避免版本不存在问题"
echo "  🛡️ 可选依赖失败不影响核心功能"
echo "  ⚡ 智能跳过已安装的包，提高效率"
echo "  🔧 自动处理 Python 版本兼容性"
echo "  📊 详细的安装状态报告"

echo ""
echo "🚀 运行完整安装："
echo "  ./setup_macos.sh"
echo ""
echo "📚 查看详细文档："
echo "  cat DEPENDENCY_STRATEGY.md"