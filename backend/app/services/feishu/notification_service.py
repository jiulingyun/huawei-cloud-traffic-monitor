"""
飞书通知服务

实现关机通知、流量告警等通知模板和发送功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from app.services.feishu.webhook_client import FeishuWebhookClient


class NotificationTemplate:
    """通知模板基类"""
    
    def render(self, **kwargs) -> Dict[str, Any]:
        """
        渲染模板
        
        Args:
            **kwargs: 模板变量
            
        Returns:
            卡片配置
        """
        raise NotImplementedError


class TrafficWarningTemplate(NotificationTemplate):
    """流量告警通知模板"""
    
    def render(
        self,
        account_name: str,
        remaining_traffic_gb: float,
        threshold_gb: float,
        usage_percentage: float,
        server_count: int = 0,
        region: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染流量告警通知
        
        Args:
            account_name: 账户名称
            remaining_traffic_gb: 剩余流量（GB）
            threshold_gb: 流量阈值（GB）
            usage_percentage: 使用百分比
            server_count: 服务器数量
            region: 区域
            
        Returns:
            卡片配置
        """
        # 根据使用率确定颜色
        if usage_percentage >= 90:
            color = "red"
            level = "🔴 严重告警"
        elif usage_percentage >= 80:
            color = "orange"
            level = "🟠 高级告警"
        elif usage_percentage >= 70:
            color = "yellow"
            level = "🟡 中级告警"
        else:
            color = "blue"
            level = "🔵 提醒"
        
        # 构建内容
        content = f"""**告警级别**: {level}
**账户名称**: {account_name}
**所属区域**: {region or '未知'}
**服务器数量**: {server_count} 台

---

**剩余流量**: {remaining_traffic_gb:.2f} GB
**流量阈值**: {threshold_gb:.2f} GB
**使用百分比**: {usage_percentage:.1f}%

---

**告警时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "⚠️ 流量使用告警"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }


class ShutdownNotificationTemplate(NotificationTemplate):
    """关机通知模板"""
    
    def render(
        self,
        account_name: str,
        server_list: List[Dict[str, str]],
        reason: str = "流量不足",
        job_id: str = "",
        region: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染关机通知
        
        Args:
            account_name: 账户名称
            server_list: 服务器列表 [{"name": "服务器名", "id": "服务器ID", "ip": "IP地址"}, ...]
            reason: 关机原因
            job_id: 任务 ID
            region: 区域
            
        Returns:
            卡片配置
        """
        # 构建服务器列表
        server_info = "\n".join([
            f"• **{server.get('name', '未命名')}** ({server.get('id', 'N/A')})"
            for server in server_list[:10]  # 最多显示 10 台
        ])
        
        if len(server_list) > 10:
            server_info += f"\n... 还有 {len(server_list) - 10} 台服务器"
        
        # 构建内容
        content = f"""**账户名称**: {account_name}
**所属区域**: {region or '未知'}
**关机原因**: {reason}
**服务器数量**: {len(server_list)} 台

---

**关机服务器列表**:
{server_info}

---

**任务 ID**: `{job_id}`
**操作时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ℹ️ 系统已自动关闭上述服务器以节省流量"""
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🔌 服务器自动关机通知"
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }


class ShutdownSuccessTemplate(NotificationTemplate):
    """关机成功通知模板"""
    
    def render(
        self,
        account_name: str,
        server_count: int,
        job_id: str,
        duration_seconds: float = 0,
        server: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染关机成功通知
        
        Args:
            account_name: 账户名称
            server_count: 服务器数量
            job_id: 任务 ID
            duration_seconds: 执行时长（秒）
            
        Returns:
            卡片配置
        """
        # 若传入单台服务器信息，展示实例详情
        server_details = ""
        if server:
            name = server.get("name", "未命名")
            ip = server.get("ip", "N/A")
            remaining = server.get("remaining", None)
            threshold = server.get("threshold", None)
            server_details = "\n\n---\n\n**实例信息**:\n"
            server_details += f"• **{name}** ({ip})\n"
            if remaining is not None:
                server_details += f"• 剩余流量: {float(remaining):.2f} GB\n"
            if threshold is not None:
                server_details += f"• 阈值: {float(threshold):.2f} GB\n"

        content = f"""**账户名称**: {account_name}
**关机数量**: {server_count} 台
**任务 ID**: `{job_id}`
**执行时长**: {duration_seconds:.1f} 秒
**完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{server_details}

✅ 关机操作已完成"""
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "✅ 关机任务完成"
                },
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }


class ShutdownDelayTemplate(NotificationTemplate):
    """关机延迟通知模板"""
    
    def render(
        self,
        account_name: str,
        delay_minutes: int,
        remaining_traffic_gb: float,
        threshold_gb: float,
        region: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染关机延迟通知
        
        Args:
            account_name: 账户名称
            delay_minutes: 延迟时间（分钟）
            remaining_traffic_gb: 剩余流量（GB）
            threshold_gb: 流量阈值（GB）
            region: 区域
            
        Returns:
            卡片配置
        """
        from datetime import timedelta
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        
        content = f"""**账户名称**: {account_name}
**所属区域**: {region or '未知'}

---

**剩余流量**: {remaining_traffic_gb:.2f} GB
**流量阈值**: {threshold_gb:.2f} GB
**延迟时间**: {delay_minutes} 分钟
**预计关机时间**: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}

---

⏰ 流量低于阈值，系统将在 {delay_minutes} 分钟后执行自动关机
💡 在延迟期间内流量恢复正常将自动取消关机"""
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "⏰ 关机延迟通知"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }


