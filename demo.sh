#!/bin/bash

# 股票交易系统演示脚本

set -e

echo "🎬 股票交易系统功能演示"
echo "================================"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行 ./setup_macos.sh"
    exit 1
fi

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."

# 检查 PostgreSQL
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "✅ PostgreSQL 服务正常"
else
    echo "❌ PostgreSQL 服务未运行，请先启动服务"
    exit 1
fi

# 检查 Redis
if redis-cli ping &> /dev/null; then
    echo "✅ Redis 服务正常"
else
    echo "❌ Redis 服务未运行，请先启动服务"
    exit 1
fi

echo ""
echo "📊 演示功能列表："
echo "1. 数据库连接测试"
echo "2. 缓存功能测试"
echo "3. 技术指标计算演示"
echo "4. API 接口测试"
echo "5. WebSocket 连接测试"

echo ""
read -p "请选择要演示的功能 (1-5, 或按 Enter 演示所有功能): " choice

case "$choice" in
    1|"")
        echo ""
        echo "🗄️ 数据库连接测试..."
        python -c "
from app.database import init_db, get_sync_session
from app.models import StockBasic
import asyncio

async def test_db():
    await init_db()
    print('✅ 数据库连接成功')
    
    with get_sync_session() as session:
        count = session.query(StockBasic).count()
        print(f'📊 股票基础信息表记录数: {count}')

asyncio.run(test_db())
"
        ;;
esac

if [ "$choice" = "2" ] || [ "$choice" = "" ]; then
    echo ""
    echo "💾 缓存功能测试..."
    python -c "
from app.cache import init_redis, CacheManager
import asyncio

async def test_cache():
    await init_redis()
    cache = CacheManager()
    
    # 测试缓存设置和获取
    await cache.set('test_key', 'Hello, Stock Trading System!', ttl=60)
    value = await cache.get('test_key')
    print(f'✅ 缓存测试成功: {value}')
    
    # 清理测试数据
    await cache.delete('test_key')

asyncio.run(test_cache())
"
fi

if [ "$choice" = "3" ] || [ "$choice" = "" ]; then
    echo ""
    echo "📈 技术指标计算演示..."
    python -c "
from app.technical_analysis import TechnicalIndicators, NineTurnSequential
import pandas as pd
import numpy as np

# 生成模拟数据
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=50, freq='D')
prices = 100 + np.cumsum(np.random.randn(50) * 0.5)

data = pd.DataFrame({
    'trade_date': dates,
    'close': prices,
    'high': prices + np.random.rand(50) * 2,
    'low': prices - np.random.rand(50) * 2,
    'volume': np.random.randint(1000000, 10000000, 50)
})

print('📊 计算技术指标...')
indicators = TechnicalIndicators()

# 计算移动平均线
ma5 = indicators.calculate_ma(data['close'], 5)
ma20 = indicators.calculate_ma(data['close'], 20)
print(f'✅ MA5 最新值: {ma5.iloc[-1]:.2f}')
print(f'✅ MA20 最新值: {ma20.iloc[-1]:.2f}')

# 计算 RSI
rsi = indicators.calculate_rsi(data['close'])
print(f'✅ RSI 最新值: {rsi.iloc[-1]:.2f}')

# 计算九转序列
nine_turn = NineTurnSequential()
td_setup = nine_turn.calculate_td_setup(data['close'])
print(f'✅ TD Setup 最新值: {td_setup.iloc[-1]}')

print('🎉 技术指标计算演示完成')
"
fi

if [ "$choice" = "4" ] || [ "$choice" = "" ]; then
    echo ""
    echo "🌐 API 接口测试..."
    
    # 启动 API 服务（后台运行）
    echo "🚀 启动 API 服务..."
    python main.py &
    API_PID=$!
    
    # 等待服务启动
    sleep 5
    
    # 测试健康检查接口
    echo "🔍 测试健康检查接口..."
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ 健康检查接口正常"
        
        # 测试 API 文档
        echo "📚 API 文档地址: http://localhost:8080/docs"
        
        # 测试股票列表接口
        echo "📊 测试股票列表接口..."
        response=$(curl -s http://localhost:8080/api/v1/stocks?limit=5)
        echo "✅ 股票列表接口响应: $response"
        
    else
        echo "❌ API 服务启动失败"
    fi
    
    # 停止 API 服务
    kill $API_PID 2>/dev/null || true
    echo "🛑 API 服务已停止"
fi

if [ "$choice" = "5" ] || [ "$choice" = "" ]; then
    echo ""
    echo "🔌 WebSocket 连接测试..."
    python -c "
import asyncio
import websockets
import json

async def test_websocket():
    try:
        # 启动 WebSocket 服务需要先启动主应用
        print('⚠️ WebSocket 测试需要先启动主应用服务')
        print('💡 请运行 ./start_dev.sh 启动服务后再测试 WebSocket')
        print('🔗 WebSocket 地址: ws://localhost:8080/ws')
        
        # 这里只是演示 WebSocket 客户端代码
        print('📝 WebSocket 客户端示例代码:')
        print('''
import asyncio
import websockets
import json

async def websocket_client():
    uri = \"ws://localhost:8080/ws\"
    async with websockets.connect(uri) as websocket:
        # 订阅股票数据
        subscribe_msg = {
            \"action\": \"subscribe\",
            \"type\": \"stock\",
            \"symbols\": [\"000001.SZ\", \"000002.SZ\"]
        }
        await websocket.send(json.dumps(subscribe_msg))
        
        # 接收数据
        async for message in websocket:
            data = json.loads(message)
            print(f\"收到数据: {data}\")

asyncio.run(websocket_client())
        ''')
        
    except Exception as e:
        print(f'❌ WebSocket 测试失败: {e}')

asyncio.run(test_websocket())
"
fi

echo ""
echo "🎉 演示完成！"
echo ""
echo "📋 下一步操作建议："
echo "1. 运行 './start_dev.sh' 启动完整的开发环境"
echo "2. 访问 http://localhost:8080/docs 查看 API 文档"
echo "3. 配置 .env 文件中的 TUSHARE_TOKEN 获取真实数据"
echo "4. 运行 './run_tests.sh' 执行完整测试"
echo ""
echo "🔗 相关链接："
echo "- API 文档: http://localhost:8080/docs"
echo "- 系统主页: http://localhost:8080/"
echo "- Flower 监控: http://localhost:5555 (需要启动 Celery)"
echo ""