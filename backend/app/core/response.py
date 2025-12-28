"""
统一响应模型
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": None
            }
        }


class ListResponse(BaseModel, Generic[T]):
    """列表响应格式"""
    success: bool = True
    message: str = "查询成功"
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "查询成功",
                "data": [],
                "total": 0,
                "page": 1,
                "page_size": 10
            }
        }


def success_response(data: Any = None, message: str = "操作成功") -> dict:
    """成功响应"""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message: str = "操作失败", data: Any = None) -> dict:
    """错误响应"""
    return {
        "success": False,
        "message": message,
        "data": data
    }


def list_response(
    data: list = None,
    total: int = 0,
    page: int = 1,
    page_size: int = 10,
    message: str = "查询成功"
) -> dict:
    """列表响应"""
    return {
        "success": True,
        "message": message,
        "data": data or [],
        "total": total,
        "page": page,
        "page_size": page_size
    }
