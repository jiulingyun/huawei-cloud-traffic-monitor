"""
监控管理 API
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.models.monitor_log import MonitorLog
from app.models.account import Account
from app.models.config import Config
from app.services.scheduler import monitor_scheduler
from app.services.config_service import config_service

router = APIRouter(prefix="/monitor", tags=["监控管理"])


# Pydantic 模型
class MonitorLogResponse(BaseModel):
    """监控日志响应模型"""
    id: int
    account_id: int
    server_id: int
    traffic_remaining: float
    traffic_total: Optional[float]
    traffic_used: Optional[float]
    usage_percentage: Optional[float]
    threshold: float
    is_below_threshold: bool
    check_time: str
    message: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class MonitorStatusResponse(BaseModel):
    """监控状态响应模型"""
    scheduler_running: bool
    total_jobs: int
    jobs: List[dict]


class StartMonitorRequest(BaseModel):
    """启动监控请求模型"""
    account_id: Optional[int] = Field(None, description="账户 ID（留空则启动所有已配置的账户）")


class StopMonitorRequest(BaseModel):
    """停止监控请求模型"""
    account_id: Optional[int] = Field(None, description="账户 ID（留空则停止所有监控任务）")


@router.get("/logs")
async def get_monitor_logs(
    account_id: Optional[int] = Query(None, description="账户 ID 过滤"),
    is_below_threshold: Optional[bool] = Query(None, description="是否低于阈值"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取监控日志
    
    - **account_id**: 账户 ID 过滤（可选）
    - **is_below_threshold**: 是否低于阈值过滤（可选）
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    query = db.query(MonitorLog)
    
    if account_id is not None:
        query = query.filter(MonitorLog.account_id == account_id)
    
    if is_below_threshold is not None:
        query = query.filter(MonitorLog.is_below_threshold == is_below_threshold)
    
    # 按检查时间倒序
    query = query.order_by(desc(MonitorLog.check_time))
    
    # 获取总数
    total = query.count()
    
    # 分页
    logs = query.offset(offset).limit(limit).all()
    
    # 转换为响应格式
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "account_id": log.account_id,
            "server_id": log.server_id,
            "traffic_remaining": log.traffic_remaining,
            "traffic_total": log.traffic_total,
            "traffic_used": log.traffic_used,
            "usage_percentage": log.usage_percentage,
            "threshold": log.threshold,
            "is_below_threshold": log.is_below_threshold,
            "check_time": log.check_time.isoformat() if log.check_time else None,
            "message": log.message,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return success_response(
        data={
            "total": total,
            "items": result
        },
        message="查询成功"
    )


@router.get("/status")
async def get_monitor_status(db: Session = Depends(get_db)):
    """
    获取监控状态
    
    返回调度器运行状态和所有监控任务信息
    """
    # 获取调度器状态
    is_running = monitor_scheduler.is_running()
    jobs = monitor_scheduler.list_jobs()
    
    return success_response(
        data={
            "scheduler_running": is_running,
            "total_jobs": len(jobs),
            "jobs": jobs
        },
        message="查询成功"
    )


@router.post("/start")
async def start_monitor(
    request: Optional[StartMonitorRequest] = None,
    db: Session = Depends(get_db)
):
    """
    启动监控
    
    - 如果指定 account_id，只启动该账户的监控任务
    - 如果不指定，启动所有已配置账户的监控任务
    """
    # 确保调度器已启动
    if not monitor_scheduler.is_running():
        monitor_scheduler.start()
    
    account_id = request.account_id if request else None
    started_tasks = []
    errors = []
    
    # 获取需要启动监控的账户
    if account_id:
        accounts = db.query(Account).filter(
            Account.id == account_id,
            Account.is_enabled == True
        ).all()
    else:
        accounts = db.query(Account).filter(Account.is_enabled == True).all()
    
    if not accounts:
        return error_response(message="没有可用的账户")
    
    for account in accounts:
        try:
            # 获取账户的有效配置
            config = config_service.get_effective_config(db, account.id)
            
            if not config:
                logger.warning(f"账户 {account.name} 没有配置，跳过")
                continue
            
            # 检查任务是否已存在
            job_id = f"monitor_account_{account.id}"
            existing_job = monitor_scheduler.get_job_info(job_id)
            
            if existing_job:
                logger.info(f"账户 {account.name} 的监控任务已存在，跳过")
                continue
            
            # 创建监控任务
            from app.services.monitor_service import create_monitor_job_for_account
            success = create_monitor_job_for_account(db, account, config)
            
            if success:
                started_tasks.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "job_id": job_id,
                    "interval_minutes": config.check_interval
                })
            else:
                errors.append({
                    "account_id": account.id,
                    "account_name": account.name,
                    "error": "创建任务失败"
                })
                
        except Exception as e:
            logger.error(f"启动账户 {account.name} 的监控任务失败: {e}")
            errors.append({
                "account_id": account.id,
                "account_name": account.name,
                "error": str(e)
            })
    
    return success_response(
        data={
            "started_tasks": started_tasks,
            "errors": errors
        },
        message=f"成功启动 {len(started_tasks)} 个监控任务"
    )


@router.post("/stop")
async def stop_monitor(
    request: Optional[StopMonitorRequest] = None,
    db: Session = Depends(get_db)
):
    """
    停止监控
    
    - 如果指定 account_id，只停止该账户的监控任务
    - 如果不指定，停止所有监控任务
    """
    account_id = request.account_id if request else None
    stopped_tasks = []
    
    if account_id:
        # 停止指定账户的监控任务
        job_id = f"monitor_account_{account_id}"
        if monitor_scheduler.remove_job(job_id):
            stopped_tasks.append(job_id)
    else:
        # 停止所有监控任务
        jobs = monitor_scheduler.list_jobs()
        for job in jobs:
            if job['id'].startswith('monitor_'):
                if monitor_scheduler.remove_job(job['id']):
                    stopped_tasks.append(job['id'])
    
    return success_response(
        data={
            "stopped_tasks": stopped_tasks
        },
        message=f"成功停止 {len(stopped_tasks)} 个监控任务"
    )


@router.post("/pause/{account_id}")
async def pause_monitor(account_id: int, db: Session = Depends(get_db)):
    """
    暂停指定账户的监控任务
    
    - **account_id**: 账户 ID
    """
    job_id = f"monitor_account_{account_id}"
    
    if monitor_scheduler.pause_job(job_id):
        return success_response(message=f"监控任务已暂停: {job_id}")
    else:
        raise HTTPException(status_code=404, detail="监控任务不存在")


@router.post("/resume/{account_id}")
async def resume_monitor(account_id: int, db: Session = Depends(get_db)):
    """
    恢复指定账户的监控任务
    
    - **account_id**: 账户 ID
    """
    job_id = f"monitor_account_{account_id}"
    
    if monitor_scheduler.resume_job(job_id):
        return success_response(message=f"监控任务已恢复: {job_id}")
    else:
        raise HTTPException(status_code=404, detail="监控任务不存在")


@router.get("/job/{account_id}")
async def get_monitor_job(account_id: int, db: Session = Depends(get_db)):
    """
    获取指定账户的监控任务信息
    
    - **account_id**: 账户 ID
    """
    job_id = f"monitor_account_{account_id}"
    
    job_info = monitor_scheduler.get_job_info(job_id)
    
    if job_info:
        return success_response(data=job_info, message="查询成功")
    else:
        raise HTTPException(status_code=404, detail="监控任务不存在")
