"""
服务器管理 API

支持按区域查询服务器列表
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response
from app.services.account_service import AccountService
from app.services.huawei_cloud.client import HuaweiCloudClient
from app.services.huawei_cloud.ecs_service import ECSService
from app.services.huawei_cloud.iam_service import IAMService, IAMException
from app.utils.encryption import get_encryption_service

router = APIRouter(prefix="/servers", tags=["服务器管理"])
account_service = AccountService()


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
    """获取所有账户的服务器列表"""
    return success_response(data=[], message="查询成功")


@router.get("/{account_id}/regions")
async def list_account_regions(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    获取账户可访问的区域列表
    
    返回该账户 AK/SK 可以访问的所有区域（项目）
    """
    logger.info(f"获取账户区域列表: account_id={account_id}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        
        # 使用 IAM 服务获取所有项目（区域）
        iam_service = IAMService(ak=ak, sk=sk)
        projects = iam_service.list_projects()
        
        if not projects:
            return success_response(
                data=[],
                message="未获取到任何区域"
            )
        
        # 转换为区域列表
        regions = []
        for project in projects:
            regions.append({
                "id": project.id,
                "name": project.name,
                "display_name": REGION_NAMES.get(project.name, project.name),
                "enabled": project.enabled
            })
        
        # 按区域名排序
        regions.sort(key=lambda x: x['name'])
        
        logger.info(f"获取到 {len(regions)} 个区域")
        
        return success_response(data=regions, message="查询成功")
        
    except IAMException as e:
        logger.error(f"IAM 服务调用失败: {e}")
        return success_response(
            data=[],
            message=f"IAM 认证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"获取区域列表失败: {e}")
        return success_response(
            data=[],
            message=f"查询失败: {str(e)}"
        )


@router.get("/{account_id}")
async def list_servers_by_account(
    account_id: int,
    region: Optional[str] = Query(None, description="区域名称，如 cn-north-4"),
    project_id: Optional[str] = Query(None, description="项目 ID"),
    limit: int = Query(1000, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    获取指定账户的服务器列表
    
    - 如果指定 region 和 project_id，只查询该区域
    - 如果未指定，返回空列表（需要先选择区域）
    """
    logger.info(f"查询账户服务器列表: account_id={account_id}, region={region}")
    
    # 获取账户信息
    account = account_service.get_account(db=db, account_id=account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    # 如果未指定区域，返回提示
    if not region or not project_id:
        return success_response(
            data=[],
            message="请先选择区域"
        )
    
    try:
        # 解密 AK/SK
        encryption_service = get_encryption_service()
        ak = encryption_service.decrypt(account.ak)
        sk = encryption_service.decrypt(account.sk)
        
        logger.info(f"查询区域 {region} 的服务器 (project_id={project_id})")
        
        # 创建客户端
        client = HuaweiCloudClient(
            access_key=ak,
            secret_key=sk,
            region=region
        )
        
        # 查询服务器
        ecs_service = ECSService(client=client, project_id=project_id)
        servers = ecs_service.list_servers(limit=limit)
        
        # 转换为字典列表，添加区域信息
        server_list = []
        for server in servers:
            server_dict = server.to_dict()
            server_dict['region'] = region
            server_dict['region_name'] = REGION_NAMES.get(region, region)
            server_dict['project_id'] = project_id
            server_list.append(server_dict)
        
        logger.info(f"查询到 {len(server_list)} 台服务器")
        
        return success_response(
            data=server_list,
            message=f"查询成功，共 {len(server_list)} 台服务器"
        )
        
    except Exception as e:
        logger.error(f"查询服务器列表失败: {e}")
        return success_response(
            data=[],
            message=f"查询失败: {str(e)}"
        )


@router.post("/sync/{account_id}")
async def sync_servers(
    account_id: int,
    db: Session = Depends(get_db)
):
    """同步指定账户的服务器信息"""
    # 复用 list_servers_by_account 的逻辑
    return await list_servers_by_account(account_id=account_id, limit=1000, db=db)
