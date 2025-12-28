"""
配置管理 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success_response

router = APIRouter(prefix="/configs", tags=["配置管理"])


@router.get("")
async def get_config(db: Session = Depends(get_db)):
    """获取配置"""
    return success_response(data=None, message="查询成功")


@router.put("")
async def update_config(db: Session = Depends(get_db)):
    """更新配置"""
    return success_response(message="更新成功")
