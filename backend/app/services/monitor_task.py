"""
监控任务管理服务

管理流量监控任务的创建、执行和状态跟踪
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.services.scheduler import monitor_scheduler
from app.models.config import MonitorConfig
from app.models.monitor_log import MonitorLog
from app.services.huawei_cloud import client_manager, TrafficService, ECSService
from app.services.monitor_logic import monitor_logic
from app.core.database import get_db


class MonitorTaskManager:
    """监控任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        logger.info("初始化监控任务管理器")
    
    def create_monitor_task(
        self,
        config_id: int,
        account_id: int,
        encrypted_ak: str,
        encrypted_sk: str,
        region: str,
        project_id: str,
        traffic_resource_ids: List[str],
        traffic_threshold: float,
        interval_minutes: int
    ) -> bool:
        """
        创建监控任务
        
        Args:
            config_id: 监控配置 ID
            account_id: 账户 ID
            encrypted_ak: 加密的 AK
            encrypted_sk: 加密的 SK
            region: 区域
            project_id: 项目 ID
            traffic_resource_ids: 流量包资源 ID 列表
            traffic_threshold: 流量阈值（GB）
            interval_minutes: 监控间隔（分钟）
            
        Returns:
            是否创建成功
        """
        job_id = f"monitor_config_{config_id}"
        
        logger.info(
            f"创建监控任务: config_id={config_id}, "
            f"interval={interval_minutes}分钟"
        )
        
        # 添加定时任务
        success = monitor_scheduler.add_interval_job(
            job_id=job_id,
            func=self._execute_monitor_task,
            minutes=interval_minutes,
            config_id=config_id,
            account_id=account_id,
            encrypted_ak=encrypted_ak,
            encrypted_sk=encrypted_sk,
            region=region,
            project_id=project_id,
            traffic_resource_ids=traffic_resource_ids,
            traffic_threshold=traffic_threshold
        )
        
        if success:
            logger.info(f"监控任务创建成功: job_id={job_id}")
        else:
            logger.error(f"监控任务创建失败: job_id={job_id}")
        
        return success
    
    def _execute_monitor_task(
        self,
        config_id: int,
        account_id: int,
        encrypted_ak: str,
        encrypted_sk: str,
        region: str,
        project_id: str,
        traffic_resource_ids: List[str],
        traffic_threshold: float
    ):
        """
        执行监控任务
        
        Args:
            config_id: 监控配置 ID
            account_id: 账户 ID
            encrypted_ak: 加密的 AK
            encrypted_sk: 加密的 SK
            region: 区域
            project_id: 项目 ID
            traffic_resource_ids: 流量包资源 ID 列表
            traffic_threshold: 流量阈值（GB）
        """
        logger.info(f"执行监控任务: config_id={config_id}")
        
        try:
            # 获取华为云客户端
            client = client_manager.get_client(
                account_id=account_id,
                encrypted_ak=encrypted_ak,
                encrypted_sk=encrypted_sk,
                region=region
            )
            
            # 创建流量服务
            traffic_service = TrafficService(client)
            
            # 查询流量包信息
            logger.info(f"查询流量包: resource_ids={traffic_resource_ids}")
            is_below_threshold, remaining_traffic = traffic_service.check_traffic_threshold(
                resource_ids=traffic_resource_ids,
                threshold=traffic_threshold
            )
            
            # 使用监控逻辑判断
            is_below, result_desc = monitor_logic.check_traffic_threshold(
                remaining_traffic=remaining_traffic,
                threshold=traffic_threshold
            )
            
            logger.info(
                f"监控检查完成: remaining={remaining_traffic}GB, "
                f"threshold={traffic_threshold}GB, "
                f"is_below={is_below}"
            )
            
            # 保存监控日志到数据库
            db = next(get_db())
            try:
                monitor_logic.create_monitor_log(
                    db=db,
                    config_id=config_id,
                    remaining_traffic=remaining_traffic,
                    threshold=traffic_threshold,
                    is_below_threshold=is_below,
                    check_result=result_desc
                )
            finally:
                db.close()
            
            # 如果流量低于阈值，触发关机逻辑
            if is_below:
                logger.warning(
                    f"流量低于阈值！config_id={config_id}, "
                    f"remaining={remaining_traffic}GB, "
                    f"threshold={traffic_threshold}GB"
                )
                # TODO: 调用关机服务（将在下一个里程碑实现）
            
        except Exception as e:
            logger.error(f"执行监控任务失败: config_id={config_id}, error={e}")
            
            # 记录错误日志到数据库
            db = next(get_db())
            try:
                monitor_logic.create_monitor_log(
                    db=db,
                    config_id=config_id,
                    remaining_traffic=0,
                    threshold=traffic_threshold,
                    is_below_threshold=False,
                    check_result="error",
                    error_message=str(e)
                )
            except:
                pass
            finally:
                db.close()
    
    def remove_monitor_task(self, config_id: int) -> bool:
        """
        移除监控任务
        
        Args:
            config_id: 监控配置 ID
            
        Returns:
            是否移除成功
        """
        job_id = f"monitor_config_{config_id}"
        
        logger.info(f"移除监控任务: config_id={config_id}")
        
        success = monitor_scheduler.remove_job(job_id)
        
        if success:
            logger.info(f"监控任务移除成功: job_id={job_id}")
        else:
            logger.warning(f"监控任务移除失败: job_id={job_id}")
        
        return success
    
    def pause_monitor_task(self, config_id: int) -> bool:
        """
        暂停监控任务
        
        Args:
            config_id: 监控配置 ID
            
        Returns:
            是否暂停成功
        """
        job_id = f"monitor_config_{config_id}"
        
        logger.info(f"暂停监控任务: config_id={config_id}")
        
        return monitor_scheduler.pause_job(job_id)
    
    def resume_monitor_task(self, config_id: int) -> bool:
        """
        恢复监控任务
        
        Args:
            config_id: 监控配置 ID
            
        Returns:
            是否恢复成功
        """
        job_id = f"monitor_config_{config_id}"
        
        logger.info(f"恢复监控任务: config_id={config_id}")
        
        return monitor_scheduler.resume_job(job_id)
    
    def get_task_info(self, config_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            config_id: 监控配置 ID
            
        Returns:
            任务信息
        """
        job_id = f"monitor_config_{config_id}"
        
        return monitor_scheduler.get_job_info(job_id)
    
    def list_all_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有监控任务
        
        Returns:
            任务列表
        """
        return monitor_scheduler.list_jobs()


# 创建全局任务管理器实例
monitor_task_manager = MonitorTaskManager()
