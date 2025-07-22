from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
from pathlib import Path

from app.core.config import settings
from app.api.v1.api import api_router
from app.database.init_db import init_database
from app.core.exceptions import setup_exception_handlers

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于 TUshare 和 AKshare API 的股票交易系统",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None
    )
    
    # 设置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加受信任主机中间件
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
        )
    
    # 添加请求处理时间中间件
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # 设置异常处理器
    setup_exception_handlers(app)
    
    # 包含API路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 静态文件服务
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    else:
        logger.warning(f"静态文件目录不存在: {static_dir}")
    
    return app

# 创建应用实例
app = create_application()

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")
    logger.info(f"🌐 运行在端口: {settings.BACKEND_PORT}")
    logger.info(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    
    # 初始化数据库
    try:
        await init_database()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    
    logger.info("✅ 应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 应用正在关闭...")
    logger.info("✅ 应用已安全关闭")

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回首页"""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        # 如果首页文件不存在，返回JSON响应
        return JSONResponse({
            "message": f"欢迎使用{settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "API文档在生产环境中不可用",
            "status": "running",
            "note": "首页文件未找到，请检查静态文件配置"
        })

@app.get("/api")
async def api_root():
    """API根路径"""
    return {
        "message": f"欢迎使用{settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "API文档在生产环境中不可用",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION
    }