#!/bin/bash

# 数据库服务启动脚本
# 用于单独启动PostgreSQL和Redis服务

set -e

echo "🗄️ 启动数据库服务..."

# 检查操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "检测到操作系统: $MACHINE"

# 启动PostgreSQL
echo "🐘 启动PostgreSQL..."
if [ "$MACHINE" = "Mac" ]; then
    # macOS使用brew
    if command -v brew &> /dev/null; then
        if brew services list | grep postgresql | grep started > /dev/null; then
            echo "✅ PostgreSQL已在运行"
        else
            echo "启动PostgreSQL..."
            brew services start postgresql
            echo "✅ PostgreSQL启动成功"
        fi
    else
        echo "❌ 未找到brew，请手动安装PostgreSQL"
        echo "   安装命令: brew install postgresql"
    fi
elif [ "$MACHINE" = "Linux" ]; then
    # Linux使用systemctl
    if systemctl is-active --quiet postgresql; then
        echo "✅ PostgreSQL已在运行"
    else
        echo "启动PostgreSQL..."
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
        echo "✅ PostgreSQL启动成功"
    fi
else
    echo "❌ 不支持的操作系统: $MACHINE"
    echo "💡 建议使用Docker: bash start_docker.sh"
    exit 1
fi

# 启动Redis
echo "🔴 启动Redis..."
if [ "$MACHINE" = "Mac" ]; then
    # macOS使用brew
    if command -v brew &> /dev/null; then
        if brew services list | grep redis | grep started > /dev/null; then
            echo "✅ Redis已在运行"
        else
            echo "启动Redis..."
            brew services start redis
            echo "✅ Redis启动成功"
        fi
    else
        echo "❌ 未找到brew，请手动安装Redis"
        echo "   安装命令: brew install redis"
    fi
elif [ "$MACHINE" = "Linux" ]; then
    # Linux使用systemctl
    if systemctl is-active --quiet redis; then
        echo "✅ Redis已在运行"
    else
        echo "启动Redis..."
        sudo systemctl start redis
        sudo systemctl enable redis
        echo "✅ Redis启动成功"
    fi
fi

# 等待服务启动
echo "⏳ 等待服务完全启动..."
sleep 5

# 测试连接
echo "🔗 测试数据库连接..."

# 测试PostgreSQL
if command -v psql &> /dev/null; then
    if psql -h localhost -U postgres -c "SELECT 1;" &> /dev/null; then
        echo "✅ PostgreSQL连接测试成功"
    else
        echo "⚠️ PostgreSQL连接测试失败，可能需要配置用户权限"
    fi
else
    echo "⚠️ 未安装psql客户端，跳过PostgreSQL连接测试"
fi

# 测试Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping | grep -q PONG; then
        echo "✅ Redis连接测试成功"
    else
        echo "⚠️ Redis连接测试失败"
    fi
else
    echo "⚠️ 未安装redis-cli客户端，跳过Redis连接测试"
fi

echo ""
echo "🎉 数据库服务启动完成！"
echo ""
echo "📋 服务状态:"
if [ "$MACHINE" = "Mac" ]; then
    echo "   PostgreSQL: $(brew services list | grep postgresql | awk '{print $2}')"
    echo "   Redis: $(brew services list | grep redis | awk '{print $2}')"
elif [ "$MACHINE" = "Linux" ]; then
    echo "   PostgreSQL: $(systemctl is-active postgresql)"
    echo "   Redis: $(systemctl is-active redis)"
fi
echo ""
echo "🚀 现在可以运行应用:"
echo "   bash deploy.sh  # 完整部署"
echo "   python3 main.py # 直接启动"