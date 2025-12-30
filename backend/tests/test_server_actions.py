#!/usr/bin/env python
"""
Flexus L 服务器操作测试脚本

测试启动、关机、重启功能

使用方法:
    # 设置环境变量
    export HUAWEI_AK="your_access_key"
    export HUAWEI_SK="your_secret_key"
    export HUAWEI_INTL="true"  # 国际站
    
    # 列出实例（不执行操作）
    python tests/test_server_actions.py --list
    
    # 测试关机（危险操作！）
    python tests/test_server_actions.py --stop --server-id <ID> --region <REGION>
    
    # 测试开机
    python tests/test_server_actions.py --start --server-id <ID> --region <REGION>
    
    # 测试重启（危险操作！）
    python tests/test_server_actions.py --reboot --server-id <ID> --region <REGION>
"""
import os
import sys
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.huawei_cloud.flexusl_service import (
    FlexusLService,
    FlexusLException,
    ServerActionResult,
    JobStatus
)


def get_service():
    """获取 FlexusL 服务实例"""
    ak = os.environ.get('HUAWEI_AK')
    sk = os.environ.get('HUAWEI_SK')
    is_intl = os.environ.get('HUAWEI_INTL', 'true').lower() == 'true'
    
    if not ak or not sk:
        print("❌ 错误: 请设置 HUAWEI_AK 和 HUAWEI_SK 环境变量")
        print()
        print("示例:")
        print('   export HUAWEI_AK="your_access_key"')
        print('   export HUAWEI_SK="your_secret_key"')
        print('   export HUAWEI_INTL="true"  # 国际站')
        sys.exit(1)
    
    return FlexusLService(ak=ak, sk=sk, is_international=is_intl)


def list_instances():
    """列出所有实例"""
    print("\n" + "=" * 60)
    print("📋 Flexus L 实例列表")
    print("=" * 60)
    
    service = get_service()
    
    try:
        instances = service.list_instances()
        
        if not instances:
            print("⚠️ 未发现任何 Flexus L 实例")
            return
        
        print(f"\n共 {len(instances)} 个实例:\n")
        
        for i, inst in enumerate(instances, 1):
            print(f"  {i}. {inst.name}")
            print(f"     Flexus L ID: {inst.id}")
            print(f"     云主机 ID: {inst.server_id or 'N/A'}")
            print(f"     区域: {inst.region}")
            print(f"     状态: {inst.status}")
            print(f"     公网IP: {inst.public_ip or 'N/A'}")
            print()
        
        print("\n可用操作命令示例:")
        if instances:
            first = instances[0]
            server_id = first.server_id or first.id
            print(f"  # 关机 (使用云主机 ID)")
            print(f"  python tests/test_server_actions.py --stop --server-id {server_id} --region {first.region}")
            print(f"  # 开机")
            print(f"  python tests/test_server_actions.py --start --server-id {server_id} --region {first.region}")
            print(f"  # 重启")
            print(f"  python tests/test_server_actions.py --reboot --server-id {server_id} --region {first.region}")
        
    except FlexusLException as e:
        print(f"❌ 查询失败: {e}")


def stop_server(server_id: str, region: str, force: bool = False):
    """关闭服务器"""
    print("\n" + "=" * 60)
    print("🔴 关闭 Flexus L 实例")
    print("=" * 60)
    
    stop_type = "HARD" if force else "SOFT"
    
    print(f"\n⚠️ 即将关闭服务器:")
    print(f"   服务器 ID: {server_id}")
    print(f"   区域: {region}")
    print(f"   关机类型: {stop_type}")
    
    confirm = input("\n确认关闭? (输入 'yes' 继续): ")
    if confirm.lower() != 'yes':
        print("已取消")
        return
    
    service = get_service()
    
    try:
        result = service.stop_server(server_id, region, stop_type)
        
        if result.success:
            print(f"\n✅ 关机请求已提交")
            print(f"   Job ID: {result.job_id or 'N/A'}")
            print(f"   消息: {result.message}")
        else:
            print(f"\n❌ 关机失败: {result.message}")
            
    except FlexusLException as e:
        print(f"❌ 操作失败: {e}")


