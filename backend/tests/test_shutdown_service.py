"""
关机服务测试脚本

测试华为云批量关机 API 和 Job 状态跟踪功能
"""
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.huawei_cloud.client import HuaweiCloudClient
from app.services.huawei_cloud.shutdown_service import ShutdownService, ShutdownType
from app.services.huawei_cloud.job_service import JobService
from app.services.huawei_cloud.ecs_service import ECSService


def test_batch_stop_servers_mock():
    """测试批量关机（模拟模式）"""
    print("\n" + "="*60)
    print("测试：批量关机（模拟模式）")
    print("="*60)
    
    # 创建客户端（使用假凭证进行模拟）
    client = HuaweiCloudClient(
        access_key="test_ak",
        secret_key="test_sk",
        region="cn-north-4"
    )
    
    # 创建服务
    project_id = "test_project_id"
    shutdown_service = ShutdownService(client, project_id)
    
    # 模拟服务器 ID 列表
    server_ids = [
        "server-001",
        "server-002",
        "server-003"
    ]
    
    print(f"\n模拟关闭服务器:")
    print(f"  服务器数量: {len(server_ids)}")
    print(f"  服务器 IDs: {server_ids}")
    print(f"  关机类型: SOFT (正常关机)")
    
    # 获取关机摘要（不实际调用 API）
    summary = shutdown_service.get_shutdown_summary(server_ids, ShutdownType.SOFT)
    print(f"\n关机操作摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 模拟测试完成")


def test_batch_stop_servers_real():
    """测试批量关机（真实 API 调用）"""
    print("\n" + "="*60)
    print("测试：批量关机（真实 API）")
    print("="*60)
    
    # 从环境变量获取凭证
    ak = os.getenv('HUAWEI_AK')
    sk = os.getenv('HUAWEI_SK')
    region = os.getenv('HUAWEI_REGION', 'cn-north-4')
    project_id = os.getenv('HUAWEI_PROJECT_ID')
    
    if not all([ak, sk, project_id]):
        print("❌ 错误: 缺少必要的环境变量")
        print("   需要设置: HUAWEI_AK, HUAWEI_SK, HUAWEI_PROJECT_ID")
        print("   可选设置: HUAWEI_REGION (默认: cn-north-4)")
        return
    
    print(f"\n配置信息:")
    print(f"  Region: {region}")
    print(f"  Project ID: {project_id}")
    print(f"  AK: {ak[:8]}...")
    
    # 创建客户端
    client = HuaweiCloudClient(
        access_key=ak,
        secret_key=sk,
        region=region
    )
    
    # 创建服务
    shutdown_service = ShutdownService(client, project_id)
    ecs_service = ECSService(client, project_id)
    job_service = JobService(client, project_id)
    
    # 先查询运行中的服务器
    print(f"\n查询运行中的服务器...")
    try:
        running_servers = ecs_service.list_servers(status="ACTIVE")
        print(f"  找到 {len(running_servers)} 台运行中的服务器")
        
        if not running_servers:
            print("  没有运行中的服务器，跳过关机测试")
            return
        
        # 显示服务器信息
        for server in running_servers[:5]:  # 最多显示前 5 台
            print(f"    - {server.name} ({server.id}): {server.status}")
        
        if len(running_servers) > 5:
            print(f"    ... 还有 {len(running_servers) - 5} 台服务器")
        
        # 询问是否继续
        server_ids = [s.id for s in running_servers]
        print(f"\n⚠️  警告: 即将关闭 {len(server_ids)} 台服务器")
        confirm = input("是否继续？(yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("已取消操作")
            return
        
        # 批量关机
        print(f"\n批量关闭服务器...")
        task = shutdown_service.batch_stop_servers(server_ids, ShutdownType.SOFT)
        print(f"  Job ID: {task.job_id}")
        
        # 查询任务状态
        print(f"\n查询任务状态...")
        job_info = job_service.get_job_status(task.job_id)
        print(f"  状态: {job_info.status}")
        print(f"  类型: {job_info.job_type}")
        
        # 等待任务完成（可选）
        wait = input("\n是否等待任务完成？(yes/no): ").strip().lower()
        if wait == 'yes':
            print(f"\n等待任务完成（最多5分钟）...")
            try:
                final_job = job_service.wait_for_job_completion(
                    task.job_id,
                    timeout=300,
                    poll_interval=5
                )
                print(f"\n✅ 任务完成")
                print(f"  最终状态: {final_job.status}")
                if final_job.is_failed():
                    print(f"  失败原因: {final_job.fail_reason}")
            except TimeoutError as e:
                print(f"⚠️  {e}")
        else:
            print(f"\n提示: 可使用以下命令查询任务状态:")
            print(f"  job_id = '{task.job_id}'")
        
        print("\n✅ 真实测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_job_status():
    """测试 Job 状态查询"""
    print("\n" + "="*60)
    print("测试：Job 状态查询")
    print("="*60)
    
    # 从环境变量获取凭证
    ak = os.getenv('HUAWEI_AK')
    sk = os.getenv('HUAWEI_SK')
    region = os.getenv('HUAWEI_REGION', 'cn-north-4')
    project_id = os.getenv('HUAWEI_PROJECT_ID')
    job_id = os.getenv('HUAWEI_JOB_ID')
    
    if not all([ak, sk, project_id, job_id]):
        print("❌ 错误: 缺少必要的环境变量")
        print("   需要设置: HUAWEI_AK, HUAWEI_SK, HUAWEI_PROJECT_ID, HUAWEI_JOB_ID")
        return
    
    print(f"\n配置信息:")
    print(f"  Region: {region}")
    print(f"  Project ID: {project_id}")
    print(f"  Job ID: {job_id}")
    
    # 创建客户端
    client = HuaweiCloudClient(
        access_key=ak,
        secret_key=sk,
        region=region
    )
    
    # 创建服务
    job_service = JobService(client, project_id)
    
    try:
        # 查询任务状态
        print(f"\n查询任务状态...")
        job_info = job_service.get_job_status(job_id)
        
        print(f"\n任务信息:")
        print(f"  Job ID: {job_info.job_id}")
        print(f"  状态: {job_info.status}")
        print(f"  类型: {job_info.job_type}")
        print(f"  开始时间: {job_info.begin_time}")
        print(f"  结束时间: {job_info.end_time}")
        
        if job_info.is_failed():
            print(f"  错误码: {job_info.error_code}")
            print(f"  失败原因: {job_info.fail_reason}")
        
        # 获取摘要
        summary = job_service.get_job_summary(job_id)
        print(f"\n任务摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="华为云关机服务测试")
    parser.add_argument(
        '--real',
        action='store_true',
        help='使用真实 API（需要设置环境变量 HUAWEI_AK, HUAWEI_SK, HUAWEI_PROJECT_ID）'
    )
    parser.add_argument(
        '--job',
        action='store_true',
        help='测试 Job 状态查询（需要设置环境变量 HUAWEI_JOB_ID）'
    )
    
    args = parser.parse_args()
    
    if args.job:
        test_job_status()
    elif args.real:
        test_batch_stop_servers_real()
    else:
        test_batch_stop_servers_mock()


if __name__ == '__main__':
    main()
