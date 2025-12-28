#!/usr/bin/env python3
"""
测试监控调度器服务
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.scheduler import MonitorScheduler


# 测试用的简单函数
def test_job_func(message: str):
    """测试任务函数"""
    print(f"[{time.strftime('%H:%M:%S')}] 执行任务: {message}")


def test_scheduler_init():
    """测试调度器初始化"""
    print("=" * 50)
    print("测试调度器初始化")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    
    print(f"✅ 调度器初始化成功")
    print(f"   Is Running: {scheduler.is_running()}")
    
    assert scheduler.is_running() is False
    
    print("\n✅ 调度器初始化测试通过！\n")


def test_scheduler_start_shutdown():
    """测试调度器启动和关闭"""
    print("=" * 50)
    print("测试调度器启动和关闭")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    
    # 启动
    scheduler.start()
    print(f"✅ 调度器已启动: running={scheduler.is_running()}")
    assert scheduler.is_running() is True
    
    # 等待一下
    time.sleep(0.5)
    
    # 关闭
    scheduler.shutdown(wait=False)
    print(f"✅ 调度器已关闭: running={scheduler.is_running()}")
    assert scheduler.is_running() is False
    
    print("\n✅ 调度器启动/关闭测试通过！\n")


def test_add_interval_job():
    """测试添加间隔任务"""
    print("=" * 50)
    print("测试添加间隔任务")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    # 添加任务（每2秒执行一次）
    success = scheduler.add_interval_job(
        job_id="test_job_1",
        func=test_job_func,
        seconds=2,
        message="间隔任务测试"
    )
    
    print(f"✅ 添加间隔任务: success={success}")
    assert success is True
    
    # 获取任务信息
    job_info = scheduler.get_job_info("test_job_1")
    print(f"✅ 任务信息: {job_info}")
    assert job_info is not None
    assert job_info['id'] == 'test_job_1'
    
    # 等待任务执行几次
    print("\n等待任务执行...")
    time.sleep(5)
    
    # 移除任务
    success = scheduler.remove_job("test_job_1")
    print(f"\n✅ 移除任务: success={success}")
    assert success is True
    
    scheduler.shutdown(wait=False)
    
    print("\n✅ 间隔任务测试通过！\n")


def test_add_cron_job():
    """测试添加 cron 任务"""
    print("=" * 50)
    print("测试添加 cron 任务")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    # 添加 cron 任务（每分钟执行一次）
    success = scheduler.add_cron_job(
        job_id="test_cron_1",
        func=test_job_func,
        cron_expression="* * * * *",
        message="cron 任务测试"
    )
    
    print(f"✅ 添加 cron 任务: success={success}")
    assert success is True
    
    # 获取任务信息
    job_info = scheduler.get_job_info("test_cron_1")
    print(f"✅ 任务信息: {job_info}")
    assert job_info is not None
    
    # 移除任务
    scheduler.remove_job("test_cron_1")
    scheduler.shutdown(wait=False)
    
    print("\n✅ cron 任务测试通过！\n")


def test_pause_resume_job():
    """测试暂停和恢复任务"""
    print("=" * 50)
    print("测试暂停和恢复任务")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    # 添加任务
    scheduler.add_interval_job(
        job_id="test_pause_job",
        func=test_job_func,
        seconds=1,
        message="暂停/恢复测试"
    )
    
    print("任务运行中...")
    time.sleep(2)
    
    # 暂停任务
    success = scheduler.pause_job("test_pause_job")
    print(f"\n✅ 暂停任务: success={success}")
    assert success is True
    
    print("任务已暂停（不应该有输出）...")
    time.sleep(2)
    
    # 恢复任务
    success = scheduler.resume_job("test_pause_job")
    print(f"\n✅ 恢复任务: success={success}")
    assert success is True
    
    print("任务已恢复...")
    time.sleep(2)
    
    # 清理
    scheduler.remove_job("test_pause_job")
    scheduler.shutdown(wait=False)
    
    print("\n✅ 暂停/恢复任务测试通过！\n")


def test_list_jobs():
    """测试列出所有任务"""
    print("=" * 50)
    print("测试列出所有任务")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    # 添加多个任务
    scheduler.add_interval_job(
        job_id="job_1",
        func=test_job_func,
        seconds=10,
        message="任务1"
    )
    
    scheduler.add_interval_job(
        job_id="job_2",
        func=test_job_func,
        seconds=20,
        message="任务2"
    )
    
    # 列出所有任务
    jobs = scheduler.list_jobs()
    print(f"✅ 任务列表（{len(jobs)} 个任务）:")
    for i, job in enumerate(jobs, 1):
        print(f"   {i}. ID: {job['id']}, Next Run: {job['next_run_time']}")
    
    assert len(jobs) == 2
    
    # 清理
    scheduler.remove_job("job_1")
    scheduler.remove_job("job_2")
    scheduler.shutdown(wait=False)
    
    print("\n✅ 列出任务测试通过！\n")


def test_job_replace_prevention():
    """测试防止任务重复添加"""
    print("=" * 50)
    print("测试防止任务重复添加")
    print("=" * 50)
    
    scheduler = MonitorScheduler()
    scheduler.start()
    
    # 第一次添加
    success1 = scheduler.add_interval_job(
        job_id="duplicate_job",
        func=test_job_func,
        seconds=10,
        message="测试"
    )
    print(f"✅ 第一次添加: success={success1}")
    assert success1 is True
    
    # 第二次添加（应该失败）
    success2 = scheduler.add_interval_job(
        job_id="duplicate_job",
        func=test_job_func,
        seconds=10,
        message="测试"
    )
    print(f"✅ 第二次添加: success={success2} (应该为 False)")
    assert success2 is False
    
    # 清理
    scheduler.remove_job("duplicate_job")
    scheduler.shutdown(wait=False)
    
    print("\n✅ 防止重复添加测试通过！\n")


if __name__ == "__main__":
    try:
        test_scheduler_init()
        test_scheduler_start_shutdown()
        test_add_interval_job()
        test_add_cron_job()
        test_pause_resume_job()
        test_list_jobs()
        test_job_replace_prevention()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
