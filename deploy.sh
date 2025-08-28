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
sudo apt install -y python3 python3-pip python3-venv git > /dev/null 2>&1
print_success "系统包安装完成"

# 2. 创建虚拟环境
echo
print_info "=== 步骤2: 创建Python虚拟环境 ==="
if [ -d "$VENV_DIR" ]; then
    print_warning "虚拟环境已存在，删除旧环境..."
    rm -rf "$VENV_DIR"
fi

print_info "创建新的虚拟环境..."
python3 -m venv "$VENV_DIR"
print_success "虚拟环境创建完成: $VENV_DIR"

# 3. 激活虚拟环境并安装依赖
echo
print_info "=== 步骤3: 安装Python依赖包 ==="
source "$VENV_DIR/bin/activate"
print_info "升级pip..."
pip install --upgrade pip > /dev/null 2>&1

# 检查requirements.txt是否存在
if [ -f "$APP_DIR/requirements.txt" ]; then
    print_info "安装项目依赖包..."
    pip install -r "$APP_DIR/requirements.txt" > /dev/null 2>&1
    print_success "依赖包安装完成"
else
    print_warning "requirements.txt文件不存在，请手动安装依赖包"
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
# 使用 EnvironmentFile 或 Environment 定义变量
Environment="USER_NAME=ubuntu"
Environment="APP_DIR=/home/ubuntu/stock"
Environment="VENV_DIR=/home/ubuntu/stock-venv"
Environment="APP_ENV=production"

User=%E{USER_NAME}
Group=%E{USER_NAME}
WorkingDirectory=%E{APP_DIR}
ExecStart=%E{VENV_DIR}/bin/python %E{APP_DIR}/app.py
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
echo
print_info "常用管理命令:"
echo "  查看服务状态: sudo systemctl status $SERVICE_NAME"
echo "  重启服务: sudo systemctl restart $SERVICE_NAME"
echo "  停止服务: sudo systemctl stop $SERVICE_NAME"
echo "  查看实时日志: sudo journalctl -u $SERVICE_NAME -f"
echo "  查看错误日志: sudo journalctl -u $SERVICE_NAME --since today"
echo
print_info "访问地址: http://服务器IP:8888"
echo
print_success "🚀 股票选股系统已成功部署并启动！"