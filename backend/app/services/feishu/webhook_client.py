"""
飞书 Webhook 客户端

API 文档: https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN
"""
import requests
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from loguru import logger


class FeishuException(Exception):
    """飞书 API 异常"""
    pass


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"  # 文本消息
    POST = "post"  # 富文本消息
    INTERACTIVE = "interactive"  # 交互式消息
    SHARE_CHAT = "share_chat"  # 分享群名片


class FeishuWebhookClient:
    """飞书 Webhook 客户端"""
    
    def __init__(
        self,
        webhook_url: str,
        retry_times: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 10
    ):
        """
        初始化飞书 Webhook 客户端
        
        Args:
            webhook_url: Webhook URL
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
            timeout: 请求超时时间（秒）
        """
        if not webhook_url:
            raise ValueError("webhook_url 不能为空")
        
        self.webhook_url = webhook_url
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        logger.info(
            f"初始化飞书 Webhook 客户端: "
            f"url={webhook_url[:50]}..., retry_times={retry_times}"
        )
    
    def send_message(
        self,
        msg_type: MessageType,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送消息
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            
        Returns:
            响应结果
            
        Raises:
            FeishuException: 发送失败
        """
        # 构建请求体
        payload = {
            "msg_type": msg_type.value,
            "content": content
        }
        
        logger.info(f"发送飞书消息: type={msg_type.value}")
        
        # 重试机制
        last_error = None
        for attempt in range(self.retry_times):
            try:
                # 发送请求
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                # 解析响应
                result = response.json()
                
                # 检查响应状态
                if result.get('code') == 0:
                    logger.info("飞书消息发送成功")
                    return result
                else:
                    error_msg = result.get('msg', '未知错误')
                    logger.error(
                        f"飞书消息发送失败: code={result.get('code')}, "
                        f"msg={error_msg}"
                    )
                    raise FeishuException(f"发送失败: {error_msg}")
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(
                    f"飞书消息发送失败 (尝试 {attempt + 1}/{self.retry_times}): {e}"
                )
                
                # 如果还有重试机会，等待后重试
                if attempt < self.retry_times - 1:
                    time.sleep(self.retry_delay)
                    continue
                
            except Exception as e:
                logger.error(f"飞书消息发送异常: {e}")
                raise FeishuException(f"发送异常: {e}")
        
        # 所有重试都失败
        raise FeishuException(f"发送失败（已重试 {self.retry_times} 次）: {last_error}")
    
    def send_text(self, text: str) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            text: 文本内容
            
        Returns:
            响应结果
        """
        content = {"text": text}
        return self.send_message(MessageType.TEXT, content)
    
    def send_markdown(
        self,
        title: str,
        content: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        发送富文本消息（Markdown）
        
        Args:
            title: 标题
            content: 富文本内容（二维数组）
            
        Returns:
            响应结果
            
        Example:
            content = [
                [{"tag": "text", "text": "项目有更新: "}],
                [{"tag": "a", "text": "请查看", "href": "https://example.com"}]
            ]
        """
        post_content = {
            "zh_cn": {
                "title": title,
                "content": content
            }
        }
        return self.send_message(MessageType.POST, {"post": post_content})
    
    def send_card(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送交互式卡片消息
        
        Args:
            card: 卡片内容
            
        Returns:
            响应结果
        """
        return self.send_message(MessageType.INTERACTIVE, {"card": card})
    
    def create_text_card(
        self,
        title: str,
        content: str,
        color: str = "blue"
    ) -> Dict[str, Any]:
        """
        创建简单的文本卡片
        
        Args:
            title: 卡片标题
            content: 卡片内容
            color: 标题颜色（blue/wathet/turquoise/green/yellow/orange/red/carmine/violet/purple/indigo/grey）
            
        Returns:
            卡片配置
        """
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
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
    
    def create_info_card(
        self,
        title: str,
        fields: List[Dict[str, str]],
        color: str = "blue"
    ) -> Dict[str, Any]:
        """
        创建信息卡片（键值对形式）
        
        Args:
            title: 卡片标题
            fields: 字段列表 [{"key": "字段名", "value": "字段值"}, ...]
            color: 标题颜色
            
        Returns:
            卡片配置
        """
        # 构建字段元素
        field_elements = []
        for field in fields:
            field_elements.append({
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{field['key']}**\n{field['value']}"
                        }
                    }
                ]
            })
        
        return {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": color
            },
            "elements": field_elements
        }
    
    def send_text_card(
        self,
        title: str,
        content: str,
        color: str = "blue"
    ) -> Dict[str, Any]:
        """
        发送简单文本卡片
        
        Args:
            title: 卡片标题
            content: 卡片内容
            color: 标题颜色
            
        Returns:
            响应结果
        """
        card = self.create_text_card(title, content, color)
        return self.send_card(card)
    
    def send_info_card(
        self,
        title: str,
        fields: List[Dict[str, str]],
        color: str = "blue"
    ) -> Dict[str, Any]:
        """
        发送信息卡片
        
        Args:
            title: 卡片标题
            fields: 字段列表
            color: 标题颜色
            
        Returns:
            响应结果
        """
        card = self.create_info_card(title, fields, color)
        return self.send_card(card)
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否可用
        """
        try:
            # 发送测试消息
            self.send_text("飞书 Webhook 健康检查")
            return True
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
