"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1 import accounts, servers, configs, monitor, auth, dashboard, traffic

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(accounts.router)
api_router.include_router(servers.router)
api_router.include_router(traffic.router)
api_router.include_router(configs.router)
api_router.include_router(monitor.router)
