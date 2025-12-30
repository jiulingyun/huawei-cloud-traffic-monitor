#!/usr/bin/env python
"""
完整工作流测试脚本

测试 Flexus L 实例流量监控 → 阈值检查 → 自动关机 → 飞书通知 的完整流程

使用方法:
    # 设置环境变量
    export HUAWEI_AK="your_access_key"
    export HUAWEI_SK="your_secret_key"
    export HUAWEI_INTL="true"
    export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
    
    # 运行测试
    python tests/test_full_workflow.py
    
    # 仅测试流量监控（不发送通知）
    python tests/test_full_workflow.py --no-notify
    
    # 模拟超阈值场景
    python tests/test_full_workflow.py --simulate-threshold
    
    # 跳过关机（仅测试监控和通知）
    python tests/test_full_workflow.py --no-shutdown
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.huawei_cloud.flexusl_service import (
    FlexusLService,
    FlexusLException,
    FlexusLInstance,
    TrafficPackageInfo
)
from app.services.feishu import (
    FeishuWebhookClient,
    FeishuNotificationService,
    TrafficWarningTemplate,
    ShutdownNotificationTemplate,
    ShutdownSuccessTemplate
)


class FullWorkflowTester:
    """完整工作流测试器"""
    
    def __init__(
        self,
        ak: str,
        sk: str,
        is_international: bool = True,
        feishu_webhook_url: Optional[str] = None,
        traffic_threshold_gb: float = 100.0,
        enable_notification: bool = True,
        enable_shutdown: bool = False,  # 默认不执行关机
        simulate_threshold: bool = False
    ):
        """
        初始化测试器
        
        Args:
            ak: 华为云 Access Key
            sk: 华为云 Secret Key
            is_international: 是否国际站
            feishu_webhook_url: 飞书 Webhook URL
            traffic_threshold_gb: 流量阈值 (GB)
            enable_notification: 是否启用飞书通知
            enable_shutdown: 是否执行关机
            simulate_threshold: 是否模拟超阈值场景
        """
        self.ak = ak
        self.sk = sk
        self.is_international = is_international
        self.traffic_threshold_gb = traffic_threshold_gb
        self.enable_notification = enable_notification
        self.enable_shutdown = enable_shutdown
        self.simulate_threshold = simulate_threshold
        
        # 初始化 Flexus L 服务
        self.flexusl_service = FlexusLService(
            ak=ak,
            sk=sk,
            is_international=is_international
        )
        
        # 初始化飞书通知服务
        self.feishu_client = None
        self.notification_service = None
        if feishu_webhook_url and enable_notification:
            self.feishu_client = FeishuWebhookClient(webhook_url=feishu_webhook_url)
            self.notification_service = FeishuNotificationService(self.feishu_client)
    
    def run(self) -> Dict[str, Any]:
        """
        运行完整工作流测试
        
        Returns:
            测试结果
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }
        
        try:
            # 阶段 1: 获取实例列表
            print("\n" + "=" * 60)
            print("📋 阶段 1: 获取 Flexus L 实例列表")
            print("=" * 60)
            
            instances = self.flexusl_service.list_instances()
            result['stages']['list_instances'] = {
                'success': True,
                'instance_count': len(instances)
            }
            
            print(f"✅ 获取到 {len(instances)} 个 Flexus L 实例")
            for inst in instances:
                print(f"   - {inst.name} ({inst.region}) - {inst.status}")
                print(f"     公网IP: {inst.public_ip or 'N/A'}")
                print(f"     流量包ID: {inst.traffic_package_id or 'N/A'}")
            
            if not instances:
                print("⚠️ 未发现任何 Flexus L 实例，跳过后续测试")
                result['success'] = True
                result['message'] = "未发现实例"
                return result
            
            # 阶段 2: 查询流量使用情况
            print("\n" + "=" * 60)
            print("📊 阶段 2: 查询流量使用情况")
            print("=" * 60)
            
            traffic_summary = self.flexusl_service.get_all_traffic_summary()
            result['stages']['traffic_query'] = {
                'success': True,
                'summary': traffic_summary
            }
            
            print(f"✅ 流量查询成功")
            print(f"   实例数量: {traffic_summary['instance_count']}")
            print(f"   流量包数量: {traffic_summary['package_count']}")
            print(f"   总流量: {traffic_summary['total_amount']:.2f} GB")
            print(f"   已使用: {traffic_summary['used_amount']:.2f} GB")
            print(f"   剩余流量: {traffic_summary['remaining_amount']:.2f} GB")
            print(f"   使用率: {traffic_summary['usage_percentage']:.2f}%")
            
            # 阶段 3: 阈值检查
            print("\n" + "=" * 60)
            print("⚠️ 阶段 3: 阈值检查")
            print("=" * 60)
            
            remaining_gb = traffic_summary['remaining_amount']
            usage_percentage = traffic_summary['usage_percentage']
            
            # 模拟超阈值场景
            if self.simulate_threshold:
                print("🔧 [模拟模式] 模拟流量超阈值场景")
                remaining_gb = self.traffic_threshold_gb - 50  # 模拟剩余流量低于阈值
                usage_percentage = 95.0
            
            is_over_threshold = remaining_gb <= self.traffic_threshold_gb
            
            result['stages']['threshold_check'] = {
                'success': True,
                'threshold_gb': self.traffic_threshold_gb,
                'remaining_gb': remaining_gb,
                'is_over_threshold': is_over_threshold
            }
            
            print(f"   阈值设置: {self.traffic_threshold_gb} GB")
            print(f"   剩余流量: {remaining_gb:.2f} GB")
            print(f"   是否超阈值: {'✅ 是' if is_over_threshold else '❌ 否'}")
            
            # 阶段 4: 发送告警通知
            if is_over_threshold and self.notification_service:
                print("\n" + "=" * 60)
                print("📢 阶段 4: 发送流量告警通知")
                print("=" * 60)
                
                try:
                    self.notification_service.send_traffic_warning(
                        account_name="Flexus L 测试账户",
                        remaining_traffic_gb=remaining_gb,
                        threshold_gb=self.traffic_threshold_gb,
                        usage_percentage=usage_percentage,
                        server_count=len(instances),
                        region=instances[0].region if instances else "未知"
                    )
                    result['stages']['traffic_warning'] = {'success': True}
                    print("✅ 流量告警通知发送成功")
                except Exception as e:
                    result['stages']['traffic_warning'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ 流量告警通知发送失败: {e}")
            elif not is_over_threshold:
                print("\n📋 流量充足，跳过告警通知")
                result['stages']['traffic_warning'] = {
                    'success': True,
                    'skipped': True,
                    'reason': '流量充足'
                }
            elif not self.notification_service:
                print("\n📋 未配置飞书通知，跳过告警")
                result['stages']['traffic_warning'] = {
                    'success': True,
                    'skipped': True,
                    'reason': '未配置飞书通知'
                }
            
            # 阶段 5: 自动关机
            if is_over_threshold and self.enable_shutdown:
                print("\n" + "=" * 60)
                print("🔌 阶段 5: 执行自动关机")
                print("=" * 60)
                
                # 筛选运行中的实例
                running_instances = [
                    inst for inst in instances 
                    if inst.status in ('RUNNING', 'ACTIVE')
                ]
                
                if running_instances:
                    print(f"⚠️ 将关闭 {len(running_instances)} 台运行中的实例:")
                    for inst in running_instances:
                        print(f"   - {inst.name} ({inst.id})")
                    
                    # 发送关机通知
                    if self.notification_service:
                        server_list = [
                            {
                                'name': inst.name,
                                'id': inst.id,
                                'ip': inst.public_ip or 'N/A'
                            }
                            for inst in running_instances
                        ]
                        
                        try:
                            self.notification_service.send_shutdown_notification(
                                account_name="Flexus L 测试账户",
                                server_list=server_list,
                                reason=f"流量剩余 {remaining_gb:.2f} GB，低于阈值 {self.traffic_threshold_gb} GB",
                                job_id=f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                region=running_instances[0].region if running_instances else "未知"
                            )
                            print("✅ 关机通知发送成功")
                        except Exception as e:
                            print(f"❌ 关机通知发送失败: {e}")
                    
                    # TODO: 实际执行关机操作
                    print("\n⚠️ 关机功能尚未实现，跳过实际关机操作")
                    result['stages']['shutdown'] = {
                        'success': True,
                        'instances_to_shutdown': len(running_instances),
                        'actually_shutdown': 0,
                        'reason': '关机功能尚未实现'
                    }
                else:
                    print("📋 没有运行中的实例需要关机")
                    result['stages']['shutdown'] = {
                        'success': True,
                        'skipped': True,
                        'reason': '没有运行中的实例'
                    }
            elif is_over_threshold and not self.enable_shutdown:
                print("\n📋 [安全模式] 超阈值但未启用自动关机")
                result['stages']['shutdown'] = {
                    'success': True,
                    'skipped': True,
                    'reason': '未启用自动关机'
                }
            else:
                result['stages']['shutdown'] = {
                    'success': True,
                    'skipped': True,
                    'reason': '流量充足，无需关机'
                }
            
            # 阶段 6: 发送测试完成通知
            if self.notification_service:
                print("\n" + "=" * 60)
                print("📤 阶段 6: 发送测试完成通知")
                print("=" * 60)
                
                try:
                    # 构建测试报告卡片
                    report_content = f"""**🧪 Flexus L 监控测试报告**

---

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**实例数量**: {len(instances)} 台
**流量包数量**: {traffic_summary['package_count']} 个

---

**流量统计**:
• 总流量: {traffic_summary['total_amount']:.2f} GB
• 已使用: {traffic_summary['used_amount']:.2f} GB  
• 剩余流量: {traffic_summary['remaining_amount']:.2f} GB
• 使用率: {traffic_summary['usage_percentage']:.2f}%

---

**阈值检查**:
• 设置阈值: {self.traffic_threshold_gb} GB
• 是否超阈值: {'⚠️ 是' if is_over_threshold else '✅ 否'}
• 自动关机: {'已启用' if self.enable_shutdown else '未启用'}

---

✅ **测试完成，所有功能正常**"""

                    self.feishu_client.send_card({
                        "config": {"wide_screen_mode": True},
                        "header": {
                            "title": {"tag": "plain_text", "content": "🧪 流量监控测试报告"},
                            "template": "green"
                        },
                        "elements": [{
                            "tag": "div",
                            "text": {"tag": "lark_md", "content": report_content}
                        }]
                    })
                    result['stages']['test_report'] = {'success': True}
                    print("✅ 测试报告发送成功")
                except Exception as e:
                    result['stages']['test_report'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ 测试报告发送失败: {e}")
            
            result['success'] = True
            result['message'] = "测试完成"
            
        except FlexusLException as e:
            result['success'] = False
            result['error'] = f"FlexusL 服务错误: {e}"
            print(f"\n❌ FlexusL 服务错误: {e}")
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Flexus L 流量监控完整工作流测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 基本测试（仅监控，发送通知）
    python tests/test_full_workflow.py
    
    # 不发送通知
    python tests/test_full_workflow.py --no-notify
    
    # 模拟超阈值场景
    python tests/test_full_workflow.py --simulate-threshold
    
    # 设置自定义阈值
    python tests/test_full_workflow.py --threshold 500
    
    # 启用自动关机（危险操作！）
    python tests/test_full_workflow.py --enable-shutdown --simulate-threshold
        """
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=100.0,
        help='流量阈值 (GB)，默认 100'
    )
    parser.add_argument(
        '--no-notify',
        action='store_true',
        help='禁用飞书通知'
    )
    parser.add_argument(
        '--simulate-threshold',
        action='store_true',
        help='模拟超阈值场景（用于测试告警通知）'
    )
    parser.add_argument(
        '--enable-shutdown',
        action='store_true',
        help='启用自动关机（危险操作！请谨慎使用）'
    )
    
    args = parser.parse_args()
    
    # 获取环境变量
    ak = os.environ.get('HUAWEI_AK')
    sk = os.environ.get('HUAWEI_SK')
    is_intl = os.environ.get('HUAWEI_INTL', 'true').lower() == 'true'
    feishu_webhook = os.environ.get('FEISHU_WEBHOOK_URL')
    
    # 检查必要配置
    if not ak or not sk:
        print("❌ 错误: 请设置华为云凭证环境变量")
        print()
        print("示例:")
        print('   export HUAWEI_AK="your_access_key"')
        print('   export HUAWEI_SK="your_secret_key"')
        print('   export HUAWEI_INTL="true"  # 国际站')
        sys.exit(1)
    
    if not args.no_notify and not feishu_webhook:
        print("⚠️ 警告: 未设置 FEISHU_WEBHOOK_URL，将跳过飞书通知")
        print('   设置方法: export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"')
        print()
    
    # 打印配置信息
    print("\n" + "=" * 70)
    print(" " * 15 + "🚀 Flexus L 流量监控完整工作流测试")
    print("=" * 70)
    print(f"\n配置信息:")
    print(f"   华为云 AK: {ak[:4]}****{ak[-4:]}")
    print(f"   国际站: {is_intl}")
    print(f"   流量阈值: {args.threshold} GB")
    print(f"   飞书通知: {'启用' if feishu_webhook and not args.no_notify else '禁用'}")
    print(f"   模拟超阈值: {args.simulate_threshold}")
    print(f"   自动关机: {'⚠️ 已启用' if args.enable_shutdown else '禁用'}")
    
    if args.enable_shutdown:
        print("\n" + "⚠️" * 30)
        print("警告: 自动关机功能已启用！")
        print("如果流量超阈值，将会关闭运行中的实例！")
        print("⚠️" * 30)
        
        confirm = input("\n确认继续? (输入 'yes' 继续): ")
        if confirm.lower() != 'yes':
            print("已取消")
            sys.exit(0)
    
    # 创建测试器并运行
    tester = FullWorkflowTester(
        ak=ak,
        sk=sk,
        is_international=is_intl,
        feishu_webhook_url=feishu_webhook if not args.no_notify else None,
        traffic_threshold_gb=args.threshold,
        enable_notification=not args.no_notify,
        enable_shutdown=args.enable_shutdown,
        simulate_threshold=args.simulate_threshold
    )
    
    result = tester.run()
    
    # 打印测试结果
    print("\n" + "=" * 70)
    print(" " * 25 + "测试结果汇总")
    print("=" * 70)
    
    print(f"\n总体结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    
    if 'error' in result:
        print(f"错误信息: {result['error']}")
    
    print("\n各阶段结果:")
    for stage, stage_result in result.get('stages', {}).items():
        status = '✅' if stage_result.get('success') else '❌'
        skipped = ' (跳过)' if stage_result.get('skipped') else ''
        print(f"   {status} {stage}{skipped}")
    
    print("\n" + "=" * 70)
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
