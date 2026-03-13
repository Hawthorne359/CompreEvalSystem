# 输出本机局域网 IP，便于手机访问学生端
# 用法：在 PowerShell 中执行 .\show-lan-ip.ps1

$port = 5173
$addr = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|VMware|VirtualBox|Docker' -and $_.IPAddress -match '^192\.168\.' } | Select-Object -First 1).IPAddress

if ($addr) {
    Write-Host ""
    Write-Host "本机局域网 IP: $addr" -ForegroundColor Green
    Write-Host "手机浏览器访问: http://${addr}:${port}" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "未检测到 192.168.x.x 地址，请确认已连接 WiFi，或运行 ipconfig 查看。" -ForegroundColor Yellow
}
