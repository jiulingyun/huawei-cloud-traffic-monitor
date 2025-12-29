"""
飞书 Webhook 客户端测试脚本

测试飞书消息发送、卡片、重试机制等功能
"""
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.feishu import FeishuWebhookClient, MessageType


def test_webhook_mock():
    """测试 Webhook 客户端（模拟模式）"""
    print("\n" + "="*60)
    print("测试：飞书 Webhook 客户端（模拟模式）")
    print("="*60)
    
    # 使用假 Webhook URL
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test-webhook"
    
    print(f"\nWebhook URL: {webhook_url}")
    
    # 创建客户端
    client = FeishuWebhookClient(
        webhook_url=webhook_url,
        retry_times=3,
        retry_delay=1.0,
        timeout=10
    )
    
    print(f"\n客户端配置:")
    print(f"  重试次数: {client.retry_times}")
    print(f"  重试延迟: {client.retry_delay}s")
    print(f"  超时时间: {client.timeout}s")
    
    # 创建文本卡片
    print(f"\n创建文本卡片...")
    text_card = client.create_text_card(
        title="服务器监控告警",
        content="流量包即将用尽，请及时处理",
        color="red"
    )
    print(f"  卡片类型: 文本卡片")
    print(f"  标题: 服务器监控告警")
    print(f"  颜色: red")
    
    # 创建信息卡片
    print(f"\n创建信息卡片...")
    info_card = client.create_info_card(
        title="服务器信息",
        fields=[
            {"key": "服务器名称", "value": "server-001"},
            {"key": "IP 地址", "value": "192.168.1.100"},
            {"key": "流量剩余", "value": "500 GB"}
        ],
        color="blue"
    )
    print(f"  卡片类型: 信息卡片")
    print(f"  字段数量: 3")
    
    print("\n✅ 模拟测试完成")


def test_send_text():
    """测试发送文本消息（真实 API）"""
    print("\n" + "="*60)
    print("测试：发送文本消息")
    print("="*60)
    
    # 从环境变量获取 Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ 错误: 缺少环境变量 FEISHU_WEBHOOK_URL")
        print("   请设置飞书 Webhook URL")
        return
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    
    # 创建客户端
    client = FeishuWebhookClient(webhook_url=webhook_url)
    
    try:
        # 发送文本消息
        print(f"\n发送文本消息...")
        result = client.send_text("【测试】飞书 Webhook 客户端测试消息")
        print(f"  响应: {result}")
        
        print("\n✅ 测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_send_card():
    """测试发送卡片消息（真实 API）"""
    print("\n" + "="*60)
    print("测试：发送卡片消息")
    print("="*60)
    
    # 从环境变量获取 Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ 错误: 缺少环境变量 FEISHU_WEBHOOK_URL")
        return
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    
    # 创建客户端
    client = FeishuWebhookClient(webhook_url=webhook_url)
    
    try:
        # 发送文本卡片
        print(f"\n发送文本卡片...")
        result = client.send_text_card(
            title="流量监控告警",
            content="**账户**: 测试账户\n**剩余流量**: 500 GB\n**阈值**: 1000 GB\n\n流量使用已达到阈值，请注意！",
            color="orange"
        )
        print(f"  文本卡片发送成功")
        
        # 发送信息卡片
        print(f"\n发送信息卡片...")
        result = client.send_info_card(
            title="服务器状态",
            fields=[
                {"key": "服务器名称", "value": "test-server-001"},
                {"key": "IP 地址", "value": "192.168.1.100"},
                {"key": "状态", "value": "运行中"},
                {"key": "流量剩余", "value": "500 GB"},
                {"key": "流量阈值", "value": "1000 GB"},
                {"key": "使用率", "value": "50%"}
            ],
            color="blue"
        )
        print(f"  信息卡片发送成功")
        
        print("\n✅ 测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_retry_mechanism():
    """测试重试机制"""
    print("\n" + "="*60)
    print("测试：重试机制")
    print("="*60)
    
    # 使用一个无效的 Webhook URL 来测试重试
    invalid_url = "https://invalid-webhook-url.example.com/test"
    
    print(f"\n使用无效 URL 测试重试机制: {invalid_url}")
    
    # 创建客户端（减少重试次数和延迟以加快测试）
    client = FeishuWebhookClient(
        webhook_url=invalid_url,
        retry_times=3,
        retry_delay=0.5,
        timeout=2
    )
    
    try:
        print(f"\n发送消息（预期会失败）...")
        client.send_text("测试消息")
        print("❌ 意外：消息发送成功了")
        
    except Exception as e:
        print(f"✅ 符合预期：消息发送失败")
        print(f"  错误信息: {e}")
        print(f"  已执行 {client.retry_times} 次重试")


def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试：健康检查")
    print("="*60)
    
    # 从环境变量获取 Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ 错误: 缺少环境变量 FEISHU_WEBHOOK_URL")
        return
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    
    # 创建客户端
    client = FeishuWebhookClient(webhook_url=webhook_url)
    
    try:
        print(f"\n执行健康检查...")
        is_healthy = client.health_check()
        
        if is_healthy:
            print(f"✅ 健康检查通过")
        else:
            print(f"❌ 健康检查失败")
        
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书 Webhook 客户端测试")
    parser.add_argument(
        '--text',
        action='store_true',
        help='测试发送文本消息（需要设置环境变量 FEISHU_WEBHOOK_URL）'
    )
    parser.add_argument(
        '--card',
        action='store_true',
        help='测试发送卡片消息（需要设置环境变量 FEISHU_WEBHOOK_URL）'
    )
    parser.add_argument(
        '--retry',
        action='store_true',
        help='测试重试机制'
    )
    parser.add_argument(
        '--health',
        action='store_true',
        help='测试健康检查（需要设置环境变量 FEISHU_WEBHOOK_URL）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='运行所有真实 API 测试（需要设置环境变量 FEISHU_WEBHOOK_URL）'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，运行模拟测试
    if not any([args.text, args.card, args.retry, args.health, args.all]):
        test_webhook_mock()
        return
    
    # 运行指定的测试
    if args.text or args.all:
        test_send_text()
    
    if args.card or args.all:
        test_send_card()
    
    if args.retry:
        test_retry_mechanism()
    
    if args.health or args.all:
        test_health_check()


if __name__ == '__main__':
    main()
