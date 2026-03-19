# ═══════════════════════════════════════════════════════════
# 梦帮小助 v3.0 · 一键停止脚本 (PowerShell)
# ═══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "  停止所有服务..." -ForegroundColor Yellow
Write-Host ""

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# 停止 WSL2 中的 Node/Python 进程
Write-Host "  [1/2] 停止 WSL2 应用服务..." -ForegroundColor Cyan
wsl -d Ubuntu-22.04 -- bash -c "pkill -f 'next dev' 2>/dev/null; pkill -f 'uvicorn' 2>/dev/null; pkill -f 'node.*gateway' 2>/dev/null; echo 'WSL2 processes stopped'"

# 停止 Docker 容器
Write-Host "  [2/2] 停止 Docker 基础设施..." -ForegroundColor Cyan
docker compose -f "$ProjectDir\docker-compose.yml" stop 2>&1 | Out-Null

Write-Host ""
Write-Host "  所有服务已停止" -ForegroundColor Green
Write-Host ""
