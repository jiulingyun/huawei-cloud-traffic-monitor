"""
监控业务流程整合服务

整合流量监控、阈值判断、自动关机、飞书通知的完整业务流程
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from loguru import logger
from sqlalchemy.orm import Session

from app.services.huawei_cloud import (
    client_manager,
    TrafficService,
    ECSService
)
from app.services.huawei_cloud.shutdown_service import ShutdownService, ShutdownType
from app.services.huawei_cloud.job_service import JobService
from app.services.feishu import FeishuWebhookClient, FeishuNotificationService
from app.services.monitor_logic import monitor_logic


class MonitorWorkflowExecutor:
    """监控业务流程执行器"""
    
    def __init__(
        self,
        feishu_webhook_url: Optional[str] = None,
        enable_notifications: bool = True,
        enable_auto_shutdown: bool = True
    ):
        """
        初始化工作流执行器
        
        Args:
            feishu_webhook_url: 飞书 Webhook URL
            enable_notifications: 是否启用通知
            enable_auto_shutdown: 是否启用自动关机
        """
        self.enable_notifications = enable_notifications and feishu_webhook_url
        self.enable_auto_shutdown = enable_auto_shutdown
        
        # 初始化飞书通知服务
        if self.enable_notifications:
            self.feishu_client = FeishuWebhookClient(webhook_url=feishu_webhook_url)
            self.notification_service = FeishuNotificationService(self.feishu_client)
            logger.info("飞书通知服务已启用")
        else:
            self.feishu_client = None
            self.notification_service = None
            logger.info("飞书通知服务已禁用")
        
        logger.info(
            f"监控工作流执行器已初始化: "
            f"notifications={self.enable_notifications}, "
            f"auto_shutdown={self.enable_auto_shutdown}"
        )
    
    def execute_monitor_workflow(
        self,
        db: Session,
        config_id: int,
        account_id: int,
        account_name: str,
        encrypted_ak: str,
        encrypted_sk: str,
        region: str,
        project_id: str,
        traffic_threshold: float,
        auto_shutdown_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的监控工作流
        
        工作流程：
        1. 查询流量包信息
        2. 判断是否低于阈值
        3. 记录监控日志
        4. 发送流量告警通知（如果需要）
        5. 执行自动关机（如果低于阈值）
        6. 发送关机通知
        7. 等待关机完成
        8. 发送完成通知
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            account_id: 账户 ID
            account_name: 账户名称
            encrypted_ak: 加密的 AK
            encrypted_sk: 加密的 SK
            region: 区域
            project_id: 项目 ID
            traffic_threshold: 流量阈值（GB）
            auto_shutdown_enabled: 是否启用自动关机
            
        Returns:
            执行结果
        """
        logger.info(
            f"开始执行监控工作流: "
            f"config_id={config_id}, account={account_name}, region={region}"
        )
        
        result = {
            'success': False,
            'config_id': config_id,
            'account_name': account_name,
            'region': region,
            'traffic_checked': False,
            'notification_sent': False,
            'shutdown_executed': False,
            'error': None
        }
        
        try:
            # 步骤 1: 获取华为云客户端
            logger.info("步骤 1: 获取华为云客户端")
            client = client_manager.get_client(
                account_id=account_id,
                encrypted_ak=encrypted_ak,
                encrypted_sk=encrypted_sk,
                region=region
            )
            
            # 步骤 2: 查询流量包信息
            logger.info("步骤 2: 查询流量包信息")
            traffic_service = TrafficService(client)
            traffic_summary = traffic_service.get_traffic_summary()
            
            remaining_traffic = traffic_summary['total_remaining_gb']
            usage_percentage = (
                (1 - remaining_traffic / traffic_threshold) * 100
                if traffic_threshold > 0 else 0
            )
            
            result['traffic_checked'] = True
            result['remaining_traffic'] = remaining_traffic
            result['usage_percentage'] = usage_percentage
            
            logger.info(
                f"流量查询完成: remaining={remaining_traffic:.2f}GB, "
                f"threshold={traffic_threshold:.2f}GB, "
                f"usage={usage_percentage:.1f}%"
            )
            
            # 步骤 3: 判断是否低于阈值
            logger.info("步骤 3: 判断流量阈值")
            is_below_threshold, check_result = monitor_logic.check_traffic_threshold(
                remaining_traffic=remaining_traffic,
                threshold=traffic_threshold
            )
            
            result['is_below_threshold'] = is_below_threshold
            
            # 步骤 4: 记录监控日志
            logger.info("步骤 4: 记录监控日志")
            monitor_log = monitor_logic.create_monitor_log(
                db=db,
                config_id=config_id,
                remaining_traffic=remaining_traffic,
                threshold=traffic_threshold,
                is_below_threshold=is_below_threshold,
                check_result=check_result
            )
            
            # 步骤 5: 发送流量告警通知（如果使用率超过70%）
            if self.enable_notifications and usage_percentage >= 70:
                logger.info("步骤 5: 发送流量告警通知")
                try:
                    # 查询服务器数量
                    ecs_service = ECSService(client, project_id)
                    servers = ecs_service.list_servers()
                    
                    self.notification_service.send_traffic_warning(
                        account_name=account_name,
                        remaining_traffic_gb=remaining_traffic,
                        threshold_gb=traffic_threshold,
                        usage_percentage=usage_percentage,
                        server_count=len(servers),
                        region=region
                    )
                    result['notification_sent'] = True
                    logger.info("流量告警通知发送成功")
                except Exception as e:
                    logger.error(f"发送流量告警通知失败: {e}")
            
            # 步骤 6: 执行自动关机（如果低于阈值且启用）
            if is_below_threshold and auto_shutdown_enabled and self.enable_auto_shutdown:
                logger.warning(
                    f"流量低于阈值，准备执行自动关机: "
                    f"remaining={remaining_traffic:.2f}GB < threshold={traffic_threshold:.2f}GB"
                )
                
                shutdown_result = self._execute_shutdown_workflow(
                    db=db,
                    client=client,
                    project_id=project_id,
                    account_name=account_name,
                    region=region
                )
                
                result['shutdown_executed'] = shutdown_result['success']
                result['shutdown_details'] = shutdown_result
            
            result['success'] = True
            logger.info(f"监控工作流执行成功: config_id={config_id}")
            
        except Exception as e:
            logger.error(f"监控工作流执行失败: config_id={config_id}, error={e}")
            result['error'] = str(e)
            
            # 记录错误日志
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
        
        return result
    
    def _execute_shutdown_workflow(
        self,
        db: Session,
        client,
        project_id: str,
        account_name: str,
        region: str
    ) -> Dict[str, Any]:
        """
        执行关机工作流
        
        Args:
            db: 数据库会话
            client: 华为云客户端
            project_id: 项目 ID
            account_name: 账户名称
            region: 区域
            
        Returns:
            关机结果
        """
        result = {
            'success': False,
            'job_id': None,
            'server_count': 0,
            'servers': [],
            'error': None
        }
        
        try:
            # 1. 查询运行中的服务器
            logger.info("查询运行中的服务器")
            ecs_service = ECSService(client, project_id)
            running_servers = ecs_service.get_running_servers()
            
            if not running_servers:
                logger.info("没有运行中的服务器，跳过关机")
                result['success'] = True
                return result
            
            server_ids = [s.id for s in running_servers]
            server_list = [
                {'name': s.name, 'id': s.id, 'ip': ','.join(s.private_ips)}
                for s in running_servers
            ]
            
            result['server_count'] = len(running_servers)
            result['servers'] = server_list
            
            logger.info(f"找到 {len(running_servers)} 台运行中的服务器")
            
            # 2. 发送关机通知
            if self.enable_notifications:
                try:
                    logger.info("发送关机通知")
                    self.notification_service.send_shutdown_notification(
                        account_name=account_name,
                        server_list=server_list,
                        reason="流量不足，自动关机",
                        job_id="pending",
                        region=region
                    )
                except Exception as e:
                    logger.error(f"发送关机通知失败: {e}")
            
            # 3. 执行批量关机
            logger.info("执行批量关机")
            shutdown_service = ShutdownService(client, project_id)
            start_time = time.time()
            
            shutdown_task = shutdown_service.batch_stop_servers(
                server_ids=server_ids,
                shutdown_type=ShutdownType.SOFT
            )
            
            result['job_id'] = shutdown_task.job_id
            logger.info(f"关机任务已提交: job_id={shutdown_task.job_id}")
            
            # 4. 等待关机完成（可选）
            job_service = JobService(client, project_id)
            try:
                logger.info("等待关机任务完成（最多5分钟）")
                job_info = job_service.wait_for_job_completion(
                    job_id=shutdown_task.job_id,
                    timeout=300,
                    poll_interval=10
                )
                
                duration = time.time() - start_time
                
                if job_info.is_success():
                    logger.info(f"关机任务完成: duration={duration:.1f}s")
                    result['success'] = True
                    result['duration'] = duration
                    
                    # 5. 发送成功通知
                    if self.enable_notifications:
                        try:
                            self.notification_service.send_shutdown_success(
                                account_name=account_name,
                                server_count=len(running_servers),
                                job_id=shutdown_task.job_id,
                                duration_seconds=duration
                            )
                        except Exception as e:
                            logger.error(f"发送成功通知失败: {e}")
                else:
                    logger.error(f"关机任务失败: {job_info.fail_reason}")
                    result['error'] = job_info.fail_reason
                    
                    # 6. 发送失败通知
                    if self.enable_notifications:
                        try:
                            self.notification_service.send_shutdown_failure(
                                account_name=account_name,
                                server_count=len(running_servers),
                                job_id=shutdown_task.job_id,
                                error_message=job_info.fail_reason or "未知错误"
                            )
                        except Exception as e:
                            logger.error(f"发送失败通知失败: {e}")
                
            except TimeoutError as e:
                logger.warning(f"等待关机任务超时: {e}")
                result['error'] = "任务超时"
                # 任务可能仍在执行，不算失败
                result['success'] = True
            
        except Exception as e:
            logger.error(f"关机工作流失败: {e}")
            result['error'] = str(e)
            
            # 发送失败通知
            if self.enable_notifications:
                try:
                    self.notification_service.send_shutdown_failure(
                        account_name=account_name,
                        server_count=result.get('server_count', 0),
                        job_id=result.get('job_id', 'unknown'),
                        error_message=str(e)
                    )
                except:
                    pass
        
        return result


# 全局工作流执行器实例（可通过配置初始化）
workflow_executor: Optional[MonitorWorkflowExecutor] = None


def initialize_workflow_executor(
    feishu_webhook_url: Optional[str] = None,
    enable_notifications: bool = True,
    enable_auto_shutdown: bool = True
):
    """
    初始化全局工作流执行器
    
    Args:
        feishu_webhook_url: 飞书 Webhook URL
        enable_notifications: 是否启用通知
        enable_auto_shutdown: 是否启用自动关机
    """
    global workflow_executor
    workflow_executor = MonitorWorkflowExecutor(
        feishu_webhook_url=feishu_webhook_url,
        enable_notifications=enable_notifications,
        enable_auto_shutdown=enable_auto_shutdown
    )
    logger.info("全局工作流执行器已初始化")


def get_workflow_executor() -> MonitorWorkflowExecutor:
    """
    获取全局工作流执行器
    
    Returns:
        工作流执行器实例
        
    Raises:
        RuntimeError: 工作流执行器未初始化
    """
    if workflow_executor is None:
        raise RuntimeError("工作流执行器未初始化，请先调用 initialize_workflow_executor")
    return workflow_executor
