"""
华为云 Job 任务状态查询服务

API 文档: https://support.huaweicloud.com/api-ecs/ecs_03_0702.html
"""
from typing import Dict, Any, Optional
from enum import Enum
from loguru import logger
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException


class JobStatus(str, Enum):
    """Job 状态枚举"""
    SUCCESS = "SUCCESS"  # 成功
    RUNNING = "RUNNING"  # 运行中
    FAIL = "FAIL"  # 失败
    INIT = "INIT"  # 初始化


class JobInfo:
    """Job 任务信息模型"""
    
    def __init__(self, data: Dict[str, Any]):
        """
        从 API 响应数据初始化
        
        Args:
            data: API 响应数据
        """
        self.job_id = data.get('job_id', '')
        self.status = data.get('status', '')
        self.job_type = data.get('job_type', '')
        
        # 子任务信息
        self.entities = data.get('entities', {})
        self.sub_jobs = data.get('sub_jobs', [])
        
        # 错误信息
        self.error_code = data.get('error_code')
        self.fail_reason = data.get('fail_reason')
        
        # 时间信息
        self.begin_time = data.get('begin_time', '')
        self.end_time = data.get('end_time', '')
        self.message = data.get('message', '')
        self.code = data.get('code')
        
        logger.debug(
            f"解析 Job 信息: job_id={self.job_id}, "
            f"status={self.status}, type={self.job_type}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'job_type': self.job_type,
            'entities': self.entities,
            'sub_jobs': self.sub_jobs,
            'error_code': self.error_code,
            'fail_reason': self.fail_reason,
            'begin_time': self.begin_time,
            'end_time': self.end_time,
            'message': self.message,
            'code': self.code,
        }
    
    def is_success(self) -> bool:
        """判断任务是否成功"""
        return self.status == JobStatus.SUCCESS.value
    
    def is_running(self) -> bool:
        """判断任务是否正在运行"""
        return self.status == JobStatus.RUNNING.value
    
    def is_failed(self) -> bool:
        """判断任务是否失败"""
        return self.status == JobStatus.FAIL.value
    
    def is_finished(self) -> bool:
        """判断任务是否已完成（成功或失败）"""
        return self.is_success() or self.is_failed()
    
    def __repr__(self):
        return (
            f"<JobInfo(job_id={self.job_id}, status={self.status}, "
            f"type={self.job_type})>"
        )


class JobService:
    """Job 任务状态查询服务"""
    
    # API 端点配置
    JOB_STATUS_ENDPOINT = '/v1/{project_id}/jobs/{job_id}'
    
    def __init__(self, client: HuaweiCloudClient, project_id: str):
        """
        初始化 Job 服务
        
        Args:
            client: 华为云客户端
            project_id: 项目 ID
        """
        self.client = client
        self.project_id = project_id
        logger.info("初始化 Job 任务状态查询服务")
    
    def get_job_status(self, job_id: str) -> JobInfo:
        """
        查询 Job 任务状态
        
        Args:
            job_id: Job ID
            
        Returns:
            Job 任务信息
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
        """
        logger.info(f"查询 Job 状态: job_id={job_id}, project_id={self.project_id}")
        
        # 构建 URI
        uri = self.JOB_STATUS_ENDPOINT.format(
            project_id=self.project_id,
            job_id=job_id
        )
        
        try:
            # 调用 API
            response = self.client.get(uri=uri)
            
            # 解析响应
            job_info = JobInfo(response)
            
            logger.info(
                f"查询 Job 状态成功: job_id={job_id}, "
                f"status={job_info.status}"
            )
            
            return job_info
            
        except HuaweiCloudAPIException as e:
            logger.error(f"查询 Job 状态失败: {e}")
            raise
        except Exception as e:
            logger.error(f"解析 Job 状态响应失败: {e}")
            raise HuaweiCloudAPIException(f"解析响应失败: {e}")
    
    def wait_for_job_completion(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> JobInfo:
        """
        等待 Job 任务完成
        
        Args:
            job_id: Job ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            完成后的 Job 信息
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
            TimeoutError: 等待超时
        """
        import time
        
        logger.info(
            f"等待 Job 完成: job_id={job_id}, "
            f"timeout={timeout}s, interval={poll_interval}s"
        )
        
        start_time = time.time()
        
        while True:
            # 查询任务状态
            job_info = self.get_job_status(job_id)
            
            # 检查是否完成
            if job_info.is_finished():
                if job_info.is_success():
                    logger.info(f"Job 执行成功: job_id={job_id}")
                else:
                    logger.error(
                        f"Job 执行失败: job_id={job_id}, "
                        f"error={job_info.fail_reason}"
                    )
                return job_info
            
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"等待 Job 完成超时: job_id={job_id}, "
                    f"elapsed={elapsed}s, timeout={timeout}s"
                )
            
            # 等待下次轮询
            logger.debug(
                f"Job 仍在运行: job_id={job_id}, "
                f"status={job_info.status}, elapsed={elapsed:.1f}s"
            )
            time.sleep(poll_interval)
    
    def get_job_summary(self, job_id: str) -> Dict[str, Any]:
        """
        获取 Job 任务摘要信息
        
        Args:
            job_id: Job ID
            
        Returns:
            任务摘要信息
        """
        job_info = self.get_job_status(job_id)
        
        return {
            'job_id': job_info.job_id,
            'status': job_info.status,
            'is_success': job_info.is_success(),
            'is_running': job_info.is_running(),
            'is_failed': job_info.is_failed(),
            'error_code': job_info.error_code,
            'fail_reason': job_info.fail_reason,
            'sub_jobs_count': len(job_info.sub_jobs),
        }
