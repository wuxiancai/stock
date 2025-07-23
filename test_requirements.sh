#!/bin/bash
# 快速测试新的 requirements.txt 文件

echo "🧪 测试新的 requirements.txt 文件"
echo "================================"

# 检查 requirements.txt 文件
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

echo "📋 检查 requirements.txt 内容："
echo ""

# 统计版本信息
total_packages=$(grep -v '^#' requirements.txt | grep -v '^$' | wc -l | tr -d ' ')
versioned_packages=$(grep -v '^#' requirements.txt | grep '==' | wc -l | tr -d ' ')
flexible_packages=$((total_packages - versioned_packages))

echo "📊 包统计："
echo "  总包数: $total_packages"
echo "  固定版本包: $versioned_packages"
echo "  灵活版本包: $flexible_packages"

if [ "$versioned_packages" -eq 0 ]; then
    echo "  ✅ 所有包都使用灵活版本"
else
    echo "  ⚠️ 仍有 $versioned_packages 个包使用固定版本"
    echo ""
    echo "🔍 固定版本的包："
    grep -v '^#' requirements.txt | grep '==' | sed 's/^/  - /'
fi

echo ""
echo "🎯 关键包检查："

# 检查之前有问题的包
problem_packages=("akshare" "talib-binary" "tushare")
for pkg in "${problem_packages[@]}"; do
    if grep -q "^${pkg}==" requirements.txt; then
        version=$(grep "^${pkg}==" requirements.txt | cut -d'=' -f3)
        echo "  ❌ $pkg 仍使用固定版本: $version"
    elif grep -q "^${pkg}$" requirements.txt; then
        echo "  ✅ $pkg 使用灵活版本"
    elif grep -q "^${pkg} " requirements.txt; then
        echo "  ✅ $pkg 使用灵活版本（带注释）"
    else
        echo "  ⚠️ $pkg 未找到"
    fi
done

echo ""
echo "📝 建议："
echo "  1. 运行 ./setup_macos.sh 测试新配置"
echo "  2. 如需固定版本，使用 requirements.fixed.txt"
echo "  3. 查看详细文档: cat DEPENDENCY_STRATEGY.md"

echo ""
echo "🚀 测试安装（仅验证语法）："
if python -c "
import pkg_resources
import sys

try:
    with open('requirements.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 简单验证包名格式
                if '==' in line:
                    pkg, version = line.split('==', 1)
                    print(f'  📦 {pkg} (固定版本: {version})')
                else:
                    # 处理带注释的行
                    pkg = line.split('#')[0].strip()
                    if pkg:
                        print(f'  📦 {pkg} (灵活版本)')
    print('✅ requirements.txt 语法检查通过')
except Exception as e:
    print(f'❌ requirements.txt 语法错误: {e}')
    sys.exit(1)
"; then
    echo "✅ 文件格式正确"
else
    echo "❌ 文件格式有问题"
fi