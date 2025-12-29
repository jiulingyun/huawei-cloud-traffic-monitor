"""
配置管理服务
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.config import Config
from app.utils.encryption import encryption_service


class ConfigService:
    """配置管理服务"""
    
    def get_config(
        self,
        db: Session,
        config_id: int
    ) -> Optional[Config]:
        """
        获取配置详情
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            
        Returns:
            Config 对象或 None
        """
        return db.query(Config).filter(Config.id == config_id).first()
    
    def get_global_config(self, db: Session) -> Optional[Config]:
        """
        获取全局配置（account_id 为 NULL）
        
        Args:
            db: 数据库会话
            
        Returns:
            Config 对象或 None
        """
        return db.query(Config).filter(Config.account_id.is_(None)).first()
    
    def get_account_config(
        self,
        db: Session,
        account_id: int
    ) -> Optional[Config]:
        """
        获取账户配置
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            
        Returns:
            Config 对象或 None
        """
        return db.query(Config).filter(Config.account_id == account_id).first()
    
    def list_configs(
        self,
        db: Session,
        account_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Config]:
        """
        获取配置列表
        
        Args:
            db: 数据库会话
            account_id: 过滤账户 ID（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            Config 列表
        """
        query = db.query(Config)
        
        if account_id is not None:
            query = query.filter(Config.account_id == account_id)
        
        return query.offset(offset).limit(limit).all()
    
    def create_config(
        self,
        db: Session,
        account_id: Optional[int] = None,
        check_interval: int = 5,
        traffic_threshold: float = 10.0,
        auto_shutdown_enabled: bool = True,
        feishu_webhook_url: Optional[str] = None,
        notification_enabled: bool = True,
        shutdown_delay: int = 0,
        retry_times: int = 3
    ) -> Config:
        """
        创建配置
        
        Args:
            db: 数据库会话
            account_id: 关联账户 ID（None 表示全局配置）
            check_interval: 检查间隔（分钟）
            traffic_threshold: 流量阈值（GB）
            auto_shutdown_enabled: 是否启用自动关机
            feishu_webhook_url: 飞书 Webhook URL
            notification_enabled: 是否启用通知
            shutdown_delay: 关机延迟（分钟）
            retry_times: 失败重试次数
            
        Returns:
            创建的 Config 对象
            
        Raises:
            ValueError: 如果配置已存在
        """
        # 检查是否已存在配置
        if account_id is None:
            existing = self.get_global_config(db)
        else:
            existing = self.get_account_config(db, account_id)
        
        if existing:
            raise ValueError(f"配置已存在: {'全局配置' if account_id is None else f'账户 {account_id} 的配置'}")
        
        # 加密飞书 Webhook URL
        encrypted_webhook = None
        if feishu_webhook_url:
            encrypted_webhook = encryption_service.encrypt(feishu_webhook_url)
        
        config = Config(
            account_id=account_id,
            check_interval=check_interval,
            traffic_threshold=traffic_threshold,
            auto_shutdown_enabled=auto_shutdown_enabled,
            feishu_webhook_url=encrypted_webhook,
            notification_enabled=notification_enabled,
            shutdown_delay=shutdown_delay,
            retry_times=retry_times
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return config
    
    def update_config(
        self,
        db: Session,
        config_id: int,
        check_interval: Optional[int] = None,
        traffic_threshold: Optional[float] = None,
        auto_shutdown_enabled: Optional[bool] = None,
        feishu_webhook_url: Optional[str] = None,
        notification_enabled: Optional[bool] = None,
        shutdown_delay: Optional[int] = None,
        retry_times: Optional[int] = None
    ) -> Optional[Config]:
        """
        更新配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            check_interval: 检查间隔（分钟）
            traffic_threshold: 流量阈值（GB）
            auto_shutdown_enabled: 是否启用自动关机
            feishu_webhook_url: 飞书 Webhook URL
            notification_enabled: 是否启用通知
            shutdown_delay: 关机延迟（分钟）
            retry_times: 失败重试次数
            
        Returns:
            更新后的 Config 对象或 None
        """
        config = self.get_config(db, config_id)
        
        if not config:
            return None
        
        # 更新字段
        if check_interval is not None:
            config.check_interval = check_interval
        if traffic_threshold is not None:
            config.traffic_threshold = traffic_threshold
        if auto_shutdown_enabled is not None:
            config.auto_shutdown_enabled = auto_shutdown_enabled
        if feishu_webhook_url is not None:
            config.feishu_webhook_url = encryption_service.encrypt(feishu_webhook_url)
        if notification_enabled is not None:
            config.notification_enabled = notification_enabled
        if shutdown_delay is not None:
            config.shutdown_delay = shutdown_delay
        if retry_times is not None:
            config.retry_times = retry_times
        
        db.commit()
        db.refresh(config)
        
        return config
    
    def delete_config(self, db: Session, config_id: int) -> bool:
        """
        删除配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            
        Returns:
            是否成功删除
        """
        config = self.get_config(db, config_id)
        
        if not config:
            return False
        
        db.delete(config)
        db.commit()
        
        return True
    
    def get_effective_config(
        self,
        db: Session,
        account_id: Optional[int] = None
    ) -> Optional[Config]:
        """
        获取有效配置（账户配置优先，否则使用全局配置）
        
        Args:
            db: 数据库会话
            account_id: 账户 ID（可选）
            
        Returns:
            有效的 Config 对象或 None
        """
        # 如果指定了账户 ID，先查找账户配置
        if account_id is not None:
            account_config = self.get_account_config(db, account_id)
            if account_config:
                return account_config
        
        # 使用全局配置
        return self.get_global_config(db)
    
    def get_decrypted_webhook_url(self, config: Config) -> Optional[str]:
        """
        获取解密后的飞书 Webhook URL
        
        Args:
            config: 配置对象
            
        Returns:
            解密后的 URL 或 None
        """
        if not config.feishu_webhook_url:
            return None
        
        try:
            return encryption_service.decrypt(config.feishu_webhook_url)
        except Exception:
            return None


# 全局实例
config_service = ConfigService()
