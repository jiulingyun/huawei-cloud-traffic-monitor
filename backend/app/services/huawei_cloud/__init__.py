"""
华为云服务模块
"""
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException
from app.services.huawei_cloud.client_manager import client_manager, HuaweiCloudClientManager
from app.services.huawei_cloud.traffic_service import TrafficService, TrafficPackage
from app.services.huawei_cloud.ecs_service import ECSService, ECSServer

__all__ = [
    'HuaweiCloudClient',
    'HuaweiCloudAPIException',
    'client_manager',
    'HuaweiCloudClientManager',
    'TrafficService',
    'TrafficPackage',
    'ECSService',
    'ECSServer',
]