def start_server(server_id: str, region: str):
    """启动服务器"""
    print("\n" + "=" * 60)
    print("🟢 启动 Flexus L 实例")
    print("=" * 60)
    
    print(f"\n即将启动服务器:")
    print(f"   服务器 ID: {server_id}")
    print(f"   区域: {region}")
    
    confirm = input("\n确认启动? (输入 'yes' 继续): ")
    if confirm.lower() != 'yes':
        print("已取消")
        return
    
    service = get_service()
    
    try:
        result = service.start_server(server_id, region)
        
        if result.success:
            print(f"\n✅ 启动请求已提交")
            print(f"   Job ID: {result.job_id or 'N/A'}")
            print(f"   消息: {result.message}")
        else:
            print(f"\n❌ 启动失败: {result.message}")
            
    except FlexusLException as e:
        print(f"❌ 操作失败: {e}")


def reboot_server(server_id: str, region: str, force: bool = False):
    """重启服务器"""
    print("\n" + "=" * 60)
    print("🔄 重启 Flexus L 实例")
    print("=" * 60)
    
    reboot_type = "HARD" if force else "SOFT"
    
    print(f"\n⚠️ 即将重启服务器:")
    print(f"   服务器 ID: {server_id}")
    print(f"   区域: {region}")
    print(f"   重启类型: {reboot_type}")
    
    confirm = input("\n确认重启? (输入 'yes' 继续): ")
    if confirm.lower() != 'yes':
        print("已取消")
        return
    
    service = get_service()
    
    try:
        result = service.reboot_server(server_id, region, reboot_type)
        
        if result.success:
            print(f"\n✅ 重启请求已提交")
            print(f"   Job ID: {result.job_id or 'N/A'}")
            print(f"   消息: {result.message}")
        else:
            print(f"\n❌ 重启失败: {result.message}")
            
    except FlexusLException as e:
        print(f"❌ 操作失败: {e}")


def query_server_status(server_id: str, region: str):
    """查询云主机实时状态"""
    print("\n" + "=" * 60)
    print("💻 查询云主机实时状态")
    print("=" * 60)
    
    print(f"\n查询云主机:")
    print(f"   Server ID: {server_id}")
    print(f"   区域: {region}")
    
    service = get_service()
    
    try:
        status = service.get_server_status(server_id=server_id, region=region)
        
        print(f"\n📊 云主机状态:")
        print(f"   Server ID: {status.get('server_id')}")
        print(f"   名称: {status.get('name')}")
        print(f"   状态: {status.get('status')}")
        print(f"   VM 状态: {status.get('OS-EXT-STS:vm_state')}")
        print(f"   电源状态: {status.get('OS-EXT-STS:power_state')}")
        print(f"   当前任务: {status.get('OS-EXT-STS:task_state') or 'N/A'}")
        print(f"   更新时间: {status.get('updated')}")
        
        # 状态摘要
        ecs_status = status.get('status')
        if ecs_status == 'ACTIVE':
            print(f"\n✅ 云主机正在运行中")
        elif ecs_status == 'SHUTOFF':
            print(f"\n⚪ 云主机已关机")
        elif ecs_status in ('REBOOT', 'HARD_REBOOT'):
            print(f"\n🔄 云主机正在重启中...")
        elif ecs_status == 'ERROR':
            print(f"\n❌ 云主机状态异常")
        
    except FlexusLException as e:
        print(f"❌ 查询失败: {e}")


