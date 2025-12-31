"""
华为云服务器流量监控系统 - 主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.response import success_response
from app.api.v1 import api_router
from fastapi.staticfiles import StaticFiles

# 初始化日志
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info(f"启动应用: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"API 文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    # 初始化监控调度器和任务
    try:
        from app.services.scheduler import monitor_scheduler
        from app.services.monitor_service import initialize_all_monitor_jobs
        from app.core.database import SessionLocal
        
        # 启动调度器
        logger.info("启动监控调度器")
        monitor_scheduler.start()
        
        # 初始化所有监控任务
        logger.info("初始化监控任务")
        db = SessionLocal()
        try:
            stats = initialize_all_monitor_jobs(db)
            logger.info(
                f"监控任务初始化完成: "
                f"success={stats['success']}, "
                f"skipped={stats['skipped']}, "
                f"failed={stats['failed']}"
            )
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"初始化监控调度器失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("关闭应用")
    
    # 关闭监控调度器
    try:
        from app.services.monitor_service import shutdown_all_monitor_jobs
        shutdown_all_monitor_jobs()
        logger.info("监控调度器已关闭")
    except Exception as e:
        logger.error(f"关闭监控调度器失败: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} "
        f"status_code={response.status_code} "
        f"duration={process_time:.3f}s"
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径 — 若前端静态文件存在则返回 index.html，否则返回健康信息"""
    index_path = "static/index.html"
    try:
        # 直接判断构建产物是否存在（避免依赖未声明的 settings.APP_ENV）
        if __import__("os").path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
    except Exception:
        # 回退到 JSON 响应
        pass

    return success_response(
        data={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        },
        message="服务运行中"
    )


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return success_response(
        data={"status": "healthy"},
        message="系统健康"
    )


# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# 将静态文件挂载放在路由注册之后，避免拦截 API 的 POST/PUT 等非 GET 请求
# 在挂载前确保 `static` 目录存在（开发时若不存在则自动创建），避免 RuntimeError
import os
from pathlib import Path

static_dir = Path("static")
if not static_dir.exists():
    try:
        # 在开发或本地运行时，自动创建以避免挂载失败
        static_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"静态目录不存在，已创建: {static_dir.resolve()}")
    except Exception as _e:
        logger.warning(f"无法创建静态目录 {static_dir}: {_e}")

app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )
