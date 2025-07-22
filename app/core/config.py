from pydantic_settings import BaseSettings
from typing import Optional
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
    BACKEND_PORT: int = 8080
    FRONTEND_PORT: int = 3000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/stock_trading"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 数据源API配置
    TUSHARE_TOKEN: Optional[str] = None
    AKSHARE_TIMEOUT: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # 缓存配置
    CACHE_TTL: int = 300
    REDIS_MAX_CONNECTIONS: int = 20
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # 市场时间配置
    MARKET_OPEN_TIME: str = "09:30"
    MARKET_CLOSE_TIME: str = "15:00"
    DATA_UPDATE_INTERVAL: int = 60
    
    # 邮件配置
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # 监控配置
    ENABLE_MONITORING: bool = True
    ALERT_EMAIL: Optional[str] = None
    
    # CORS配置
    CORS_ORIGINS: list = [
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
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return not self.DEBUG

# 创建全局配置实例
settings = Settings()