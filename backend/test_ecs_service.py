#!/usr/bin/env python3
"""
测试 ECS 服务器信息查询服务

使用方法：
1. 离线测试（默认）：
   python test_ecs_service.py

2. 真实联调：
   export HUAWEI_AK="your_access_key"
   export HUAWEI_SK="your_secret_key"
   export HUAWEI_REGION="cn-north-4"  # 可选，默认 cn-north-4
   export HUAWEI_PROJECT_ID="your_project_id"  # 项目 ID
   python test_ecs_service.py --real
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.huawei_cloud import ECSService, ECSServer, HuaweiCloudClient


def test_ecs_server_model():
    """测试 ECS 服务器模型"""
    print("=" * 50)
    print("测试 ECS 服务器模型")
    print("=" * 50)
    
    # 模拟 API 响应数据
    test_data = {
        'id': 'server-12345',
        'name': 'test-server-001',
        'status': 'ACTIVE',
        'flavor': {'id': 'c3.large.2'},
        'image': {'id': 'centos-7.6-x64'},
        'addresses': {
            'test-vpc': [
                {'addr': '192.168.1.10', 'OS-EXT-IPS:type': 'fixed'},
                {'addr': '1.2.3.4', 'OS-EXT-IPS:type': 'floating'}
            ]
        },
        'metadata': {'charging_mode': '0'},
        'OS-EXT-AZ:availability_zone': 'cn-north-4a',
        'created': '2024-01-01T00:00:00Z',
        'os-extended-volumes:volumes_attached': [
            {'id': 'vol-123', 'device': '/dev/sda'}
        ],
        'OS-EXT-STS:task_state': None,
        'OS-EXT-STS:power_state': 1,
        'OS-EXT-STS:vm_state': 'active',
        'enterprise_project_id': '0'
    }
    
    server = ECSServer(test_data)
    
    print(f"✅ ECS 服务器模型创建成功")
    print(f"   Server ID: {server.id}")
    print(f"   Server Name: {server.name}")
    print(f"   Status: {server.status}")
    print(f"   Private IPs: {server.private_ips}")
    print(f"   Public IPs: {server.public_ips}")
    print(f"   Is Running: {server.is_running()}")
    
    # 验证
    assert server.id == 'server-12345'
    assert server.name == 'test-server-001'
    assert server.status == 'ACTIVE'
    assert '192.168.1.10' in server.private_ips
    assert '1.2.3.4' in server.public_ips
    assert server.is_running() is True
    
    # 测试 to_dict
    data_dict = server.to_dict()
    print(f"✅ 转换为字典: {len(data_dict)} 个字段")
    assert 'id' in data_dict
    assert 'private_ips' in data_dict
    
    print("\n✅ ECS 服务器模型测试通过！\n")


def test_ecs_service_init():
    """测试 ECS 服务初始化"""
    print("=" * 50)
    print("测试 ECS 服务初始化")
    print("=" * 50)
    
    # 创建测试客户端
    client = HuaweiCloudClient(
        access_key="TEST_AK",
        secret_key="TEST_SK",
        region="cn-north-4"
    )
    
    # 创建 ECS 服务
    service = ECSService(client, project_id="test-project-id")
    
    print(f"✅ ECS 服务初始化成功")
    print(f"   Client: {type(service.client).__name__}")
    print(f"   Project ID: {service.project_id}")
    print(f"   API Endpoint: {service.SERVER_LIST_ENDPOINT}")
    
    assert service.client is client
    assert service.project_id == "test-project-id"
    assert '/cloudservers/detail' in service.SERVER_LIST_ENDPOINT
    
    print("\n✅ ECS 服务初始化测试通过！\n")


def test_parse_response():
    """测试响应解析"""
    print("=" * 50)
    print("测试响应解析")
    print("=" * 50)
    
    client = HuaweiCloudClient("TEST_AK", "TEST_SK")
    service = ECSService(client, project_id="test-project")
    
    # 模拟 API 响应
    mock_response = {
        'servers': [
            {
                'id': 'server-1',
                'name': 'web-server-01',
                'status': 'ACTIVE',
                'flavor': {'id': 'c3.large.2'},
                'image': {'id': 'centos-7.6'},
                'addresses': {
                    'vpc-1': [{'addr': '192.168.1.10', 'OS-EXT-IPS:type': 'fixed'}]
                },
                'metadata': {},
                'OS-EXT-AZ:availability_zone': 'az1',
                'created': '2024-01-01T00:00:00Z',
                'os-extended-volumes:volumes_attached': [],
                'OS-EXT-STS:vm_state': 'active'
            },
            {
                'id': 'server-2',
                'name': 'db-server-01',
                'status': 'SHUTOFF',
                'flavor': {'id': 'c3.xlarge.2'},
                'image': {'id': 'ubuntu-20.04'},
                'addresses': {
                    'vpc-1': [{'addr': '192.168.1.20', 'OS-EXT-IPS:type': 'fixed'}]
                },
                'metadata': {},
                'OS-EXT-AZ:availability_zone': 'az1',
                'created': '2024-01-02T00:00:00Z',
                'os-extended-volumes:volumes_attached': [],
                'OS-EXT-STS:vm_state': 'stopped'
            }
        ]
    }
    
    servers = service._parse_response(mock_response)
    
    print(f"✅ 响应解析成功: {len(servers)} 个服务器")
    
    assert len(servers) == 2
    assert servers[0].id == 'server-1'
    assert servers[0].status == 'ACTIVE'
    assert servers[1].id == 'server-2'
    assert servers[1].status == 'SHUTOFF'
    
    print(f"   服务器1: {servers[0].name} - {servers[0].status}")
    print(f"   服务器2: {servers[1].name} - {servers[1].status}")
    
    print("\n✅ 响应解析测试通过！\n")


def test_server_status_check():
    """测试服务器状态判断"""
    print("=" * 50)
    print("测试服务器状态判断")
    print("=" * 50)
    
    # 创建不同状态的服务器
    running_server = ECSServer({
        'id': 's1',
        'name': 'running',
        'status': 'ACTIVE',
        'flavor': {},
        'image': {},
        'addresses': {},
        'metadata': {},
        'created': '2024-01-01T00:00:00Z',
        'os-extended-volumes:volumes_attached': [],
        'OS-EXT-STS:vm_state': 'active'
    })
    
    stopped_server = ECSServer({
        'id': 's2',
        'name': 'stopped',
        'status': 'SHUTOFF',
        'flavor': {},
        'image': {},
        'addresses': {},
        'metadata': {},
        'created': '2024-01-01T00:00:00Z',
        'os-extended-volumes:volumes_attached': [],
        'OS-EXT-STS:vm_state': 'stopped'
    })
    
    print(f"✅ 状态判断测试")
    print(f"   运行中服务器: is_running={running_server.is_running()}, is_stopped={running_server.is_stopped()}")
    print(f"   已关机服务器: is_running={stopped_server.is_running()}, is_stopped={stopped_server.is_stopped()}")
    
    assert running_server.is_running() is True
    assert running_server.is_stopped() is False
    assert stopped_server.is_running() is False
    assert stopped_server.is_stopped() is True
    
    print("\n✅ 服务器状态判断测试通过！\n")


def test_real_api_call():
    """真实 API 调用测试"""
    print("=" * 50)
    print("真实 API 调用测试")
    print("=" * 50)
    
    # 从环境变量获取配置
    ak = os.getenv('HUAWEI_AK')
    sk = os.getenv('HUAWEI_SK')
    region = os.getenv('HUAWEI_REGION', 'cn-north-4')
    project_id = os.getenv('HUAWEI_PROJECT_ID')
    
    if not ak or not sk:
        print("❌ 缺少环境变量: HUAWEI_AK 和 HUAWEI_SK")
        print("   请设置环境变量后重试：")
        print("   export HUAWEI_AK='your_access_key'")
        print("   export HUAWEI_SK='your_secret_key'")
        return False
    
    if not project_id:
        print("❌ 缺少环境变量: HUAWEI_PROJECT_ID")
        print("   请设置项目 ID：")
        print("   export HUAWEI_PROJECT_ID='your_project_id'")
        return False
    
    print(f"配置信息：")
    print(f"   AK: {ak[:4]}****{ak[-4:] if len(ak) > 8 else '****'}")
    print(f"   Region: {region}")
    print(f"   Project ID: {project_id}")
    print()
    
    try:
        # 创建客户端
        client = HuaweiCloudClient(
            access_key=ak,
            secret_key=sk,
            region=region
        )
        print("✅ 客户端创建成功")
        
        # 创建 ECS 服务
        service = ECSService(client, project_id=project_id)
        print("✅ ECS 服务初始化成功")
        print()
        
        # 测试1: 查询所有服务器
        print("🔍 测试 1: 查询所有服务器")
        servers = service.list_servers()
        print(f"✅ 查询成功，返回 {len(servers)} 个服务器")
        
        for i, server in enumerate(servers[:5], 1):  # 只显示前5个
            print(f"\n   服务器 {i}:")
            print(f"   - ID: {server.id}")
            print(f"   - Name: {server.name}")
            print(f"   - Status: {server.status}")
            print(f"   - Private IPs: {', '.join(server.private_ips)}")
            print(f"   - Public IPs: {', '.join(server.public_ips)}")
            print(f"   - Availability Zone: {server.availability_zone}")
            print(f"   - Created: {server.created}")
        
        if len(servers) > 5:
            print(f"\n   ... 还有 {len(servers) - 5} 个服务器")
        
        print()
        
        # 测试2: 获取运行中的服务器
        print("🔍 测试 2: 获取运行中的服务器")
        running = service.get_running_servers()
        print(f"✅ 运行中服务器: {len(running)} 个")
        
        # 测试3: 获取已关机的服务器
        print("🔍 测试 3: 获取已关机的服务器")
        stopped = service.get_stopped_servers()
        print(f"✅ 已关机服务器: {len(stopped)} 个")
        
        # 测试4: 获取服务器汇总
        print("\n🔍 测试 4: 获取服务器汇总")
        summary = service.get_server_summary()
        print(f"✅ 服务器汇总信息:")
        print(f"   - 总数: {summary['total_count']}")
        print(f"   - 状态分布: {summary['status_count']}")
        
        print("\n" + "=" * 50)
        print("🎉 真实 API 调用测试全部通过！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ API 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ECS 服务器信息查询服务测试')
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
            
            test_ecs_server_model()
            test_ecs_service_init()
            test_parse_response()
            test_server_status_check()
            
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
