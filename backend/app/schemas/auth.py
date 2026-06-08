from typing import Optional

from pydantic import BaseModel, Field


# ──── 请求模型 ────

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码(SHA-256哈希)")
    nickname: Optional[str] = Field("", max_length=50, description="昵称")
    email: Optional[str] = Field("", max_length=100, description="邮箱")
    phone: Optional[str] = Field("", max_length=20, description="手机号")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码(SHA-256哈希)")


# ──── 响应模型 ────

class LoginResponse(BaseModel):
    """登录响应"""
    token: str


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    nickname: str = ""
    email: str = ""
    phone: str = ""
    status: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
