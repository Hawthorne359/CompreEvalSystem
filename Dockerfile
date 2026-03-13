# ============================================================
# CompreEvalSystem — 多阶段 Docker 构建
# Stage 1: 构建前端 Vue 产物
# Stage 2: 运行 Django + Uvicorn
# ============================================================

# ── Stage 1: 前端构建 ────────────────────────────────────────
FROM node:20-alpine AS node-builder

WORKDIR /build/frontend

# 先只复制依赖文件，利用 Docker 层缓存
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python 应用 ─────────────────────────────────────
FROM python:3.12-slim AS runner

# 设置工作目录
WORKDIR /app

# 安装系统依赖（PyMySQL 不需要 mysql-client 编译，但 cryptography 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用层缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目后端源码
COPY manage.py ./
COPY CompreEvalSystem/ ./CompreEvalSystem/
COPY org/ ./org/
COPY users/ ./users/
COPY eval/ ./eval/
COPY submission/ ./submission/
COPY scoring/ ./scoring/
COPY appeal/ ./appeal/
COPY audit/ ./audit/
COPY report/ ./report/
COPY dashboard/ ./dashboard/
COPY realtime/ ./realtime/

# 将 Stage 1 构建的前端产物复制进来（Nginx 容器从此路径读取）
COPY --from=node-builder /build/frontend/dist ./frontend/dist

# 创建运行时目录（media/logs/cache 在容器外通过 volume 挂载，此处仅为保险）
RUN mkdir -p media logs cache staticfiles

# 收集 Django 静态文件（admin CSS/JS 等）
# 此时 .env 尚未挂载，使用默认值即可（STATIC_ROOT 不依赖环境变量）
RUN python manage.py collectstatic --noinput

# 容器监听端口（Nginx 反代到此端口）
EXPOSE 8000

# 启动 Uvicorn（workers 数量可根据服务器 CPU 核数调整）
CMD ["uvicorn", "CompreEvalSystem.asgi:application", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--log-level", "info"]
