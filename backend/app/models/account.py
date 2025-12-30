"""
账户模型 - 存储华为云账户信息
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Account(Base):
    """
    华为云账户模型
    
    一个账户对应一组 AK/SK，可以访问该账户下所有区域的资源
    region 字段保留作为首选/默认区域，实际查询时会自动发现所有区域
    """
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="账户名称")
    ak = Column(String(255), nullable=False, comment="Access Key（加密）")
    sk = Column(String(255), nullable=False, comment="Secret Key（加密）")
    region = Column(String(50), nullable=False, default="ap-southeast-1", comment="首选区域")
    is_international = Column(Boolean, default=True, comment="是否国际站账户（影响 API 端点选择）")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    description = Column(String(500), comment="账户描述")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    servers = relationship("Server", back_populates="account", cascade="all, delete-orphan")
    configs = relationship("Config", back_populates="account", cascade="all, delete-orphan")
    monitor_logs = relationship("MonitorLog", back_populates="account")
    shutdown_logs = relationship("ShutdownLog", back_populates="account")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', region='{self.region}')>"
