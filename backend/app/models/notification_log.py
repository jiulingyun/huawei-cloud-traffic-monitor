"""
通知日志模型 - 记录飞书通知发送记录
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.core.database import Base


class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    
    # 通知信息
    notification_type = Column(String(50), nullable=False, comment="通知类型：alert/shutdown/error")
    title = Column(String(200), comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    
    # 发送状态
    status = Column(String(50), nullable=False, comment="发送状态：pending/success/failed")
    webhook_url = Column(String(500), comment="Webhook URL（脱敏）")
    response_code = Column(Integer, comment="响应状态码")
    error_message = Column(Text, comment="错误信息")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type='{self.notification_type}', status='{self.status}')>"
