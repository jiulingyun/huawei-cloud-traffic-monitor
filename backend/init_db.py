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

if __name__ == "__main__":
    print("开始初始化数据库...")
    init_db()
    print("数据库初始化完成！")
    print("\n创建的表：")
    print("  - accounts: 账户表")
    print("  - servers: 服务器表")
    print("  - configs: 配置表")
    print("  - monitor_logs: 监控日志表")
    print("  - shutdown_logs: 关机日志表")
    print("  - notification_logs: 通知日志表")
