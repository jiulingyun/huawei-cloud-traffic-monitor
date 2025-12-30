"""
流量监控 API

查询 Flexus L 实例流量使用情况
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from loguru import logger

from app.core.database import get_db
from app.core.response import success_response
from app.services.account_service import AccountService
from app.services.huawei_cloud.flexusl_service import FlexusLService, FlexusLException
from app.utils.encryption import get_encryption_service

router = APIRouter(prefix="/traffic", tags=["流量监控"])
account_service = AccountService()


@router.get("/summary")
async def get_all_traffic_summary(db: Session = Depends(get_db)):
    """
    获取所有账户的流量汇总
    
    遍历所有启用的账户，汇总流量使用情况
    """
    logger.info("查询所有账户流量汇总")
    
    accounts = account_service.list_accounts(db=db, is_enabled=True)
    
    if not accounts:
        return success_response(
            data={
                "total_accounts": 0,
                "total_instances": 0,
                "total_packages": 0,
                "total_amount": 0,
                "used_amount": 0,
                "remaining_amount": 0,
                "usage_percentage": 0,
                "accounts": []
            },
            message="没有启用的账户"
        )
    
    encryption_service = get_encryption_service()
    
    total_instances = 0
    total_packages = 0
    total_amount = 0.0
    used_amount = 0.0
    remaining_amount = 0.0
    account_summaries = []
    
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
            
            summary = service.get_all_traffic_summary()
            
            # 累加统计
            total_instances += summary['instance_count']
            total_packages += summary['package_count']
            total_amount += summary['total_amount']
            used_amount += summary['used_amount']
            remaining_amount += summary['remaining_amount']
            
            # 添加账户摘要
            account_summaries.append({
                "account_id": account.id,
                "account_name": account.name,
                "instance_count": summary['instance_count'],
                "package_count": summary['package_count'],
                "total_amount": summary['total_amount'],
                "used_amount": summary['used_amount'],
                "remaining_amount": summary['remaining_amount'],
                "usage_percentage": summary['usage_percentage']
            })
            
        except Exception as e:
            logger.warning(f"账户 {account.name} 流量查询失败: {e}")
            account_summaries.append({
                "account_id": account.id,
                "account_name": account.name,
                "error": str(e)
            })
            continue
    
    # 计算总体使用率
    usage_percentage = (used_amount / total_amount * 100) if total_amount > 0 else 0
    
    result = {
        "total_accounts": len(accounts),
        "total_instances": total_instances,
        "total_packages": total_packages,
        "total_amount": round(total_amount, 2),
        "used_amount": round(used_amount, 2),
        "remaining_amount": round(remaining_amount, 2),
        "usage_percentage": round(usage_percentage, 2),
        "accounts": account_summaries
    }
    
    logger.info(
        f"流量汇总: {total_instances} 实例, "
        f"总量 {total_amount:.2f} GB, 剩余 {remaining_amount:.2f} GB"
    )
    
    return success_response(data=result, message="查询成功")


@router.get("/{account_id}")
async def get_account_traffic_detail(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定账户的流量详情
    
    返回账户下每个实例的流量包详情
    """
    logger.info(f"查询账户流量详情: account_id={account_id}")
    
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
        
        # 获取流量汇总（包含实例和流量包详情）
        summary = service.get_all_traffic_summary()
        
        # 添加账户信息
        result = {
            "account_id": account.id,
            "account_name": account.name,
            "instance_count": summary['instance_count'],
            "package_count": summary['package_count'],
            "total_amount": summary['total_amount'],
            "used_amount": summary['used_amount'],
            "remaining_amount": summary['remaining_amount'],
            "usage_percentage": summary['usage_percentage'],
            "instances": summary['instances'],
            "packages": summary['packages']
        }
        
        return success_response(data=result, message="查询成功")
        
    except FlexusLException as e:
        logger.error(f"FlexusL 服务调用失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"查询流量详情失败: {e}")
        return success_response(
            data=None,
            message=f"查询失败: {str(e)}"
        )


@router.get("/{account_id}/check")
async def check_traffic_threshold(
    account_id: int,
    threshold_gb: float = 100.0,
    db: Session = Depends(get_db)
):
    """
    检查账户流量是否低于阈值
    
    用于流量监控告警
    
    Args:
        account_id: 账户 ID
        threshold_gb: 剩余流量阈值（GB），低于此值触发告警
    """
    logger.info(f"检查账户流量阈值: account_id={account_id}, threshold={threshold_gb}GB")
    
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
        
        remaining = summary['remaining_amount']
        is_below_threshold = remaining < threshold_gb
        
        result = {
            "account_id": account.id,
            "account_name": account.name,
            "threshold_gb": threshold_gb,
            "remaining_amount": remaining,
            "is_below_threshold": is_below_threshold,
            "status": "warning" if is_below_threshold else "normal",
            "message": f"剩余流量 {remaining:.2f} GB" + (
                f"，低于阈值 {threshold_gb} GB！" if is_below_threshold else ""
            )
        }
        
        if is_below_threshold:
            logger.warning(
                f"账户 {account.name} 流量告警: "
                f"剩余 {remaining:.2f} GB < 阈值 {threshold_gb} GB"
            )
        
        return success_response(data=result, message="检查完成")
        
    except FlexusLException as e:
        logger.error(f"FlexusL 服务调用失败: {e}")
        return success_response(
            data={"status": "error", "message": str(e)},
            message=f"检查失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"检查流量阈值失败: {e}")
        return success_response(
            data={"status": "error", "message": str(e)},
            message=f"检查失败: {str(e)}"
        )
