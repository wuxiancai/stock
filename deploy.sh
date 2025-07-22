#!/bin/bash

# 股票交易系统一键部署脚本
# 执行后可直接运行: python3 main.py

set -e

echo "🚀 股票交易系统一键部署开始..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "当前Python版本: $python_version"

if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
    echo "❌ 需要Python 3.8+，当前: $python_version"
    exit 1
fi

# 创建并激活虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 升级pip并安装依赖
echo "📦 安装依赖..."
pip install --upgrade pip setuptools wheel

# 使用requirements.txt安装所有依赖
echo "📚 从requirements.txt安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt文件不存在"
    exit 1
fi

# 创建必要目录
mkdir -p logs uploads

# 配置环境变量
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📋 已创建.env文件，请根据需要修改配置"
fi

# 检查核心模块
echo "🔍 检查核心模块..."
python3 -c "
modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'redis', 'pydantic', 'pandas', 'numpy', 'tushare']
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
else:
    print('\\n🎉 所有核心模块正常')
"

echo ""
echo "✅ 部署完成！"
echo ""
echo "🚀 启动应用:"
echo "   python3 main.py"
echo ""
echo "📖 访问地址:"
echo "   API文档: http://localhost:8080/docs"
echo "   应用首页: http://localhost:8080"
echo ""
echo "💡 提示:"
echo "   - 确保PostgreSQL和Redis服务已启动"
echo "   - 根据需要修改.env文件中的配置"
echo "   - 使用Docker部署: bash start_docker.sh"