from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bcrypt import checkpw, hashpw, gensalt

from app.core.database import get_db
from app.core.result import Result
from app.core.security import create_access_token, decode_access_token
from app.models.sys_user import SysUser
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse, UserInfoResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", summary="用户注册")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    stmt = select(SysUser).where(SysUser.username == body.username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return Result.bad_request("用户名已存在")

    # 密码使用 BCrypt 加密（前端传来的已经是 SHA-256 哈希值）
    hashed = hashpw(body.password.encode("utf-8"), gensalt()).decode("utf-8")

    # 创建用户
    user = SysUser(
        username=body.username,
        password=hashed,
        nickname=body.nickname or None,
        email=body.email or None,
        phone=body.phone or None,
        status=1,
    )
    db.add(user)
    await db.flush()

    return Result.ok(message="注册成功")


@router.post("/login", summary="用户登录")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    # 查询用户
    stmt = select(SysUser).where(SysUser.username == body.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return Result.error(code=400, message="用户名或密码错误")

    if not user.is_active:
        return Result.error(code=403, message="账号已被禁用")

    # 验证密码：前端传来的是 SHA-256 哈希值，与数据库中 BCrypt 加密后的值比对
    if not checkpw(body.password.encode("utf-8"), user.password.encode("utf-8")):
        return Result.error(code=400, message="用户名或密码错误")

    # 生成 JWT Token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    return Result.ok(data=LoginResponse(token=token).dict())


@router.get("/user-info", summary="获取当前用户信息")
async def get_user_info(request: Request, db: AsyncSession = Depends(get_db)):
    """获取当前登录用户信息"""
    # 从 Header 提取 Token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return Result.unauthorized()

    token = auth_header[7:]
    payload = decode_access_token(token)
    if not payload:
        return Result.unauthorized()

    user_id = payload.get("sub")
    if not user_id:
        return Result.unauthorized()

    # 查询用户（id 为 bigint，需将 JWT 中的字符串转为 int）
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return Result.unauthorized()

    # 查询用户
    stmt = select(SysUser).where(SysUser.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return Result.unauthorized("用户不存在")

    if not user.is_active:
        return Result.forbidden("账号已被禁用")

    return Result.ok(data=user.to_dict(exclude_fields=["password"]))
