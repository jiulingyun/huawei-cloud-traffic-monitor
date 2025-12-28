"""
加密工具模块
用于敏感数据（AK/SK、Webhook URL等）的加密和解密
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional
from loguru import logger


class EncryptionService:
    """加密服务"""
    
    def __init__(self, key: Optional[str] = None):
        """
        初始化加密服务
        
        Args:
            key: 加密密钥，如果不提供则使用环境变量或生成新密钥
        """
        if key:
            self.key = key.encode()
        else:
            # 从环境变量获取或生成新密钥
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                self.key = env_key.encode()
            else:
                # 生成新密钥（开发环境）
                self.key = Fernet.generate_key()
                logger.warning("未配置 ENCRYPTION_KEY，使用临时密钥（不推荐用于生产环境）")
        
        # 创建 Fernet 实例
        try:
            self.cipher = Fernet(self._derive_key(self.key))
        except Exception as e:
            logger.error(f"加密服务初始化失败: {e}")
            raise
    
    def _derive_key(self, password: bytes) -> bytes:
        """
        从密码派生密钥
        
        Args:
            password: 原始密码
            
        Returns:
            派生后的密钥
        """
        # 使用固定的盐值（生产环境应该使用随机盐值并存储）
        salt = b'huawei_cloud_monitor_salt_2024'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文
            
        Returns:
            加密后的字符串（Base64编码）
        """
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise ValueError(f"加密失败: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: 密文（Base64编码）
            
        Returns:
            解密后的明文
        """
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError(f"解密失败: {e}")
    
    def encrypt_ak_sk(self, ak: str, sk: str) -> tuple[str, str]:
        """
        加密 AK/SK
        
        Args:
            ak: Access Key
            sk: Secret Key
            
        Returns:
            (加密后的AK, 加密后的SK)
        """
        encrypted_ak = self.encrypt(ak)
        encrypted_sk = self.encrypt(sk)
        return encrypted_ak, encrypted_sk
    
    def decrypt_ak_sk(self, encrypted_ak: str, encrypted_sk: str) -> tuple[str, str]:
        """
        解密 AK/SK
        
        Args:
            encrypted_ak: 加密的 Access Key
            encrypted_sk: 加密的 Secret Key
            
        Returns:
            (解密后的AK, 解密后的SK)
        """
        ak = self.decrypt(encrypted_ak)
        sk = self.decrypt(encrypted_sk)
        return ak, sk
    
    @staticmethod
    def generate_key() -> str:
        """
        生成新的加密密钥
        
        Returns:
            Base64 编码的密钥
        """
        key = Fernet.generate_key()
        return key.decode()
    
    @staticmethod
    def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
        """
        脱敏处理敏感数据
        
        Args:
            data: 原始数据
            show_chars: 显示的字符数
            
        Returns:
            脱敏后的数据
        """
        if not data or len(data) <= show_chars:
            return "****"
        
        return data[:show_chars] + "*" * (len(data) - show_chars)


# 创建全局加密服务实例
encryption_service = EncryptionService()
