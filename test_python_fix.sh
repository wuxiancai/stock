#!/bin/bash

echo "🧪 测试修复后的 Python 版本选择..."

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

# 测试虚拟环境创建
echo "🧪 测试虚拟环境创建..."
if [ -d "test_venv" ]; then
    rm -rf test_venv
fi

echo "📦 使用 $PYTHON_CMD 创建测试虚拟环境..."
$PYTHON_CMD -m venv test_venv

echo "🔄 激活测试虚拟环境..."
source test_venv/bin/activate

# 验证虚拟环境中的 Python 版本
VENV_PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ 测试虚拟环境 Python 版本: $VENV_PYTHON_VERSION"

# 检查版本是否匹配
if [[ "$VENV_PYTHON_VERSION" == "$PYTHON_VERSION" ]]; then
    echo "✅ 版本匹配成功！"
else
    echo "❌ 版本不匹配！期望: $PYTHON_VERSION, 实际: $VENV_PYTHON_VERSION"
fi

# 清理
deactivate
rm -rf test_venv

echo "🎯 测试完成！"

# 如果是 Python 3.13，给出建议
if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo ""
    echo "⚠️ 检测到 Python 3.13，建议安装 Python 3.12："
    echo "   brew install python@3.12"
    echo "   然后重新运行安装脚本"
fi