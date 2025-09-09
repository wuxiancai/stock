#!/bin/bash

# 部署测试脚本 - 用于诊断部署问题
# 使用方法: bash deploy_test.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取当前目录
APP_DIR=$(pwd)
VENV_DIR="$APP_DIR/venv"

echo "======================================"
echo "      股票选股系统部署诊断工具"
echo "======================================"
echo

# 1. 检查系统环境
print_info "=== 步骤1: 检查系统环境 ==="
print_info "操作系统: $(uname -a)"
print_info "Python版本检查..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python3已安装: $PYTHON_VERSION"
    if [[ $PYTHON_VERSION == *"3.12"* ]]; then
        print_info "检测到Python 3.12，已优化依赖包版本以确保兼容性"
    fi
else
    print_error "Python3未安装"
    exit 1
fi

print_info "pip版本检查..."
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    print_success "pip3已安装: $PIP_VERSION"
else
    print_error "pip3未安装"
    exit 1
fi

# 2. 检查网络连接
echo
print_info "=== 步骤2: 检查网络连接 ==="
print_info "测试PyPI连接..."
if curl -s --connect-timeout 10 https://pypi.org > /dev/null; then
    print_success "PyPI连接正常"
else
    print_warning "PyPI连接失败，尝试国内镜像源"
    if curl -s --connect-timeout 10 https://pypi.tuna.tsinghua.edu.cn > /dev/null; then
        print_success "清华镜像源连接正常"
    else
        print_error "所有PyPI镜像源连接失败"
    fi
fi

print_info "测试Tushare API连接..."
if curl -s --connect-timeout 10 https://api.tushare.pro > /dev/null; then
    print_success "Tushare API连接正常"
else
    print_warning "Tushare API连接失败，可能影响数据同步"
fi

# 3. 测试虚拟环境创建
echo
print_info "=== 步骤3: 测试虚拟环境创建 ==="
if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在，删除重建"
    rm -rf "$VENV_DIR"
fi

print_info "创建虚拟环境（使用系统Python3）..."
if python3 -m venv "$VENV_DIR"; then
    print_success "虚拟环境创建成功"
    print_info "虚拟环境Python版本: $("$VENV_DIR/bin/python" --version)"
else
    print_error "虚拟环境创建失败"
    exit 1
fi

# 4. 测试pip升级
echo
print_info "=== 步骤4: 测试pip升级 ==="
source "$VENV_DIR/bin/activate"
print_info "当前pip版本: $(pip --version)"
print_info "升级pip..."
if pip install --upgrade pip; then
    print_success "pip升级成功"
    print_info "新pip版本: $(pip --version)"
else
    print_error "pip升级失败"
    exit 1
fi

# 5. 测试关键依赖包安装
echo
print_info "=== 步骤5: 测试关键依赖包安装 ==="
print_info "测试安装Flask..."
if pip install Flask; then
    print_success "Flask安装成功"
else
    print_error "Flask安装失败"
    print_info "尝试使用镜像源..."
    if pip install Flask -i https://pypi.tuna.tsinghua.edu.cn/simple/; then
        print_success "使用镜像源安装Flask成功"
    else
        print_error "Flask安装彻底失败"
        exit 1
    fi
fi

print_info "测试安装psutil..."
if pip install psutil; then
    print_success "psutil安装成功"
else
    print_error "psutil安装失败"
    print_info "尝试使用镜像源..."
    if pip install psutil -i https://pypi.tuna.tsinghua.edu.cn/simple/; then
        print_success "使用镜像源安装psutil成功"
    else
        print_error "psutil安装彻底失败"
        exit 1
    fi
fi

# 6. 测试数据库初始化
echo
print_info "=== 步骤6: 测试数据库初始化 ==="
if [ -f "run.py" ]; then
    print_info "测试数据库初始化..."
    if python run.py init_db; then
        print_success "数据库初始化测试成功"
    else
        print_error "数据库初始化测试失败"
    fi
else
    print_warning "run.py文件不存在，跳过数据库测试"
fi

# 7. 清理测试环境
echo
print_info "=== 步骤7: 清理测试环境 ==="
deactivate 2>/dev/null || true
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    print_success "测试虚拟环境已清理"
fi

echo
print_success "======================================"
print_success "        部署诊断测试完成"
print_success "======================================"
print_info "如果所有测试都通过，可以尝试运行完整的deploy.sh脚本"
print_info "如果有测试失败，请根据错误信息解决相应问题"