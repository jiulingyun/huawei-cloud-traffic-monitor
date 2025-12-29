"""
监控工作流测试脚本

测试完整的监控业务流程
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.monitor_workflow import MonitorWorkflowExecutor


def test_workflow_init():
    """测试工作流初始化"""
    print("\n" + "="*60)
    print("测试：工作流执行器初始化")
    print("="*60)
    
    # 测试禁用通知
    print("\n1. 禁用通知模式")
    print("-" * 40)
    executor1 = MonitorWorkflowExecutor(
        feishu_webhook_url=None,
        enable_notifications=False,
        enable_auto_shutdown=True
    )
    print(f"  通知启用: {executor1.enable_notifications}")
    print(f"  自动关机启用: {executor1.enable_auto_shutdown}")
    print(f"  通知服务: {executor1.notification_service is not None}")
    
    # 测试启用通知
    print("\n2. 启用通知模式")
    print("-" * 40)
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test"
    executor2 = MonitorWorkflowExecutor(
        feishu_webhook_url=webhook_url,
        enable_notifications=True,
        enable_auto_shutdown=True
    )
    print(f"  通知启用: {executor2.enable_notifications}")
    print(f"  自动关机启用: {executor2.enable_auto_shutdown}")
    print(f"  通知服务: {executor2.notification_service is not None}")
    
    # 测试禁用自动关机
    print("\n3. 禁用自动关机模式")
    print("-" * 40)
    executor3 = MonitorWorkflowExecutor(
        feishu_webhook_url=webhook_url,
        enable_notifications=True,
        enable_auto_shutdown=False
    )
    print(f"  通知启用: {executor3.enable_notifications}")
    print(f"  自动关机启用: {executor3.enable_auto_shutdown}")
    
    print("\n✅ 测试完成")


def test_workflow_structure():
    """测试工作流结构"""
    print("\n" + "="*60)
    print("测试：工作流结构")
    print("="*60)
    
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test"
    executor = MonitorWorkflowExecutor(
        feishu_webhook_url=webhook_url,
        enable_notifications=True,
        enable_auto_shutdown=True
    )
    
    # 检查方法存在
    print("\n检查核心方法:")
    methods = [
        'execute_monitor_workflow',
        '_execute_shutdown_workflow'
    ]
    
    for method_name in methods:
        has_method = hasattr(executor, method_name)
        print(f"  {method_name}: {'✅' if has_method else '❌'}")
    
    print("\n检查服务组件:")
    components = [
        ('feishu_client', executor.feishu_client),
        ('notification_service', executor.notification_service)
    ]
    
    for comp_name, comp in components:
        print(f"  {comp_name}: {'✅' if comp is not None else '❌'}")
    
    print("\n✅ 测试完成")


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" "*20 + "监控工作流测试")
    print("="*70)
    
    test_workflow_init()
    test_workflow_structure()
    
    print("\n" + "="*70)
    print(" "*25 + "所有测试完成")
    print("="*70)


if __name__ == '__main__':
    main()
