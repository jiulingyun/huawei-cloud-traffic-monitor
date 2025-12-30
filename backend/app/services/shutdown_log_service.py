"""
关机日志服务

提供关机日志的创建和查询功能
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.models.shutdown_log import ShutdownLog


class ShutdownLogService:
    """关机日志服务"""
    
    @staticmethod
    def create_shutdown_log(
        db: Session,
        account_id: int,
        server_id: int,
        reason: str,
        status: str = "pending",
        job_id: Optional[str] = None,
        traffic_remaining: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> ShutdownLog:
        """
        创建关机日志
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            server_id: 服务器 ID
            reason: 关机原因
            status: 状态 (pending/success/failed)
            job_id: 华为云任务 ID
            traffic_remaining: 关机时剩余流量
            error_message: 错误信息
            
        Returns:
            创建的关机日志
        """
        try:
            log = ShutdownLog(
                account_id=account_id,
                server_id=server_id,
                reason=reason,
                status=status,
                job_id=job_id,
                traffic_remaining=traffic_remaining,
                error_message=error_message
            )
            
            db.add(log)
            db.commit()
            db.refresh(log)
            
            logger.info(
                f"关机日志已创建: log_id={log.id}, "
                f"account_id={account_id}, server_id={server_id}, "
                f"status={status}"
            )
            
            return log
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建关机日志失败: {e}")
            raise
    
    @staticmethod
    def update_shutdown_log(
        db: Session,
        log_id: int,
        status: Optional[str] = None,
        job_id: Optional[str] = None,
        error_message: Optional[str] = None,
        shutdown_time: Optional[datetime] = None
    ) -> Optional[ShutdownLog]:
        """
        更新关机日志
        
        Args:
            db: 数据库会话
            log_id: 日志 ID
            status: 新状态
            job_id: 任务 ID
            error_message: 错误信息
            shutdown_time: 实际关机时间
            
        Returns:
            更新后的日志，不存在返回 None
        """
        try:
            log = db.query(ShutdownLog).filter(ShutdownLog.id == log_id).first()
            
            if not log:
                return None
            
            if status is not None:
                log.status = status
            if job_id is not None:
                log.job_id = job_id
            if error_message is not None:
                log.error_message = error_message
            if shutdown_time is not None:
                log.shutdown_time = shutdown_time
            
            db.commit()
            db.refresh(log)
            
            logger.info(f"关机日志已更新: log_id={log_id}, status={log.status}")
            
            return log
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新关机日志失败: {e}")
            raise
    
    @staticmethod
    def create_batch_shutdown_logs(
        db: Session,
        account_id: int,
        server_ids: List[int],
        reason: str,
        job_id: Optional[str] = None,
        traffic_remaining: Optional[str] = None
    ) -> List[ShutdownLog]:
        """
        批量创建关机日志
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            server_ids: 服务器 ID 列表
            reason: 关机原因
            job_id: 华为云任务 ID
            traffic_remaining: 关机时剩余流量
            
        Returns:
            创建的关机日志列表
        """
        logs = []
        
        try:
            for server_id in server_ids:
                log = ShutdownLog(
                    account_id=account_id,
                    server_id=server_id,
                    reason=reason,
                    status="pending",
                    job_id=job_id,
                    traffic_remaining=traffic_remaining
                )
                db.add(log)
                logs.append(log)
            
            db.commit()
            
            for log in logs:
                db.refresh(log)
            
            logger.info(
                f"批量创建关机日志: count={len(logs)}, "
                f"account_id={account_id}, job_id={job_id}"
            )
            
            return logs
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量创建关机日志失败: {e}")
            raise
    
    @staticmethod
    def update_batch_shutdown_logs_by_job(
        db: Session,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        shutdown_time: Optional[datetime] = None
    ) -> int:
        """
        根据任务 ID 批量更新关机日志状态
        
        Args:
            db: 数据库会话
            job_id: 任务 ID
            status: 新状态
            error_message: 错误信息
            shutdown_time: 实际关机时间
            
        Returns:
            更新的记录数
        """
        try:
            query = db.query(ShutdownLog).filter(ShutdownLog.job_id == job_id)
            
            update_data = {"status": status}
            if error_message is not None:
                update_data["error_message"] = error_message
            if shutdown_time is not None:
                update_data["shutdown_time"] = shutdown_time
            
            count = query.update(update_data, synchronize_session=False)
            db.commit()
            
            logger.info(f"批量更新关机日志: job_id={job_id}, count={count}, status={status}")
            
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(f"批量更新关机日志失败: {e}")
            raise


# 全局实例
shutdown_log_service = ShutdownLogService()
