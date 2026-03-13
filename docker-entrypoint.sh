#!/bin/sh
# 瀹瑰櫒鍚姩鏃舵妸鍓嶇浜х墿鍜岄潤鎬佹枃浠跺鍒跺埌鍏变韩 volume
# 锛圖ocker named volume 鎸傝浇鏃朵細閬洊闀滃儚灞傚唴鐨勬枃浠讹紝鎵€浠ラ渶瑕佸湪鍚姩鏃舵墜鍔ㄥ鍒讹級

echo "==> 鍚屾鍓嶇浜х墿鍒板叡浜?volume..."
if [ -d /tmp/frontend_dist_seed ] && [ -z "$(ls -A /app/frontend/dist 2>/dev/null)" ]; then
    cp -r /tmp/frontend_dist_seed/. /app/frontend/dist/
    echo "==> 鍓嶇浜х墿鍚屾瀹屾垚"
else
    echo "==> 鍓嶇浜х墿宸插瓨鍦紝璺宠繃鍚屾"
fi

echo "==> 鍚屾闈欐€佹枃浠跺埌鍏变韩 volume..."
if [ -d /tmp/staticfiles_seed ] && [ -z "$(ls -A /app/staticfiles 2>/dev/null)" ]; then
    cp -r /tmp/staticfiles_seed/. /app/staticfiles/
    echo "==> 闈欐€佹枃浠跺悓姝ュ畬鎴?
else
    echo "==> 闈欐€佹枃浠跺凡瀛樺湪锛岃烦杩囧悓姝?
fi

echo "==> 鍚姩 Uvicorn..."
exec uvicorn CompreEvalSystem.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info
