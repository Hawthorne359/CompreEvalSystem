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

# 将 Stage 1 构建的前端产物复制进来
COPY --from=node-builder /build/frontend/dist ./frontend/dist

# 创建运行时目录
RUN mkdir -p media logs cache

# 收集 Django 静态文件（admin CSS/JS 等）
RUN python manage.py collectstatic --noinput

# 把前端产物和静态文件暂存到 seed 目录
# 容器启动时由 entrypoint 脚本复制到共享 volume（因为 volume 挂载会遮盖镜像层文件）
RUN cp -r /app/frontend/dist /tmp/frontend_dist_seed && \
    cp -r /app/staticfiles /tmp/staticfiles_seed

# 复制启动脚本（ARG 用于在需要时强制此层及之后不用缓存）
ARG CACHE_BUST=1
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 容器监听端口（Nginx 反代到此端口）
EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
