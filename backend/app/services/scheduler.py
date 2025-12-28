"""
监控调度器服务

使用 APScheduler 实现定时监控任务调度
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger


class MonitorScheduler:
    """监控调度器"""
    
    def __init__(self):
        """初始化调度器"""
        # 配置 jobstores 和 executors
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }
        
        job_defaults = {
            'coalesce': True,  # 合并错过的任务
            'max_instances': 1,  # 每个任务最多只能有一个实例运行
            'misfire_grace_time': 60  # 任务错过执行时间后的宽限时间（秒）
        }
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self._started = False
        logger.info("初始化监控调度器")
    
    def start(self):
        """启动调度器"""
        if not self._started:
            self.scheduler.start()
            self._started = True
            logger.info("监控调度器已启动")
        else:
            logger.warning("监控调度器已经在运行")
    
    def shutdown(self, wait: bool = True):
        """
        关闭调度器
        
        Args:
            wait: 是否等待所有任务完成
        """
        if self._started:
            self.scheduler.shutdown(wait=wait)
            self._started = False
            logger.info("监控调度器已关闭")
        else:
            logger.warning("监控调度器未在运行")
    
    def is_running(self) -> bool:
        """检查调度器是否在运行"""
        return self._started and self.scheduler.running
    
    def add_interval_job(
        self,
        job_id: str,
        func: Callable,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        添加间隔执行的任务
        
        Args:
            job_id: 任务唯一标识
            func: 要执行的函数
            seconds: 秒间隔
            minutes: 分钟间隔
            hours: 小时间隔
            **kwargs: 传递给任务函数的参数
            
        Returns:
            是否添加成功
        """
        try:
            # 检查任务是否已存在
            if self.scheduler.get_job(job_id):
                logger.warning(f"任务已存在: {job_id}")
                return False
            
            # 创建间隔触发器
            trigger = IntervalTrigger(
                seconds=seconds or 0,
                minutes=minutes or 0,
                hours=hours or 0
            )
            
            # 添加任务
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=False
            )
            
            logger.info(
                f"添加间隔任务: id={job_id}, "
                f"interval={hours}h {minutes}m {seconds}s"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"添加间隔任务失败: {e}")
            return False
    
    def add_cron_job(
        self,
        job_id: str,
        func: Callable,
        cron_expression: str,
        **kwargs
    ) -> bool:
        """
        添加 cron 表达式任务
        
        Args:
            job_id: 任务唯一标识
            func: 要执行的函数
            cron_expression: cron 表达式（例如：'0 */2 * * *' 每2小时执行）
            **kwargs: 传递给任务函数的参数
            
        Returns:
            是否添加成功
        """
        try:
            # 检查任务是否已存在
            if self.scheduler.get_job(job_id):
                logger.warning(f"任务已存在: {job_id}")
                return False
            
            # 解析 cron 表达式
            parts = cron_expression.split()
            if len(parts) != 5:
                logger.error(f"无效的 cron 表达式: {cron_expression}")
                return False
            
            minute, hour, day, month, day_of_week = parts
            
            # 创建 cron 触发器
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # 添加任务
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=False
            )
            
            logger.info(f"添加 cron 任务: id={job_id}, cron={cron_expression}")
            
            return True
            
        except Exception as e:
            logger.error(f"添加 cron 任务失败: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除任务
        
        Args:
            job_id: 任务标识
            
        Returns:
            是否移除成功
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.remove_job(job_id)
                logger.info(f"移除任务: id={job_id}")
                return True
            else:
                logger.warning(f"任务不存在: {job_id}")
                return False
        except Exception as e:
            logger.error(f"移除任务失败: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """
        暂停任务
        
        Args:
            job_id: 任务标识
            
        Returns:
            是否暂停成功
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.pause_job(job_id)
                logger.info(f"暂停任务: id={job_id}")
                return True
            else:
                logger.warning(f"任务不存在: {job_id}")
                return False
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """
        恢复任务
        
        Args:
            job_id: 任务标识
            
        Returns:
            是否恢复成功
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.resume_job(job_id)
                logger.info(f"恢复任务: id={job_id}")
                return True
            else:
                logger.warning(f"任务不存在: {job_id}")
                return False
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            job_id: 任务标识
            
        Returns:
            任务信息字典，不存在返回 None
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'func': str(job.func),
                    'trigger': str(job.trigger),
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'pending': job.pending
                }
            return None
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None
    
    def list_jobs(self) -> list:
        """
        列出所有任务
        
        Returns:
            任务信息列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'func': str(job.func),
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'pending': job.pending
            })
        return jobs


# 创建全局调度器实例
monitor_scheduler = MonitorScheduler()
