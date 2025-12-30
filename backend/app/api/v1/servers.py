"""
服务器管理 API

查询 Flexus L 实例列表和流量信息
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response
from app.services.account_service import AccountService
from app.services.huawei_cloud.flexusl_service import FlexusLService, FlexusLException
from app.utils.encryption import get_encryption_service

router = APIRouter(prefix="/servers", tags=["服务器管理"])
account_service = AccountService()


# 请求模型
class ServerActionRequest(BaseModel):
    """服务器操作请求"""
    server_id: str  # 云主机 ID
    region: str  # 区域 ID
    action_type: str = "SOFT"  # 操作类型: SOFT/HARD


# 区域名称映射
REGION_NAMES = {
    'cn-north-1': '华北-北京一',
    'cn-north-4': '华北-北京四',
    'cn-north-9': '华北-乌兰察布一',
    'cn-east-2': '华东-上海二',
    'cn-east-3': '华东-上海一',
    'cn-south-1': '华南-广州',
    'cn-south-2': '华南-深圳',
    'cn-southwest-2': '西南-贵阳一',
    'ap-southeast-1': '亚太-新加坡',
    'ap-southeast-2': '亚太-曼谷',
    'ap-southeast-3': '亚太-雅加达',
    'af-south-1': '非洲-约翰内斯堡',
}


@router.get("")
async def list_all_servers(db: Session = Depends(get_db)):
    """
    获取所有账户的 Flexus L 实例列表
    
    遍历所有启用的账户，查询其 Flexus L 实例
    """
    accounts = account_service.list_accounts(db=db, is_enabled=True)
    
    if not accounts:
        return success_response(data=[], message="没有启用的账户")
    
    all_servers = []
    encryption_service = get_encryption_service()
    
    for account in accounts:
        try:
            ak = encryption_service.decrypt(account.ak)
            sk = encryption_service.decrypt(account.sk)
            is_intl = getattr(account, 'is_international', True)
            
            service = FlexusLService(
                ak=ak,
                sk=sk,
                region=account.region,
                is_international=is_intl
            )
            
            instances = service.list_instances()
            
            for inst in instances:
                server_dict = inst.to_dict()
                server_dict['account_id'] = account.id
                server_dict['account_name'] = account.name
                server_dict['region_name'] = REGION_NAMES.get(inst.region, inst.region)
                all_servers.append(server_dict)
                
        except Exception as e:
            logger.warning(f"账户 {account.name} 查询失败: {e}")
            continue
    
    return success_response(
        data=all_servers,
        message=f"查询成功，共 {len(all_servers)} 台实例"
    )


@router.get("/{account_id}")
async def list_servers_by_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定账户的 Flexus L 实例列表
    
    Flexus L 实例是全局查询，不需要选择区域
    """
    logger.info(f"查询账户 Flexus L 实例: account_id={account_id}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        # 创建 FlexusL 服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        # 查询实例列表
        instances = service.list_instances()
        
        # 转换为字典列表
        server_list = []
        for inst in instances:
            server_dict = inst.to_dict()
            server_dict['account_id'] = account.id
            server_dict['account_name'] = account.name
            server_dict['region_name'] = REGION_NAMES.get(inst.region, inst.region)
            server_list.append(server_dict)
        
        logger.info(f"查询到 {len(server_list)} 台 Flexus L 实例")
        
        return success_response(
            data=server_list,
            message=f"查询成功，共 {len(server_list)} 台实例"
        )
        
    except FlexusLException as e:
        logger.error(f"FlexusL 服务调用失败: {e}")
        return success_response(
            data=[],
            message=f"查询失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"查询实例列表失败: {e}")
        return success_response(
            data=[],
            message=f"查询失败: {str(e)}"
        )


@router.get("/{account_id}/traffic")
async def get_account_traffic(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定账户的流量汇总信息
    
    返回账户下所有 Flexus L 实例的流量使用情况
    """
    logger.info(f"查询账户流量汇总: account_id={account_id}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        # 创建 FlexusL 服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        # 获取流量汇总
        summary = service.get_all_traffic_summary()
        
        # 添加账户信息
        summary['account_id'] = account.id
        summary['account_name'] = account.name
        
        logger.info(
            f"流量汇总: {summary['instance_count']} 实例, "
            f"剩余 {summary['remaining_amount']} GB"
        )
        
        return success_response(
            data=summary,
            message="查询成功"
        )
        
    except FlexusLException as e:
        logger.error(f"FlexusL 服务调用失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"查询流量失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )


@router.get("/{account_id}/instance/{instance_id}/traffic")
async def get_instance_traffic(
    account_id: int,
    instance_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定实例的流量使用情况
    
    - **account_id**: 账户 ID
    - **instance_id**: Flexus L 实例 ID
    """
    logger.info(f"查询实例流量: account_id={account_id}, instance_id={instance_id}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        # 创建 FlexusL 服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        # 获取实例列表，找到指定实例
        instances = service.list_instances()
        target_instance = None
        for inst in instances:
            if inst.id == instance_id:
                target_instance = inst
                break
        
        if not target_instance:
            raise HTTPException(status_code=404, detail="实例不存在")
        
        # 检查是否有流量包
        if not target_instance.traffic_package_id:
            return success_response(
                data={
                    'instance_id': instance_id,
                    'instance_name': target_instance.name,
                    'has_traffic_package': False,
                    'message': '该实例没有关联的流量包'
                },
                message="该实例没有流量包"
            )
        
        # 查询流量包使用情况
        traffic_packages = service.query_traffic_usage([target_instance.traffic_package_id])
        
        if not traffic_packages:
            return success_response(
                data={
                    'instance_id': instance_id,
                    'instance_name': target_instance.name,
                    'traffic_package_id': target_instance.traffic_package_id,
                    'has_traffic_package': True,
                    'message': '无法获取流量包使用信息'
                },
                message="查询流量包信息失败"
            )
        
        # 返回流量信息
        traffic_info = traffic_packages[0].to_dict()
        
        return success_response(
            data={
                'instance_id': instance_id,
                'instance_name': target_instance.name,
                'region': target_instance.region,
                'region_name': REGION_NAMES.get(target_instance.region, target_instance.region),
                'has_traffic_package': True,
                'traffic': traffic_info
            },
            message="查询成功"
        )
        
    except FlexusLException as e:
        logger.error(f"FlexusL 服务调用失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询实例流量失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )


@router.post("/sync/{account_id}")
async def sync_servers(
    account_id: int,
    db: Session = Depends(get_db)
):
    """同步指定账户的 Flexus L 实例信息"""
    return await list_servers_by_account(account_id=account_id, db=db)


@router.get("/{account_id}/server/{server_id}/status")
async def get_server_real_status(
    account_id: int,
    server_id: str,
    region: str = Query(..., description="区域 ID，如 ap-southeast-2"),
    db: Session = Depends(get_db)
):
    """
    查询云主机实时状态
    
    通过 ECS API 获取云主机的实时运行状态，而不是 Config 服务的缓存状态
    
    - **account_id**: 账户 ID
    - **server_id**: 云主机 ID (FlexusLInstance.server_id)
    - **region**: 区域 ID，如 ap-southeast-2
    
    返回的 status 可能值:
    - ACTIVE: 运行中
    - SHUTOFF: 已关机
    - REBOOT: 重启中
    - HARD_REBOOT: 强制重启中
    - PAUSED: 暂停
    - SUSPENDED: 挂起
    - ERROR: 错误
    """
    logger.info(f"查询云主机实时状态: account_id={account_id}, server_id={server_id}, region={region}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        # 创建 FlexusL 服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        # 查询云主机实时状态
        server_status = service.get_server_status(server_id=server_id, region=region)
        
        return success_response(
            data=server_status,
            message=f"云主机状态: {server_status.get('status')}"
        )
        
    except FlexusLException as e:
        logger.error(f"查询云主机状态失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"查询云主机状态异常: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )


@router.get("/{account_id}/jobs/{job_id}")
async def get_job_status(
    account_id: int,
    job_id: str,
    region: str = Query(..., description="区域 ID，如 ap-southeast-2"),
    db: Session = Depends(get_db)
):
    """
    查询任务执行状态
    
    用于查询异步请求任务的执行状态，如关机、开机、重启等操作的执行结果
    
    - **account_id**: 账户 ID
    - **job_id**: 任务 ID（由异步操作返回）
    - **region**: 区域 ID，如 ap-southeast-2
    
    返回的 status 可能值:
    - SUCCESS: 成功
    - FAIL: 失败
    - RUNNING: 运行中
    - INIT: 初始化
    """
    logger.info(f"查询 Job 状态: account_id={account_id}, job_id={job_id}, region={region}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        # 创建 FlexusL 服务
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        # 查询 Job 状态
        job_status = service.get_job_status(job_id=job_id, region=region)
        
        return success_response(
            data=job_status.to_dict(),
            message=f"任务状态: {job_status.status}"
        )
        
    except FlexusLException as e:
        logger.error(f"查询 Job 状态失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"查询 Job 状态异常: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )


@router.post("/{account_id}/server/start")
async def start_server(
    account_id: int,
    request: ServerActionRequest,
    db: Session = Depends(get_db)
):
    """
    启动云主机
    
    - **account_id**: 账户 ID
    - **server_id**: 云主机 ID
    - **region**: 区域 ID
    
    返回 job_id 用于查询任务状态
    """
    logger.info(f"启动云主机: account_id={account_id}, server_id={request.server_id}, region={request.region}")
    
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        result = service.start_server(server_id=request.server_id, region=request.region)
        
        if result.success:
            return success_response(
                data={
                    'job_id': result.job_id,
                    'server_id': request.server_id,
                    'region': request.region,
                    'action': 'start'
                },
                message="启动请求已提交"
            )
        else:
            return success_response(
                data=None,
                message=f"启动失败: {result.message}"
            )
        
    except FlexusLException as e:
        logger.error(f"启动云主机失败: {e}")
        return success_response(data=None, message=f"启动失败: {str(e)}")
    except Exception as e:
        logger.error(f"启动云主机异常: {e}")
        return success_response(data=None, message=f"启动失败: {str(e)}")


@router.post("/{account_id}/server/stop")
async def stop_server(
    account_id: int,
    request: ServerActionRequest,
    db: Session = Depends(get_db)
):
    """
    关闭云主机
    
    - **account_id**: 账户 ID
    - **server_id**: 云主机 ID
    - **region**: 区域 ID
    - **action_type**: SOFT(正常关机) 或 HARD(强制关机)
    
    返回 job_id 用于查询任务状态
    """
    logger.info(f"关闭云主机: account_id={account_id}, server_id={request.server_id}, region={request.region}, type={request.action_type}")
    
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        result = service.stop_server(
            server_id=request.server_id,
            region=request.region,
            stop_type=request.action_type
        )
        
        if result.success:
            return success_response(
                data={
                    'job_id': result.job_id,
                    'server_id': request.server_id,
                    'region': request.region,
                    'action': 'stop'
                },
                message="关机请求已提交"
            )
        else:
            return success_response(
                data=None,
                message=f"关机失败: {result.message}"
            )
        
    except FlexusLException as e:
        logger.error(f"关闭云主机失败: {e}")
        return success_response(data=None, message=f"关机失败: {str(e)}")
    except Exception as e:
        logger.error(f"关闭云主机异常: {e}")
        return success_response(data=None, message=f"关机失败: {str(e)}")


@router.post("/{account_id}/server/reboot")
async def reboot_server(
    account_id: int,
    request: ServerActionRequest,
    db: Session = Depends(get_db)
):
    """
    重启云主机
    
    - **account_id**: 账户 ID
    - **server_id**: 云主机 ID
    - **region**: 区域 ID
    - **action_type**: SOFT(正常重启) 或 HARD(强制重启)
    
    返回 job_id 用于查询任务状态
    """
    logger.info(f"重启云主机: account_id={account_id}, server_id={request.server_id}, region={request.region}, type={request.action_type}")
    
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        is_intl = getattr(account, 'is_international', True)
        
        service = FlexusLService(
            ak=ak,
            sk=sk,
            region=account.region,
            is_international=is_intl
        )
        
        result = service.reboot_server(
            server_id=request.server_id,
            region=request.region,
            reboot_type=request.action_type
        )
        
        if result.success:
            return success_response(
                data={
                    'job_id': result.job_id,
                    'server_id': request.server_id,
                    'region': request.region,
                    'action': 'reboot'
                },
                message="重启请求已提交"
            )
        else:
            return success_response(
                data=None,
                message=f"重启失败: {result.message}"
            )
        
    except FlexusLException as e:
        logger.error(f"重启云主机失败: {e}")
        return success_response(data=None, message=f"重启失败: {str(e)}")
    except Exception as e:
        logger.error(f"重启云主机异常: {e}")
        return success_response(data=None, message=f"重启失败: {str(e)}")
