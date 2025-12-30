#!/usr/bin/env python
"""
Flexus L 服务测试脚本

测试 Flexus L 实例查询和流量包查询功能

使用方法:
    # 真实 API 调用测试
    export HUAWEI_AK="your_access_key"
    export HUAWEI_SK="your_secret_key"
    export HUAWEI_INTL="true"  # 国际站
    python tests/test_flexusl_service.py
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.huawei_cloud.flexusl_service import (
    FlexusLService,
    FlexusLException,
    FlexusLInstance,
    TrafficPackageInfo
)


def test_real_api():
    """真实 API 调用测试"""
    print("\n" + "=" * 60)
    print("🚀 Flexus L 服务真实 API 测试")
    print("=" * 60)
    
    # 获取配置
    ak = os.environ.get('HUAWEI_AK')
    sk = os.environ.get('HUAWEI_SK')
    is_intl = os.environ.get('HUAWEI_INTL', 'true').lower() == 'true'
    
    if not ak or not sk:
        print("❌ 错误: 请设置 HUAWEI_AK 和 HUAWEI_SK 环境变量")
        print("\n示例:")
        print('   export HUAWEI_AK="your_access_key"')
        print('   export HUAWEI_SK="your_secret_key"')
        print('   export HUAWEI_INTL="true"  # 国际站')
        return False
    
    print(f"\n配置信息:")
    print(f"   AK: {ak[:4]}****{ak[-4:]}")
    print(f"   国际站: {is_intl}")
    
    try:
        # 初始化服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            is_international=is_intl
        )
        print(f"✅ Flexus L 服务初始化成功")
        print(f"   Config 端点: {service.config_endpoint}")
        print(f"   BSS 端点: {service.bss_client.endpoint}")
        
        # 测试 1: 获取 domain_id
        print(f"\n🔍 测试 1: 获取账户 domain_id")
        domain_id = service.get_domain_id()
        print(f"✅ 获取 domain_id 成功: {domain_id}")
        
        # 测试 2: 查询 Flexus L 实例列表
        print(f"\n🔍 测试 2: 查询 Flexus L 实例列表")
        instances = service.list_instances()
        print(f"✅ 获取到 {len(instances)} 个 Flexus L 实例")
        
        for i, inst in enumerate(instances, 1):
            print(f"\n   实例 {i}:")
            print(f"      ID: {inst.id}")
            print(f"      名称: {inst.name}")
            print(f"      区域: {inst.region}")
            print(f"      状态: {inst.status}")
            print(f"      公网IP: {inst.public_ip}")
            print(f"      流量包ID: {inst.traffic_package_id}")
        
        if not instances:
            print("\n⚠️ 未发现任何 Flexus L 实例")
            return True
        
        # 测试 3: 获取流量包 ID
        print(f"\n🔍 测试 3: 提取流量包 ID")
        traffic_ids = service.get_traffic_package_ids()
        print(f"✅ 获取到 {len(traffic_ids)} 个流量包 ID")
        
        for tid in traffic_ids:
            print(f"   - {tid}")
        
        if not traffic_ids:
            print("\n⚠️ 实例中未发现流量包 ID，可能需要从其他字段获取")
            # 尝试直接查询流量汇总
            print(f"\n🔍 测试 4: 获取流量汇总 (跳过)")
            return True
        
        # 测试 4: 查询流量使用情况
        print(f"\n🔍 测试 4: 查询流量使用情况")
        packages = service.query_traffic_usage(traffic_ids)
        print(f"✅ 获取到 {len(packages)} 个流量包使用信息")
        
        for pkg in packages:
            print(f"\n   流量包:")
            print(f"      ID: {pkg.resource_id}")
            print(f"      类型: {pkg.resource_type_name}")
            print(f"      总量: {pkg.total_amount} {pkg.measure_unit}")
            print(f"      已用: {pkg.used_amount} {pkg.measure_unit}")
            print(f"      剩余: {pkg.remaining_amount} {pkg.measure_unit}")
            print(f"      使用率: {pkg.usage_percentage:.1f}%")
        
        # 测试 5: 获取完整汇总
        print(f"\n🔍 测试 5: 获取流量汇总")
        summary = service.get_all_traffic_summary()
        print(f"✅ 流量汇总:")
        print(f"   实例数量: {summary['instance_count']}")
        print(f"   流量包数量: {summary['package_count']}")
        print(f"   总流量: {summary['total_amount']} GB")
        print(f"   已用流量: {summary['used_amount']} GB")
        print(f"   剩余流量: {summary['remaining_amount']} GB")
        print(f"   使用率: {summary['usage_percentage']:.2f}%")
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        return True
        
    except FlexusLException as e:
        print(f"\n❌ Flexus L 服务错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_real_api()
    sys.exit(0 if success else 1)
