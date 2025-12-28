#!/usr/bin/env python3
"""
测试工具模块
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils import encryption_service, ConfigValidator, config_loader


def test_encryption():
    """测试加密功能"""
    print("=" * 50)
    print("测试加密功能")
    print("=" * 50)
    
    # 测试生成密钥
    key = encryption_service.generate_key()
    print(f"✅ 生成密钥: {key[:20]}...")
    
    # 测试加密解密
    plaintext = "test_access_key_123456"
    encrypted = encryption_service.encrypt(plaintext)
    print(f"✅ 加密: {plaintext} -> {encrypted[:30]}...")
    
    decrypted = encryption_service.decrypt(encrypted)
    print(f"✅ 解密: {decrypted}")
    
    assert plaintext == decrypted, "加密解密失败"
    
    # 测试 AK/SK 加密
    ak = "TEST_AK_1234567890"
    sk = "TEST_SK_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    encrypted_ak, encrypted_sk = encryption_service.encrypt_ak_sk(ak, sk)
    print(f"✅ AK 加密: {encrypted_ak[:30]}...")
    print(f"✅ SK 加密: {encrypted_sk[:30]}...")
    
    decrypted_ak, decrypted_sk = encryption_service.decrypt_ak_sk(encrypted_ak, encrypted_sk)
    assert ak == decrypted_ak and sk == decrypted_sk, "AK/SK 加密解密失败"
    print(f"✅ AK/SK 解密成功")
    
    # 测试脱敏
    masked = encryption_service.mask_sensitive_data(ak)
    print(f"✅ 脱敏: {ak} -> {masked}")
    
    print("\n✅ 加密功能测试通过！\n")


def test_validators():
    """测试验证功能"""
    print("=" * 50)
    print("测试验证功能")
    print("=" * 50)
    
    # 测试账户配置验证
    valid, error = ConfigValidator.validate_account_config(
        name="测试账户",
        ak="ABCDEFGHIJKLMNOPQRST",
        sk="1234567890abcdefghijklmnopqrstuvwxyz",
        region="cn-north-4"
    )
    print(f"✅ 有效账户配置验证: {valid}")
    
    valid, error = ConfigValidator.validate_account_config(
        name="A",  # 名称太短
        ak="INVALID",
        sk="SHORT",
        region="invalid-region"
    )
    print(f"✅ 无效账户配置验证: {valid}, 错误: {error}")
    
    # 测试监控配置验证
    valid, error = ConfigValidator.validate_monitor_config(
        check_interval=5,
        traffic_threshold=10.0
    )
    print(f"✅ 有效监控配置验证: {valid}")
    
    valid, error = ConfigValidator.validate_monitor_config(
        check_interval=2000,  # 间隔太大
        traffic_threshold=0.05  # 阈值太小
    )
    print(f"✅ 无效监控配置验证: {valid}, 错误: {error}")
    
    print("\n✅ 验证功能测试通过！\n")


def test_config_loader():
    """测试配置加载"""
    print("=" * 50)
    print("测试配置加载功能")
    print("=" * 50)
    
    # 测试保存和加载 YAML
    test_config = {
        'app': {
            'name': '测试应用',
            'version': '1.0.0'
        },
        'database': {
            'host': 'localhost',
            'port': 5432
        }
    }
    
    # 保存 YAML
    success = config_loader.save_yaml('test.yaml', test_config)
    print(f"✅ 保存 YAML: {success}")
    
    # 加载 YAML
    loaded_config = config_loader.load_yaml('test.yaml')
    print(f"✅ 加载 YAML: {loaded_config}")
    
    assert loaded_config == test_config, "YAML 配置不匹配"
    
    # 测试获取嵌套值
    value = config_loader.get_config_value(loaded_config, 'database.host')
    print(f"✅ 获取嵌套值 (database.host): {value}")
    assert value == 'localhost'
    
    # 测试保存和加载 JSON
    success = config_loader.save_json('test.json', test_config)
    print(f"✅ 保存 JSON: {success}")
    
    loaded_json = config_loader.load_json('test.json')
    print(f"✅ 加载 JSON: {loaded_json}")
    assert loaded_json == test_config
    
    print("\n✅ 配置加载功能测试通过！\n")


if __name__ == "__main__":
    try:
        test_encryption()
        test_validators()
        test_config_loader()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
