"""
配置模型 - 存储监控配置
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Config(Base):
    """监控配置模型"""
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True, comment="关联账户ID（为空表示全局配置）")
    
    # 监控配置
    check_interval = Column(Integer, default=5, comment="检查间隔（分钟）")
    traffic_threshold = Column(Float, default=10.0, comment="流量阈值（GB）")
    auto_shutdown_enabled = Column(Boolean, default=True, comment="是否启用自动关机")
    
    # 通知配置
    feishu_webhook_url = Column(String(500), comment="飞书 Webhook URL（加密）")
    notification_enabled = Column(Boolean, default=True, comment="是否启用通知")
    
    # 高级配置
    shutdown_delay = Column(Integer, default=0, comment="关机延迟（分钟）")
    retry_times = Column(Integer, default=3, comment="失败重试次数")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    account = relationship("Account", back_populates="configs")

    def __repr__(self):
        return f"<Config(id={self.id}, threshold={self.traffic_threshold}GB, interval={self.check_interval}min)>"
