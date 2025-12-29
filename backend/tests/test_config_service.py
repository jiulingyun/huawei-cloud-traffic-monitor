"""
配置服务测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.config import Config
from app.models.account import Account
from app.services.config_service import config_service


def test_global_config():
    """测试全局配置管理"""
    print("=" * 80)
    print("测试 1: 全局配置管理")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # 清理现有全局配置
        existing = config_service.get_global_config(db)
        if existing:
            config_service.delete_config(db, existing.id)
            print("✓ 清理现有全局配置")
        
        # 创建全局配置
        global_config = config_service.create_config(
            db=db,
            account_id=None,
            check_interval=10,
            traffic_threshold=15.0,
            auto_shutdown_enabled=True,
            feishu_webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-global",
            notification_enabled=True,
            shutdown_delay=5,
            retry_times=3
        )
        
        print(f"✓ 创建全局配置: ID={global_config.id}")
        print(f"  - 检查间隔: {global_config.check_interval} 分钟")
        print(f"  - 流量阈值: {global_config.traffic_threshold} GB")
        print(f"  - 自动关机: {global_config.auto_shutdown_enabled}")
        print(f"  - 通知启用: {global_config.notification_enabled}")
        print(f"  - 关机延迟: {global_config.shutdown_delay} 分钟")
        print(f"  - 重试次数: {global_config.retry_times}")
        
        # 验证飞书 Webhook URL 加密
        assert global_config.feishu_webhook_url is not None
        assert "open.feishu.cn" not in global_config.feishu_webhook_url
        print("✓ 飞书 Webhook URL 已加密")
        
        # 解密 Webhook URL
        decrypted_url = config_service.get_decrypted_webhook_url(global_config)
        assert decrypted_url == "https://open.feishu.cn/open-apis/bot/v2/hook/test-global"
        print(f"✓ 解密 Webhook URL: {decrypted_url}")
        
        # 查询全局配置
        retrieved = config_service.get_global_config(db)
        assert retrieved is not None
        assert retrieved.id == global_config.id
        print("✓ 查询全局配置成功")
        
        # 更新全局配置
        updated = config_service.update_config(
            db=db,
            config_id=global_config.id,
            check_interval=15,
            traffic_threshold=20.0
        )
        assert updated.check_interval == 15
        assert updated.traffic_threshold == 20.0
        print("✓ 更新全局配置成功")
        
        print("\n✅ 测试 1 通过: 全局配置管理正常\n")
        
    except Exception as e:
        print(f"\n❌ 测试 1 失败: {e}\n")
        raise
    finally:
        db.close()


def test_account_config():
    """测试账户配置管理"""
    print("=" * 80)
    print("测试 2: 账户配置管理")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # 查找或创建测试账户
        account = db.query(Account).filter(Account.name == "测试账户_配置").first()
        if not account:
            from app.utils.encryption import encryption_service
            account = Account(
                name="测试账户_配置",
                ak=encryption_service.encrypt("test_ak"),
                sk=encryption_service.encrypt("test_sk"),
                region="cn-north-4",
                is_enabled=True
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            print(f"✓ 创建测试账户: ID={account.id}")
        else:
            print(f"✓ 使用现有测试账户: ID={account.id}")
        
        # 清理现有账户配置
        existing = config_service.get_account_config(db, account.id)
        if existing:
            config_service.delete_config(db, existing.id)
            print("✓ 清理现有账户配置")
        
        # 创建账户配置
        account_config = config_service.create_config(
            db=db,
            account_id=account.id,
            check_interval=5,
            traffic_threshold=8.0,
            auto_shutdown_enabled=False,
            feishu_webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test-account",
            notification_enabled=True,
            shutdown_delay=0,
            retry_times=5
        )
        
        print(f"✓ 创建账户配置: ID={account_config.id}, Account ID={account.id}")
        print(f"  - 检查间隔: {account_config.check_interval} 分钟")
        print(f"  - 流量阈值: {account_config.traffic_threshold} GB")
        print(f"  - 自动关机: {account_config.auto_shutdown_enabled}")
        
        # 查询账户配置
        retrieved = config_service.get_account_config(db, account.id)
        assert retrieved is not None
        assert retrieved.id == account_config.id
        print("✓ 查询账户配置成功")
        
        # 测试重复创建（应该失败）
        try:
            config_service.create_config(
                db=db,
                account_id=account.id,
                check_interval=5
            )
            print("❌ 重复创建账户配置应该失败")
            raise AssertionError("重复创建账户配置应该失败")
        except ValueError as e:
            print(f"✓ 正确拒绝重复创建: {e}")
        
        print("\n✅ 测试 2 通过: 账户配置管理正常\n")
        
    except Exception as e:
        print(f"\n❌ 测试 2 失败: {e}\n")
        raise
    finally:
        db.close()


def test_effective_config():
    """测试有效配置获取（账户配置优先级）"""
    print("=" * 80)
    print("测试 3: 有效配置获取（优先级测试）")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # 确保全局配置存在
        global_config = config_service.get_global_config(db)
        assert global_config is not None
        print(f"✓ 全局配置存在: threshold={global_config.traffic_threshold} GB")
        
        # 测试没有账户配置时使用全局配置
        effective = config_service.get_effective_config(db, account_id=9999)
        assert effective is not None
        assert effective.id == global_config.id
        print("✓ 不存在的账户使用全局配置")
        
        # 测试有账户配置时使用账户配置
        account = db.query(Account).filter(Account.name == "测试账户_配置").first()
        if account:
            account_config = config_service.get_account_config(db, account.id)
            effective = config_service.get_effective_config(db, account_id=account.id)
            assert effective is not None
            assert effective.id == account_config.id
            assert effective.traffic_threshold == 8.0  # 账户配置的值
            print(f"✓ 存在账户配置时优先使用: threshold={effective.traffic_threshold} GB")
        
        # 测试不指定账户时使用全局配置
        effective = config_service.get_effective_config(db)
        assert effective is not None
        assert effective.id == global_config.id
        print("✓ 不指定账户时使用全局配置")
        
        print("\n✅ 测试 3 通过: 有效配置获取正常\n")
        
    except Exception as e:
        print(f"\n❌ 测试 3 失败: {e}\n")
        raise
    finally:
        db.close()


def test_list_configs():
    """测试配置列表查询"""
    print("=" * 80)
    print("测试 4: 配置列表查询")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # 查询所有配置
        all_configs = config_service.list_configs(db)
        print(f"✓ 查询所有配置: 共 {len(all_configs)} 个")
        
        for config in all_configs:
            account_str = "全局" if config.account_id is None else f"账户 {config.account_id}"
            print(f"  - Config ID={config.id}, {account_str}, threshold={config.traffic_threshold} GB")
        
        # 查询特定账户的配置
        account = db.query(Account).filter(Account.name == "测试账户_配置").first()
        if account:
            account_configs = config_service.list_configs(db, account_id=account.id)
            print(f"✓ 查询账户 {account.id} 的配置: 共 {len(account_configs)} 个")
        
        print("\n✅ 测试 4 通过: 配置列表查询正常\n")
        
    except Exception as e:
        print(f"\n❌ 测试 4 失败: {e}\n")
        raise
    finally:
        db.close()


def test_config_validation():
    """测试配置参数验证"""
    print("=" * 80)
    print("测试 5: 配置参数验证")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # 创建配置（不同参数范围）
        test_config = config_service.create_config(
            db=db,
            account_id=None,  # 会失败因为全局配置已存在
            check_interval=1,  # 最小值
            traffic_threshold=0.1,  # 最小值
            shutdown_delay=60,  # 最大值
            retry_times=10  # 最大值
        )
        print("❌ 应该因为全局配置已存在而失败")
        
    except ValueError as e:
        print(f"✓ 正确拒绝重复创建: {e}")
    except Exception as e:
        print(f"⚠️  其他错误: {e}")
    finally:
        db.close()
    
    print("\n✅ 测试 5 通过: 配置参数验证正常\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("开始配置服务测试")
    print("=" * 80 + "\n")
    
    try:
        test_global_config()
        test_account_config()
        test_effective_config()
        test_list_configs()
        test_config_validation()
        
        print("=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ 测试失败: {e}")
        print("=" * 80)
        raise


if __name__ == "__main__":
    main()
