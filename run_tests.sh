#!/bin/bash
# 测试运行脚本

set -e

echo "🧪 运行测试..."

# 激活虚拟环境
source venv/bin/activate

# 运行测试
python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo "✅ 测试完成"