class ShutdownFailureTemplate(NotificationTemplate):
    """关机失败通知模板"""
    
    def render(
        self,
        account_name: str,
        server_count: int,
        job_id: str,
        error_message: str,
        server: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        渲染关机失败通知
        
        Args:
            account_name: 账户名称
            server_count: 服务器数量
            job_id: 任务 ID
            error_message: 错误信息
            
        Returns:
            卡片配置
        """
        server_details = ""
        if server:
            name = server.get("name", "未命名")
            ip = server.get("ip", "N/A")
            remaining = server.get("remaining", None)
            threshold = server.get("threshold", None)
            server_details = "\n\n---\n\n**实例信息**:\n"
            server_details += f"• **{name}** ({ip})\n"
            if remaining is not None:
                server_details += f"• 剩余流量: {float(remaining):.2f} GB\n"
            if threshold is not None:
                server_details += f"• 阈值: {float(threshold):.2f} GB\n"

        content = f"""**账户名称**: {account_name}
**关机数量**: {server_count} 台
**任务 ID**: `{job_id}`
**失败时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{server_details}

---

**错误信息**:
```
{error_message}
```

❌ 关机任务执行失败，请检查错误信息"""
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "❌ 关机任务失败"
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }


class FeishuNotificationService:
    """飞书通知服务"""
    
    def __init__(self, webhook_client: FeishuWebhookClient):
        """
        初始化通知服务
        
        Args:
            webhook_client: 飞书 Webhook 客户端
        """
        self.client = webhook_client
        self.templates = {
            'traffic_warning': TrafficWarningTemplate(),
            'shutdown_notification': ShutdownNotificationTemplate(),
            'shutdown_delay': ShutdownDelayTemplate(),
            'shutdown_success': ShutdownSuccessTemplate(),
            'shutdown_failure': ShutdownFailureTemplate(),
        }
        logger.info("初始化飞书通知服务")
    
    def send_notification(
        self,
        template_name: str,
        **template_vars
    ) -> Dict[str, Any]:
        """
        发送通知
        
        Args:
            template_name: 模板名称
            **template_vars: 模板变量
            
        Returns:
            发送结果
            
        Raises:
            ValueError: 模板不存在
        """
        # 获取模板
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        logger.info(f"发送通知: template={template_name}")
        
        # 渲染模板
        card = template.render(**template_vars)
        
        # 发送卡片
        result = self.client.send_card(card)
        
        logger.info(f"通知发送成功: template={template_name}")
        
        return result
    
    def send_traffic_warning(
        self,
        account_name: str,
        remaining_traffic_gb: float,
        threshold_gb: float,
        usage_percentage: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送流量告警通知
        
        Args:
            account_name: 账户名称
            remaining_traffic_gb: 剩余流量（GB）
            threshold_gb: 流量阈值（GB）
            usage_percentage: 使用百分比
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        return self.send_notification(
            'traffic_warning',
            account_name=account_name,
            remaining_traffic_gb=remaining_traffic_gb,
            threshold_gb=threshold_gb,
            usage_percentage=usage_percentage,
            **kwargs
        )
    
    def send_shutdown_notification(
        self,
        account_name: str,
        server_list: List[Dict[str, str]],
        reason: str = "流量不足",
        job_id: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送关机通知
        
        Args:
            account_name: 账户名称
            server_list: 服务器列表
            reason: 关机原因
            job_id: 任务 ID
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        return self.send_notification(
            'shutdown_notification',
            account_name=account_name,
            server_list=server_list,
            reason=reason,
            job_id=job_id,
            **kwargs
        )
    
    def send_shutdown_success(
        self,
        account_name: str,
        server_count: int,
        job_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送关机成功通知
        
        Args:
            account_name: 账户名称
            server_count: 服务器数量
            job_id: 任务 ID
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        return self.send_notification(
            'shutdown_success',
            account_name=account_name,
            server_count=server_count,
            job_id=job_id,
            **kwargs
        )
    
    def send_shutdown_delay_notification(
        self,
        account_name: str,
        delay_minutes: int,
        remaining_traffic_gb: float,
        threshold_gb: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送关机延迟通知
        
        Args:
            account_name: 账户名称
            delay_minutes: 延迟时间（分钟）
            remaining_traffic_gb: 剩余流量（GB）
            threshold_gb: 流量阈值（GB）
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        return self.send_notification(
            'shutdown_delay',
            account_name=account_name,
            delay_minutes=delay_minutes,
            remaining_traffic_gb=remaining_traffic_gb,
            threshold_gb=threshold_gb,
            **kwargs
        )
    
    def send_shutdown_failure(
        self,
        account_name: str,
        server_count: int,
        job_id: str,
        error_message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送关机失败通知
        
        Args:
            account_name: 账户名称
            server_count: 服务器数量
            job_id: 任务 ID
            error_message: 错误信息
            **kwargs: 其他参数
            
        Returns:
            发送结果
        """
        return self.send_notification(
            'shutdown_failure',
            account_name=account_name,
            server_count=server_count,
            job_id=job_id,
            error_message=error_message,
            **kwargs
        )
