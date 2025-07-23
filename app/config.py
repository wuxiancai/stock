"""
股票交易系统配置模块
支持多环境配置和动态加载
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    app_name: str = "Stock Trading System"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    
    # 数据库配置
    database_url: str
    database_url_sync: str
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # API密钥配置
    tushare_token: str
    akshare_timeout: int = 30
    
    # JWT配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # 时区配置
    timezone: str = "Asia/Shanghai"
    
    # 数据更新配置
    update_interval_minutes: int = 5
    batch_size: int = 100
    max_retries: int = 3
    
    # 缓存配置
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000
    
    # 监控配置
    prometheus_port: int = 9090
    health_check_interval: int = 60
    
    # 跨域配置
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # WebSocket配置
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 1000
    
    # 文件上传配置
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads"
    
    # 邮件配置
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # 第三方API配置
    request_timeout: int = 30
    max_concurrent_requests: int = 10
    rate_limit_per_minute: int = 60
    
    # 中间件配置
    enable_rate_limit: bool = True
    rate_limit_calls: int = 100
    rate_limit_period: int = 60
    max_request_size: int = 10485760  # 10MB
    allowed_hosts: List[str] = ["*"]
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator('cors_allow_methods', mode='before')
    @classmethod
    def assemble_cors_methods(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator('cors_allow_headers', mode='before')
    @classmethod
    def assemble_cors_headers(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


class DevelopmentSettings(Settings):
    """开发环境配置"""
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """生产环境配置"""
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    
    # 生产环境安全配置
    cors_origins: List[str] = []  # 生产环境需要明确指定
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your-secret-key-here-change-in-production":
            raise ValueError("生产环境必须设置安全的SECRET_KEY")
        return v


class TestSettings(Settings):
    """测试环境配置"""
    environment: str = "testing"
    debug: bool = True
    log_level: str = "DEBUG"
    
    # 测试数据库
    database_url: str = "postgresql+asyncpg://stock_user:stock_password@localhost:5432/stock_trading_test_db"
    database_url_sync: str = "postgresql://stock_user:stock_password@localhost:5432/stock_trading_test_db"
    
    # 测试Redis
    redis_db: int = 15  # 使用不同的Redis数据库


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()


# 数据库配置
class DatabaseConfig:
    """数据库配置类"""
    
    @staticmethod
    def get_async_url() -> str:
        """获取异步数据库URL"""
        return settings.database_url
    
    @staticmethod
    def get_sync_url() -> str:
        """获取同步数据库URL"""
        return settings.database_url_sync
    
    @staticmethod
    def get_engine_config() -> dict:
        """获取数据库引擎配置"""
        config = {
            "echo": settings.debug,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
        
        if settings.environment == "production":
            config.update({
                "pool_size": 50,
                "max_overflow": 100,
            })
        
        return config


# Redis配置
class RedisConfig:
    """Redis配置类"""
    
    @staticmethod
    def get_connection_config() -> dict:
        """获取Redis连接配置"""
        return {
            "host": settings.redis_host,
            "port": settings.redis_port,
            "db": settings.redis_db,
            "password": settings.redis_password,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }


# 日志配置
class LogConfig:
    """日志配置类"""
    
    @staticmethod
    def get_config() -> dict:
        """获取日志配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[{time:YYYY-MM-DD HH:mm:ss}] {level} | {name}:{function}:{line} - {message}",
                    "style": "{",
                },
                "access": {
                    "format": "[{time:YYYY-MM-DD HH:mm:ss}] {level} | {extra[client_ip]} - {message}",
                    "style": "{",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "loguru.logger",
                    "level": settings.log_level,
                },
                "access": {
                    "formatter": "access",
                    "class": "loguru.logger",
                    "level": "INFO",
                },
            },
            "loggers": {
                "": {
                    "level": settings.log_level,
                    "handlers": ["default"],
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["access"],
                    "propagate": False,
                },
            },
        }


# Celery配置
class CeleryConfig:
    """Celery配置类"""
    
    broker_url = settings.celery_broker_url
    result_backend = settings.celery_result_backend
    task_serializer = "json"
    accept_content = ["json"]
    result_serializer = "json"
    timezone = "Asia/Shanghai"
    enable_utc = True
    
    # 任务路由
    task_routes = {
        "app.tasks.data_update.*": {"queue": "data_update"},
        "app.tasks.analysis.*": {"queue": "analysis"},
        "app.tasks.notification.*": {"queue": "notification"},
    }
    
    # 任务配置
    task_annotations = {
        "*": {"rate_limit": "100/m"},
        "app.tasks.data_update.update_realtime_quotes": {"rate_limit": "10/s"},
        "app.tasks.analysis.calculate_nine_turn": {"rate_limit": "5/m"},
    }
    
    # 工作进程配置
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # 结果过期时间
    result_expires = 3600
    
    # 任务重试配置
    task_acks_late = True
    task_reject_on_worker_lost = True


# API配置
class APIConfig:
    """API配置类"""
    
    # Tushare配置
    TUSHARE_BASE_URL = "http://api.tushare.pro"
    TUSHARE_TOKEN = settings.tushare_token
    TUSHARE_TIMEOUT = 30
    TUSHARE_MAX_RETRIES = 3
    
    # AKShare配置
    AKSHARE_TIMEOUT = settings.akshare_timeout
    AKSHARE_MAX_RETRIES = 3
    
    # 请求配置
    REQUEST_TIMEOUT = settings.request_timeout
    MAX_CONCURRENT_REQUESTS = settings.max_concurrent_requests
    RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute


# 导出配置
__all__ = [
    "settings",
    "get_settings",
    "DatabaseConfig",
    "RedisConfig",
    "LogConfig",
    "CeleryConfig",
    "APIConfig",
    "DevelopmentSettings",
    "ProductionSettings",
    "TestSettings",
]