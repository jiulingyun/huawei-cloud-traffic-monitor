"""
华为云客户端管理器
支持多账户管理
"""
from typing import Dict, Optional
from loguru import logger
from app.services.huawei_cloud.client import HuaweiCloudClient
from app.utils.encryption import encryption_service


class HuaweiCloudClientManager:
    """华为云客户端管理器"""
    
    def __init__(self):
        """初始化客户端管理器"""
        self._clients: Dict[int, HuaweiCloudClient] = {}
        logger.info("初始化华为云客户端管理器")
    
    def get_client(
        self,
        account_id: int,
        encrypted_ak: str,
        encrypted_sk: str,
        region: str
    ) -> HuaweiCloudClient:
        """
        获取或创建华为云客户端
        
        Args:
            account_id: 账户 ID
            encrypted_ak: 加密的 Access Key
            encrypted_sk: 加密的 Secret Key
            region: 区域
            
        Returns:
            华为云客户端实例
        """
        # 如果客户端已存在，直接返回
        if account_id in self._clients:
            logger.debug(f"使用缓存的华为云客户端: account_id={account_id}")
            return self._clients[account_id]
        
        # 解密 AK/SK
        try:
            ak, sk = encryption_service.decrypt_ak_sk(encrypted_ak, encrypted_sk)
            logger.debug(f"解密 AK/SK 成功: account_id={account_id}")
        except Exception as e:
            logger.error(f"解密 AK/SK 失败: account_id={account_id}, error={e}")
            raise ValueError(f"解密 AK/SK 失败: {e}")
        
        # 创建新客户端
        try:
            client = HuaweiCloudClient(
                access_key=ak,
                secret_key=sk,
                region=region
            )
            
            # 缓存客户端
            self._clients[account_id] = client
            
            logger.info(f"创建新的华为云客户端: account_id={account_id}, region={region}")
            
            return client
            
        except Exception as e:
            logger.error(f"创建华为云客户端失败: account_id={account_id}, error={e}")
            raise ValueError(f"创建华为云客户端失败: {e}")
    
    def remove_client(self, account_id: int) -> bool:
        """
        移除客户端缓存
        
        Args:
            account_id: 账户 ID
            
        Returns:
            是否成功
        """
        if account_id in self._clients:
            del self._clients[account_id]
            logger.info(f"移除华为云客户端缓存: account_id={account_id}")
            return True
        return False
    
    def clear_clients(self):
        """清空所有客户端缓存"""
        count = len(self._clients)
        self._clients.clear()
        logger.info(f"清空所有华为云客户端缓存: count={count}")
    
    def get_client_count(self) -> int:
        """获取缓存的客户端数量"""
        return len(self._clients)


# 创建全局客户端管理器实例
client_manager = HuaweiCloudClientManager()
