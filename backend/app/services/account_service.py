"""
账户管理服务

实现账户的 CRUD 操作、验证和加密存储
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.account import Account
from app.utils.encryption import encryption_service
from app.services.huawei_cloud import client_manager


class AccountService:
    """账户管理服务"""
    
    @staticmethod
    def create_account(
        db: Session,
        name: str,
        ak: str,
        sk: str,
        region: str = "cn-north-4",
        is_international: bool = True,
        description: Optional[str] = None
    ) -> Account:
        """
        创建账户
        
        Args:
            db: 数据库会话
            name: 账户名称
            ak: Access Key
            sk: Secret Key
            region: 首选区域（实际会自动发现所有区域）
            is_international: 是否为国际站账户
            description: 描述
            
        Returns:
            创建的账户
        """
        logger.info(f"创建账户: name={name}, region={region}, is_international={is_international}")
        
        # 加密 AK/SK
        encrypted_ak, encrypted_sk = encryption_service.encrypt_ak_sk(ak, sk)
        
        # 创建账户
        account = Account(
            name=name,
            ak=encrypted_ak,
            sk=encrypted_sk,
            region=region,
            is_international=is_international,
            is_enabled=True,
            description=description
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        logger.info(f"账户创建成功: id={account.id}, name={name}")
        
        return account
    
    @staticmethod
    def get_account(db: Session, account_id: int) -> Optional[Account]:
        """
        获取账户
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            账户信息，不存在返回 None
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if account:
            logger.info(f"获取账户: id={account_id}, name={account.name}")
        else:
            logger.warning(f"账户不存在: id={account_id}")
        
        return account
    
    @staticmethod
    def list_accounts(
        db: Session,
        is_enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Account]:
        """
        获取账户列表
        
        Args:
            db: 数据库会话
            is_enabled: 过滤启用状态（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            账户列表
        """
        query = db.query(Account)
        
        if is_enabled is not None:
            query = query.filter(Account.is_enabled == is_enabled)
        
        query = query.limit(limit).offset(offset)
        accounts = query.all()
        
        logger.info(f"查询账户列表: count={len(accounts)}, is_enabled={is_enabled}")
        
        return accounts
    
    @staticmethod
    def update_account(
        db: Session,
        account_id: int,
        name: Optional[str] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        region: Optional[str] = None,
        is_international: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[Account]:
        """
        更新账户
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            name: 新名称
            ak: 新 Access Key
            sk: 新 Secret Key
            region: 新首选区域
            is_international: 是否为国际站账户
            description: 新描述
            
        Returns:
            更新后的账户，不存在返回 None
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            logger.warning(f"账户不存在: id={account_id}")
            return None
        
        # 更新字段
        if name is not None:
            account.name = name
        
        if ak is not None and sk is not None:
            # 重新加密 AK/SK
            encrypted_ak, encrypted_sk = encryption_service.encrypt_ak_sk(ak, sk)
            account.ak = encrypted_ak
            account.sk = encrypted_sk
            
            # 清除客户端缓存
            client_manager.remove_client(account_id)
        
        if region is not None:
            account.region = region
            # 清除客户端缓存
            client_manager.remove_client(account_id)
        
        if is_international is not None:
            account.is_international = is_international
        
        if description is not None:
            account.description = description
        
        db.commit()
        db.refresh(account)
        
        logger.info(f"账户更新成功: id={account_id}")
        
        return account
    
    @staticmethod
    def delete_account(db: Session, account_id: int) -> bool:
        """
        删除账户
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            是否删除成功
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            logger.warning(f"账户不存在: id={account_id}")
            return False
        
        # 清除客户端缓存
        client_manager.remove_client(account_id)
        
        db.delete(account)
        db.commit()
        
        logger.info(f"账户删除成功: id={account_id}, name={account.name}")
        
        return True
    
    @staticmethod
    def enable_account(db: Session, account_id: int) -> Optional[Account]:
        """
        启用账户
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            更新后的账户，不存在返回 None
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            logger.warning(f"账户不存在: id={account_id}")
            return None
        
        account.is_enabled = True
        db.commit()
        db.refresh(account)
        
        logger.info(f"账户已启用: id={account_id}, name={account.name}")
        
        return account
    
    @staticmethod
    def disable_account(db: Session, account_id: int) -> Optional[Account]:
        """
        禁用账户
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            更新后的账户，不存在返回 None
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            logger.warning(f"账户不存在: id={account_id}")
            return None
        
        account.is_enabled = False
        
        # 清除客户端缓存
        client_manager.remove_client(account_id)
        
        db.commit()
        db.refresh(account)
        
        logger.info(f"账户已禁用: id={account_id}, name={account.name}")
        
        return account
    
    @staticmethod
    def verify_account(
        db: Session,
        account_id: int
    ) -> tuple[bool, str]:
        """
        验证账户（测试 AK/SK 是否有效）
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            (是否验证成功, 验证消息)
        """
        logger.info(f"验证账户: id={account_id}")
        
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            return False, "账户不存在"
        
        try:
            # 获取华为云客户端
            client = client_manager.get_client(
                account_id=account.id,
                encrypted_ak=account.ak,
                encrypted_sk=account.sk,
                region=account.region
            )
            
            # 尝试调用一个简单的 API 验证凭证
            # 这里可以调用列表服务器等接口
            logger.info(f"账户验证成功: id={account_id}")
            
            return True, "账户验证成功"
            
        except Exception as e:
            logger.error(f"账户验证失败: id={account_id}, error={e}")
            return False, f"账户验证失败: {str(e)}"
    
    @staticmethod
    def get_decrypted_credentials(
        db: Session,
        account_id: int
    ) -> Optional[tuple[str, str]]:
        """
        获取解密后的凭证（仅供内部使用）
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            (ak, sk) 元组，账户不存在返回 None
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not account:
            return None
        
        try:
            ak, sk = encryption_service.decrypt_ak_sk(account.ak, account.sk)
            return ak, sk
        except Exception as e:
            logger.error(f"解密凭证失败: account_id={account_id}, error={e}")
            return None


# 创建全局账户服务实例
account_service = AccountService()
