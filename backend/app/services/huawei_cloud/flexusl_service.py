"""
Flexus L 实例服务

查询 Flexus L 实例列表和流量包信息

API 流程:
1. 使用 IAM 服务获取 domain_id
2. 使用 Config 服务 (配置审计) 列举 Flexus L 实例
3. 使用 BSS 服务查询流量包使用情况
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import requests
import hashlib
import hmac
import json
from datetime import datetime
from urllib.parse import quote

from .iam_service import IAMService
from .bss_client import HuaweiCloudBSSClient, HuaweiCloudBSSException


@dataclass
class FlexusLInstance:
    """Flexus L 实例信息"""
    id: str
    name: str
    region: str
    status: str
    public_ip: Optional[str]
    private_ip: Optional[str]
    created_at: Optional[str]
    expire_time: Optional[str]
    # 流量包信息
    traffic_package_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'status': self.status,
            'public_ip': self.public_ip,
            'private_ip': self.private_ip,
            'created_at': self.created_at,
            'expire_time': self.expire_time,
            'traffic_package_id': self.traffic_package_id,
        }


@dataclass
class TrafficPackageInfo:
    """流量包使用信息"""
    resource_id: str
    resource_type_name: str
    usage_type_name: str
    total_amount: float  # 原始额度 (GB)
    remaining_amount: float  # 剩余额度 (GB)
    used_amount: float  # 已使用 (GB)
    usage_percentage: float  # 使用百分比
    measure_unit: str
    start_time: Optional[str]
    end_time: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_type_name': self.resource_type_name,
            'usage_type_name': self.usage_type_name,
            'total_amount': self.total_amount,
            'remaining_amount': self.remaining_amount,
            'used_amount': self.used_amount,
            'usage_percentage': round(self.usage_percentage, 2),
            'measure_unit': self.measure_unit,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }


# 计量单位映射
MEASURE_UNIT_MAP = {
    10: 'GB',
    11: 'MB',
    12: 'KB',
    17: 'Byte',
}


class FlexusLService:
    """
    Flexus L 实例服务
    
    功能:
    - 查询 Flexus L 实例列表
    - 查询流量包使用情况
    """
    
    # Config 服务端点 - 配置审计是全局服务
    # 中国站全局端点
    CONFIG_ENDPOINT_CN = 'https://rms.myhuaweicloud.com'
    # 国际站全局端点
    CONFIG_ENDPOINT_INTL = 'https://rms.myhuaweicloud.com'
    
    # Flexus L 资源类型
    FLEXUS_L_PROVIDER = 'hcss'
    FLEXUS_L_TYPE = 'hcss.l-instance'
    
    # 流量使用量查询 API
    TRAFFIC_USAGE_API = '/v2/payments/free-resources/usages/details/query'
    
    def __init__(
        self,
        ak: str,
        sk: str,
        region: str = 'ap-southeast-1',
        is_international: bool = True
    ):
        """
        初始化 Flexus L 服务
        
        Args:
            ak: Access Key
            sk: Secret Key
            region: 区域（用于 Config API）
            is_international: 是否国际站
        """
        self.ak = ak
        self.sk = sk
        self.region = region
        self.is_international = is_international
        
        # 初始化 IAM 服务获取 domain_id
        self.iam_service = IAMService(ak, sk)
        
        # 初始化 BSS 客户端
        self.bss_client = HuaweiCloudBSSClient(ak, sk, is_international)
        
        # Config 端点 - 全局服务
        if is_international:
            self.config_endpoint = self.CONFIG_ENDPOINT_INTL
        else:
            self.config_endpoint = self.CONFIG_ENDPOINT_CN
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # 缓存 domain_id
        self._domain_id: Optional[str] = None
        
        logger.info(f"初始化 Flexus L 服务: region={region}, config_endpoint={self.config_endpoint}")
    
    def _sign_request(
        self,
        method: str,
        uri: str,
        host: str,
        query_params: Optional[Dict[str, str]] = None,
        body: str = ""
    ) -> Dict[str, str]:
        """生成 AK/SK 签名"""
        # 规范化 URI
        canonical_uri = '/'.join(
            quote(segment, safe='')
            for segment in uri.split('/')
        )
        if not canonical_uri.endswith('/'):
            canonical_uri += '/'
        
        # 规范化查询字符串
        canonical_query_string = ""
        if query_params:
            sorted_params = sorted(query_params.items())
            canonical_query_string = "&".join(
                f"{quote(k, safe='')}={quote(str(v), safe='')}"
                for k, v in sorted_params
            )
        
        # 获取当前时间戳
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # 规范化请求头
        signed_headers_str = "content-type;host;x-sdk-date"
        canonical_headers = f"content-type:application/json\nhost:{host}\nx-sdk-date:{timestamp}\n"
        
        # 计算请求体哈希
        hashed_request_payload = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        # 构建规范请求
        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_query_string}\n"
            f"{canonical_headers}\n"
            f"{signed_headers_str}\n"
            f"{hashed_request_payload}"
        )
        
        # 计算签名
        string_to_sign = (
            f"SDK-HMAC-SHA256\n"
            f"{timestamp}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        
        signature = hmac.new(
            self.sk.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Sdk-Date': timestamp,
            'Host': host,
            'Authorization': (
                f'SDK-HMAC-SHA256 '
                f'Access={self.ak}, '
                f'SignedHeaders={signed_headers_str}, '
                f'Signature={signature}'
            )
        }
    
    def get_domain_id(self) -> str:
        """
        获取账户的 domain_id
        
        通过 IAM API 获取项目列表，从中提取 domain_id
        """
        if self._domain_id:
            return self._domain_id
        
        logger.info("获取账户 domain_id...")
        projects = self.iam_service.list_projects()
        
        if not projects:
            raise FlexusLException("无法获取项目列表，无法确定 domain_id")
        
        # 从第一个项目中获取 domain_id
        self._domain_id = projects[0].domain_id
        logger.info(f"获取到 domain_id: {self._domain_id}")
        
        return self._domain_id
    
    def list_instances(self, limit: int = 200) -> List[FlexusLInstance]:
        """
        查询 Flexus L 实例列表
        
        使用 Config 服务（配置审计）的"列举所有资源"接口
        
        Args:
            limit: 返回数量限制
            
        Returns:
            Flexus L 实例列表
        """
        domain_id = self.get_domain_id()
        
        uri = f"/v1/resource-manager/domains/{domain_id}/all-resources"
        
        query_params = {
            'provider': self.FLEXUS_L_PROVIDER,
            'type': self.FLEXUS_L_TYPE,
            'limit': str(limit)
        }
        
        url = f"{self.config_endpoint}{uri}"
        host = self.config_endpoint.replace('https://', '').replace('http://', '')
        
        headers = self._sign_request(
            method='GET',
            uri=uri,
            host=host,
            query_params=query_params,
            body=""
        )
        
        try:
            logger.info(f"查询 Flexus L 实例列表: GET {url}")
            
            response = self.session.request(
                method='GET',
                url=url,
                params=query_params,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Config API 响应: status={response.status_code}")
            
            if response.status_code >= 400:
                error_msg = f"Config API 请求失败: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    error_msg += f", 响应: {response.text}"
                logger.error(error_msg)
                raise FlexusLException(error_msg)
            
            data = response.json()
            return self._parse_instances(data)
            
        except FlexusLException:
            raise
        except Exception as e:
            logger.error(f"查询 Flexus L 实例失败: {e}")
            raise FlexusLException(f"查询实例失败: {e}")
    
    def _parse_instances(self, response: Dict[str, Any]) -> List[FlexusLInstance]:
        """解析实例列表响应"""
        instances = []
        resources = response.get('resources', [])
        
        logger.info(f"解析 {len(resources)} 个 Flexus L 资源")
        
        for resource in resources:
            try:
                # 提取基本信息
                instance_id = resource.get('id', '')
                name = resource.get('name', '')
                region = resource.get('region_id', '')
                
                # 解析 properties
                properties = resource.get('properties', {})
                if isinstance(properties, str):
                    try:
                        properties = json.loads(properties)
                    except:
                        properties = {}
                
                # 从 properties 中获取状态和子资源列表
                status = properties.get('status', 'unknown')
                sub_resources = properties.get('resources', [])
                
                # 遍历子资源，提取流量包 ID 和公网 IP
                traffic_package_id = None
                public_ip = None
                private_ip = None
                
                for sub_res in sub_resources:
                    logical_type = sub_res.get('logical_resource_type', '')
                    physical_id = sub_res.get('physical_resource_id', '')
                    resource_attrs = sub_res.get('resource_attributes', [])
                    
                    # 查找流量包: logical_resource_type = huaweicloudinternal_cbc_freeresource
                    if logical_type == 'huaweicloudinternal_cbc_freeresource':
                        traffic_package_id = physical_id
                        logger.debug(f"发现流量包 ID: {traffic_package_id}")
                    
                    # 查找公网 IP: logical_resource_type = huaweicloudinternal_eip
                    elif logical_type == 'huaweicloudinternal_eip':
                        # 从 resource_attributes 中提取 public_ip_address
                        for attr in resource_attrs:
                            if attr.get('key') == 'public_ip_address':
                                public_ip = attr.get('value')
                                break
                    
                    # 查找云主机信息: logical_resource_type = huaweicloudinternal_ecs_instance
                    elif 'ecs_instance' in logical_type:
                        # 从 resource_attributes 中提取私有 IP
                        for attr in resource_attrs:
                            if attr.get('key') == 'nics':
                                try:
                                    nics = json.loads(attr.get('value', '[]'))
                                    if nics and isinstance(nics, list) and len(nics) > 0:
                                        private_ip = nics[0].get('ip_address')
                                except:
                                    pass
                                break
                
                instance = FlexusLInstance(
                    id=instance_id,
                    name=name,
                    region=region,
                    status=status,
                    public_ip=public_ip,
                    private_ip=private_ip,
                    created_at=resource.get('created', None),
                    expire_time=None,
                    traffic_package_id=traffic_package_id
                )
                
                instances.append(instance)
                logger.debug(
                    f"解析实例: id={instance_id}, name={name}, "
                    f"ip={public_ip}, traffic_pkg={traffic_package_id}"
                )
                
            except Exception as e:
                logger.warning(f"解析实例失败: {e}, resource={resource}")
                continue
        
        logger.info(f"共解析 {len(instances)} 个 Flexus L 实例")
        return instances
    
    def get_traffic_package_ids(self) -> List[str]:
        """
        获取所有 Flexus L 实例的流量包 ID
        
        Returns:
            流量包 ID 列表
        """
        instances = self.list_instances()
        
        traffic_ids = []
        for instance in instances:
            if instance.traffic_package_id:
                traffic_ids.append(instance.traffic_package_id)
        
        # 去重
        traffic_ids = list(set(traffic_ids))
        
        logger.info(f"获取到 {len(traffic_ids)} 个流量包 ID")
        return traffic_ids
    
    def query_traffic_usage(
        self,
        free_resource_ids: List[str]
    ) -> List[TrafficPackageInfo]:
        """
        查询流量包使用情况
        
        使用 BSS API: POST /v2/payments/free-resources/usages/details/query
        
        Args:
            free_resource_ids: 流量包资源 ID 列表
            
        Returns:
            流量包使用信息列表
        """
        if not free_resource_ids:
            logger.warning("没有流量包 ID，跳过查询")
            return []
        
        logger.info(f"查询 {len(free_resource_ids)} 个流量包使用情况")
        
        # 构建请求体
        request_body = {
            'free_resource_ids': free_resource_ids
        }
        
        try:
            response = self.bss_client.post(
                uri=self.TRAFFIC_USAGE_API,
                body=request_body
            )
            
            return self._parse_traffic_usage(response)
            
        except HuaweiCloudBSSException as e:
            logger.error(f"查询流量使用情况失败: {e}")
            raise FlexusLException(f"查询流量失败: {e}")
    
    def _parse_traffic_usage(self, response: Dict[str, Any]) -> List[TrafficPackageInfo]:
        """解析流量使用情况响应"""
        packages = []
        free_resources = response.get('free_resources', [])
        
        logger.info(f"解析 {len(free_resources)} 个流量包使用信息")
        
        for resource in free_resources:
            try:
                resource_id = resource.get('free_resource_id', '')
                resource_type_name = resource.get('free_resource_type_name', '')
                usage_type_name = resource.get('usage_type_name', '')
                
                # amount = 剩余额度, original_amount = 原始额度
                remaining = float(resource.get('amount', 0))
                total = float(resource.get('original_amount', 0))
                used = total - remaining if total > 0 else 0
                usage_pct = (used / total * 100) if total > 0 else 0
                
                # 计量单位
                measure_id = resource.get('measure_id', 10)
                measure_unit = MEASURE_UNIT_MAP.get(measure_id, 'GB')
                
                package = TrafficPackageInfo(
                    resource_id=resource_id,
                    resource_type_name=resource_type_name,
                    usage_type_name=usage_type_name,
                    total_amount=total,
                    remaining_amount=remaining,
                    used_amount=used,
                    usage_percentage=usage_pct,
                    measure_unit=measure_unit,
                    start_time=resource.get('start_time'),
                    end_time=resource.get('end_time')
                )
                
                packages.append(package)
                logger.debug(
                    f"解析流量包: id={resource_id}, "
                    f"total={total}{measure_unit}, used={used}{measure_unit}, "
                    f"remaining={remaining}{measure_unit}"
                )
                
            except Exception as e:
                logger.warning(f"解析流量包失败: {e}, resource={resource}")
                continue
        
        return packages
    
    def get_all_traffic_summary(self) -> Dict[str, Any]:
        """
        获取所有 Flexus L 实例流量包的汇总信息
        
        自动发现实例 -> 提取流量包 ID -> 查询使用情况 -> 汇总
        
        Returns:
            流量汇总信息
        """
        # 获取所有实例
        instances = self.list_instances()
        
        if not instances:
            logger.warning("未发现任何 Flexus L 实例")
            return {
                'instance_count': 0,
                'package_count': 0,
                'total_amount': 0,
                'used_amount': 0,
                'remaining_amount': 0,
                'usage_percentage': 0,
                'instances': [],
                'packages': []
            }
        
        # 提取流量包 ID
        traffic_ids = []
        for instance in instances:
            if instance.traffic_package_id:
                traffic_ids.append(instance.traffic_package_id)
        
        traffic_ids = list(set(traffic_ids))
        
        if not traffic_ids:
            logger.warning("Flexus L 实例中未发现流量包 ID")
            return {
                'instance_count': len(instances),
                'package_count': 0,
                'total_amount': 0,
                'used_amount': 0,
                'remaining_amount': 0,
                'usage_percentage': 0,
                'instances': [inst.to_dict() for inst in instances],
                'packages': []
            }
        
        # 查询流量使用情况
        packages = self.query_traffic_usage(traffic_ids)
        
        # 汇总
        total = sum(pkg.total_amount for pkg in packages)
        used = sum(pkg.used_amount for pkg in packages)
        remaining = sum(pkg.remaining_amount for pkg in packages)
        usage_pct = (used / total * 100) if total > 0 else 0
        
        summary = {
            'instance_count': len(instances),
            'package_count': len(packages),
            'total_amount': round(total, 2),
            'used_amount': round(used, 2),
            'remaining_amount': round(remaining, 2),
            'usage_percentage': round(usage_pct, 2),
            'instances': [inst.to_dict() for inst in instances],
            'packages': [pkg.to_dict() for pkg in packages]
        }
        
        logger.info(
            f"流量汇总: {len(instances)} 实例, {len(packages)} 流量包, "
            f"总量={total}GB, 已用={used}GB, 剩余={remaining}GB, 使用率={usage_pct:.1f}%"
        )
        
        return summary


class FlexusLException(Exception):
    """Flexus L 服务异常"""
    pass
