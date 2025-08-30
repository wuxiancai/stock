#!/bin/bash
set -e

# 国内常用 pip 镜像源
MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

# 升级 pip
echo "🔄 升级 pip ..."
pip install --upgrade pip -i $MIRROR

# 带重试的安装函数
install_requirements() {
    for i in {1..3}; do
        echo "📥 第 $i 次尝试安装依赖 ..."
        if pip install -r requirements.txt -i $MIRROR --timeout=60 --retries=3; then
            echo "✅ 依赖安装成功"
            return 0
        else
            echo "⚠️ 第 $i 次安装失败，重试中..."
            sleep 3
        fi
    done
    echo "❌ 多次尝试仍然失败，请检查网络或 requirements.txt"
    exit 1
}

# 开始安装
install_requirements

echo "🎉 所有依赖安装完成！"