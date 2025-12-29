"""
仪表板 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.response import success_response
from app.models.account import Account
from app.models.config import Config

router = APIRouter(prefix="/dashboard", tags=["仪表板"])


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    获取仪表板统计数据
    
    返回:
    - accounts: 账户总数
    - enabled_accounts: 启用的账户数
    - servers: 服务器总数（模拟数据）
    - alerts: 今日告警数（模拟数据）
    - monitoring: 监控中的账户数
    """
    # 账户统计
    total_accounts = db.query(func.count(Account.id)).scalar() or 0
    enabled_accounts = db.query(func.count(Account.id)).filter(
        Account.is_enabled == True
    ).scalar() or 0
    
    # TODO: 从监控日志中获取真实数据
    # 这里暂时使用模拟数据
    servers_count = 0  # 需要从华为云 API 获取
    alerts_count = 0   # 需要从日志中统计今日告警
    
    return success_response(data={
        "accounts": total_accounts,
        "enabled_accounts": enabled_accounts,
        "servers": servers_count,
        "alerts": alerts_count,
        "monitoring": enabled_accounts
    })


@router.get("/accounts")
async def get_dashboard_accounts(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取仪表板账户列表
    
    返回账户信息，包括名称、区域、服务器数、流量等
    """
    accounts = db.query(Account).filter(
        Account.is_enabled == True
    ).limit(limit).all()
    
    result = []
    for account in accounts:
        result.append({
            "id": account.id,
            "name": account.name,
            "region": account.region,
            "servers": 0,  # TODO: 从华为云 API 获取
            "traffic": 0.0,  # TODO: 从监控数据中获取
            "status": "active" if account.is_enabled else "disabled",
            "created_at": account.created_at.isoformat() if account.created_at else None
        })
    
    return success_response(data=result)


@router.get("/notifications")
async def get_dashboard_notifications(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取最近通知列表
    
    从监控日志中获取最近的通知记录
    """
    # TODO: 从监控日志表中查询
    # 暂时返回空列表
    notifications = []
    
    return success_response(data=notifications)


@router.get("/system-info")
async def get_system_info(db: Session = Depends(get_db)):
    """
    获取系统信息
    
    返回系统版本、监控状态、上次检查时间等
    """
    # 获取配置数量
    config_count = db.query(func.count(Config.id)).scalar() or 0
    
    # TODO: 从监控任务中获取上次检查时间
    last_check = "未运行"
    
    return success_response(data={
        "version": "v1.0.0",
        "monitoring_status": "running",
        "last_check": last_check,
        "config_count": config_count,
        "uptime": "-"  # TODO: 从启动时间计算
    })
