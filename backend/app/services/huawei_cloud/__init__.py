"""
华为云服务模块
"""
from app.services.huawei_cloud.client import HuaweiCloudClient, HuaweiCloudAPIException
from app.services.huawei_cloud.bss_client import HuaweiCloudBSSClient, HuaweiCloudBSSException
from app.services.huawei_cloud.client_manager import client_manager, HuaweiCloudClientManager
from app.services.huawei_cloud.traffic_service import TrafficService, TrafficPackage
from app.services.huawei_cloud.ecs_service import ECSService, ECSServer
from app.services.huawei_cloud.iam_service import IAMService
from app.services.huawei_cloud.flexusl_service import (
    FlexusLService,
    FlexusLInstance,
    TrafficPackageInfo,
    ServerActionResult,
    JobStatus,
    FlexusLException
)

__all__ = [
    'HuaweiCloudClient',
    'HuaweiCloudAPIException',
    'HuaweiCloudBSSClient',
    'HuaweiCloudBSSException',
    'client_manager',
    'HuaweiCloudClientManager',
    'TrafficService',
    'TrafficPackage',
    'ECSService',
    'ECSServer',
    'IAMService',
    'FlexusLService',
    'FlexusLInstance',
    'TrafficPackageInfo',
    'ServerActionResult',
    'JobStatus',
    'FlexusLException',
]
