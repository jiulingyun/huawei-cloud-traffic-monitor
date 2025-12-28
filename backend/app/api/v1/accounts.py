"""
账户管理 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success_response

router = APIRouter(prefix="/accounts", tags=["账户管理"])


@router.get("")
async def list_accounts(db: Session = Depends(get_db)):
    """获取账户列表"""
    return success_response(data=[], message="查询成功")


@router.get("/{account_id}")
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取账户详情"""
    return success_response(data=None, message="查询成功")


@router.post("")
async def create_account(db: Session = Depends(get_db)):
    """创建账户"""
    return success_response(data=None, message="创建成功")


@router.put("/{account_id}")
async def update_account(account_id: int, db: Session = Depends(get_db)):
    """更新账户"""
    return success_response(data=None, message="更新成功")


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账户"""
    return success_response(message="删除成功")
