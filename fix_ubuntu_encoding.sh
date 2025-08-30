#!/bin/bash

# Ubuntu环境中文编码修复脚本
# 用于解决股票行情系统在Ubuntu环境下中文字符显示异常的问题

echo "=== Ubuntu环境中文编码修复脚本 ==="
echo "开始修复Ubuntu环境下的中文字符显示问题..."
echo

# 1. 检查当前环境
echo "1. 检查当前环境设置"
echo "当前locale设置:"
locale
echo
echo "当前环境变量:"
echo "LANG: ${LANG:-未设置}"
echo "LC_ALL: ${LC_ALL:-未设置}"
echo "PYTHONIOENCODING: ${PYTHONIOENCODING:-未设置}"
echo

# 2. 安装必要的语言包
echo "2. 安装UTF-8语言支持"
echo "正在更新包列表..."
sudo apt-get update -qq

echo "正在安装语言包..."
sudo apt-get install -y language-pack-zh-hans language-pack-en locales

# 3. 配置locale
echo "3. 配置系统locale"
echo "正在生成locale..."
sudo locale-gen en_US.UTF-8
sudo locale-gen zh_CN.UTF-8

# 4. 设置环境变量
echo "4. 设置环境变量"

# 检查并添加环境变量到.bashrc
BASHRC_FILE="$HOME/.bashrc"

# 备份原始.bashrc
if [ -f "$BASHRC_FILE" ]; then
    cp "$BASHRC_FILE" "$BASHRC_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "已备份原始.bashrc文件"
fi

# 添加环境变量（如果不存在）
if ! grep -q "export LANG=en_US.UTF-8" "$BASHRC_FILE"; then
    echo "export LANG=en_US.UTF-8" >> "$BASHRC_FILE"
    echo "已添加LANG环境变量"
fi

if ! grep -q "export LC_ALL=en_US.UTF-8" "$BASHRC_FILE"; then
    echo "export LC_ALL=en_US.UTF-8" >> "$BASHRC_FILE"
    echo "已添加LC_ALL环境变量"
fi

if ! grep -q "export PYTHONIOENCODING=utf-8" "$BASHRC_FILE"; then
    echo "export PYTHONIOENCODING=utf-8" >> "$BASHRC_FILE"
    echo "已添加PYTHONIOENCODING环境变量"
fi

# 立即应用环境变量
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export PYTHONIOENCODING=utf-8

echo "环境变量设置完成"
echo

# 5. 检查Python环境
echo "5. 检查Python环境"
echo "Python版本: $(python3 --version)"
echo "Python默认编码: $(python3 -c 'import sys; print(sys.getdefaultencoding())')"
echo "Python文件系统编码: $(python3 -c 'import sys; print(sys.getfilesystemencoding())')"
echo

# 6. 验证修复效果
echo "6. 验证修复效果"
if [ -f "test_encoding.py" ]; then
    echo "运行编码测试脚本..."
    python3 test_encoding.py
else
    echo "编码测试脚本不存在，跳过测试"
fi
echo

# 7. 重新同步数据
echo "7. 重新同步股票基础信息"
if [ -f "run.py" ]; then
    echo "正在重新同步股票基础信息..."
    python3 run.py sync_stock_basic_info
    echo "股票基础信息同步完成"
else
    echo "run.py文件不存在，请手动运行数据同步"
fi
echo

# 8. 验证数据库数据
echo "8. 验证数据库中的中文数据"
if [ -f "stock_data.db" ]; then
    echo "检查数据库中的股票信息..."
    sqlite3 stock_data.db "SELECT ts_code, name, area, industry FROM stock_basic_info WHERE name IS NOT NULL AND name != '' LIMIT 5;" 2>/dev/null || echo "数据库查询失败或无数据"
else
    echo "数据库文件不存在"
fi
echo

# 9. 提供后续操作建议
echo "=== 修复完成 ==="
echo "后续操作建议:"
echo "1. 重新启动终端或运行 'source ~/.bashrc' 使环境变量生效"
echo "2. 重启股票应用程序"
echo "3. 在浏览器中访问应用，检查中文字符是否正常显示"
echo "4. 如果问题仍然存在，请检查应用程序日志"
echo
echo "如需回滚更改，可以恢复备份的.bashrc文件:"
echo "cp ~/.bashrc.backup.* ~/.bashrc"
echo
echo "修复脚本执行完成！"