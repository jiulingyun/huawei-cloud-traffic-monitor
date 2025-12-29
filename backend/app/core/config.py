"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "华为云服务器流量监控系统"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "实时监控华为云服务器流量，自动关机并发送飞书通知"
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]  # 生产环境需要配置具体域名
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/monitor.db"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "30 days"
    
    # 加密密钥
    ENCRYPTION_KEY: Optional[str] = None
    
    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 管理员配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # 监控配置
    DEFAULT_CHECK_INTERVAL: int = 5  # 分钟
    DEFAULT_TRAFFIC_THRESHOLD: float = 10.0  # GB
    
    # 飞书配置
    FEISHU_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建配置实例
settings = Settings()
