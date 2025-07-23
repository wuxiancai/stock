#!/bin/bash

echo "🐍 安装 Python 3.12 以解决兼容性问题..."

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ 需要先安装 Homebrew"
    echo "请运行: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 安装 Python 3.12
echo "📦 安装 Python 3.12..."
brew install python@3.12

# 验证安装
if command -v python3.12 >/dev/null 2>&1; then
    echo "✅ Python 3.12 安装成功！"
    echo "版本: $(python3.12 --version)"
    echo ""
    echo "🚀 现在可以运行安装脚本："
    echo "   ./setup_macos.sh"
else
    echo "❌ Python 3.12 安装失败"
    echo "请手动检查 Homebrew 安装"
fi