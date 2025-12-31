#!/usr/bin/env python3
"""
数据库初始化脚本
运行此脚本创建所有数据库表
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db
from app.core.database import SessionLocal
from app.models.config import Config

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_db()
    # 确保存在全局配置（account_id 为 NULL）
    db = SessionLocal()
    try:
        existing = db.query(Config).filter(Config.account_id.is_(None)).first()
        if not existing:
            print("未发现全局配置，创建默认全局配置...")
            default = Config(
                account_id=None,
                check_interval=5,
                traffic_threshold=10.0,
                auto_shutdown_enabled=True,
                notification_enabled=True,
                shutdown_delay=0,
                retry_times=3
            )
            db.add(default)
            db.commit()
            print("默认全局配置已创建")
        else:
            print("全局配置已存在，跳过创建")
    finally:
        db.close()
    print("数据库初始化完成！")
    print("\n创建的表：")
    print("  - accounts: 账户表")
    print("  - servers: 服务器表")
    print("  - configs: 配置表")
    print("  - monitor_logs: 监控日志表")
    print("  - shutdown_logs: 关机日志表")
    print("  - notification_logs: 通知日志表")
