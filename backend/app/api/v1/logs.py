"""
日志管理 API
"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response
from app.models.monitor_log import MonitorLog
from app.models.shutdown_log import ShutdownLog
from app.models.operation_log import OperationLog
from app.models.account import Account

router = APIRouter(prefix="/logs", tags=["日志管理"])

# 操作类型名称映射
OPERATION_TYPE_NAMES = {
    'start': '启动',
    'stop': '关机',
    'reboot': '重启',
    'auto_shutdown': '自动关机'
}


class LogStatsResponse(BaseModel):
    """日志统计响应模型"""
    total_monitor_logs: int
    total_shutdown_logs: int
    total_operation_logs: int
    today_monitor_logs: int
    today_shutdown_logs: int
    today_operation_logs: int
    below_threshold_count: int
    shutdown_success_count: int
    shutdown_failed_count: int
    operation_success_count: int
    operation_failed_count: int


@router.get("")
async def get_all_logs(
    log_type: Optional[str] = Query(None, description="日志类型: monitor/shutdown/operation"),
    account_id: Optional[int] = Query(None, description="账户 ID"),
    level: Optional[str] = Query(None, description="日志级别: INFO/WARNING/ERROR/SUCCESS"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取所有日志（监控日志 + 关机日志 + 操作日志合并）
    
    - **log_type**: 日志类型过滤 (monitor/shutdown/operation)
    - **account_id**: 账户 ID 过滤
    - **level**: 日志级别过滤
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **keyword**: 搜索关键词
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    all_logs = []
    
    # 解析日期
    start_datetime = None
    end_datetime = None
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            pass
    
    # 获取监控日志
    if log_type is None or log_type == 'monitor':
        monitor_query = db.query(MonitorLog).join(Account, MonitorLog.account_id == Account.id, isouter=True)
        
        if account_id:
            monitor_query = monitor_query.filter(MonitorLog.account_id == account_id)
        if start_datetime:
            monitor_query = monitor_query.filter(MonitorLog.check_time >= start_datetime)
        if end_datetime:
            monitor_query = monitor_query.filter(MonitorLog.check_time < end_datetime)
        if keyword:
            monitor_query = monitor_query.filter(
                or_(
                    MonitorLog.message.ilike(f"%{keyword}%"),
                    Account.name.ilike(f"%{keyword}%")
                )
            )
        
        # 级别过滤（根据 is_below_threshold 映射）
        if level == 'WARNING':
            monitor_query = monitor_query.filter(MonitorLog.is_below_threshold == True)
        elif level == 'INFO':
            monitor_query = monitor_query.filter(MonitorLog.is_below_threshold == False)
        
        monitor_logs = monitor_query.all()
        
        for log in monitor_logs:
            account = db.query(Account).filter(Account.id == log.account_id).first()
            all_logs.append({
                "id": f"m_{log.id}",
                "type": "monitor",
                "level": "WARNING" if log.is_below_threshold else "INFO",
                "message": log.message or f"流量检查: 剩余 {log.traffic_remaining:.2f}GB, 阈值 {log.threshold:.2f}GB",
                "account_id": log.account_id,
                "account_name": account.name if account else "未知",
                "created_at": log.check_time.isoformat() if log.check_time else log.created_at.isoformat(),
                "details": {
                    "traffic_remaining": log.traffic_remaining,
                    "traffic_total": log.traffic_total,
                    "traffic_used": log.traffic_used,
                    "usage_percentage": log.usage_percentage,
                    "threshold": log.threshold,
                    "is_below_threshold": log.is_below_threshold
                }
            })
    
    # 获取关机日志
    if log_type is None or log_type == 'shutdown':
        shutdown_query = db.query(ShutdownLog).join(Account, ShutdownLog.account_id == Account.id, isouter=True)
        
        if account_id:
            shutdown_query = shutdown_query.filter(ShutdownLog.account_id == account_id)
        if start_datetime:
            shutdown_query = shutdown_query.filter(ShutdownLog.created_at >= start_datetime)
        if end_datetime:
            shutdown_query = shutdown_query.filter(ShutdownLog.created_at < end_datetime)
        if keyword:
            shutdown_query = shutdown_query.filter(
                or_(
                    ShutdownLog.reason.ilike(f"%{keyword}%"),
                    ShutdownLog.error_message.ilike(f"%{keyword}%"),
                    Account.name.ilike(f"%{keyword}%")
                )
            )
        
        # 级别过滤
        if level == 'SUCCESS':
            shutdown_query = shutdown_query.filter(ShutdownLog.status == 'success')
        elif level == 'ERROR':
            shutdown_query = shutdown_query.filter(ShutdownLog.status == 'failed')
        elif level == 'INFO':
            shutdown_query = shutdown_query.filter(ShutdownLog.status == 'pending')
        
        shutdown_logs = shutdown_query.all()
        
        for log in shutdown_logs:
            account = db.query(Account).filter(Account.id == log.account_id).first()
            
            # 根据状态映射级别
            if log.status == 'success':
                log_level = 'SUCCESS'
            elif log.status == 'failed':
                log_level = 'ERROR'
            else:
                log_level = 'INFO'
            
            all_logs.append({
                "id": f"s_{log.id}",
                "type": "shutdown",
                "level": log_level,
                "message": f"[{log.status.upper()}] {log.reason}" + (f" - {log.error_message}" if log.error_message else ""),
                "account_id": log.account_id,
                "account_name": account.name if account else "未知",
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "details": {
                    "server_id": log.server_id,
                    "status": log.status,
                    "job_id": log.job_id,
                    "traffic_remaining": log.traffic_remaining,
                    "error_message": log.error_message,
                    "shutdown_time": log.shutdown_time.isoformat() if log.shutdown_time else None
                }
            })
    
    # 获取操作日志
    if log_type is None or log_type == 'operation':
        op_query = db.query(OperationLog).join(Account, OperationLog.account_id == Account.id, isouter=True)
        
        if account_id:
            op_query = op_query.filter(OperationLog.account_id == account_id)
        if start_datetime:
            op_query = op_query.filter(OperationLog.created_at >= start_datetime)
        if end_datetime:
            op_query = op_query.filter(OperationLog.created_at < end_datetime)
        if keyword:
            op_query = op_query.filter(
                or_(
                    OperationLog.reason.ilike(f"%{keyword}%"),
                    OperationLog.target_id.ilike(f"%{keyword}%"),
                    OperationLog.target_name.ilike(f"%{keyword}%"),
                    Account.name.ilike(f"%{keyword}%")
                )
            )
        
        # 级别过滤
        if level == 'SUCCESS':
            op_query = op_query.filter(OperationLog.status == 'success')
        elif level == 'ERROR':
            op_query = op_query.filter(OperationLog.status == 'failed')
        elif level == 'INFO':
            op_query = op_query.filter(OperationLog.status == 'pending')
        
        operation_logs = op_query.all()
        
        for log in operation_logs:
            account = db.query(Account).filter(Account.id == log.account_id).first()
            
            # 根据状态映射级别
            if log.status == 'success':
                log_level = 'SUCCESS'
            elif log.status == 'failed':
                log_level = 'ERROR'
            else:
                log_level = 'INFO'
            
            op_name = OPERATION_TYPE_NAMES.get(log.operation_type, log.operation_type)
            message = f"[{log.status.upper()}] {op_name} {log.target_type}"
            if log.reason:
                message += f" - {log.reason}"
            if log.error_message:
                message += f" (错误: {log.error_message})"
            
            all_logs.append({
                "id": f"o_{log.id}",
                "type": "operation",
                "level": log_level,
                "message": message,
                "account_id": log.account_id,
                "account_name": account.name if account else "未知",
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "details": {
                    "operation_type": log.operation_type,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "target_name": log.target_name,
                    "region": log.region,
                    "status": log.status,
                    "job_id": log.job_id,
                    "error_message": log.error_message,
                    "start_time": log.start_time.isoformat() if log.start_time else None,
                    "end_time": log.end_time.isoformat() if log.end_time else None
                }
            })
    
    # 按时间倒序排序
    all_logs.sort(key=lambda x: x['created_at'] or '', reverse=True)
    
    # 分页
    total = len(all_logs)
    paginated_logs = all_logs[offset:offset + limit]
    
    return success_response(
        data={
            "total": total,
            "items": paginated_logs
        },
        message="查询成功"
    )


@router.get("/monitor")
async def get_monitor_logs(
    account_id: Optional[int] = Query(None, description="账户 ID"),
    is_below_threshold: Optional[bool] = Query(None, description="是否低于阈值"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取监控日志
    """
    query = db.query(MonitorLog)
    
    if account_id:
        query = query.filter(MonitorLog.account_id == account_id)
    if is_below_threshold is not None:
        query = query.filter(MonitorLog.is_below_threshold == is_below_threshold)
    
    # 日期过滤
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(MonitorLog.check_time >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(MonitorLog.check_time < end_datetime)
        except ValueError:
            pass
    
    # 获取总数
    total = query.count()
    
    # 排序和分页
    query = query.order_by(desc(MonitorLog.check_time))
    logs = query.offset(offset).limit(limit).all()
    
    # 格式化结果
    result = []
    for log in logs:
        account = db.query(Account).filter(Account.id == log.account_id).first()
        result.append({
            "id": log.id,
            "account_id": log.account_id,
            "account_name": account.name if account else "未知",
            "server_id": log.server_id,
            "traffic_remaining": log.traffic_remaining,
            "traffic_total": log.traffic_total,
            "traffic_used": log.traffic_used,
            "usage_percentage": log.usage_percentage,
            "threshold": log.threshold,
            "is_below_threshold": log.is_below_threshold,
            "message": log.message,
            "check_time": log.check_time.isoformat() if log.check_time else None,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return success_response(
        data={
            "total": total,
            "items": result
        },
        message="查询成功"
    )


@router.get("/shutdown")
async def get_shutdown_logs(
    account_id: Optional[int] = Query(None, description="账户 ID"),
    status: Optional[str] = Query(None, description="状态: pending/success/failed"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取关机日志
    """
    query = db.query(ShutdownLog)
    
    if account_id:
        query = query.filter(ShutdownLog.account_id == account_id)
    if status:
        query = query.filter(ShutdownLog.status == status)
    
    # 日期过滤
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ShutdownLog.created_at >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(ShutdownLog.created_at < end_datetime)
        except ValueError:
            pass
    
    # 获取总数
    total = query.count()
    
    # 排序和分页
    query = query.order_by(desc(ShutdownLog.created_at))
    logs = query.offset(offset).limit(limit).all()
    
    # 格式化结果
    result = []
    for log in logs:
        account = db.query(Account).filter(Account.id == log.account_id).first()
        result.append({
            "id": log.id,
            "account_id": log.account_id,
            "account_name": account.name if account else "未知",
            "server_id": log.server_id,
            "reason": log.reason,
            "status": log.status,
            "job_id": log.job_id,
            "traffic_remaining": log.traffic_remaining,
            "error_message": log.error_message,
            "shutdown_time": log.shutdown_time.isoformat() if log.shutdown_time else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None
        })
    
    return success_response(
        data={
            "total": total,
            "items": result
        },
        message="查询成功"
    )


@router.get("/operation")
async def get_operation_logs(
    account_id: Optional[int] = Query(None, description="账户 ID"),
    operation_type: Optional[str] = Query(None, description="操作类型: start/stop/reboot/auto_shutdown"),
    status: Optional[str] = Query(None, description="状态: pending/success/failed"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取操作日志
    """
    query = db.query(OperationLog)
    
    if account_id:
        query = query.filter(OperationLog.account_id == account_id)
    if operation_type:
        query = query.filter(OperationLog.operation_type == operation_type)
    if status:
        query = query.filter(OperationLog.status == status)
    
    # 日期过滤
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(OperationLog.created_at >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(OperationLog.created_at < end_datetime)
        except ValueError:
            pass
    
    # 获取总数
    total = query.count()
    
    # 排序和分页
    query = query.order_by(desc(OperationLog.created_at))
    logs = query.offset(offset).limit(limit).all()
    
    # 格式化结果
    result = []
    for log in logs:
        account = db.query(Account).filter(Account.id == log.account_id).first()
        result.append({
            "id": log.id,
            "account_id": log.account_id,
            "account_name": account.name if account else "未知",
            "operation_type": log.operation_type,
            "operation_name": OPERATION_TYPE_NAMES.get(log.operation_type, log.operation_type),
            "target_type": log.target_type,
            "target_id": log.target_id,
            "target_name": log.target_name,
            "region": log.region,
            "status": log.status,
            "job_id": log.job_id,
            "reason": log.reason,
            "error_message": log.error_message,
            "start_time": log.start_time.isoformat() if log.start_time else None,
            "end_time": log.end_time.isoformat() if log.end_time else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None
        })
    
    return success_response(
        data={
            "total": total,
            "items": result
        },
        message="查询成功"
    )


@router.get("/stats")
async def get_log_stats(db: Session = Depends(get_db)):
    """
    获取日志统计信息
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 统计监控日志
    total_monitor_logs = db.query(func.count(MonitorLog.id)).scalar() or 0
    today_monitor_logs = db.query(func.count(MonitorLog.id)).filter(
        MonitorLog.check_time >= today
    ).scalar() or 0
    below_threshold_count = db.query(func.count(MonitorLog.id)).filter(
        MonitorLog.is_below_threshold == True
    ).scalar() or 0
    
    # 统计关机日志
    total_shutdown_logs = db.query(func.count(ShutdownLog.id)).scalar() or 0
    today_shutdown_logs = db.query(func.count(ShutdownLog.id)).filter(
        ShutdownLog.created_at >= today
    ).scalar() or 0
    shutdown_success_count = db.query(func.count(ShutdownLog.id)).filter(
        ShutdownLog.status == 'success'
    ).scalar() or 0
    shutdown_failed_count = db.query(func.count(ShutdownLog.id)).filter(
        ShutdownLog.status == 'failed'
    ).scalar() or 0
    
    # 统计操作日志
    total_operation_logs = db.query(func.count(OperationLog.id)).scalar() or 0
    today_operation_logs = db.query(func.count(OperationLog.id)).filter(
        OperationLog.created_at >= today
    ).scalar() or 0
    operation_success_count = db.query(func.count(OperationLog.id)).filter(
        OperationLog.status == 'success'
    ).scalar() or 0
    operation_failed_count = db.query(func.count(OperationLog.id)).filter(
        OperationLog.status == 'failed'
    ).scalar() or 0
    
    return success_response(
        data={
            "total_monitor_logs": total_monitor_logs,
            "total_shutdown_logs": total_shutdown_logs,
            "total_operation_logs": total_operation_logs,
            "today_monitor_logs": today_monitor_logs,
            "today_shutdown_logs": today_shutdown_logs,
            "today_operation_logs": today_operation_logs,
            "below_threshold_count": below_threshold_count,
            "shutdown_success_count": shutdown_success_count,
            "shutdown_failed_count": shutdown_failed_count,
            "operation_success_count": operation_success_count,
            "operation_failed_count": operation_failed_count
        },
        message="查询成功"
    )


@router.post("/clean")
async def clean_old_logs(
    days: int = Query(30, ge=1, le=365, description="保留天数"),
    db: Session = Depends(get_db)
):
    """
    清理旧日志
    
    - **days**: 保留最近多少天的日志，默认 30 天
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 清理监控日志
    monitor_deleted = db.query(MonitorLog).filter(
        MonitorLog.check_time < cutoff_date
    ).delete(synchronize_session=False)
    
    # 清理关机日志
    shutdown_deleted = db.query(ShutdownLog).filter(
        ShutdownLog.created_at < cutoff_date
    ).delete(synchronize_session=False)
    
    # 清理操作日志
    operation_deleted = db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_date
    ).delete(synchronize_session=False)
    
    db.commit()
    
    total_deleted = monitor_deleted + shutdown_deleted + operation_deleted
    logger.info(f"清理旧日志: monitor={monitor_deleted}, shutdown={shutdown_deleted}, operation={operation_deleted}, days={days}")
    
    return success_response(
        data={
            "monitor_deleted": monitor_deleted,
            "shutdown_deleted": shutdown_deleted,
            "operation_deleted": operation_deleted,
            "cutoff_date": cutoff_date.isoformat()
        },
        message=f"成功清理 {total_deleted} 条日志"
    )
