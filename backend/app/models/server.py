"""
服务器模型 - 存储服务器信息
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Server(Base):
    """服务器模型"""
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, comment="所属账户ID")
    server_id = Column(String(100), nullable=False, unique=True, comment="华为云服务器ID")
    name = Column(String(200), nullable=False, comment="服务器名称")
    ip_address = Column(String(50), comment="IP地址")
    status = Column(String(50), comment="服务器状态")
    
    # 流量信息
    traffic_total = Column(Float, comment="总流量包大小（GB）")
    traffic_remaining = Column(Float, comment="剩余流量（GB）")
    traffic_used = Column(Float, comment="已用流量（GB）")
    last_check_time = Column(DateTime, comment="最后检查时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    account = relationship("Account", back_populates="servers")
    monitor_logs = relationship("MonitorLog", back_populates="server")
    shutdown_logs = relationship("ShutdownLog", back_populates="server")

    def __repr__(self):
        return f"<Server(id={self.id}, name='{self.name}', server_id='{self.server_id}')>"
