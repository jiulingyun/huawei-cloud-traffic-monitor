"""
飞书通知服务测试脚本

测试通知模板和发送功能
"""
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.feishu import (
    FeishuWebhookClient,
    FeishuNotificationService,
    TrafficWarningTemplate,
    ShutdownNotificationTemplate,
    ShutdownSuccessTemplate,
    ShutdownFailureTemplate
)


def test_templates_mock():
    """测试模板渲染（模拟模式）"""
    print("\n" + "="*60)
    print("测试：通知模板渲染（模拟模式）")
    print("="*60)
    
    # 测试流量告警模板
    print("\n1. 流量告警模板")
    print("-" * 40)
    traffic_template = TrafficWarningTemplate()
    traffic_card = traffic_template.render(
        account_name="测试账户",
        remaining_traffic_gb=500.5,
        threshold_gb=1000.0,
        usage_percentage=85.5,
        server_count=5,
        region="cn-north-4"
    )
    print(f"  模板类型: 流量告警")
    print(f"  卡片标题: {traffic_card['header']['title']['content']}")
    print(f"  颜色主题: {traffic_card['header']['template']}")
    print(f"  内容长度: {len(traffic_card['elements'][0]['text']['content'])} 字符")
    
    # 测试关机通知模板
    print("\n2. 关机通知模板")
    print("-" * 40)
    shutdown_template = ShutdownNotificationTemplate()
    server_list = [
        {"name": "server-001", "id": "abc123", "ip": "192.168.1.1"},
        {"name": "server-002", "id": "def456", "ip": "192.168.1.2"},
        {"name": "server-003", "id": "ghi789", "ip": "192.168.1.3"}
    ]
    shutdown_card = shutdown_template.render(
        account_name="测试账户",
        server_list=server_list,
        reason="流量不足",
        job_id="job-123456",
        region="cn-north-4"
    )
    print(f"  模板类型: 关机通知")
    print(f"  卡片标题: {shutdown_card['header']['title']['content']}")
    print(f"  服务器数量: {len(server_list)} 台")
    
    # 测试关机成功模板
    print("\n3. 关机成功模板")
    print("-" * 40)
    success_template = ShutdownSuccessTemplate()
    success_card = success_template.render(
        account_name="测试账户",
        server_count=3,
        job_id="job-123456",
        duration_seconds=12.5
    )
    print(f"  模板类型: 关机成功")
    print(f"  卡片标题: {success_card['header']['title']['content']}")
    print(f"  颜色主题: {success_card['header']['template']}")
    
    # 测试关机失败模板
    print("\n4. 关机失败模板")
    print("-" * 40)
    failure_template = ShutdownFailureTemplate()
    failure_card = failure_template.render(
        account_name="测试账户",
        server_count=3,
        job_id="job-123456",
        error_message="网络连接超时"
    )
    print(f"  模板类型: 关机失败")
    print(f"  卡片标题: {failure_card['header']['title']['content']}")
    print(f"  颜色主题: {failure_card['header']['template']}")
    
    print("\n✅ 模拟测试完成")


def test_notification_service():
    """测试通知服务（真实 API）"""
    print("\n" + "="*60)
    print("测试：通知服务发送")
    print("="*60)
    
    # 从环境变量获取 Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ 错误: 缺少环境变量 FEISHU_WEBHOOK_URL")
        return
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    
    # 创建客户端和服务
    client = FeishuWebhookClient(webhook_url=webhook_url)
    service = FeishuNotificationService(client)
    
    try:
        # 1. 发送流量告警通知
        print("\n1. 发送流量告警通知...")
        print("-" * 40)
        result = service.send_traffic_warning(
            account_name="测试账户",
            remaining_traffic_gb=300.5,
            threshold_gb=1000.0,
            usage_percentage=70.05,
            server_count=5,
            region="cn-north-4"
        )
        print(f"  ✅ 发送成功")
        
        # 2. 发送关机通知
        print("\n2. 发送关机通知...")
        print("-" * 40)
        server_list = [
            {"name": "test-server-001", "id": "abc123"},
            {"name": "test-server-002", "id": "def456"},
            {"name": "test-server-003", "id": "ghi789"}
        ]
        result = service.send_shutdown_notification(
            account_name="测试账户",
            server_list=server_list,
            reason="流量使用已达阈值",
            job_id="job-test-123456",
            region="cn-north-4"
        )
        print(f"  ✅ 发送成功")
        
        # 3. 发送关机成功通知
        print("\n3. 发送关机成功通知...")
        print("-" * 40)
        result = service.send_shutdown_success(
            account_name="测试账户",
            server_count=3,
            job_id="job-test-123456",
            duration_seconds=15.8
        )
        print(f"  ✅ 发送成功")
        
        # 4. 发送关机失败通知
        print("\n4. 发送关机失败通知...")
        print("-" * 40)
        result = service.send_shutdown_failure(
            account_name="测试账户",
            server_count=3,
            job_id="job-test-123456",
            error_message="API 调用失败: 网络连接超时"
        )
        print(f"  ✅ 发送成功")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_traffic_warning_levels():
    """测试不同告警级别"""
    print("\n" + "="*60)
    print("测试：流量告警级别")
    print("="*60)
    
    template = TrafficWarningTemplate()
    
    # 测试不同使用率的告警级别
    test_cases = [
        (60, "blue", "🔵 提醒"),
        (75, "yellow", "🟡 中级告警"),
        (85, "orange", "🟠 高级告警"),
        (95, "red", "🔴 严重告警")
    ]
    
    for usage, expected_color, expected_level in test_cases:
        card = template.render(
            account_name="测试账户",
            remaining_traffic_gb=100.0,
            threshold_gb=1000.0,
            usage_percentage=usage
        )
        actual_color = card['header']['template']
        actual_content = card['elements'][0]['text']['content']
        
        print(f"\n使用率 {usage}%:")
        print(f"  预期颜色: {expected_color}")
        print(f"  实际颜色: {actual_color}")
        print(f"  匹配: {'✅' if actual_color == expected_color else '❌'}")
        print(f"  告警级别: {expected_level in actual_content and '✅' or '❌'}")
    
    print("\n✅ 测试完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书通知服务测试")
    parser.add_argument(
        '--real',
        action='store_true',
        help='运行真实 API 测试（需要设置环境变量 FEISHU_WEBHOOK_URL）'
    )
    parser.add_argument(
        '--levels',
        action='store_true',
        help='测试告警级别'
    )
    
    args = parser.parse_args()
    
    if args.real:
        test_notification_service()
    elif args.levels:
        test_traffic_warning_levels()
    else:
        test_templates_mock()


if __name__ == '__main__':
    main()
