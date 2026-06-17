import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.auth import router as auth_router
from app.api.xzqh import router as xzqh_router
from app.api.feature import router as feature_router
from app.api.doorplate import router as doorplate_router
from app.api.attachment import router as attachment_router
from app.api.ingest import router as ingest_router
from app.api.spatial_analysis import router as spatial_router
from app.core.config import settings
from app.core.security import decode_access_token

# 不需要鉴权的路径前缀（白名单）
AUTH_WHITELIST = [
    "/api/auth/login",
    "/api/auth/register",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT 鉴权中间件 —— 统一拦截所有需要登录的接口"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 白名单放行
        if any(path.startswith(w) for w in AUTH_WHITELIST):
            return await call_next(request)

        # 静态文件放行
        if not path.startswith("/api/"):
            return await call_next(request)

        # 验证 Token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response(
                content=json.dumps({"code": 401, "message": "未登录或Token已过期", "data": None}, ensure_ascii=False),
                status_code=200,
                media_type="application/json",
            )

        payload = decode_access_token(auth_header[7:])
        if not payload:
            return Response(
                content=json.dumps({"code": 401, "message": "未登录或Token已过期", "data": None}, ensure_ascii=False),
                status_code=200,
                media_type="application/json",
            )

        return await call_next(request)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS —— 允许前端开发服务器访问（需在鉴权中间件之前注册）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 鉴权中间件
app.add_middleware(JWTAuthMiddleware)

# 注册路由
app.include_router(auth_router)
app.include_router(xzqh_router)
app.include_router(feature_router)
app.include_router(doorplate_router)
app.include_router(attachment_router)
app.include_router(ingest_router)
app.include_router(spatial_router)


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok"}
