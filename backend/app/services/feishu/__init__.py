"""
飞书服务包
"""
from app.services.feishu.webhook_client import (
    FeishuWebhookClient,
    FeishuException,
    MessageType
)
from app.services.feishu.notification_service import (
    FeishuNotificationService,
    NotificationTemplate,
    TrafficWarningTemplate,
    ShutdownNotificationTemplate,
    ShutdownSuccessTemplate,
    ShutdownFailureTemplate
)

__all__ = [
    'FeishuWebhookClient',
    'FeishuException',
    'MessageType',
    'FeishuNotificationService',
    'NotificationTemplate',
    'TrafficWarningTemplate',
    'ShutdownNotificationTemplate',
    'ShutdownSuccessTemplate',
    'ShutdownFailureTemplate',
]
