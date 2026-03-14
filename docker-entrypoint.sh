#!/bin/sh
# 容器启动时把前端产物和静态文件复制到共享 volume
# （Docker named volume 挂载时会遮盖镜像层内的文件，所以需要在启动时手动复制）

echo "==> 同步前端产物到共享 volume..."
if [ -d /tmp/frontend_dist_seed ] && [ -z "$(ls -A /app/frontend/dist 2>/dev/null)" ]; then
    cp -r /tmp/frontend_dist_seed/. /app/frontend/dist/
    echo "==> 前端产物同步完成"
else
    echo "==> 前端产物已存在，跳过同步"
fi

echo "==> 同步静态文件到共享 volume..."
if [ -d /tmp/staticfiles_seed ] && [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
    cp -r /tmp/staticfiles_seed/. /app/staticfiles/
    echo "==> 静态文件同步完成"
else
    echo "==> 静态文件已存在，跳过同步"
fi

echo "==> 执行数据库迁移..."
python manage.py migrate --noinput

echo "==> 初始化超级管理员..."
python manage.py init_superadmin

echo "==> 启动 Uvicorn..."
exec uvicorn CompreEvalSystem.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
