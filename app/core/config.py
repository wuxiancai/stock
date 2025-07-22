from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union
import os
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本信息
    APP_NAME: str = "股票交易系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    
    # 服务端口配置
    PORT: int = 8080  # 兼容性字段
    BACKEND_PORT: int = 8080
    FRONTEND_PORT: int = 3000
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "stock_db"
    DB_USER: str = "stock_user"
    DB_PASSWORD: str = "stock_password"
    DATABASE_URL: str = "postgresql://stock_user:stock_password@localhost:5432/stock_db"
    ASYNC_DATABASE_URL: Optional[str] = None  # 异步数据库URL
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20
    
    # 数据源API配置
    TUSHARE_TOKEN: Optional[str] = None
    AKSHARE_TIMEOUT: int = 30
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    ALGORITHM: str = "HS256"  # JWT算法
    JWT_ALGORITHM: str = "HS256"  # 兼容性字段
    JWT_EXPIRE_MINUTES: int = 1440
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 访问令牌过期时间
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新令牌过期天数
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "1 day"  # 日志轮转
    LOG_RETENTION: str = "30 days"  # 日志保留时间
    
    # 缓存配置
    CACHE_TTL: int = 300
    STOCK_DATA_CACHE_TTL: int = 60  # 股票数据缓存TTL
    REALTIME_DATA_CACHE_TTL: int = 5  # 实时数据缓存TTL
    
    # 数据更新配置
    MARKET_OPEN_TIME: str = "09:30"
    MARKET_CLOSE_TIME: str = "15:00"
    DATA_UPDATE_INTERVAL: int = 60
    AUTO_UPDATE_ENABLED: bool = True  # 自动更新开关
    
    # 技术分析配置
    NINE_TURN_LOOKBACK_DAYS: int = 30  # 九转回看天数
    TECHNICAL_INDICATOR_PERIODS: str = "5,10,20,30,60"  # 技术指标周期
    
    # 邮件配置
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True  # SMTP TLS开关
    
    # 监控配置
    ENABLE_MONITORING: bool = True
    ALERT_EMAIL: Optional[str] = None
    HEALTH_CHECK_INTERVAL: int = 60  # 健康检查间隔
    
    # CORS配置
    CORS_ORIGINS: Union[str, list] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True  # CORS允许凭据
    
    @field_validator('CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS_ORIGINS，支持字符串和列表格式"""
        if isinstance(v, str):
            # 如果是字符串，按逗号分割
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            # 如果已经是列表，直接返回
            return v
        else:
            # 默认值
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ]
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # API限流配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 动态构建数据库URL（如果没有直接设置）
        if self.DATABASE_URL == "postgresql://stock_user:stock_password@localhost:5432/stock_db":
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        # 确保必要的目录存在
        self._ensure_directories()
        
        # 验证关键配置
        self._validate_config()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            Path(self.LOG_FILE).parent,
            Path(self.UPLOAD_DIR)
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """验证关键配置"""
        if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-here":
            if not self.DEBUG:
                raise ValueError("生产环境必须设置有效的 SECRET_KEY")
        
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "your-jwt-secret-key":
            if not self.DEBUG:
                raise ValueError("生产环境必须设置有效的 JWT_SECRET_KEY")
    
    @property
    def database_url_async(self) -> str:
        """异步数据库连接URL"""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG

# 创建全局配置实例
settings = Settings()