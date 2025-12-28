"""
配置验证工具
"""
import re
from typing import Optional
from loguru import logger


def validate_ak(ak: str) -> bool:
    """
    验证华为云 Access Key 格式
    
    Args:
        ak: Access Key
        
    Returns:
        是否有效
    """
    if not ak:
        return False
    
    # AK 通常是 20-30 位的大写字母和数字
    pattern = r'^[A-Z0-9]{20,30}$'
    return bool(re.match(pattern, ak))


def validate_sk(sk: str) -> bool:
    """
    验证华为云 Secret Key 格式
    
    Args:
        sk: Secret Key
        
    Returns:
        是否有效
    """
    if not sk:
        return False
    
    # SK 通常是 40 位左右的字符
    return len(sk) >= 30


def validate_region(region: str) -> bool:
    """
    验证华为云区域
    
    Args:
        region: 区域代码
        
    Returns:
        是否有效
    """
    valid_regions = [
        'cn-north-1',  # 华北-北京一
        'cn-north-4',  # 华北-北京四
        'cn-east-2',   # 华东-上海二
        'cn-east-3',   # 华东-上海一
        'cn-south-1',  # 华南-广州
        'cn-southwest-2',  # 西南-贵阳一
        'ap-southeast-1',  # 中国-香港
        'ap-southeast-2',  # 亚太-曼谷
        'ap-southeast-3',  # 亚太-新加坡
    ]
    
    return region in valid_regions


def validate_webhook_url(url: str) -> bool:
    """
    验证飞书 Webhook URL
    
    Args:
        url: Webhook URL
        
    Returns:
        是否有效
    """
    if not url:
        return False
    
    # 飞书 Webhook URL 格式验证
    pattern = r'^https://open\.feishu\.cn/open-apis/bot/v2/hook/[a-zA-Z0-9-]+$'
    return bool(re.match(pattern, url))


def validate_traffic_threshold(threshold: float) -> bool:
    """
    验证流量阈值
    
    Args:
        threshold: 阈值（GB）
        
    Returns:
        是否有效
    """
    # 阈值应该在 0.1GB 到 1000GB 之间
    return 0.1 <= threshold <= 1000


def validate_check_interval(interval: int) -> bool:
    """
    验证检查间隔
    
    Args:
        interval: 间隔（分钟）
        
    Returns:
        是否有效
    """
    # 间隔应该在 1 到 1440 分钟（24小时）之间
    return 1 <= interval <= 1440


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否有效
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_account_config(
        name: str,
        ak: str,
        sk: str,
        region: str
    ) -> tuple[bool, Optional[str]]:
        """
        验证账户配置
        
        Args:
            name: 账户名称
            ak: Access Key
            sk: Secret Key
            region: 区域
            
        Returns:
            (是否有效, 错误信息)
        """
        if not name or len(name) < 2:
            return False, "账户名称至少需要2个字符"
        
        if not validate_ak(ak):
            return False, "Access Key 格式无效"
        
        if not validate_sk(sk):
            return False, "Secret Key 格式无效"
        
        if not validate_region(region):
            return False, f"不支持的区域: {region}"
        
        return True, None
    
    @staticmethod
    def validate_monitor_config(
        check_interval: int,
        traffic_threshold: float,
        feishu_webhook_url: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        验证监控配置
        
        Args:
            check_interval: 检查间隔
            traffic_threshold: 流量阈值
            feishu_webhook_url: 飞书 Webhook URL
            
        Returns:
            (是否有效, 错误信息)
        """
        if not validate_check_interval(check_interval):
            return False, "检查间隔必须在 1-1440 分钟之间"
        
        if not validate_traffic_threshold(traffic_threshold):
            return False, "流量阈值必须在 0.1-1000 GB 之间"
        
        if feishu_webhook_url and not validate_webhook_url(feishu_webhook_url):
            return False, "飞书 Webhook URL 格式无效"
        
        return True, None
