"""
服务器操作日志模型 - 记录所有服务器操作（开机、关机、重启等）
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class OperationLog(Base):
    """服务器操作日志模型"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, comment="账户ID")
    
    # 操作信息
    operation_type = Column(String(50), nullable=False, comment="操作类型: start/stop/reboot/auto_shutdown")
    target_type = Column(String(50), nullable=False, default="server", comment="目标类型: server/instance")
    target_id = Column(String(100), nullable=False, comment="目标ID（云主机ID或实例ID）")
    target_name = Column(String(200), comment="目标名称")
    region = Column(String(50), comment="区域")
    
    # 状态信息
    status = Column(String(50), nullable=False, default="pending", comment="状态: pending/success/failed")
    job_id = Column(String(100), comment="华为云任务ID")
    
    # 详细信息
    reason = Column(String(500), comment="操作原因")
    error_message = Column(Text, comment="错误信息")
    extra_data = Column(Text, comment="额外数据（JSON格式）")
    
    # 时间信息
    start_time = Column(DateTime, default=datetime.utcnow, comment="操作开始时间")
    end_time = Column(DateTime, comment="操作结束时间")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    account = relationship("Account")

    def __repr__(self):
        return f"<OperationLog(id={self.id}, type='{self.operation_type}', status='{self.status}')>"
