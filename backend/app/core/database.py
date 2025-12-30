"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库 URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/monitor.db")

# 控制是否在控制台输出 SQL 语句（用于开发环境调试）
# 在生产环境请将 环境变量 DATABASE_ECHO=false
_db_echo = os.getenv("DATABASE_ECHO", "True")
DB_ECHO = str(_db_echo).lower() in ("1", "true", "yes")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=DB_ECHO
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    # 导入所有模型，确保它们被注册到 Base
    from app.models import account, server, config, monitor_log, shutdown_log, notification_log, operation_log
    
    # 创建数据目录
    os.makedirs("./data", exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")
