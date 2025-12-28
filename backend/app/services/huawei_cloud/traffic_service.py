"""
华为云流量包查询服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException


class TrafficPackage:
    """流量包信息模型"""
    
    def __init__(self, data: Dict[str, Any]):
        """
        从 API 响应数据初始化
        
        Args:
            data: API 响应数据
        """
        self.resource_id = data.get('free_resource_id', '')
        self.resource_type_code = data.get('free_resource_type_code', '')
        
        # 流量信息（单位：GB）
        measure_info = data.get('free_resource_measure', {})
        self.total_amount = self._parse_amount(measure_info.get('amount', 0))
        self.used_amount = self._parse_amount(measure_info.get('used_amount', 0))
        self.remaining_amount = self._parse_amount(measure_info.get('available_amount', 0))
        
        # 计算使用百分比
        if self.total_amount > 0:
            self.usage_percentage = (self.used_amount / self.total_amount) * 100
        else:
            self.usage_percentage = 0
        
        # 时间信息
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        self.order_id = data.get('order_id', '')
        
        logger.debug(
            f"解析流量包: id={self.resource_id}, "
            f"total={self.total_amount}GB, "
            f"used={self.used_amount}GB, "
            f"remaining={self.remaining_amount}GB"
        )
    
    def _parse_amount(self, amount: Any) -> float:
        """
        解析流量数值（转换为GB）
        
        Args:
            amount: 原始数值
            
        Returns:
            GB 为单位的流量
        """
        try:
            return float(amount)
        except (ValueError, TypeError):
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'resource_id': self.resource_id,
            'resource_type_code': self.resource_type_code,
            'total_amount': self.total_amount,
            'used_amount': self.used_amount,
            'remaining_amount': self.remaining_amount,
            'usage_percentage': round(self.usage_percentage, 2),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'order_id': self.order_id,
        }
    
    def __repr__(self):
        return (
            f"<TrafficPackage(id={self.resource_id}, "
            f"remaining={self.remaining_amount}GB, "
            f"usage={self.usage_percentage:.1f}%)>"
        )


class TrafficService:
    """流量包查询服务"""
    
    # API 端点配置
    TRAFFIC_API_ENDPOINT = '/v2/payments/free-resources/usages/details/query'
    
    def __init__(self, client: HuaweiCloudClient):
        """
        初始化流量服务
        
        Args:
            client: 华为云客户端
        """
        self.client = client
        logger.info("初始化流量查询服务")
    
    def query_traffic_packages(
        self,
        resource_ids: List[str]
    ) -> List[TrafficPackage]:
        """
        查询流量包剩余量
        
        Args:
            resource_ids: 流量包资源ID列表（最多100个）
            
        Returns:
            流量包信息列表
            
        Raises:
            HuaweiCloudAPIException: API 调用失败
            ValueError: 参数验证失败
        """
        # 参数验证
        if not resource_ids:
            raise ValueError("resource_ids 不能为空")
        
        if len(resource_ids) > 100:
            raise ValueError("resource_ids 最多支持100个")
        
        logger.info(f"查询流量包剩余量: count={len(resource_ids)}")
        
        # 构建请求体
        request_body = {
            'free_resource_ids': resource_ids
        }
        
        try:
            # 调用 API
            response = self.client.post(
                uri=self.TRAFFIC_API_ENDPOINT,
                body=request_body
            )
            
            # 解析响应
            packages = self._parse_response(response)
            
            logger.info(f"成功查询流量包: count={len(packages)}")
            
            return packages
            
        except HuaweiCloudAPIException as e:
            logger.error(f"查询流量包失败: {e}")
            raise
        except Exception as e:
            logger.error(f"解析流量包响应失败: {e}")
            raise HuaweiCloudAPIException(f"解析响应失败: {e}")
    
    def _parse_response(self, response: Dict[str, Any]) -> List[TrafficPackage]:
        """
        解析 API 响应
        
        Args:
            response: API 响应
            
        Returns:
            流量包信息列表
        """
        packages = []
        
        # 获取资源列表
        free_resources = response.get('free_resources', [])
        
        for resource_data in free_resources:
            try:
                package = TrafficPackage(resource_data)
                packages.append(package)
            except Exception as e:
                logger.warning(f"解析流量包数据失败: {e}, data={resource_data}")
                continue
        
        return packages
    
    def get_total_remaining_traffic(
        self,
        resource_ids: List[str]
    ) -> float:
        """
        获取总剩余流量
        
        Args:
            resource_ids: 流量包资源ID列表
            
        Returns:
            总剩余流量（GB）
        """
        packages = self.query_traffic_packages(resource_ids)
        total_remaining = sum(pkg.remaining_amount for pkg in packages)
        
        logger.info(f"计算总剩余流量: {total_remaining}GB")
        
        return total_remaining
    
    def check_traffic_threshold(
        self,
        resource_ids: List[str],
        threshold: float
    ) -> tuple[bool, float]:
        """
        检查流量是否低于阈值
        
        Args:
            resource_ids: 流量包资源ID列表
            threshold: 阈值（GB）
            
        Returns:
            (是否低于阈值, 总剩余流量)
        """
        total_remaining = self.get_total_remaining_traffic(resource_ids)
        is_below = total_remaining < threshold
        
        if is_below:
            logger.warning(
                f"流量低于阈值: remaining={total_remaining}GB, "
                f"threshold={threshold}GB"
            )
        else:
            logger.info(
                f"流量正常: remaining={total_remaining}GB, "
                f"threshold={threshold}GB"
            )
        
        return is_below, total_remaining
    
    def get_traffic_summary(
        self,
        resource_ids: List[str]
    ) -> Dict[str, Any]:
        """
        获取流量汇总信息
        
        Args:
            resource_ids: 流量包资源ID列表
            
        Returns:
            流量汇总信息
        """
        packages = self.query_traffic_packages(resource_ids)
        
        total = sum(pkg.total_amount for pkg in packages)
        used = sum(pkg.used_amount for pkg in packages)
        remaining = sum(pkg.remaining_amount for pkg in packages)
        
        usage_percentage = (used / total * 100) if total > 0 else 0
        
        summary = {
            'package_count': len(packages),
            'total_amount': round(total, 2),
            'used_amount': round(used, 2),
            'remaining_amount': round(remaining, 2),
            'usage_percentage': round(usage_percentage, 2),
            'packages': [pkg.to_dict() for pkg in packages]
        }
        
        logger.info(
            f"流量汇总: total={total}GB, used={used}GB, "
            f"remaining={remaining}GB, usage={usage_percentage:.1f}%"
        )
        
        return summary
