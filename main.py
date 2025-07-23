"""
主应用入口文件
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from loguru import logger
import uvicorn

from app.config import settings
from app.database import init_db, close_db, create_tables
from app.cache import init_redis, close_redis
from app.middleware import setup_middleware
from app.api import router as api_router
from app.websocket import ws_router, start_websocket_service, stop_websocket_service
from app.data_sources import data_source_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动股票交易系统后端服务...")
    
    try:
        # 初始化数据库
        logger.info("初始化数据库连接...")
        await init_db()
        
        # 创建数据库表
        logger.info("创建数据库表...")
        await create_tables()
        
        # 初始化Redis
        logger.info("初始化Redis连接...")
        await init_redis()
        
        # 初始化数据源
        logger.info("初始化数据源...")
        await data_source_manager.initialize()
        
        # 启动WebSocket服务
        logger.info("启动WebSocket服务...")
        await start_websocket_service()
        
        logger.info("股票交易系统后端服务启动完成!")
        
        yield
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    
    finally:
        # 关闭时执行
        logger.info("关闭股票交易系统后端服务...")
        
        try:
            # 停止WebSocket服务
            await stop_websocket_service()
            
            # 关闭数据源
            await data_source_manager.close()
            
            # 关闭Redis连接
            await close_redis()
            
            # 关闭数据库连接
            await close_db()
            
            logger.info("股票交易系统后端服务已关闭")
            
        except Exception as e:
            logger.error(f"服务关闭异常: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="股票交易系统API",
    description="基于FastAPI的股票交易系统后端服务",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan
)

# 设置中间件
setup_middleware(app)

# 注册路由
app.include_router(api_router, tags=["API"])
app.include_router(ws_router, tags=["WebSocket"])

# 静态文件服务（用于前端部署）
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # 静态目录不存在时忽略
    pass

# 根路径
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """根路径"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>股票交易系统</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background-color: #f5f5f5; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            h1 { 
                color: #333; 
                text-align: center; 
                margin-bottom: 30px; 
            }
            .info { 
                background: #e8f4fd; 
                padding: 20px; 
                border-radius: 5px; 
                margin: 20px 0; 
            }
            .links { 
                text-align: center; 
                margin-top: 30px; 
            }
            .links a { 
                display: inline-block; 
                margin: 0 10px; 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
            }
            .links a:hover { 
                background: #0056b3; 
            }
            .status { 
                color: #28a745; 
                font-weight: bold; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 股票交易系统</h1>
            
            <div class="info">
                <h3>系统状态</h3>
                <p>服务状态: <span class="status">运行中</span></p>
                <p>版本: v1.0.0</p>
                <p>环境: """ + settings.environment + """</p>
                <p>启动时间: <span id="current-time"></span></p>
            </div>
            
            <div class="info">
                <h3>功能特性</h3>
                <ul>
                    <li>📊 实时股票数据获取</li>
                    <li>📈 技术指标计算</li>
                    <li>🔄 九转序列信号分析</li>
                    <li>⚡ WebSocket实时推送</li>
                    <li>🔄 后台任务队列</li>
                    <li>💾 数据缓存优化</li>
                </ul>
            </div>
            
            <div class="links">
                """ + ("""
                <a href="/docs" target="_blank">📚 API文档</a>
                <a href="/redoc" target="_blank">📖 ReDoc文档</a>
                """ if settings.environment != "production" else "") + """
                <a href="/api/v1/health" target="_blank">🏥 健康检查</a>
            </div>
        </div>
        
        <script>
            document.getElementById('current-time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """


# 健康检查端点
@app.get("/health", include_in_schema=False)
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "stock-trading-system",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": "2024-01-01T00:00:00Z"
    }


def create_app() -> FastAPI:
    """创建应用实例"""
    return app


if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )