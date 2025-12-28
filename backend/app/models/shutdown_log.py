"""
关机日志模型 - 记录服务器关机操作
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ShutdownLog(Base):
    """关机日志模型"""
    __tablename__ = "shutdown_logs"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, comment="账户ID")
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, comment="服务器ID")
    
    # 关机信息
    reason = Column(String(200), nullable=False, comment="关机原因")
    status = Column(String(50), nullable=False, comment="关机状态：pending/success/failed")
    job_id = Column(String(100), comment="华为云任务ID")
    
    # 详细信息
    traffic_remaining = Column(String(50), comment="关机时剩余流量")
    error_message = Column(Text, comment="错误信息")
    shutdown_time = Column(DateTime, comment="实际关机时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    account = relationship("Account", back_populates="shutdown_logs")
    server = relationship("Server", back_populates="shutdown_logs")

    def __repr__(self):
        return f"<ShutdownLog(id={self.id}, status='{self.status}', reason='{self.reason}')>"
