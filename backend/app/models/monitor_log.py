"""
监控日志模型 - 记录流量监控信息
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class MonitorLog(Base):
    """监控日志模型"""
    __tablename__ = "monitor_logs"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, comment="账户ID")
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, comment="服务器ID")
    
    # 流量信息
    traffic_remaining = Column(Float, nullable=False, comment="剩余流量（GB）")
    traffic_total = Column(Float, comment="总流量（GB）")
    traffic_used = Column(Float, comment="已用流量（GB）")
    usage_percentage = Column(Float, comment="使用百分比")
    
    # 阈值判断
    threshold = Column(Float, nullable=False, comment="当时的阈值（GB）")
    is_below_threshold = Column(Boolean, default=False, comment="是否低于阈值")
    
    # 监控信息
    check_time = Column(DateTime, default=datetime.utcnow, comment="检查时间")
    message = Column(String(500), comment="日志消息")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    account = relationship("Account", back_populates="monitor_logs")
    server = relationship("Server", back_populates="monitor_logs")

    def __repr__(self):
        return f"<MonitorLog(id={self.id}, remaining={self.traffic_remaining}GB, below_threshold={self.is_below_threshold})>"
