"""
华为云流量包查询服务 (Flexus L 实例)

基于 BSS API 查询 Flexus L 实例的流量包剩余量
API 文档: https://support.huaweicloud.com/intl/zh-cn/api-flexusl/query_traffic_0001.html
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from loguru import logger
from app.services.huawei_cloud.bss_client import HuaweiCloudBSSClient, HuaweiCloudBSSException


class TrafficPackage:
    """流量包信息模型"""
    
    # 度量单位映射 (measure_id)
    MEASURE_UNITS = {
        1: 'Byte',
        2: 'KB',
        3: 'MB',
        4: 'GB',
        5: 'TB',
        10: 'GB',  # Flexus L 流量包常用
    }
    
    def __init__(self, data: Dict[str, Any]):
        """
        从 API 响应数据初始化
        
        Flexus L 流量包 API 响应格式:
        {
            "free_resource_id": "xxx",
            "free_resource_type_name": "轻量BGP流量套餐包",
            "quota_reuse_cycle": 4,
            "quota_reuse_cycle_type": 2,
            "usage_type_name": "上行流量",
            "start_time": "2024-12-25T08:00:00Z",
            "end_time": "2025-01-25T16:00:00Z",
            "amount": 180,           // 流量剩余额度
            "original_amount": 200,  // 流量原始额度
            "measure_id": 10
        }
        
        Args:
            data: API 响应数据
        """
        self.resource_id = data.get('free_resource_id', '')
        self.resource_type_name = data.get('free_resource_type_name', '')
        self.usage_type_name = data.get('usage_type_name', '')
        
        # 流量信息（Flexus L API 返回的是 amount 和 original_amount）
        self.remaining_amount = self._parse_amount(data.get('amount', 0))
        self.total_amount = self._parse_amount(data.get('original_amount', 0))
        self.used_amount = self.total_amount - self.remaining_amount
        
        # 度量单位
        self.measure_id = data.get('measure_id', 10)
        self.measure_unit = self.MEASURE_UNITS.get(self.measure_id, 'GB')
        
        # 计算使用百分比
        if self.total_amount > 0:
            self.usage_percentage = (self.used_amount / self.total_amount) * 100
        else:
            self.usage_percentage = 0
        
        # 重置周期信息
        self.quota_reuse_cycle = data.get('quota_reuse_cycle')  # 重置周期
        self.quota_reuse_cycle_type = data.get('quota_reuse_cycle_type')  # 重置周期类型
        
        # 时间信息
        self.start_time = data.get('start_time')
        self.end_time = data.get('end_time')
        
        logger.debug(
            f"解析流量包: id={self.resource_id}, "
            f"type={self.resource_type_name}, "
            f"total={self.total_amount}{self.measure_unit}, "
            f"used={self.used_amount}{self.measure_unit}, "
            f"remaining={self.remaining_amount}{self.measure_unit}"
        )
    
    def _parse_amount(self, amount: Any) -> float:
        """
        解析流量数值
        
        Args:
            amount: 原始数值
            
        Returns:
            流量值
        """
        try:
            return float(amount)
        except (ValueError, TypeError):
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'resource_id': self.resource_id,
            'resource_type_name': self.resource_type_name,
            'usage_type_name': self.usage_type_name,
            'total_amount': self.total_amount,
            'used_amount': self.used_amount,
            'remaining_amount': self.remaining_amount,
            'usage_percentage': round(self.usage_percentage, 2),
            'measure_unit': self.measure_unit,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }
    
    def __repr__(self):
        return (
            f"<TrafficPackage(id={self.resource_id}, "
            f"remaining={self.remaining_amount}{self.measure_unit}, "
            f"usage={self.usage_percentage:.1f}%)>"
        )


class TrafficService:
    """
    Flexus L 实例流量包查询服务
    
    使用 BSS API 查询 Flexus L 实例的流量包使用情况
    支持自动发现账户下所有 Flexus L 流量包
    """
    
    # API 端点配置
    # 查询资源包列表 API (v3 版本 - 国际站和中国站都支持)
    RESOURCE_LIST_ENDPOINT = '/v3/payments/free-resources/query'
    # 查询资源包使用量 API (v2 保留用于查询详细使用情况)
    TRAFFIC_API_ENDPOINT = '/v2/payments/free-resources/usages/details/query'
    
    # Flexus L 流量包关键字 (用于过滤)
    FLEXUS_L_TRAFFIC_KEYWORDS = ['轻量BGP流量', '流量套餐包', 'BGP流量', 'Flexus']
    
    def __init__(self, client: HuaweiCloudBSSClient):
        """
        初始化流量服务
        
        Args:
            client: 华为云 BSS 客户端
        """
        self.client = client
        self._cached_resource_ids: Optional[List[str]] = None
        logger.info("初始化 Flexus L 流量查询服务")
    
    def discover_traffic_packages(
        self,
        status: int = 1,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        自动发现账户下所有 Flexus L 流量包
        
        Args:
            status: 资源状态 (0=全部, 1=生效中, 2=已失效)
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            流量包资源信息列表
        """
        logger.info("开始自动发现 Flexus L 流量包...")
        
        # 构建请求体 - 查询所有资源包
        request_body = {
            'status': status,
            'offset': offset,
            'limit': limit
        }
        
        try:
            response = self.client.post(
                uri=self.RESOURCE_LIST_ENDPOINT,
                body=request_body
            )
            
            # v3 API 返回格式: {"free_resource_packages": [...], "total_count": n}
            # 每个 package 内部有 free_resources 数组
            all_packages = response.get('free_resource_packages', [])
            total_count = response.get('total_count', 0)
            
            logger.info(f"发现 {total_count} 个资源包，本次返回 {len(all_packages)} 个")
            
            # 过滤出 Flexus L 流量包
            traffic_packages = []
            for package in all_packages:
                product_name = package.get('product_name', '')
                
                # 检查是否是 Flexus L 流量包 (检查 product_name 或内部 free_resources 的 usage_type_name)
                is_traffic_package = any(
                    keyword in product_name
                    for keyword in self.FLEXUS_L_TRAFFIC_KEYWORDS
                )
                
                # 也检查内部 free_resources
                if not is_traffic_package:
                    free_resources = package.get('free_resources', [])
                    for fr in free_resources:
                        usage_type_name = fr.get('usage_type_name', '')
                        if any(keyword in usage_type_name for keyword in self.FLEXUS_L_TRAFFIC_KEYWORDS):
                            is_traffic_package = True
                            break
                
                if is_traffic_package:
                    traffic_packages.append(package)
                    logger.debug(
                        f"发现流量包: order_id={package.get('order_id')}, "
                        f"product={product_name}"
                    )
            
            logger.info(f"筛选出 {len(traffic_packages)} 个 Flexus L 流量包")
            
            return traffic_packages
            
        except HuaweiCloudBSSException as e:
            logger.error(f"查询资源包列表失败: {e}")
            raise
    
    def get_all_traffic_resource_ids(self, force_refresh: bool = False) -> List[str]:
        """
        获取所有 Flexus L 流量包的资源 ID
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            流量包资源 ID 列表
        """
        if self._cached_resource_ids is not None and not force_refresh:
            logger.debug(f"使用缓存的流量包 ID: count={len(self._cached_resource_ids)}")
            return self._cached_resource_ids
        
        # 发现所有流量包
        packages = self.discover_traffic_packages()
        
        # 提取资源 ID (v3 格式: 从 package.free_resources 中提取)
        resource_ids = []
        for pkg in packages:
            free_resources = pkg.get('free_resources', [])
            for fr in free_resources:
                resource_id = fr.get('free_resource_id')
                if resource_id:
                    resource_ids.append(resource_id)
        
        # 缓存结果
        self._cached_resource_ids = resource_ids
        
        logger.info(f"获取到 {len(resource_ids)} 个流量包资源 ID")
        return resource_ids
    
    def query_all_traffic(self) -> List[TrafficPackage]:
        """
        查询所有 Flexus L 流量包的使用情况 (自动发现)
        
        Returns:
            流量包信息列表
        """
        # 获取所有流量包 ID
        resource_ids = self.get_all_traffic_resource_ids()
        
        if not resource_ids:
            logger.warning("未发现任何 Flexus L 流量包")
            return []
        
        # 查询流量使用情况
        return self.query_traffic_packages(resource_ids)
    
    def get_all_traffic_summary(self) -> Dict[str, Any]:
        """
        获取所有 Flexus L 流量包的汇总信息 (自动发现)
        
        Returns:
            流量汇总信息
        """
        packages = self.query_all_traffic()
        
        if not packages:
            return {
                'package_count': 0,
                'total_amount': 0,
                'used_amount': 0,
                'remaining_amount': 0,
                'usage_percentage': 0,
                'packages': []
            }
        
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
            f"流量汇总 (自动发现): total={total}GB, used={used}GB, "
            f"remaining={remaining}GB, usage={usage_percentage:.1f}%"
        )
        
        return summary
    
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
            HuaweiCloudBSSException: API 调用失败
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
            # 调用 BSS API
            response = self.client.post(
                uri=self.TRAFFIC_API_ENDPOINT,
                body=request_body
            )
            
            # 解析响应
            packages = self._parse_response(response)
            
            logger.info(f"成功查询流量包: count={len(packages)}")
            
            return packages
            
        except HuaweiCloudBSSException as e:
            logger.error(f"查询流量包失败: {e}")
            raise
        except Exception as e:
            logger.error(f"解析流量包响应失败: {e}")
            raise HuaweiCloudBSSException(f"解析响应失败: {e}")
    
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
