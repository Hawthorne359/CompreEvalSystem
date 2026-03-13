# 以前端「允许局域网访问」方式启动，供手机浏览器访问
# 使用前请先在项目根目录另开终端启动后端：.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

$frontendPath = Join-Path $PSScriptRoot '..' 'frontend'
Set-Location $frontendPath
npm run dev -- --host
