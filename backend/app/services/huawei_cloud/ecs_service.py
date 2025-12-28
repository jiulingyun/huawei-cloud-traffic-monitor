"""
华为云 ECS 服务器信息查询服务

API 文档: https://support.huaweicloud.com/api-ecs/zh-cn_topic_0094148850.html
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException


class ECSServer:
    """ECS 服务器信息模型"""
    
    def __init__(self, data: Dict[str, Any]):
        """
        从 API 响应数据初始化
        
        Args:
            data: API 响应数据
        """
        self.id = data.get('id', '')
        self.name = data.get('name', '')
        self.status = data.get('status', '')
        
        # 规格信息
        flavor = data.get('flavor', {})
        self.flavor_id = flavor.get('id', '')
        
        # 镜像信息
        image = data.get('image', {})
        self.image_id = image.get('id', '')
        
        # 网络信息
        addresses = data.get('addresses', {})
        self.private_ips = []
        self.public_ips = []
        
        for network_name, ip_list in addresses.items():
            for ip_info in ip_list:
                ip_addr = ip_info.get('addr', '')
                ip_type = ip_info.get('OS-EXT-IPS:type', '')
                
                if ip_type == 'fixed':
                    self.private_ips.append(ip_addr)
                elif ip_type == 'floating':
                    self.public_ips.append(ip_addr)
        
        # 元数据
        metadata = data.get('metadata', {})
        self.charging_mode = metadata.get('charging_mode', '')
        
        # 可用区
        self.availability_zone = data.get('OS-EXT-AZ:availability_zone', '')
        
        # 创建时间
        self.created = data.get('created', '')
        
        # 磁盘配置
        self.volumes = data.get('os-extended-volumes:volumes_attached', [])
        
        # 任务状态
        self.task_state = data.get('OS-EXT-STS:task_state')
        self.power_state = data.get('OS-EXT-STS:power_state')
        self.vm_state = data.get('OS-EXT-STS:vm_state', '')
        
        # 企业项目 ID
        self.enterprise_project_id = data.get('enterprise_project_id', '')
        
        logger.debug(
            f"解析服务器: id={self.id}, name={self.name}, "
            f"status={self.status}, private_ips={self.private_ips}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'flavor_id': self.flavor_id,
            'image_id': self.image_id,
            'private_ips': self.private_ips,
            'public_ips': self.public_ips,
            'charging_mode': self.charging_mode,
            'availability_zone': self.availability_zone,
            'created': self.created,
            'volumes': self.volumes,
            'task_state': self.task_state,
            'power_state': self.power_state,
            'vm_state': self.vm_state,
            'enterprise_project_id': self.enterprise_project_id,
        }
    
    def is_running(self) -> bool:
        """判断服务器是否正在运行"""
        return self.status.upper() == 'ACTIVE' and self.vm_state == 'active'
    
    def is_stopped(self) -> bool:
        """判断服务器是否已关机"""
        return self.status.upper() == 'SHUTOFF' and self.vm_state == 'stopped'
    
    def __repr__(self):
        return (
            f"<ECSServer(id={self.id}, name={self.name}, "
            f"status={self.status}, ips={self.private_ips})>"
        )


class ECSService:
    """ECS 服务器信息查询服务"""
    
    # API 端点配置
    SERVER_LIST_ENDPOINT = '/v1/{project_id}/cloudservers/detail'
    
    def __init__(self, client: HuaweiCloudClient, project_id: str):
        """
        初始化 ECS 服务
        
        Args:
            client: 华为云客户端
            project_id: 项目 ID
        """
        self.client = client
        self.project_id = project_id
        logger.info("初始化 ECS 服务器查询服务")
    
    def list_servers(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
        name: Optional[str] = None,
        flavor: Optional[str] = None,
        ip: Optional[str] = None
    ) -> List[ECSServer]:
        """
        查询服务器列表
        
        Args:
            limit: 查询返回数量限制（分页）
            offset: 偏移量（分页）
            status: 服务器状态过滤（ACTIVE, SHUTOFF, ERROR 等）
            name: 服务器名称过滤（模糊匹配）
            flavor: 规格 ID 过滤
            ip: IP 地址过滤
            
        Returns:
            服务器信息列表
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
        """
        logger.info(f"查询服务器列表: project_id={self.project_id}")
        
        # 构建查询参数
        query_params = {}
        
        if limit is not None:
            query_params['limit'] = str(limit)
        
        if offset is not None:
            query_params['offset'] = str(offset)
        
        if status:
            query_params['status'] = status
        
        if name:
            query_params['name'] = name
        
        if flavor:
            query_params['flavor'] = flavor
        
        if ip:
            query_params['ip'] = ip
        
        # 构建 URI
        uri = self.SERVER_LIST_ENDPOINT.format(project_id=self.project_id)
        
        try:
            # 调用 API
            response = self.client.get(
                uri=uri,
                query_params=query_params if query_params else None
            )
            
            # 解析响应
            servers = self._parse_response(response)
            
            logger.info(f"成功查询服务器列表: count={len(servers)}")
            
            return servers
            
        except HuaweiCloudAPIException as e:
            logger.error(f"查询服务器列表失败: {e}")
            raise
        except Exception as e:
            logger.error(f"解析服务器列表响应失败: {e}")
            raise HuaweiCloudAPIException(f"解析响应失败: {e}")
    
    def _parse_response(self, response: Dict[str, Any]) -> List[ECSServer]:
        """
        解析 API 响应
        
        Args:
            response: API 响应
            
        Returns:
            服务器信息列表
        """
        servers = []
        
        # 获取服务器列表
        server_list = response.get('servers', [])
        
        for server_data in server_list:
            try:
                server = ECSServer(server_data)
                servers.append(server)
            except Exception as e:
                logger.warning(f"解析服务器数据失败: {e}, data={server_data}")
                continue
        
        return servers
    
    def get_server_by_id(self, server_id: str) -> Optional[ECSServer]:
        """
        根据 ID 查询单个服务器
        
        Args:
            server_id: 服务器 ID
            
        Returns:
            服务器信息，未找到返回 None
        """
        logger.info(f"查询服务器详情: server_id={server_id}")
        
        # 使用 IP 参数可能无法精确匹配，这里使用列表查询后过滤
        servers = self.list_servers()
        
        for server in servers:
            if server.id == server_id:
                logger.info(f"找到服务器: {server}")
                return server
        
        logger.warning(f"未找到服务器: server_id={server_id}")
        return None
    
    def get_servers_by_status(self, status: str) -> List[ECSServer]:
        """
        根据状态查询服务器列表
        
        Args:
            status: 服务器状态（ACTIVE, SHUTOFF, ERROR 等）
            
        Returns:
            服务器信息列表
        """
        logger.info(f"根据状态查询服务器: status={status}")
        
        return self.list_servers(status=status)
    
    def get_running_servers(self) -> List[ECSServer]:
        """
        获取所有正在运行的服务器
        
        Returns:
            正在运行的服务器列表
        """
        servers = self.get_servers_by_status('ACTIVE')
        return [s for s in servers if s.is_running()]
    
    def get_stopped_servers(self) -> List[ECSServer]:
        """
        获取所有已关机的服务器
        
        Returns:
            已关机的服务器列表
        """
        servers = self.get_servers_by_status('SHUTOFF')
        return [s for s in servers if s.is_stopped()]
    
    def get_server_summary(self) -> Dict[str, Any]:
        """
        获取服务器汇总信息
        
        Returns:
            服务器汇总统计
        """
        logger.info("获取服务器汇总信息")
        
        servers = self.list_servers()
        
        # 按状态分组统计
        status_count = {}
        for server in servers:
            status = server.status
            status_count[status] = status_count.get(status, 0) + 1
        
        summary = {
            'total_count': len(servers),
            'status_count': status_count,
            'servers': [s.to_dict() for s in servers]
        }
        
        logger.info(
            f"服务器汇总: total={len(servers)}, "
            f"status_distribution={status_count}"
        )
        
        return summary
