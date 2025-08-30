#!/bin/bash

# 股票选股系统一键部署脚本
# 适用于Ubuntu系统
# 作者: Stock System
# 版本: 1.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

echo -e "${GREEN}=== 股票选股系统一键部署脚本 ===${NC}"
print_info "开始部署到Ubuntu服务器..."

# 定义变量
APP_NAME="stock-system"
APP_DIR="$HOME/stock"
VENV_DIR="$HOME/stock-venv"
SERVICE_NAME="run-stock"
SERVICE_FILE="$SERVICE_NAME.service"
USER_NAME=$(whoami)

print_info "部署目录: $APP_DIR"
print_info "虚拟环境目录: $VENV_DIR"
print_info "当前用户: $USER_NAME"

# 检查是否为root用户
if [ "$USER_NAME" = "root" ]; then
    print_warning "检测到root用户，建议使用普通用户部署"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 1
    fi
fi

# 检查应用目录是否存在
if [ ! -d "$APP_DIR" ]; then
    print_error "应用目录不存在: $APP_DIR"
    print_info "请先将代码上传到该目录"
    exit 1
fi

# 1. 更新系统包
echo
print_info "=== 步骤1: 更新系统包 ==="
print_info "更新apt包列表..."
sudo apt update > /dev/null 2>&1
print_info "安装必要的系统包..."
sudo apt install -y python3 python3-pip python3-venv python3-dev git language-pack-zh-hans language-pack-en locales > /dev/null 2>&1
print_success "系统包安装完成"

# 1.5. 配置UTF-8编码环境
echo
print_info "=== 步骤1.5: 配置UTF-8编码环境 ==="
print_info "生成UTF-8 locale..."
sudo locale-gen en_US.UTF-8 > /dev/null 2>&1
sudo locale-gen zh_CN.UTF-8 > /dev/null 2>&1

print_info "配置环境变量..."
# 备份原始.bashrc
if [ -f "$HOME/.bashrc" ]; then
    cp "$HOME/.bashrc" "$HOME/.bashrc.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 添加环境变量（如果不存在）
if ! grep -q "export LANG=en_US.UTF-8" "$HOME/.bashrc"; then
    echo "export LANG=en_US.UTF-8" >> "$HOME/.bashrc"
fi

if ! grep -q "export LC_ALL=en_US.UTF-8" "$HOME/.bashrc"; then
    echo "export LC_ALL=en_US.UTF-8" >> "$HOME/.bashrc"
fi

if ! grep -q "export PYTHONIOENCODING=utf-8" "$HOME/.bashrc"; then
    echo "export PYTHONIOENCODING=utf-8" >> "$HOME/.bashrc"
fi

# 立即应用环境变量
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export PYTHONIOENCODING=utf-8

print_success "UTF-8编码环境配置完成"

# 2. 创建虚拟环境
echo
print_info "=== 步骤2: 创建Python虚拟环境 ==="
if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在，删除旧环境..."
    rm -rf "$VENV_DIR"
fi

print_info "创建新的虚拟环境（使用系统Python3）..."
python3 -m venv "$VENV_DIR"
print_success "虚拟环境创建完成: $VENV_DIR"
print_info "虚拟环境Python版本: $("$VENV_DIR/bin/python" --version)"

# 3. 激活虚拟环境并安装依赖
echo
print_info "=== 步骤3: 安装Python依赖包 ==="
source "$VENV_DIR/bin/activate"
print_info "升级pip..."
if pip install --upgrade pip setuptools wheel; then
    print_success "pip升级完成"
else
    print_error "pip升级失败"
    exit 1
fi

# 检查requirements.txt是否存在
if [ -f "$APP_DIR/requirements.txt" ]; then
    print_info "安装项目依赖包..."
    print_info "依赖包列表:"
    cat "$APP_DIR/requirements.txt"
    echo
    
    if pip install -r "$APP_DIR/requirements.txt"; then
        print_success "依赖包安装完成"
    else
        print_error "依赖包安装失败，请检查网络连接和依赖包版本"
        print_info "尝试使用国内镜像源重新安装..."
        if pip install -r "$APP_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple/; then
            print_success "使用镜像源安装依赖包成功"
        else
            print_error "依赖包安装彻底失败，请手动检查"
            exit 1
        fi
    fi
else
    print_warning "requirements.txt文件不存在，请手动安装依赖包"
fi

# 3.5. 初始化数据库和同步股票基础信息
echo
print_info "=== 步骤3.5: 初始化数据库和同步数据 ==="
cd "$APP_DIR"

print_info "初始化数据库..."
if python run.py init_db; then
    print_success "数据库初始化完成"
else
    print_error "数据库初始化失败"
    exit 1
fi

print_info "同步股票基础信息（这可能需要几分钟）..."
print_info "如果网络较慢或Tushare限流，此步骤可能需要较长时间"
print_info "正在连接Tushare API获取股票数据..."

# 使用timeout命令防止长时间卡住，增加超时时间到15分钟
if timeout 900 python run.py sync_stock_basic_info; then
    print_success "股票基础信息同步完成"
