"""
华为云 ECS 批量关机服务

API 文档: https://support.huaweicloud.com/intl/zh-cn/api-flexusl/batch_server_0003.html
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from loguru import logger
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException


class ShutdownType(str, Enum):
    """关机类型枚举"""
    SOFT = "SOFT"  # 正常关机（默认）
    HARD = "HARD"  # 强制关机


class ShutdownTask:
    """关机任务状态模型"""
    
    def __init__(self, data: Dict[str, Any]):
        """
        从 API 响应数据初始化
        
        Args:
            data: API 响应数据
        """
        self.job_id = data.get('job_id', '')
        
        logger.debug(f"创建关机任务: job_id={self.job_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'job_id': self.job_id,
        }
    
    def __repr__(self):
        return f"<ShutdownTask(job_id={self.job_id})>"


class ShutdownService:
    """ECS 批量关机服务"""
    
    # API 端点配置
    BATCH_ACTION_ENDPOINT = '/v1/{project_id}/cloudservers/action'
    
    def __init__(self, client: HuaweiCloudClient, project_id: str):
        """
        初始化批量关机服务
        
        Args:
            client: 华为云客户端
            project_id: 项目 ID
        """
        self.client = client
        self.project_id = project_id
        logger.info("初始化批量关机服务")
    
    def batch_stop_servers(
        self,
        server_ids: List[str],
        shutdown_type: ShutdownType = ShutdownType.SOFT
    ) -> ShutdownTask:
        """
        批量关闭服务器
        
        Args:
            server_ids: 服务器 ID 列表（最多 1000 个）
            shutdown_type: 关机类型（SOFT: 正常关机, HARD: 强制关机）
            
        Returns:
            关机任务信息
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
            ValueError: 参数验证失败
        """
        # 参数验证
        if not server_ids:
            raise ValueError("服务器 ID 列表不能为空")
        
        if len(server_ids) > 1000:
            raise ValueError("单次最多支持关闭 1000 台服务器")
        
        logger.info(
            f"批量关闭服务器: count={len(server_ids)}, "
            f"type={shutdown_type.value}, project_id={self.project_id}"
        )
        
        # 构建请求体
        servers = [{"id": server_id} for server_id in server_ids]
        
        body = {
            "os-stop": {
                "type": shutdown_type.value,
                "servers": servers
            }
        }
        
        # 构建 URI
        uri = self.BATCH_ACTION_ENDPOINT.format(project_id=self.project_id)
        
        try:
            # 调用 API
            response = self.client.post(
                uri=uri,
                body=body
            )
            
            # 解析响应
            task = ShutdownTask(response)
            
            logger.info(
                f"批量关闭服务器成功: job_id={task.job_id}, "
                f"server_count={len(server_ids)}"
            )
            
            return task
            
        except HuaweiCloudAPIException as e:
            logger.error(f"批量关闭服务器失败: {e}")
            raise
        except Exception as e:
            logger.error(f"批量关闭服务器异常: {e}")
            raise HuaweiCloudAPIException(f"批量关闭服务器失败: {e}")
    
    def stop_server(
        self,
        server_id: str,
        shutdown_type: ShutdownType = ShutdownType.SOFT
    ) -> ShutdownTask:
        """
        关闭单个服务器
        
        Args:
            server_id: 服务器 ID
            shutdown_type: 关机类型（SOFT: 正常关机, HARD: 强制关机）
            
        Returns:
            关机任务信息
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
        """
        return self.batch_stop_servers([server_id], shutdown_type)
    
    def stop_servers_by_status(
        self,
        status: str = "ACTIVE",
        shutdown_type: ShutdownType = ShutdownType.SOFT,
        ecs_service=None
    ) -> ShutdownTask:
        """
        根据状态批量关闭服务器
        
        Args:
            status: 服务器状态（默认: ACTIVE）
            shutdown_type: 关机类型
            ecs_service: ECS 服务实例（用于查询服务器列表）
            
        Returns:
            关机任务信息
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
            ValueError: 未提供 ECS 服务实例
        """
        if ecs_service is None:
            raise ValueError("必须提供 ECS 服务实例以查询服务器列表")
        
        logger.info(f"查询状态为 {status} 的服务器")
        
        # 查询指定状态的服务器
        servers = ecs_service.list_servers(status=status)
        
        if not servers:
            logger.warning(f"未找到状态为 {status} 的服务器")
            return ShutdownTask({"job_id": ""})
        
        # 提取服务器 ID
        server_ids = [server.id for server in servers]
        
        # 批量关闭
        return self.batch_stop_servers(server_ids, shutdown_type)
    
    def get_shutdown_summary(
        self,
        server_ids: List[str],
        shutdown_type: ShutdownType = ShutdownType.SOFT
    ) -> Dict[str, Any]:
        """
        获取关机操作摘要信息（不实际执行关机）
        
        Args:
            server_ids: 服务器 ID 列表
            shutdown_type: 关机类型
            
        Returns:
            关机操作摘要
        """
        return {
            'server_count': len(server_ids),
            'server_ids': server_ids,
            'shutdown_type': shutdown_type.value,
            'max_batch_size': 1000,
            'will_batch': len(server_ids) > 1000
        }
