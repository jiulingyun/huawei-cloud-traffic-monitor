"""
仪表板 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response
from app.models.account import Account
from app.models.config import Config
from app.services.huawei_cloud.flexusl_service import FlexusLService
from app.utils.encryption import get_encryption_service

router = APIRouter(prefix="/dashboard", tags=["仪表板"])


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    获取仪表板统计数据
    
    返回:
    - accounts: 账户总数
    - enabled_accounts: 启用的账户数
    - servers: Flexus L 实例总数
    - traffic_remaining: 剩余流量 (GB)
    - traffic_usage: 流量使用率 (%)
    - alerts: 今日告警数
    """
    # 账户统计
    total_accounts = db.query(func.count(Account.id)).scalar() or 0
    enabled_accounts = db.query(func.count(Account.id)).filter(
        Account.is_enabled == True
    ).scalar() or 0
    
    # 获取所有启用账户的实例和流量数据
    servers_count = 0
    total_traffic = 0.0
    used_traffic = 0.0
    remaining_traffic = 0.0
    alerts_count = 0
    
    accounts = db.query(Account).filter(Account.is_enabled == True).all()
    encryption_service = get_encryption_service()
    
    for account in accounts:
        try:
            ak = encryption_service.decrypt(account.ak)
            sk = encryption_service.decrypt(account.sk)
            is_intl = getattr(account, 'is_international', True)
            
            service = FlexusLService(
                ak=ak,
                sk=sk,
                region=account.region,
                is_international=is_intl
            )
            
            summary = service.get_all_traffic_summary()
            servers_count += summary['instance_count']
            total_traffic += summary['total_amount']
            used_traffic += summary['used_amount']
            remaining_traffic += summary['remaining_amount']
            
        except Exception as e:
            logger.warning(f"账户 {account.name} 查询失败: {e}")
            continue
    
    # 计算流量使用率
    traffic_usage = (used_traffic / total_traffic * 100) if total_traffic > 0 else 0
    
    return success_response(data={
        "accounts": total_accounts,
        "enabled_accounts": enabled_accounts,
        "servers": servers_count,
        "traffic_total": round(total_traffic, 2),
        "traffic_used": round(used_traffic, 2),
        "traffic_remaining": round(remaining_traffic, 2),
        "traffic_usage": round(traffic_usage, 2),
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
    
    返回账户信息，包括名称、实例数、流量使用情况
    """
    accounts = db.query(Account).filter(
        Account.is_enabled == True
    ).limit(limit).all()
    
    result = []
    encryption_service = get_encryption_service()
    
    for account in accounts:
        account_data = {
            "id": account.id,
            "name": account.name,
            "region": account.region,
            "servers": 0,
            "traffic_total": 0.0,
            "traffic_remaining": 0.0,
            "traffic_usage": 0.0,
            "status": "active" if account.is_enabled else "disabled",
            "created_at": account.created_at.isoformat() if account.created_at else None
        }
        
        # 获取实时数据
        try:
            ak = encryption_service.decrypt(account.ak)
            sk = encryption_service.decrypt(account.sk)
            is_intl = getattr(account, 'is_international', True)
            
            service = FlexusLService(
                ak=ak,
                sk=sk,
                region=account.region,
                is_international=is_intl
            )
            
            summary = service.get_all_traffic_summary()
            account_data['servers'] = summary['instance_count']
            account_data['traffic_total'] = summary['total_amount']
            account_data['traffic_remaining'] = summary['remaining_amount']
            account_data['traffic_usage'] = summary['usage_percentage']
            
        except Exception as e:
            logger.warning(f"账户 {account.name} 数据获取失败: {e}")
            account_data['status'] = 'error'
        
        result.append(account_data)
    
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
        "version": "v1.0.1",
        "monitoring_status": "running",
        "last_check": last_check,
        "config_count": config_count,
        "uptime": "-"  # TODO: 从启动时间计算
    })
