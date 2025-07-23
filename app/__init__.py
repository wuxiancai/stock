"""
股票交易系统应用初始化模块
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import asyncio
from loguru import logger

from app.config import settings
from app.database import init_db, close_db
from app.cache import init_redis, close_redis
from app.middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware
)
from app.api import router as api_router
from app.websocket import ws_router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动股票交易系统...")
    
    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库连接已建立")
    
    # 初始化Redis
    await init_redis()
    logger.info("✅ Redis连接已建立")
    
    # 启动后台任务
    # asyncio.create_task(start_background_tasks())
    
    logger.info("🎉 股票交易系统启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 关闭股票交易系统...")
    
    # 关闭数据库连接
    await close_db()
    logger.info("✅ 数据库连接已关闭")
    
    # 关闭Redis连接
    await close_redis()
    logger.info("✅ Redis连接已关闭")
    
    logger.info("👋 股票交易系统已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="专业的股票交易系统，支持九转选股策略",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )
    
    # 添加中间件
    setup_middleware(app)
    
    # 注册路由
    setup_routes(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """设置中间件"""
    
    # 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 安全中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 信任主机中间件
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # 生产环境应该配置具体的主机
        )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 限流中间件
    app.add_middleware(RateLimitMiddleware)
    
    # 日志中间件（最内层）
    app.add_middleware(RequestLoggingMiddleware)


def setup_routes(app: FastAPI) -> None:
    """设置路由"""
    
    # API路由
    app.include_router(api_router, prefix="/api/v1")
    
    # WebSocket路由
    app.include_router(websocket_router, prefix="/ws")
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment
        }
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": f"欢迎使用{settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "文档已禁用",
            "health": "/health"
        }


# 创建应用实例
app = create_app()


# 导出
__all__ = ["app", "create_app"]