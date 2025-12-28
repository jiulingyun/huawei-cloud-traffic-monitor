"""
日志配置
"""
from loguru import logger
import sys
import os
from app.core.config import settings


def setup_logging():
    """
    配置日志系统
    """
    # 移除默认的日志处理器
    logger.remove()
    
    # 创建日志目录
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # 控制台输出 - 开发环境
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # 文件输出 - 所有日志
    logger.add(
        f"{settings.LOG_DIR}/app.log",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
    )
    
    # 文件输出 - 错误日志
    logger.add(
        f"{settings.LOG_DIR}/error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
    )
    
    logger.info("日志系统初始化完成")
    
    return logger
