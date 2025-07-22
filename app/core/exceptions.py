from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

class CustomHTTPException(HTTPException):
    """自定义HTTP异常"""
    pass

class DatabaseException(Exception):
    """数据库异常"""
    pass

class DataSourceException(Exception):
    """数据源异常"""
    pass

class AuthenticationException(Exception):
    """认证异常"""
    pass

class AuthorizationException(Exception):
    """授权异常"""
    pass

def setup_exception_handlers(app):
    """设置异常处理器"""
    
    @app.exception_handler(CustomHTTPException)
    async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
        logger.error(f"自定义HTTP异常: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "CustomHTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP异常: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"请求验证异常: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "请求参数验证失败",
                "details": exc.errors(),
                "status_code": 422
            }
        )
    
    @app.exception_handler(DatabaseException)
    async def database_exception_handler(request: Request, exc: DatabaseException):
        logger.error(f"数据库异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "DatabaseException",
                "message": "数据库操作失败",
                "status_code": 500
            }
        )
    
    @app.exception_handler(DataSourceException)
    async def data_source_exception_handler(request: Request, exc: DataSourceException):
        logger.error(f"数据源异常: {str(exc)}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "DataSourceException",
                "message": "数据源服务不可用",
                "status_code": 503
            }
        )
    
    @app.exception_handler(AuthenticationException)
    async def authentication_exception_handler(request: Request, exc: AuthenticationException):
        logger.error(f"认证异常: {str(exc)}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "AuthenticationException",
                "message": "认证失败",
                "status_code": 401
            }
        )
    
    @app.exception_handler(AuthorizationException)
    async def authorization_exception_handler(request: Request, exc: AuthorizationException):
        logger.error(f"授权异常: {str(exc)}")
        return JSONResponse(
            status_code=403,
            content={
                "error": "AuthorizationException",
                "message": "权限不足",
                "status_code": 403
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "服务器内部错误",
                "status_code": 500
            }
        )