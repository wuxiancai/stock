#!/bin/bash

# 股票交易系统启动脚本
# 自动激活虚拟环境并启动应用

echo "🚀 启动股票交易系统..."

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 激活虚拟环境..."
    source venv/bin/activate
    
    # 检查 pydantic_settings 是否存在
    if ! python3 -c "import pydantic_settings" 2>/dev/null; then
        echo "📦 安装缺失的 pydantic-settings..."
        pip install pydantic-settings>=2.0.0
    fi
    
    echo "🌟 在虚拟环境中启动应用..."
    python3 main.py
else
    echo "⚠️ 未发现虚拟环境，请先运行部署脚本："
    echo "   bash deploy.sh"
    echo ""
    echo "或者直接安装依赖："
    echo "   pip3 install pydantic-settings>=2.0.0"
    echo "   python3 main.py"
fi