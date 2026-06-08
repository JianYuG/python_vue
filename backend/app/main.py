from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.xzqh import router as xzqh_router
from app.api.feature import router as feature_router
from app.api.doorplate import router as doorplate_router
from app.api.attachment import router as attachment_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS —— 允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(xzqh_router)
app.include_router(feature_router)
app.include_router(doorplate_router)
app.include_router(attachment_router)


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok"}