def query_job_status(job_id: str, region: str):
    """查询 Job 状态"""
    print("\n" + "=" * 60)
    print("🔍 查询任务执行状态")
    print("=" * 60)
    
    print(f"\n查询任务:")
    print(f"   Job ID: {job_id}")
    print(f"   区域: {region}")
    
    service = get_service()
    
    try:
        job_status = service.get_job_status(job_id=job_id, region=region)
        
        print(f"\n📋 任务状态:")
        print(f"   Job ID: {job_status.job_id}")
        print(f"   类型: {job_status.job_type}")
        print(f"   状态: {job_status.status}")
        print(f"   开始时间: {job_status.begin_time or 'N/A'}")
        print(f"   结束时间: {job_status.end_time or 'N/A'}")
        
        if job_status.error_code:
            print(f"   错误码: {job_status.error_code}")
        if job_status.fail_reason:
            print(f"   失败原因: {job_status.fail_reason}")
        if job_status.entities:
            print(f"   关联实体: {job_status.entities}")
        
        # 状态摘要
        if job_status.is_success:
            print(f"\n✅ 任务已成功完成")
        elif job_status.is_failed:
            print(f"\n❌ 任务执行失败")
        elif job_status.is_running:
            print(f"\n⏳ 任务正在执行中...")
        
    except FlexusLException as e:
        print(f"❌ 查询失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Flexus L 服务器操作测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 列出所有实例
    python tests/test_server_actions.py --list
    
    # 关机
    python tests/test_server_actions.py --stop --server-id <ID> --region <REGION>
    
    # 强制关机
    python tests/test_server_actions.py --stop --server-id <ID> --region <REGION> --force
    
    # 开机
    python tests/test_server_actions.py --start --server-id <ID> --region <REGION>
    
    # 重启
    python tests/test_server_actions.py --reboot --server-id <ID> --region <REGION>
    
    # 查询云主机实时状态
    python tests/test_server_actions.py --status --server-id <ID> --region <REGION>
    
    # 查询任务状态
    python tests/test_server_actions.py --job --job-id <JOB_ID> --region <REGION>
        """
    )
    
    parser.add_argument('--list', action='store_true', help='列出所有 Flexus L 实例')
    parser.add_argument('--stop', action='store_true', help='关闭服务器')
    parser.add_argument('--start', action='store_true', help='启动服务器')
    parser.add_argument('--reboot', action='store_true', help='重启服务器')
    parser.add_argument('--status', action='store_true', help='查询云主机实时状态')
    parser.add_argument('--job', action='store_true', help='查询任务状态')
    parser.add_argument('--server-id', type=str, help='服务器 ID')
    parser.add_argument('--job-id', type=str, help='任务 ID')
    parser.add_argument('--region', type=str, help='区域 ID')
    parser.add_argument('--force', action='store_true', help='强制操作 (HARD)')
    
    args = parser.parse_args()
    
    # 检查配置
    ak = os.environ.get('HUAWEI_AK')
    sk = os.environ.get('HUAWEI_SK')
    
    if not ak or not sk:
        print("❌ 错误: 请设置环境变量")
        print()
        print('   export HUAWEI_AK="your_access_key"')
        print('   export HUAWEI_SK="your_secret_key"')
        print('   export HUAWEI_INTL="true"')
        sys.exit(1)
    
    print(f"\n配置: AK={ak[:4]}****{ak[-4:]}, 国际站={os.environ.get('HUAWEI_INTL', 'true')}")
    
    # 执行操作
    if args.list:
        list_instances()
    elif args.stop:
        if not args.server_id or not args.region:
            print("❌ 错误: --stop 需要 --server-id 和 --region 参数")
            sys.exit(1)
        stop_server(args.server_id, args.region, args.force)
    elif args.start:
        if not args.server_id or not args.region:
            print("❌ 错误: --start 需要 --server-id 和 --region 参数")
            sys.exit(1)
        start_server(args.server_id, args.region)
    elif args.reboot:
        if not args.server_id or not args.region:
            print("❌ 错误: --reboot 需要 --server-id 和 --region 参数")
            sys.exit(1)
        reboot_server(args.server_id, args.region, args.force)
    elif args.status:
        if not args.server_id or not args.region:
            print("❌ 错误: --status 需要 --server-id 和 --region 参数")
            sys.exit(1)
        query_server_status(args.server_id, args.region)
    elif args.job:
        if not args.job_id or not args.region:
            print("❌ 错误: --job 需要 --job-id 和 --region 参数")
            sys.exit(1)
        query_job_status(args.job_id, args.region)
    else:
        # 默认列出实例
        list_instances()


if __name__ == '__main__':
    main()
