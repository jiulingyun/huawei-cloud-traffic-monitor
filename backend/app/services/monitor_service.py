"""
监控服务

提供监控任务创建和管理的辅助函数
"""
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.config import Config
from app.services.scheduler import monitor_scheduler
from app.services.config_service import config_service
from app.services.monitor_workflow import MonitorWorkflowExecutor
from app.core.database import get_db


def execute_monitor_task(account_id: int):
    """
    执行监控任务的回调函数

    这个函数会被调度器调用，会动态获取最新的配置信息
    """
    logger.info(f"执行监控任务: account_id={account_id}")

    try:
        # 获取数据库会话
        db = next(get_db())

        try:
            # 获取账户信息
            from app.models.account import Account
            account = db.query(Account).filter(Account.id == account_id).first()

            if not account:
                logger.error(f"账户不存在: account_id={account_id}")
                return

            if not account.is_enabled:
                logger.info(f"账户已被禁用，跳过监控: account_id={account_id}")
                return

            # 获取最新的有效配置
            config = config_service.get_effective_config(db, account_id)

            if not config:
                logger.warning(f"账户 {account.name} 没有配置，跳过监控")
                return

            # 解密飞书 Webhook URL
            feishu_webhook_url = None
            if config.feishu_webhook_url:
                feishu_webhook_url = config_service.get_decrypted_webhook_url(config)

            # 获取账户的默认区域
            region = account.region or 'cn-north-4'

            # 创建工作流执行器
            executor = MonitorWorkflowExecutor(
                feishu_webhook_url=feishu_webhook_url,
                enable_notifications=config.notification_enabled,
                enable_auto_shutdown=config.auto_shutdown_enabled
            )

            # 执行监控工作流
            result = executor.execute_monitor_workflow(
                db=db,
                config_id=account_id,  # 使用 account_id 作为 config_id
                account_id=account_id,
                account_name=account.name,
                encrypted_ak=account.ak,
                encrypted_sk=account.sk,
                region=region,
                project_id='',  # 项目 ID 将在执行时动态获取
                traffic_threshold=config.traffic_threshold,
                auto_shutdown_enabled=config.auto_shutdown_enabled,
                shutdown_delay=config.shutdown_delay,
                retry_times=config.retry_times,
                is_international=account.is_international
            )

            if result['success']:
                logger.info(f"监控任务执行成功: account_id={account_id}")
            else:
                logger.error(f"监控任务执行失败: account_id={account_id}, error={result.get('error')}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"监控任务异常: account_id={account_id}, error={e}")


def create_monitor_job_for_account(
    db: Session,
    account: Account,
    config: Config
) -> bool:
    """
    为账户创建监控任务
    
    Args:
        db: 数据库会话
        account: 账户对象
        config: 配置对象
        
    Returns:
        是否创建成功
    """
    try:
        job_id = f"monitor_account_{account.id}"
        
        # 检查任务是否已存在
        if monitor_scheduler.get_job_info(job_id):
            logger.warning(f"监控任务已存在: {job_id}")
            return False
        
        # 解密飞书 Webhook URL
        feishu_webhook_url = None
        if config.feishu_webhook_url:
            feishu_webhook_url = config_service.get_decrypted_webhook_url(config)
        
        # 获取账户的默认区域
        region = account.region or 'cn-north-4'
        
        # 添加定时任务
        success = monitor_scheduler.add_interval_job(
            job_id=job_id,
            func=execute_monitor_task,
            minutes=config.check_interval,
            # 只传递 account_id，任务执行时动态获取最新配置
            account_id=account.id
        )
        
        if success:
            logger.info(
                f"创建监控任务成功: job_id={job_id}, "
                f"interval={config.check_interval}分钟"
            )
        else:
            logger.error(f"创建监控任务失败: job_id={job_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"创建监控任务异常: account_id={account.id}, error={e}")
        return False


def initialize_all_monitor_jobs(db: Session) -> dict:
    """
    初始化所有账户的监控任务
    
    Args:
        db: 数据库会话
        
    Returns:
        初始化结果统计
    """
    from app.models.account import Account
    
    logger.info("开始初始化所有监控任务")
    
    # 确保调度器已启动
    if not monitor_scheduler.is_running():
        monitor_scheduler.start()
    
    # 获取所有启用的账户
    accounts = db.query(Account).filter(Account.is_enabled == True).all()
    
    stats = {
        "total": len(accounts),
        "success": 0,
        "skipped": 0,
        "failed": 0
    }
    
    for account in accounts:
        try:
            # 获取账户的有效配置
            config = config_service.get_effective_config(db, account.id)
            
            if not config:
                logger.warning(f"账户 {account.name} 没有配置，跳过")
                stats["skipped"] += 1
                continue
            
            # 检查任务是否已存在
            job_id = f"monitor_account_{account.id}"
            if monitor_scheduler.get_job_info(job_id):
                logger.info(f"账户 {account.name} 的监控任务已存在，跳过")
                stats["skipped"] += 1
                continue
            
            # 创建监控任务
            if create_monitor_job_for_account(db, account, config):
                stats["success"] += 1
            else:
                stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"初始化账户 {account.name} 的监控任务失败: {e}")
            stats["failed"] += 1
    
    logger.info(
        f"监控任务初始化完成: "
        f"total={stats['total']}, "
        f"success={stats['success']}, "
        f"skipped={stats['skipped']}, "
        f"failed={stats['failed']}"
    )
    
    return stats


def reschedule_monitor_job_for_config(db: Session, config_id: int):
    """
    重新调度受配置变更影响的监控任务

    Args:
        db: 数据库会话
        config_id: 配置 ID
    """
    try:
        # 获取配置
        config = config_service.get_config(db, config_id)
        if not config:
            logger.warning(f"配置不存在: config_id={config_id}")
            return

        # 如果是全局配置，需要重新调度所有账户的任务
        if config.account_id is None:
            logger.info("全局配置变更，重新调度所有监控任务")
            reschedule_all_monitor_jobs(db)
        else:
            # 如果是账户配置，只重新调度该账户的任务
            logger.info(f"账户配置变更，重新调度账户 {config.account_id} 的监控任务")
            reschedule_monitor_job_for_account(db, config.account_id)

    except Exception as e:
        logger.error(f"重新调度监控任务失败: config_id={config_id}, error={e}")


def reschedule_monitor_job_for_account(db: Session, account_id: int):
    """
    重新调度指定账户的监控任务

    Args:
        db: 数据库会话
        account_id: 账户 ID
    """
    try:
        from app.models.account import Account

        # 获取账户
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            logger.warning(f"账户不存在: account_id={account_id}")
            return

        if not account.is_enabled:
            logger.info(f"账户已被禁用，移除监控任务: account_id={account_id}")
            job_id = f"monitor_account_{account_id}"
            monitor_scheduler.remove_job(job_id)
            return

        # 获取账户的有效配置
        config = config_service.get_effective_config(db, account_id)
        if not config:
            logger.warning(f"账户 {account.name} 没有配置，移除监控任务")
            job_id = f"monitor_account_{account_id}"
            monitor_scheduler.remove_job(job_id)
            return

        # 移除现有任务
        job_id = f"monitor_account_{account_id}"
        monitor_scheduler.remove_job(job_id)

        # 创建新任务
        create_monitor_job_for_account(db, account, config)

    except Exception as e:
        logger.error(f"重新调度账户监控任务失败: account_id={account_id}, error={e}")


def reschedule_all_monitor_jobs(db: Session):
    """
    重新调度所有监控任务

    Args:
        db: 数据库会话
    """
    try:
        from app.models.account import Account

        logger.info("开始重新调度所有监控任务")

        # 获取所有启用的账户
        accounts = db.query(Account).filter(Account.is_enabled == True).all()

        for account in accounts:
            try:
                reschedule_monitor_job_for_account(db, account.id)
            except Exception as e:
                logger.error(f"重新调度账户 {account.name} 的监控任务失败: {e}")

        logger.info(f"重新调度完成，共处理 {len(accounts)} 个账户")

    except Exception as e:
        logger.error(f"重新调度所有监控任务失败: {e}")


def shutdown_all_monitor_jobs():
    """
    关闭所有监控任务
    """
    logger.info("关闭所有监控任务")

    jobs = monitor_scheduler.list_jobs()
    stopped = 0

    for job in jobs:
        if job['id'].startswith('monitor_'):
            if monitor_scheduler.remove_job(job['id']):
                stopped += 1

    logger.info(f"已停止 {stopped} 个监控任务")

    # 关闭调度器
    if monitor_scheduler.is_running():
        monitor_scheduler.shutdown(wait=True)
