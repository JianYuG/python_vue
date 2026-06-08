# ──── 阶段1: 构建依赖 ────
FROM python:3.8-slim AS builder

WORKDIR /build

# 安装编译依赖（asyncpg/bcrypt 编译需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# ──── 阶段2: 运行时镜像 ────
FROM python:3.8-slim

LABEL maintainer="地图采集系统"
LABEL description="地图采集系统 - FastAPI 后端服务"

WORKDIR /app

# 仅安装运行时必需的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 依赖
COPY --from=builder /install /usr/local

# 复制项目代码
COPY app/ ./app/
COPY run.py .
COPY init_db.py .

# 复制 .env 配置（生产环境建议用环境变量覆盖）
COPY .env.example .env

# 暴露端口
EXPOSE 8090

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/api/health')" || exit 1

# 启动命令
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8090"]
