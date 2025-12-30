"""
操作日志服务

提供服务器操作日志的创建和管理功能
"""
from typing import Optional, List
from datetime import datetime
import json
from loguru import logger
from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


class OperationLogService:
    """操作日志服务"""
    
    # 操作类型常量
    OP_START = "start"
    OP_STOP = "stop"
    OP_REBOOT = "reboot"
    OP_AUTO_SHUTDOWN = "auto_shutdown"
    
    # 状态常量
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    
    @staticmethod
    def create_operation_log(
        db: Session,
        account_id: int,
        operation_type: str,
        target_id: str,
        target_name: Optional[str] = None,
        target_type: str = "server",
        region: Optional[str] = None,
        reason: Optional[str] = None,
        job_id: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> OperationLog:
        """
        创建操作日志
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            operation_type: 操作类型 (start/stop/reboot/auto_shutdown)
            target_id: 目标 ID
            target_name: 目标名称
            target_type: 目标类型 (server/instance)
            region: 区域
            reason: 操作原因
            job_id: 华为云任务 ID
            extra_data: 额外数据
            
        Returns:
            创建的操作日志
        """
        try:
            log = OperationLog(
                account_id=account_id,
                operation_type=operation_type,
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                region=region,
                status=OperationLogService.STATUS_PENDING,
                job_id=job_id,
                reason=reason,
                extra_data=json.dumps(extra_data) if extra_data else None,
                start_time=datetime.now()
            )
            
            db.add(log)
            db.commit()
            db.refresh(log)
            
            logger.info(
                f"操作日志已创建: log_id={log.id}, "
                f"type={operation_type}, target={target_id}"
            )
            
            return log
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建操作日志失败: {e}")
            raise
    
    @staticmethod
    def update_operation_status(
        db: Session,
        log_id: int,
        status: str,
        job_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[OperationLog]:
        """
        更新操作状态
        
        Args:
            db: 数据库会话
            log_id: 日志 ID
            status: 新状态 (pending/success/failed)
            job_id: 任务 ID
            error_message: 错误信息
            
        Returns:
            更新后的日志
        """
        try:
            log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
            
            if not log:
                return None
            
            log.status = status
            if job_id:
                log.job_id = job_id
            if error_message:
                log.error_message = error_message
            if status in [OperationLogService.STATUS_SUCCESS, OperationLogService.STATUS_FAILED]:
                log.end_time = datetime.now()
            
            db.commit()
            db.refresh(log)
            
            logger.info(f"操作日志已更新: log_id={log_id}, status={status}")
            
            return log
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新操作日志失败: {e}")
            raise
    
    @staticmethod
    def mark_success(
        db: Session,
        log_id: int,
        job_id: Optional[str] = None
    ) -> Optional[OperationLog]:
        """标记操作成功"""
        return OperationLogService.update_operation_status(
            db=db,
            log_id=log_id,
            status=OperationLogService.STATUS_SUCCESS,
            job_id=job_id
        )
    
    @staticmethod
    def mark_failed(
        db: Session,
        log_id: int,
        error_message: str,
        job_id: Optional[str] = None
    ) -> Optional[OperationLog]:
        """标记操作失败"""
        return OperationLogService.update_operation_status(
            db=db,
            log_id=log_id,
            status=OperationLogService.STATUS_FAILED,
            job_id=job_id,
            error_message=error_message
        )
    
    @staticmethod
    def get_operation_logs(
        db: Session,
        account_id: Optional[int] = None,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OperationLog]:
        """
        查询操作日志
        
        Args:
            db: 数据库会话
            account_id: 账户 ID 过滤
            operation_type: 操作类型过滤
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            操作日志列表
        """
        query = db.query(OperationLog)
        
        if account_id:
            query = query.filter(OperationLog.account_id == account_id)
        if operation_type:
            query = query.filter(OperationLog.operation_type == operation_type)
        if status:
            query = query.filter(OperationLog.status == status)
        
        query = query.order_by(OperationLog.created_at.desc())
        
        return query.offset(offset).limit(limit).all()


# 全局实例
operation_log_service = OperationLogService()
