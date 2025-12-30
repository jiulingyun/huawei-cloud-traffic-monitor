#!/usr/bin/env python3
"""
测试流量包查询服务 (Flexus L 实例)

使用方法：
1. 离线测试（默认）：
   python test_traffic_service.py

2. 真实联调（自动发现流量包，无需手动配置流量包 ID）：
   export HUAWEI_AK="your_access_key"
   export HUAWEI_SK="your_secret_key"
   export HUAWEI_INTL="false"  # 可选，是否国际站，默认 false
   python test_traffic_service.py --real
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.huawei_cloud.traffic_service import TrafficService, TrafficPackage
from app.services.huawei_cloud.bss_client import HuaweiCloudBSSClient


def test_traffic_package_model():
    """测试流量包模型 (Flexus L API 响应格式)"""
    print("=" * 50)
    print("测试流量包模型 (Flexus L 格式)")
    print("=" * 50)
    
    # 模拟 Flexus L API 响应数据
    test_data = {
        'free_resource_id': 'test_resource_id_123',
        'free_resource_type_name': '轻量BGP流量套餐包',
        'quota_reuse_cycle': 4,
        'quota_reuse_cycle_type': 2,
        'usage_type_name': '上行流量',
        'start_time': '2024-12-25T08:00:00Z',
        'end_time': '2025-01-25T16:00:00Z',
        'amount': 649.5,            # 流量剩余额度
        'original_amount': 1000.0,  # 流量原始额度
        'measure_id': 10
    }
    
    package = TrafficPackage(test_data)
    
    print(f"✅ 流量包模型创建成功")
    print(f"   Resource ID: {package.resource_id}")
    print(f"   类型: {package.resource_type_name}")
    print(f"   总流量: {package.total_amount} {package.measure_unit}")
    print(f"   已用流量: {package.used_amount} {package.measure_unit}")
    print(f"   剩余流量: {package.remaining_amount} {package.measure_unit}")
    print(f"   使用率: {package.usage_percentage:.2f}%")
    
    # 验证计算
    assert package.total_amount == 1000.0
    assert package.remaining_amount == 649.5
    assert package.used_amount == 350.5  # total - remaining
    assert 35 <= package.usage_percentage <= 35.1
    
    # 测试 to_dict
    data_dict = package.to_dict()
    print(f"✅ 转换为字典: {len(data_dict)} 个字段")
    assert 'resource_id' in data_dict
    assert 'remaining_amount' in data_dict
    assert 'measure_unit' in data_dict
    
    print("\n✅ 流量包模型测试通过！\n")


def test_traffic_service_init():
    """测试流量服务初始化"""
    print("=" * 50)
    print("测试流量服务初始化")
    print("=" * 50)
    
    # 创建 BSS 客户端
    client = HuaweiCloudBSSClient(
        access_key="TEST_AK",
        secret_key="TEST_SK",
        is_international=False
    )
    
    # 创建流量服务
    service = TrafficService(client)
    
    print(f"✅ 流量服务初始化成功")
    print(f"   Client: {type(service.client).__name__}")
    print(f"   BSS Endpoint: {client.endpoint}")
    print(f"   API Endpoint: {service.TRAFFIC_API_ENDPOINT}")
    
    assert service.client is client
    assert service.TRAFFIC_API_ENDPOINT == '/v2/payments/free-resources/usages/details/query'
    assert client.endpoint == 'https://bss.myhuaweicloud.com'
    
    print("\n✅ 流量服务初始化测试通过！\n")


def test_parse_response():
    """测试响应解析 (Flexus L API 格式)"""
    print("=" * 50)
    print("测试响应解析 (Flexus L 格式)")
    print("=" * 50)
    
    client = HuaweiCloudBSSClient("TEST_AK", "TEST_SK")
    service = TrafficService(client)
    
    # 模拟 Flexus L API 响应
    mock_response = {
        'free_resources': [
            {
                'free_resource_id': 'resource_1',
                'free_resource_type_name': '轻量BGP流量套餐包',
                'usage_type_name': '上行流量',
                'amount': 400.0,          # 剩余
                'original_amount': 500.0,  # 原始
                'measure_id': 10,
                'start_time': '2024-01-01T00:00:00Z',
                'end_time': '2024-12-31T23:59:59Z'
            },
            {
                'free_resource_id': 'resource_2',
                'free_resource_type_name': '轻量BGP流量套餐包',
                'usage_type_name': '上行流量',
                'amount': 250.0,          # 剩余
                'original_amount': 300.0,  # 原始
                'measure_id': 10,
                'start_time': '2024-01-01T00:00:00Z',
                'end_time': '2024-12-31T23:59:59Z'
            }
        ]
    }
    
    packages = service._parse_response(mock_response)
    
    print(f"✅ 响应解析成功: {len(packages)} 个流量包")
    
    assert len(packages) == 2
    assert packages[0].resource_id == 'resource_1'
    assert packages[0].remaining_amount == 400.0
    assert packages[0].total_amount == 500.0
    assert packages[0].used_amount == 100.0  # 500 - 400
    assert packages[1].resource_id == 'resource_2'
    assert packages[1].remaining_amount == 250.0
    
    print(f"   流量包1: {packages[0].remaining_amount}{packages[0].measure_unit} 剩余")
    print(f"   流量包2: {packages[1].remaining_amount}{packages[1].measure_unit} 剩余")
    
    print("\n✅ 响应解析测试通过！\n")


def test_traffic_summary():
    """测试流量汇总 (Flexus L 格式)"""
    print("=" * 50)
    print("测试流量汇总（模拟）")
    print("=" * 50)
    
    # 创建多个流量包 (Flexus L 格式)
    packages_data = [
        {
            'free_resource_id': f'resource_{i}',
            'free_resource_type_name': '轻量BGP流量套餐包',
            'usage_type_name': '上行流量',
            'amount': 70.0 * i,         # 剩余 = 70, 140, 210
            'original_amount': 100.0 * i,  # 原始 = 100, 200, 300
            'measure_id': 10,
            'start_time': '2024-01-01T00:00:00Z',
            'end_time': '2024-12-31T23:59:59Z'
        }
        for i in range(1, 4)
    ]
    
    packages = [TrafficPackage(data) for data in packages_data]
    
    # 计算汇总
    total = sum(pkg.total_amount for pkg in packages)
    used = sum(pkg.used_amount for pkg in packages)
    remaining = sum(pkg.remaining_amount for pkg in packages)
    
    print(f"✅ 流量汇总计算成功")
    print(f"   流量包数量: {len(packages)}")
    print(f"   总流量: {total} GB")
    print(f"   已用流量: {used} GB")
    print(f"   剩余流量: {remaining} GB")
    print(f"   使用率: {(used/total*100):.2f}%")
    
    # 验证计算
    assert total == 600.0  # 100 + 200 + 300
    assert remaining == 420.0  # 70 + 140 + 210
    assert used == 180.0   # total - remaining = 600 - 420
    
    print("\n✅ 流量汇总测试通过！\n")


def test_threshold_check():
    """测试阈值检查逻辑"""
    print("=" * 50)
    print("测试阈值检查逻辑")
    print("=" * 50)
    
    # 模拟不同的流量情况
    test_cases = [
        {'remaining': 500.0, 'threshold': 100.0, 'expected': False},  # 正常
        {'remaining': 50.0, 'threshold': 100.0, 'expected': True},    # 低于阈值
        {'remaining': 100.0, 'threshold': 100.0, 'expected': False},  # 刚好等于
        {'remaining': 99.9, 'threshold': 100.0, 'expected': True},    # 略低于
    ]
    
    for i, case in enumerate(test_cases, 1):
        remaining = case['remaining']
        threshold = case['threshold']
        expected = case['expected']
        
        is_below = remaining < threshold
        
        status = "⚠️ 低于阈值" if is_below else "✅ 正常"
        print(f"   测试{i}: 剩余={remaining}GB, 阈值={threshold}GB => {status}")
        
        assert is_below == expected, f"测试{i}失败"
    
    print("\n✅ 阈值检查逻辑测试通过！\n")


def test_real_api_call():
    """真实 API 调用测试 (自动发现流量包)"""
    print("=" * 50)
    print("真实 API 调用测试 (自动发现模式)")
    print("=" * 50)
    
    # 读取环境变量
    ak = os.environ.get('HUAWEI_AK')
    sk = os.environ.get('HUAWEI_SK')
    is_intl = os.environ.get('HUAWEI_INTL', 'false').lower() == 'true'
    
    # 检查必要的环境变量
    if not ak or not sk:
        print("❌ 错误: 请设置 HUAWEI_AK 和 HUAWEI_SK 环境变量")
        print("\n示例:")
        print('   export HUAWEI_AK="your_access_key"')
        print('   export HUAWEI_SK="your_secret_key"')
        return False
    
    # 显示配置信息
    print(f"\n配置信息:")
    print(f"   AK: {ak[:4]}****{ak[-4:]}")
    print(f"   国际站: {is_intl}")
    print()
    
    try:
        # 创建 BSS 客户端
        client = HuaweiCloudBSSClient(
            access_key=ak,
            secret_key=sk,
            is_international=is_intl
        )
        print(f"✅ BSS 客户端创建成功")
        print(f"   Endpoint: {client.endpoint}")
        
        # 创建流量服务
        service = TrafficService(client)
        print("✅ 流量服务初始化成功")
        print()
        
        # 测试 1: 自动发现流量包
        print("🔍 测试 1: 自动发现 Flexus L 流量包")
        discovered_packages = service.discover_traffic_packages()
        print(f"✅ 发现 {len(discovered_packages)} 个流量包")
        
        if discovered_packages:
            print("\n   发现的流量包:")
            for i, pkg in enumerate(discovered_packages[:5], 1):  # 最多显示5个
                print(f"   {i}. ID: {pkg.get('free_resource_id')}")
                print(f"      类型: {pkg.get('free_resource_type_name')}")
                print(f"      产品: {pkg.get('product_name', 'N/A')}")
            if len(discovered_packages) > 5:
                print(f"   ... 还有 {len(discovered_packages) - 5} 个流量包")
        print()
        
        # 测试 2: 获取所有流量包的资源 ID
        print("🔍 测试 2: 获取流量包资源 ID")
        resource_ids = service.get_all_traffic_resource_ids()
        print(f"✅ 获取到 {len(resource_ids)} 个流量包 ID")
        if resource_ids:
            print(f"   ID 列表: {', '.join(resource_ids[:3])}{'...' if len(resource_ids) > 3 else ''}")
        print()
        
        if not resource_ids:
            print("⚠️ 未发现任何 Flexus L 流量包，跳过后续测试")
            return True
        
        # 测试 3: 查询所有流量包使用情况
        print("🔍 测试 3: 查询所有流量包使用情况")
        packages = service.query_all_traffic()
        print(f"✅ 查询成功，返回 {len(packages)} 个流量包详情")
        print()
        
        for i, pkg in enumerate(packages, 1):
            print(f"   流量包 {i}:")
            print(f"   - ID: {pkg.resource_id}")
            print(f"   - 类型: {pkg.resource_type_name}")
            print(f"   - 总流量: {pkg.total_amount} {pkg.measure_unit}")
            print(f"   - 已用流量: {pkg.used_amount} {pkg.measure_unit}")
            print(f"   - 剩余流量: {pkg.remaining_amount} {pkg.measure_unit}")
            print(f"   - 使用率: {pkg.usage_percentage:.2f}%")
            print(f"   - 有效期: {pkg.start_time} ~ {pkg.end_time}")
            print()
        
        # 测试 4: 获取流量汇总 (自动发现)
        print("🔍 测试 4: 获取流量汇总")
        summary = service.get_all_traffic_summary()
        print(f"✅ 流量汇总:")
        print(f"   - 流量包数量: {summary['package_count']}")
        print(f"   - 总流量: {summary['total_amount']} GB")
        print(f"   - 已用流量: {summary['used_amount']} GB")
        print(f"   - 剩余流量: {summary['remaining_amount']} GB")
        print(f"   - 使用率: {summary['usage_percentage']}%")
        print()
        
        # 测试 5: 检查流量阈值
        threshold = 100.0  # 100GB 阈值
        print(f"🔍 测试 5: 检查流量阈值 (阈值={threshold}GB)")
        is_below, remaining = service.check_traffic_threshold(resource_ids, threshold)
        if is_below:
            print(f"⚠️ 警告: 流量低于阈值! 剩余={remaining}GB, 阈值={threshold}GB")
        else:
            print(f"✅ 流量正常: 剩余={remaining}GB, 阈值={threshold}GB")
        print()
        
        print("=" * 50)
        print("🎉 真实 API 调用测试全部通过！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='流量包查询服务测试')
    parser.add_argument(
        '--real',
        action='store_true',
        help='启用真实 API 调用测试（需要配置环境变量）'
    )
    args = parser.parse_args()
    
    try:
        if args.real:
            # 真实 API 调用模式
            print("\n" + "=" * 50)
            print("🚀 真实 API 调用模式")
            print("=" * 50 + "\n")
            
            success = test_real_api_call()
            
            if not success:
                sys.exit(1)
        else:
            # 离线测试模式（默认）
            print("\n" + "=" * 50)
            print("🧪 离线测试模式（模拟数据）")
            print("=" * 50 + "\n")
            
            test_traffic_package_model()
            test_traffic_service_init()
            test_parse_response()
            test_traffic_summary()
            test_threshold_check()
            
            print("=" * 50)
            print("🎉 所有离线测试通过！")
            print("=" * 50)
            print("\n💡 提示：使用 --real 参数进行真实 API 调用测试")
            print("   详见脚本顶部的使用说明\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
