#!/usr/bin/env python3
"""
测试流量包查询服务
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.huawei_cloud import TrafficService, TrafficPackage, HuaweiCloudClient


def test_traffic_package_model():
    """测试流量包模型"""
    print("=" * 50)
    print("测试流量包模型")
    print("=" * 50)
    
    # 模拟 API 响应数据
    test_data = {
        'free_resource_id': 'test_resource_id_123',
        'free_resource_type_code': 'traffic',
        'free_resource_measure': {
            'amount': 1000.0,  # 1000 GB
            'used_amount': 350.5,  # 350.5 GB
            'available_amount': 649.5  # 649.5 GB
        },
        'start_time': '2024-01-01T00:00:00Z',
        'end_time': '2024-12-31T23:59:59Z',
        'order_id': 'order_12345'
    }
    
    package = TrafficPackage(test_data)
    
    print(f"✅ 流量包模型创建成功")
    print(f"   Resource ID: {package.resource_id}")
    print(f"   总流量: {package.total_amount} GB")
    print(f"   已用流量: {package.used_amount} GB")
    print(f"   剩余流量: {package.remaining_amount} GB")
    print(f"   使用率: {package.usage_percentage:.2f}%")
    
    # 验证计算
    assert package.total_amount == 1000.0
    assert package.used_amount == 350.5
    assert package.remaining_amount == 649.5
    assert 35 <= package.usage_percentage <= 35.1
    
    # 测试 to_dict
    data_dict = package.to_dict()
    print(f"✅ 转换为字典: {len(data_dict)} 个字段")
    assert 'resource_id' in data_dict
    assert 'remaining_amount' in data_dict
    
    print("\n✅ 流量包模型测试通过！\n")


def test_traffic_service_init():
    """测试流量服务初始化"""
    print("=" * 50)
    print("测试流量服务初始化")
    print("=" * 50)
    
    # 创建测试客户端
    client = HuaweiCloudClient(
        access_key="TEST_AK",
        secret_key="TEST_SK",
        region="cn-north-4"
    )
    
    # 创建流量服务
    service = TrafficService(client)
    
    print(f"✅ 流量服务初始化成功")
    print(f"   Client: {type(service.client).__name__}")
    print(f"   API Endpoint: {service.TRAFFIC_API_ENDPOINT}")
    
    assert service.client is client
    assert service.TRAFFIC_API_ENDPOINT == '/v2/payments/free-resources/usages/details/query'
    
    print("\n✅ 流量服务初始化测试通过！\n")


def test_parse_response():
    """测试响应解析"""
    print("=" * 50)
    print("测试响应解析")
    print("=" * 50)
    
    client = HuaweiCloudClient("TEST_AK", "TEST_SK")
    service = TrafficService(client)
    
    # 模拟 API 响应
    mock_response = {
        'free_resources': [
            {
                'free_resource_id': 'resource_1',
                'free_resource_type_code': 'traffic',
                'free_resource_measure': {
                    'amount': 500.0,
                    'used_amount': 100.0,
                    'available_amount': 400.0
                },
                'start_time': '2024-01-01T00:00:00Z',
                'end_time': '2024-12-31T23:59:59Z'
            },
            {
                'free_resource_id': 'resource_2',
                'free_resource_type_code': 'traffic',
                'free_resource_measure': {
                    'amount': 300.0,
                    'used_amount': 50.0,
                    'available_amount': 250.0
                },
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
    assert packages[1].resource_id == 'resource_2'
    assert packages[1].remaining_amount == 250.0
    
    print(f"   流量包1: {packages[0].remaining_amount}GB 剩余")
    print(f"   流量包2: {packages[1].remaining_amount}GB 剩余")
    
    print("\n✅ 响应解析测试通过！\n")


def test_traffic_summary():
    """测试流量汇总"""
    print("=" * 50)
    print("测试流量汇总（模拟）")
    print("=" * 50)
    
    # 创建多个流量包
    packages_data = [
        {
            'free_resource_id': f'resource_{i}',
            'free_resource_type_code': 'traffic',
            'free_resource_measure': {
                'amount': 100.0 * i,
                'used_amount': 30.0 * i,
                'available_amount': 70.0 * i
            },
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
    assert used == 180.0   # 30 + 60 + 90
    assert remaining == 420.0  # 70 + 140 + 210
    
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


if __name__ == "__main__":
    try:
        test_traffic_package_model()
        test_traffic_service_init()
        test_parse_response()
        test_traffic_summary()
        test_threshold_check()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
