#!/usr/bin/env python3
"""
测试华为云 API 客户端
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.huawei_cloud import HuaweiCloudClient, client_manager
from app.utils.encryption import encryption_service


def test_client_init():
    """测试客户端初始化"""
    print("=" * 50)
    print("测试华为云客户端初始化")
    print("=" * 50)
    
    # 使用测试 AK/SK
    test_ak = "ABCDEFGHIJKLMNOPQRST"
    test_sk = "1234567890abcdefghijklmnopqrstuvwxyz"
    
    client = HuaweiCloudClient(
        access_key=test_ak,
        secret_key=test_sk,
        region="cn-north-4"
    )
    
    print(f"✅ 客户端初始化成功")
    print(f"   Region: {client.region}")
    print(f"   Endpoint: {client.endpoint}")
    print(f"   AK: {test_ak[:4]}...")
    
    print("\n")


def test_sign_request():
    """测试请求签名"""
    print("=" * 50)
    print("测试请求签名")
    print("=" * 50)
    
    test_ak = "ABCDEFGHIJKLMNOPQRST"
    test_sk = "1234567890abcdefghijklmnopqrstuvwxyz"
    
    client = HuaweiCloudClient(
        access_key=test_ak,
        secret_key=test_sk,
        region="cn-north-4"
    )
    
    # 生成签名
    headers = client._sign_request(
        method="GET",
        uri="/v1/test",
        query_params={"limit": "10"}
    )
    
    print(f"✅ 签名生成成功")
    print(f"   X-Sdk-Date: {headers.get('X-Sdk-Date')}")
    print(f"   Authorization: {headers.get('Authorization')[:50]}...")
    print(f"   Host: {headers.get('Host')}")
    
    # 验证签名头包含必要字段
    assert 'X-Sdk-Date' in headers
    assert 'Authorization' in headers
    assert 'SDK-HMAC-SHA256' in headers['Authorization']
    assert 'Access=' in headers['Authorization']
    assert 'Signature=' in headers['Authorization']
    
    print("\n✅ 请求签名测试通过！\n")


def test_client_manager():
    """测试客户端管理器"""
    print("=" * 50)
    print("测试客户端管理器")
    print("=" * 50)
    
    # 准备测试数据
    test_ak = "ABCDEFGHIJKLMNOPQRST"
    test_sk = "1234567890abcdefghijklmnopqrstuvwxyz"
    
    # 加密 AK/SK
    encrypted_ak, encrypted_sk = encryption_service.encrypt_ak_sk(test_ak, test_sk)
    print(f"✅ AK/SK 加密完成")
    
    # 获取客户端（首次）
    client1 = client_manager.get_client(
        account_id=1,
        encrypted_ak=encrypted_ak,
        encrypted_sk=encrypted_sk,
        region="cn-north-4"
    )
    print(f"✅ 获取客户端1成功: {type(client1).__name__}")
    
    # 获取客户端（缓存）
    client2 = client_manager.get_client(
        account_id=1,
        encrypted_ak=encrypted_ak,
        encrypted_sk=encrypted_sk,
        region="cn-north-4"
    )
    print(f"✅ 获取客户端2成功（应使用缓存）")
    
    # 验证是同一个实例
    assert client1 is client2, "应该返回缓存的客户端实例"
    print(f"✅ 客户端缓存验证通过")
    
    # 获取客户端数量
    count = client_manager.get_client_count()
    print(f"✅ 当前缓存的客户端数量: {count}")
    assert count == 1
    
    # 移除客户端
    removed = client_manager.remove_client(1)
    print(f"✅ 移除客户端: {removed}")
    assert removed is True
    
    count = client_manager.get_client_count()
    print(f"✅ 移除后客户端数量: {count}")
    assert count == 0
    
    # 清空所有客户端
    client_manager.clear_clients()
    print(f"✅ 清空所有客户端缓存")
    
    print("\n✅ 客户端管理器测试通过！\n")


def test_endpoints():
    """测试端点配置"""
    print("=" * 50)
    print("测试端点配置")
    print("=" * 50)
    
    regions = [
        'cn-north-1',
        'cn-north-4',
        'cn-east-2',
        'cn-south-1',
        'ap-southeast-1',
    ]
    
    for region in regions:
        client = HuaweiCloudClient(
            access_key="TEST",
            secret_key="TEST",
            region=region
        )
        print(f"✅ {region}: {client.endpoint}")
        assert region in client.endpoint
    
    print("\n✅ 端点配置测试通过！\n")


if __name__ == "__main__":
    try:
        test_client_init()
        test_sign_request()
        test_client_manager()
        test_endpoints()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
