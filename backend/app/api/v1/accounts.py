"""
账户管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.services.account_service import account_service

router = APIRouter(prefix="/accounts", tags=["账户管理"])


# Pydantic 模型
class AccountCreate(BaseModel):
    """$创建账户请求模型"""
    name: str = Field(..., description="账户名称", min_length=1, max_length=100)
    ak: str = Field(..., description="Access Key", min_length=1)
    sk: str = Field(..., description="Secret Key", min_length=1)
    region: str = Field(default="cn-north-4", description="区域")
    description: Optional[str] = Field(None, description="账户描述", max_length=500)


class AccountUpdate(BaseModel):
    """更新账户请求模型"""
    name: Optional[str] = Field(None, description="账户名称", min_length=1, max_length=100)
    ak: Optional[str] = Field(None, description="Access Key", min_length=1)
    sk: Optional[str] = Field(None, description="Secret Key", min_length=1)
    region: Optional[str] = Field(None, description="区域")
    description: Optional[str] = Field(None, description="账户描述", max_length=500)


class AccountResponse(BaseModel):
    """账户响应模型"""
    id: int
    name: str
    region: str
    is_enabled: bool
    description: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    is_enabled: Optional[bool] = Query(None, description="过滤启用状态"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取账户列表
    
    - **is_enabled**: 过滤启用状态（可选）
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    accounts = account_service.list_accounts(
        db=db,
        is_enabled=is_enabled,
        limit=limit,
        offset=offset
    )
    
    # 转换时间为字符串
    result = []
    for account in accounts:
        result.append({
            "id": account.id,
            "name": account.name,
            "region": account.region,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None
        })
    
    return result


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """
    获取账户详情
    
    - **account_id**: 账户 ID
    """
    account = account_service.get_account(db=db, account_id=account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    return {
        "id": account.id,
        "name": account.name,
        "region": account.region,
        "is_enabled": account.is_enabled,
        "description": account.description,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(request: AccountCreate, db: Session = Depends(get_db)):
    """
    创建账户
    
    - **name**: 账户名称
    - **ak**: Access Key
    - **sk**: Secret Key
    - **region**: 区域（默认 cn-north-4）
    - **description**: 账户描述（可选）
    """
    try:
        account = account_service.create_account(
            db=db,
            name=request.name,
            ak=request.ak,
            sk=request.sk,
            region=request.region,
            description=request.description
        )
        
        return {
            "id": account.id,
            "name": account.name,
            "region": account.region,
            "is_enabled": account.is_enabled,
            "description": account.description,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建账户失败: {str(e)}")


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    request: AccountUpdate,
    db: Session = Depends(get_db)
):
    """
    更新账户
    
    - **account_id**: 账户 ID
    - **name**: 账户名称（可选）
    - **ak**: Access Key（可选）
    - **sk**: Secret Key（可选）
    - **region**: 区域（可选）
    - **description**: 账户描述（可选）
    """
    account = account_service.update_account(
        db=db,
        account_id=account_id,
        name=request.name,
        ak=request.ak,
        sk=request.sk,
        region=request.region,
        description=request.description
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    return {
        "id": account.id,
        "name": account.name,
        "region": account.region,
        "is_enabled": account.is_enabled,
        "description": account.description,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """
    删除账户
    
    - **account_id**: 账户 ID
    """
    success = account_service.delete_account(db=db, account_id=account_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    return None


@router.post("/{account_id}/enable", response_model=AccountResponse)
async def enable_account(account_id: int, db: Session = Depends(get_db)):
    """
    启用账户
    
    - **account_id**: 账户 ID
    """
    account = account_service.enable_account(db=db, account_id=account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    return {
        "id": account.id,
        "name": account.name,
        "region": account.region,
        "is_enabled": account.is_enabled,
        "description": account.description,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.post("/{account_id}/disable", response_model=AccountResponse)
async def disable_account(account_id: int, db: Session = Depends(get_db)):
    """
    禁用账户
    
    - **account_id**: 账户 ID
    """
    account = account_service.disable_account(db=db, account_id=account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    return {
        "id": account.id,
        "name": account.name,
        "region": account.region,
        "is_enabled": account.is_enabled,
        "description": account.description,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.post("/{account_id}/verify")
async def verify_account(account_id: int, db: Session = Depends(get_db)):
    """
    验证账户
    
    测试 AK/SK 是否有效
    
    - **account_id**: 账户 ID
    """
    is_valid, message = account_service.verify_account(db=db, account_id=account_id)
    
    return {
        "is_valid": is_valid,
        "message": message
    }