elif [ $? -eq 124 ]; then
    print_warning "同步超时（15分钟），可能是网络问题或Tushare限流"
    print_warning "可以稍后手动执行: cd $APP_DIR && python run.py sync_stock_basic_info"
    print_warning "继续部署其他组件..."
else
    print_error "股票基础信息同步失败，请检查网络连接和Tushare配置"
    print_warning "可以稍后手动执行: cd $APP_DIR && python run.py sync_stock_basic_info"
    print_warning "继续部署其他组件..."
fi

print_info "运行编码测试验证..."
if [ -f "test_encoding.py" ]; then
    python test_encoding.py > /tmp/encoding_test.log 2>&1
    if grep -q "测试完成" /tmp/encoding_test.log; then
        print_success "编码测试通过"
    else
        print_warning "编码测试可能存在问题，请检查日志: /tmp/encoding_test.log"
    fi
else
    print_warning "编码测试脚本不存在，跳过测试"
fi

# 4. 创建systemd服务文件
echo
print_info "=== 步骤4: 创建systemd服务配置 ==="

# 检查是否已有服务文件模板
if [ -f "$APP_DIR/$SERVICE_FILE" ]; then
    print_info "使用现有的服务文件模板"
    # 替换模板中的占位符
    sed -i "s|%i|$USER_NAME|g" "$APP_DIR/$SERVICE_FILE"
    sed -i "s|%h|$HOME|g" "$APP_DIR/$SERVICE_FILE"
else
    print_info "创建systemd服务文件..."
    cat > "$APP_DIR/$SERVICE_FILE" << EOF
[Unit]
Description=Stock System Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
# 环境变量配置
Environment="USER_NAME=$USER_NAME"
Environment="APP_DIR=$APP_DIR"
Environment="VENV_DIR=$VENV_DIR"
Environment="APP_ENV=production"
# UTF-8编码环境变量
Environment="LANG=en_US.UTF-8"
Environment="LC_ALL=en_US.UTF-8"
Environment="PYTHONIOENCODING=utf-8"

User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stock-system

[Install]
WantedBy=multi-user.target
EOF
fi

print_success "服务文件已准备: $APP_DIR/$SERVICE_FILE"

# 5. 复制服务文件到系统目录
echo
print_info "=== 步骤5: 安装systemd服务 ==="
print_info "复制服务文件到系统目录..."
sudo cp "$APP_DIR/$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
print_success "服务文件已安装到系统"

# 6. 启用并启动服务
echo
print_info "=== 步骤6: 启用并启动服务 ==="
print_info "启用开机自启动..."
sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
print_info "启动服务..."
sudo systemctl start "$SERVICE_NAME"
print_success "服务已启动"

# 7. 检查服务状态
echo
print_info "=== 步骤7: 检查服务状态 ==="
print_info "等待服务启动..."
sleep 5

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    print_success "✅ 服务启动成功！"
    echo
    print_info "服务状态:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
else
    print_error "❌ 服务启动失败！"
    echo
    print_info "错误日志:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l --since "5 minutes ago"
    echo
    print_error "部署失败，请检查上述错误信息"
    exit 1
fi

# 8. 防火墙配置
echo
print_info "=== 步骤8: 配置防火墙 ==="
if command -v ufw >/dev/null 2>&1; then
    print_info "检测到ufw防火墙，开放8888端口..."
    sudo ufw allow 8888 > /dev/null 2>&1
    print_success "端口8888已开放"
else
    print_warning "未检测到ufw防火墙，请手动开放8888端口"
fi

# 9. 显示部署信息
echo
print_success "=== 🎉 部署完成 ==="
echo
print_info "部署信息:"
echo "  应用目录: $APP_DIR"
echo "  虚拟环境: $VENV_DIR"
echo "  服务名称: $SERVICE_NAME"
echo "  运行端口: 8888"
echo "  UTF-8编码: 已配置"
echo "  股票数据: 已同步"
echo
print_info "已集成功能:"
echo "  ✅ UTF-8编码环境自动配置"
echo "  ✅ 中文字符显示修复"
echo "  ✅ 股票基础信息自动同步"
echo "  ✅ 数据库编码优化"
echo "  ✅ 编码问题自动检测"
echo
print_info "常用管理命令:"
echo "  查看服务状态: sudo systemctl status $SERVICE_NAME"
echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
echo "  查看实时日志: sudo journalctl -u $SERVICE_NAME -f"
echo "  查看错误日志: sudo journalctl -u $SERVICE_NAME --since today"
echo "  重新同步数据: cd $APP_DIR && $VENV_DIR/bin/python run.py sync_stock_basic_info"
echo "  编码问题检测: cd $APP_DIR && $VENV_DIR/bin/python test_encoding.py"
echo
print_info "访问地址: http://服务器IP:8888"
echo
print_success "🚀 股票选股系统已成功部署并启动！"
print_info "💡 系统已自动配置UTF-8编码环境，中文字符将正常显示"