"""
中间件模块
提供安全、日志、限流等功能
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
import json
import asyncio

from app.config import settings
from app.cache import RateLimitCache


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 记录请求信息
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录请求体（如果启用且不是GET请求）
        if self.log_body and request.method != "GET":
            try:
                body = await request.body()
                if body:
                    request_info["body"] = body.decode("utf-8")[:1000]  # 限制长度
            except Exception:
                pass
        
        logger.info(f"请求开始: {json.dumps(request_info, ensure_ascii=False)}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            response_info = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "response_size": response.headers.get("content-length", "unknown")
            }
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # 根据状态码选择日志级别
            if response.status_code >= 500:
                logger.error(f"请求完成: {json.dumps(response_info, ensure_ascii=False)}")
            elif response.status_code >= 400:
                logger.warning(f"请求完成: {json.dumps(response_info, ensure_ascii=False)}")
            else:
                logger.info(f"请求完成: {json.dumps(response_info, ensure_ascii=False)}")
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常信息
            error_info = {
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time": round(process_time, 4)
            }
            
            logger.error(f"请求异常: {json.dumps(error_info, ensure_ascii=False)}")
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 返回直连IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(
        self, 
        app,
        calls: int = 100,
        period: int = 60,
        per_ip: bool = True,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.calls = calls  # 允许的调用次数
        self.period = period  # 时间窗口（秒）
        self.per_ip = per_ip  # 是否按IP限流
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.rate_limit_cache = RateLimitCache()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 检查是否需要限流
        if not self._should_rate_limit(request):
            return await call_next(request)
        
        # 获取限流键
        rate_limit_key = self._get_rate_limit_key(request)
        
        try:
            # 检查限流
            allowed = await self.rate_limit_cache.is_allowed(
                rate_limit_key, 
                self.calls, 
                self.period
            )
            
            if not allowed:
                # 获取重置时间
                reset_time = await self.rate_limit_cache.get_reset_time(rate_limit_key, self.period)
                
                # 记录限流日志
                logger.warning(f"请求被限流: {rate_limit_key}, 重置时间: {reset_time}")
                
                # 返回限流响应
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                        "reset_time": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Period": str(self.period),
                        "X-RateLimit-Reset": str(reset_time),
                        "Retry-After": str(self.period)
                    }
                )
            
            # 获取当前使用情况
            current_usage = await self.rate_limit_cache.get_current_usage(rate_limit_key)
            remaining = max(0, self.calls - current_usage)
            
            # 处理请求
            response = await call_next(request)
            
            # 添加限流信息到响应头
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Period"] = str(self.period)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"限流中间件异常: {e}")
            # 限流异常时允许请求通过
            return await call_next(request)
    
    def _should_rate_limit(self, request: Request) -> bool:
        """判断是否需要限流"""
        path = request.url.path
        
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        return True
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """获取限流键"""
        if self.per_ip:
            client_ip = self._get_client_ip(request)
            return f"rate_limit:ip:{client_ip}"
        else:
            return "rate_limit:global"
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        security_headers = {
            # 防止XSS攻击
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS相关
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # 内容安全策略
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none';"
            ),
            
            # 权限策略
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "accelerometer=(), "
                "gyroscope=()"
            ),
            
            # 引用策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # 服务器信息
            "Server": "StockTradingSystem/1.0"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # HTTP异常直接抛出，由FastAPI处理
            raise
        except Exception as e:
            # 记录未处理的异常
            request_id = getattr(request.state, "request_id", "unknown")
            
            error_info = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.error(f"未处理的异常: {json.dumps(error_info, ensure_ascii=False)}")
            
            # 返回通用错误响应
            return Response(
                content=json.dumps({
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                status_code=500,
                media_type="application/json"
            )


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """健康检查中间件"""
    
    def __init__(self, app, health_check_path: str = "/health"):
        super().__init__(app)
        self.health_check_path = health_check_path
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 如果是健康检查请求，直接返回
        if request.url.path == self.health_check_path:
            return Response(
                content=json.dumps({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "stock-trading-system"
                }),
                status_code=200,
                media_type="application/json"
            )
        
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 默认10MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 检查Content-Length头
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "error": "Request entity too large",
                            "message": f"Request size {size} exceeds maximum allowed size {self.max_size}",
                            "max_size": self.max_size
                        }
                    )
            except ValueError:
                pass
        
        return await call_next(request)


def setup_middleware(app):
    """设置中间件"""
    
    # 1. 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 2. 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 3. 请求日志中间件
    app.add_middleware(
        RequestLoggingMiddleware,
        log_body=settings.log_level == "DEBUG"
    )
    
    # 4. 限流中间件
    if settings.enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.rate_limit_calls,
            period=settings.rate_limit_period,
            per_ip=True,
            exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/ws"]
        )
    
    # 5. 请求大小限制中间件
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=settings.max_request_size
    )
    
    # 6. 健康检查中间件
    app.add_middleware(HealthCheckMiddleware)
    
    # 7. CORS中间件
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Process-Time"]
        )
    
    # 8. 受信任主机中间件
    if settings.allowed_hosts and settings.allowed_hosts != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # 9. GZip压缩中间件（最内层）
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
        compresslevel=6
    )
    
    logger.info("中间件设置完成")


# 导出
__all__ = [
    "RequestLoggingMiddleware",
    "RateLimitMiddleware", 
    "SecurityHeadersMiddleware",
    "ErrorHandlingMiddleware",
    "HealthCheckMiddleware",
    "RequestSizeLimitMiddleware",
    "setup_middleware",
]