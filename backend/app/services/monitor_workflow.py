"""
监控业务流程整合服务

整合流量监控、阈值判断、自动关机、飞书通知的完整业务流程
"""
from typing import Dict, Any, List, Optional, Callable, TypeVar
from datetime import datetime
import time
from functools import wraps
from loguru import logger
from sqlalchemy.orm import Session

T = TypeVar('T')


def retry_on_failure(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 退避因子（每次重试延迟乘以此因子）
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = retry_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"操作失败，准备重试: "
                            f"attempt={attempt + 1}/{max_retries}, "
                            f"delay={delay:.1f}s, error={e}"
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"操作失败，已达到最大重试次数: "
                            f"max_retries={max_retries}, error={e}"
                        )
            
            raise last_exception
        return wrapper
    return decorator


class RetryExecutor:
    """重试执行器"""
    
    @staticmethod
    def execute_with_retry(
        func: Callable[..., T],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs
    ) -> T:
        """
        带重试的执行函数
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子
            exceptions: 需要重试的异常类型
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            Exception: 重试失败后抛出最后一次异常
        """
        last_exception = None
        delay = retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        f"操作失败，准备重试: "
                        f"func={func.__name__}, "
                        f"attempt={attempt + 1}/{max_retries}, "
                        f"delay={delay:.1f}s, error={e}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(
                        f"操作失败，已达到最大重试次数: "
                        f"func={func.__name__}, "
                        f"max_retries={max_retries}, error={e}"
                    )
        
        raise last_exception

