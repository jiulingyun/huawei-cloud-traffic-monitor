"""
配置管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.services.config_service import config_service

router = APIRouter(prefix="/configs", tags=["配置管理"])


# Pydantic 模型
class ConfigCreate(BaseModel):
    """创建配置请求模型"""
    account_id: Optional[int] = Field(None, description="关联账户 ID（为空表示全局配置）")
    check_interval: int = Field(5, ge=1, le=1440, description="检查间隔（分钟），范围 1-1440")
    traffic_threshold: float = Field(10.0, ge=0.1, description="流量阈值（GB），最小 0.1")
    auto_shutdown_enabled: bool = Field(True, description="是否启用自动关机")
    feishu_webhook_url: Optional[str] = Field(None, description="飞书 Webhook URL", max_length=500)
    notification_enabled: bool = Field(True, description="是否启用通知")
    shutdown_delay: int = Field(0, ge=0, le=60, description="关机延迟（分钟），范围 0-60")
    retry_times: int = Field(3, ge=1, le=10, description="失败重试次数，范围 1-10")


class ConfigUpdate(BaseModel):
    """更新配置请求模型"""
    check_interval: Optional[int] = Field(None, ge=1, le=1440, description="检查间隔（分钟）")
    traffic_threshold: Optional[float] = Field(None, ge=0.1, description="流量阈值（GB）")
    auto_shutdown_enabled: Optional[bool] = Field(None, description="是否启用自动关机")
    feishu_webhook_url: Optional[str] = Field(None, description="飞书 Webhook URL", max_length=500)
    notification_enabled: Optional[bool] = Field(None, description="是否启用通知")
    shutdown_delay: Optional[int] = Field(None, ge=0, le=60, description="关机延迟（分钟）")
    retry_times: Optional[int] = Field(None, ge=1, le=10, description="失败重试次数")


class ConfigResponse(BaseModel):
    """配置响应模型"""
    id: int
    account_id: Optional[int]
    check_interval: int
    traffic_threshold: float
    auto_shutdown_enabled: bool
    notification_enabled: bool
    shutdown_delay: int
    retry_times: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ConfigResponse])
async def list_configs(
    account_id: Optional[int] = Query(None, description="过滤账户 ID"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取配置列表
    
    - **account_id**: 过滤账户 ID（可选）
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    configs = config_service.list_configs(
        db=db,
        account_id=account_id,
        limit=limit,
        offset=offset
    )
    
    # 转换时间为字符串
    result = []
    for config in configs:
        result.append({
            "id": config.id,
            "account_id": config.account_id,
            "check_interval": config.check_interval,
            "traffic_threshold": config.traffic_threshold,
            "auto_shutdown_enabled": config.auto_shutdown_enabled,
            "notification_enabled": config.notification_enabled,
            "shutdown_delay": config.shutdown_delay,
            "retry_times": config.retry_times,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        })
    
    return result


@router.get("/global", response_model=ConfigResponse)
async def get_global_config(db: Session = Depends(get_db)):
    """
    获取全局配置
    
    返回全局配置（account_id 为 NULL 的配置）
    """
    config = config_service.get_global_config(db=db)
    
    if not config:
        raise HTTPException(status_code=404, detail="全局配置不存在")
    
    return {
        "id": config.id,
        "account_id": config.account_id,
        "check_interval": config.check_interval,
        "traffic_threshold": config.traffic_threshold,
        "auto_shutdown_enabled": config.auto_shutdown_enabled,
        "notification_enabled": config.notification_enabled,
        "shutdown_delay": config.shutdown_delay,
        "retry_times": config.retry_times,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.get("/effective", response_model=ConfigResponse)
async def get_effective_config(
    account_id: Optional[int] = Query(None, description="账户 ID"),
    db: Session = Depends(get_db)
):
    """
    获取有效配置
    
    返回账户配置（如果存在），否则返回全局配置
    
    - **account_id**: 账户 ID（可选）
    """
    config = config_service.get_effective_config(db=db, account_id=account_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "id": config.id,
        "account_id": config.account_id,
        "check_interval": config.check_interval,
        "traffic_threshold": config.traffic_threshold,
        "auto_shutdown_enabled": config.auto_shutdown_enabled,
        "notification_enabled": config.notification_enabled,
        "shutdown_delay": config.shutdown_delay,
        "retry_times": config.retry_times,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(config_id: int, db: Session = Depends(get_db)):
    """
    获取配置详情
    
    - **config_id**: 配置 ID
    """
    config = config_service.get_config(db=db, config_id=config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "id": config.id,
        "account_id": config.account_id,
        "check_interval": config.check_interval,
        "traffic_threshold": config.traffic_threshold,
        "auto_shutdown_enabled": config.auto_shutdown_enabled,
        "notification_enabled": config.notification_enabled,
        "shutdown_delay": config.shutdown_delay,
        "retry_times": config.retry_times,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.post("", response_model=ConfigResponse, status_code=201)
async def create_config(request: ConfigCreate, db: Session = Depends(get_db)):
    """
    创建配置
    
    - **account_id**: 关联账户 ID（为空表示全局配置）
    - **check_interval**: 检查间隔（分钟），默认 5
    - **traffic_threshold**: 流量阈值（GB），默认 10.0
    - **auto_shutdown_enabled**: 是否启用自动关机，默认 true
    - **feishu_webhook_url**: 飞书 Webhook URL（可选）
    - **notification_enabled**: 是否启用通知，默认 true
    - **shutdown_delay**: 关机延迟（分钟），默认 0
    - **retry_times**: 失败重试次数，默认 3
    """
    try:
        config = config_service.create_config(
            db=db,
            account_id=request.account_id,
            check_interval=request.check_interval,
            traffic_threshold=request.traffic_threshold,
            auto_shutdown_enabled=request.auto_shutdown_enabled,
            feishu_webhook_url=request.feishu_webhook_url,
            notification_enabled=request.notification_enabled,
            shutdown_delay=request.shutdown_delay,
            retry_times=request.retry_times
        )
        
        return {
            "id": config.id,
            "account_id": config.account_id,
            "check_interval": config.check_interval,
            "traffic_threshold": config.traffic_threshold,
            "auto_shutdown_enabled": config.auto_shutdown_enabled,
            "notification_enabled": config.notification_enabled,
            "shutdown_delay": config.shutdown_delay,
            "retry_times": config.retry_times,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")


@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    request: ConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    更新配置
    
    - **config_id**: 配置 ID
    - **check_interval**: 检查间隔（分钟）（可选）
    - **traffic_threshold**: 流量阈值（GB）（可选）
    - **auto_shutdown_enabled**: 是否启用自动关机（可选）
    - **feishu_webhook_url**: 飞书 Webhook URL（可选）
    - **notification_enabled**: 是否启用通知（可选）
    - **shutdown_delay**: 关机延迟（分钟）（可选）
    - **retry_times**: 失败重试次数（可选）
    """
    config = config_service.update_config(
        db=db,
        config_id=config_id,
        check_interval=request.check_interval,
        traffic_threshold=request.traffic_threshold,
        auto_shutdown_enabled=request.auto_shutdown_enabled,
        feishu_webhook_url=request.feishu_webhook_url,
        notification_enabled=request.notification_enabled,
        shutdown_delay=request.shutdown_delay,
        retry_times=request.retry_times
    )
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "id": config.id,
        "account_id": config.account_id,
        "check_interval": config.check_interval,
        "traffic_threshold": config.traffic_threshold,
        "auto_shutdown_enabled": config.auto_shutdown_enabled,
        "notification_enabled": config.notification_enabled,
        "shutdown_delay": config.shutdown_delay,
        "retry_times": config.retry_times,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """
    删除配置

    - **config_id**: 配置 ID
    """
    success = config_service.delete_config(db=db, config_id=config_id)

    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")

    return None


@router.post("/reschedule/{config_id}", status_code=200)
async def reschedule_monitor_jobs(config_id: int, db: Session = Depends(get_db)):
    """
    重新调度监控任务

    当配置变更后，可以调用此接口手动重新调度相关的监控任务。

    - **config_id**: 配置 ID
    """
    try:
        from app.services.monitor_service import reschedule_monitor_job_for_config
        reschedule_monitor_job_for_config(db, config_id)
        return success_response(message="监控任务重新调度完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新调度监控任务失败: {str(e)}")


@router.post("/reschedule-all", status_code=200)
async def reschedule_all_monitor_jobs(db: Session = Depends(get_db)):
    """
    重新调度所有监控任务

    重新调度所有账户的监控任务，通常在系统配置变更后使用。
    """
    try:
        from app.services.monitor_service import reschedule_all_monitor_jobs
        reschedule_all_monitor_jobs(db)
        return success_response(message="所有监控任务重新调度完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新调度所有监控任务失败: {str(e)}")
