"""
用户认证 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os
from jose import jwt

router = APIRouter(prefix="/auth", tags=["认证"])

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 小时

# 管理员账户（从环境变量读取，默认值仅用于开发）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_in: int


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    创建 JWT token
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间
        
    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    # 验证用户名和密码
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username, "username": request.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": request.username,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 秒
    }


@router.post("/logout")
async def logout():
    """
    用户登出（前端清除 token）
    """
    return {"message": "登出成功"}


@router.get("/me")
async def get_current_user():
    """
    获取当前用户信息（需要 token）
    
    注意：这是一个简化版本，实际应该使用依赖注入来验证 token
    """
    # 简化版本：直接返回管理员信息
    return {
        "username": ADMIN_USERNAME,
        "role": "admin"
    }
