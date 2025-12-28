"""
华为云服务模块
"""
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException
from app.services.huawei_cloud.client_manager import client_manager, HuaweiCloudClientManager

__all__ = [
    'HuaweiCloudClient',
    'HuaweiCloudAPIException',
    'client_manager',
    'HuaweiCloudClientManager',
]
