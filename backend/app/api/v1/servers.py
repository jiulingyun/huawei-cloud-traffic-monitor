"""
服务器管理 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success_response

router = APIRouter(prefix="/servers", tags=["服务器管理"])


@router.get("")
async def list_servers(db: Session = Depends(get_db)):
    """获取服务器列表"""
    return success_response(data=[], message="查询成功")


@router.get("/{server_id}")
async def get_server(server_id: int, db: Session = Depends(get_db)):
    """获取服务器详情"""
    return success_response(data=None, message="查询成功")


@router.post("/sync")
async def sync_servers(db: Session = Depends(get_db)):
    """同步服务器信息"""
    return success_response(message="同步成功")
