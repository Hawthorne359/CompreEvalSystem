# 本地一键构建镜像、推送阿里云 ACR、推送代码到 GitHub
# 使用方式：在 PowerShell 中执行  .\build-push.ps1
# 如遇 "运行脚本已禁用" 错误，先执行：Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"
$ProjectDir  = "C:\Users\Hawthorne\Desktop\biyesheji\CompreEvalSystem"
$AliyunImage = "crpi-ej9pkpb3pqzbuoeg.cn-chengdu.personal.cr.aliyuncs.com/hawthorne359/compre-eval-backend:latest"

Set-Location $ProjectDir

Write-Host ""
Write-Host "===== [1/3] 构建 Docker 镜像 =====" -ForegroundColor Cyan
docker build -t $AliyunImage .
if ($LASTEXITCODE -ne 0) { Write-Host "构建失败，已终止。" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "===== [2/3] 推送镜像到阿里云 ACR =====" -ForegroundColor Cyan
docker push $AliyunImage
if ($LASTEXITCODE -ne 0) { Write-Host "推送阿里云失败，已终止。" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "===== [3/3] 推送代码到 GitHub =====" -ForegroundColor Cyan
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    $msg = "update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git commit --trailer "Made-with: Cursor" -m $msg
    git push origin main
} else {
    Write-Host "没有需要提交的代码变更，跳过 git commit --trailer "Made-with: Cursor"/push。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===== 全部完成！镜像已推送，代码已同步。=====" -ForegroundColor Green
Write-Host ""
Write-Host "服务器更新命令：" -ForegroundColor Gray
Write-Host "  docker compose pull backend; docker compose up -d" -ForegroundColor Gray