from app.services.huawei_cloud import (
    client_manager,
    ECSService
)
from app.services.huawei_cloud.flexusl_service import FlexusLService
from app.services.account_service import account_service
from app.utils.encryption import get_encryption_service
from app.services.huawei_cloud.bss_client import HuaweiCloudBSSClient
from app.services.huawei_cloud.shutdown_service import ShutdownService, ShutdownType
from app.services.huawei_cloud.job_service import JobService
from app.services.feishu import FeishuWebhookClient, FeishuNotificationService
from app.services.monitor_logic import monitor_logic
from app.services.operation_log_service import operation_log_service, OperationLogService


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
        auto_shutdown_enabled: bool = True,
        shutdown_delay: int = 0,
        retry_times: int = 3
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
            
            # 步骤 2: 查询流量包信息（带重试）
            logger.info("步骤 2: 查询流量包信息")
            # 需要解密 AK/SK 并根据账户属性判断是否为国际站，然后创建 BSS 客户端供 TrafficService 使用
            encryption_service = get_encryption_service()
            ak, sk = encryption_service.decrypt_ak_sk(encrypted_ak, encrypted_sk)
            account = account_service.get_account(db=db, account_id=account_id)
            is_intl = getattr(account, 'is_international', True) if account else True
            # 使用 FlexusLService（通过 Config + BSS 查询），行为与 tests/test_full_workflow.py 保持一致
            traffic_service = FlexusLService(
                ak=ak,
                sk=sk,
                region=account.region,
                is_international=is_intl
            )
            
            # 使用重试执行器查询流量（使用自动发现的汇总方法）
            # get_traffic_summary 需要 resource_ids 参数 —— 使用 get_all_traffic_summary 以自动发现并汇总
            traffic_summary = RetryExecutor.execute_with_retry(
                func=traffic_service.get_all_traffic_summary,
                max_retries=retry_times,
                retry_delay=2.0,
                backoff_factor=2.0
            )
            
            # FlexusLService 返回字段: remaining_amount, total_amount, used_amount
            remaining_traffic = traffic_summary.get('remaining_amount', 0)
            usage_percentage = (
                traffic_summary.get('usage_percentage', 0)
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
            
            # 步骤 4: 按实例记录监控日志并单实例处理（按全局阈值比较）
            logger.info("步骤 4: 按实例记录监控日志并单实例处理")
            instances = traffic_summary.get('instances', [])
            packages = traffic_summary.get('packages', [])
            # 构建流量包 id -> 包信息 映射
            pkg_map = {p.get('resource_id'): p for p in (packages or [])}

            for inst in instances:
                try:
                    server_id = inst.get('server_id')
                    pkg_id = inst.get('traffic_package_id')
                    inst_region = inst.get('region') or region

                    pkg = pkg_map.get(pkg_id, {})
                    inst_remaining = float(pkg.get('remaining_amount', 0) or 0)
                    inst_total = float(pkg.get('total_amount') or 0) if pkg.get('total_amount') is not None else None
                    inst_used = float(pkg.get('used_amount') or 0) if pkg.get('used_amount') is not None else None
                    inst_usage_pct = float(pkg.get('usage_percentage') or 0)

                    is_below, inst_check_desc = monitor_logic.check_traffic_threshold(
                        remaining_traffic=inst_remaining,
                        threshold=traffic_threshold
                    )

                    # 写入监控日志（按实例）
                    monitor_logic.create_monitor_log(
                        db=db,
                        account_id=account_id,
                        remaining_traffic=inst_remaining,
                        threshold=traffic_threshold,
                        is_below_threshold=is_below,
                        check_result=inst_check_desc,
                        traffic_total=inst_total,
                        traffic_used=inst_used,
                        usage_percentage=inst_usage_pct,
                        server_id=server_id
                    )

                    # 若低于阈值并启用自动关机，则对该实例执行关机（单机）
                    if is_below and auto_shutdown_enabled and self.enable_auto_shutdown and server_id:
                        logger.warning(f"实例流量低于阈值，准备对实例执行关机: server_id={server_id}, remaining={inst_remaining:.2f}GB")

                        # 记录操作日志
                        try:
                            op_log = operation_log_service.create_operation_log(
                                db=db,
                                account_id=account_id,
                                operation_type=OperationLogService.OP_AUTO_SHUTDOWN,
                                target_id=server_id,
                                target_name=inst.get('name'),
                                target_type='server',
                                region=inst_region,
                                reason=f"流量不足自动关机: 剩余 {inst_remaining:.2f}GB < 阈值 {traffic_threshold:.2f}GB"
                            )
                        except Exception as e:
                            logger.error(f"创建操作日志失败: {e}")
                            op_log = None

                        # 使用 FlexusLService 的单机关机接口（与批量接口复用）
                        try:
                            shutdown_result = traffic_service.batch_stop_servers(
                                server_ids=[server_id],
                                region=inst_region
                            )

                            # 更新操作日志状态
                            if op_log:
                                if shutdown_result.success:
                                    operation_log_service.mark_success(db=db, log_id=op_log.id)
                                else:
                                    operation_log_service.mark_failed(db=db, log_id=op_log.id, error_message=shutdown_result.message or "关机失败")

                            # 发送通知
                            if self.enable_notifications:
                                try:
                                    if shutdown_result.success:
                                        self.notification_service.send_shutdown_success(
                                            account_name=account_name,
                                            server_count=1,
                                            job_id=shutdown_result.job_id,
                                            duration_seconds=0
                                        )
                                    else:
                                        self.notification_service.send_shutdown_failure(
                                            account_name=account_name,
                                            server_count=1,
                                            job_id=shutdown_result.job_id,
                                            error_message=shutdown_result.message or "未知错误"
                                        )
                                except Exception as e:
                                    logger.error(f"发送关机通知失败: {e}")

                        except Exception as e:
                            logger.error(f"单实例关机失败: server_id={server_id}, error={e}")
                            if op_log:
                                try:
                                    operation_log_service.mark_failed(db=db, log_id=op_log.id, error_message=str(e))
                                except:
                                    pass

                except Exception as e:
                    logger.error(f"处理实例监控时出错: inst={inst}, error={e}")
            
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
                
                # 关机延迟处理
                if shutdown_delay > 0:
                    logger.info(f"等待关机延迟: {shutdown_delay} 分钟")
                    
                    # 发送延迟通知
                    if self.enable_notifications:
                        try:
                            self.notification_service.send_shutdown_delay_notification(
                                account_name=account_name,
                                delay_minutes=shutdown_delay,
                                remaining_traffic_gb=remaining_traffic,
                                threshold_gb=traffic_threshold,
                                region=region
                            )
                        except Exception as e:
                            logger.error(f"发送延迟通知失败: {e}")
                    
                    # 等待延迟时间
                    time.sleep(shutdown_delay * 60)
                    
                    # 延迟后重新检查流量，避免误关机（使用自动发现的汇总方法）
                    logger.info("延迟结束，重新检查流量")
                    traffic_summary_recheck = traffic_service.get_all_traffic_summary()
                    remaining_traffic_recheck = traffic_summary_recheck.get('remaining_amount', 0)
                    
                    is_still_below, _ = monitor_logic.check_traffic_threshold(
                        remaining_traffic=remaining_traffic_recheck,
                        threshold=traffic_threshold
                    )
                    
                    if not is_still_below:
                        logger.info(
                            f"延迟后流量恢复正常，取消关机: "
                            f"remaining={remaining_traffic_recheck:.2f}GB >= threshold={traffic_threshold:.2f}GB"
                        )
                        result['shutdown_cancelled'] = True
                        result['success'] = True
                        return result
                
                shutdown_result = self._execute_shutdown_workflow(
                    db=db,
                    client=client,
                    project_id=project_id,
                    account_id=account_id,
                    account_name=account_name,
                    region=region,
                    retry_times=retry_times,
                    remaining_traffic=remaining_traffic,
                    threshold=traffic_threshold
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
                    account_id=account_id,
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
        account_id: int,
        account_name: str,
        region: str,
        retry_times: int = 3,
        remaining_traffic: float = 0,
        threshold: float = 0
    ) -> Dict[str, Any]:
        """
        执行关机工作流
        
        Args:
            db: 数据库会话
            client: 华为云客户端
            project_id: 项目 ID
            account_name: 账户名称
            region: 区域
            retry_times: 重试次数
            
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
            
            # 创建操作日志记录（每台服务器一条）
            op_logs = []
            for server in running_servers:
                op_log = operation_log_service.create_operation_log(
                    db=db,
                    account_id=account_id,
                    operation_type=OperationLogService.OP_AUTO_SHUTDOWN,
                    target_id=server.id,
                    target_name=server.name,
                    target_type='server',
                    region=region,
                    reason=f"流量不足自动关机: 剩余 {remaining_traffic:.2f}GB < 阈值 {threshold:.2f}GB"
                )
                op_logs.append(op_log)
            
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
            
            # 3. 执行批量关机（带重试）
            logger.info("执行批量关机")
            shutdown_service = ShutdownService(client, project_id)
            start_time = time.time()
            
            # 使用重试执行器执行关机操作
            shutdown_task = RetryExecutor.execute_with_retry(
                func=lambda: shutdown_service.batch_stop_servers(
                    server_ids=server_ids,
                    shutdown_type=ShutdownType.SOFT
                ),
                max_retries=retry_times,
                retry_delay=5.0,
                backoff_factor=2.0
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
                    
                    # 更新操作日志状态为成功
                    for op_log in op_logs:
                        operation_log_service.mark_success(
                            db=db,
                            log_id=op_log.id,
                            job_id=shutdown_task.job_id
                        )
                    
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
                    
                    # 更新操作日志状态为失败
                    for op_log in op_logs:
                        operation_log_service.mark_failed(
                            db=db,
                            log_id=op_log.id,
                            error_message=job_info.fail_reason or "未知错误",
                            job_id=shutdown_task.job_id
                        )
                    
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
            
            # 更新操作日志状态为失败
            if 'op_logs' in locals():
                for op_log in op_logs:
                    try:
                        operation_log_service.mark_failed(
                            db=db,
                            log_id=op_log.id,
                            error_message=str(e)
                        )
                    except:
                        pass
            
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
