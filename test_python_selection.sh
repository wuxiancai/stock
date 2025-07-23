#!/bin/bash

echo "🧪 测试 Python 版本选择功能..."

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
        exit 1
    fi
fi

echo "🐍 选择的 Python 版本: $PYTHON_VERSION (命令: $PYTHON_CMD)"

# 显示详细版本信息
echo "📋 详细版本信息:"
$PYTHON_CMD --version
$PYTHON_CMD -c "import sys; print(f'完整版本: {sys.version}')"

# 根据版本给出建议
case "$PYTHON_VERSION" in
    "3.13")
        echo "⚠️ Python 3.13 - 最新版本，可能存在包兼容性问题"
        echo "   建议：如果遇到安装问题，考虑使用 Python 3.12"
        ;;
    "3.12")
        echo "✅ Python 3.12 - 推荐版本，兼容性最佳"
        ;;
    "3.11")
        echo "✅ Python 3.11 - 稳定版本，兼容性良好"
        ;;
    "3.10")
        echo "✅ Python 3.10 - 稳定版本，兼容性良好"
        ;;
    "3.9")
        echo "⚠️ Python 3.9 - 较老版本，建议升级到 3.12"
        ;;
    *)
        echo "⚠️ 未知版本，可能存在兼容性问题"
        ;;
esac

echo "🎯 测试完成！"