# ═══════════════════════════════════════════════════════════
# 梦帮小助 v3.0 · 一键启动脚本 (PowerShell)
# Docker 基础设施 + WSL2 应用服务
# ═══════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "  ║   DREAMVFIA · 梦帮小助 v3.0 Dev Server   ║" -ForegroundColor Red
Write-Host "  ╚═══════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# ═══ 1. 启动 Docker 基础设施 ═══
Write-Host "[1/3] 启动 Docker 基础设施..." -ForegroundColor Cyan

$services = @("postgres", "redis")
Write-Host "  启动: $($services -join ', ')"
docker compose -f "$ProjectDir\docker-compose.yml" up -d @services 2>&1 | Out-Null

# 等待健康检查
Write-Host "  等待服务就绪..." -ForegroundColor Yellow
$maxWait = 30
$waited = 0
do {
    Start-Sleep -Seconds 2
    $waited += 2
    $pgReady = docker inspect --format='{{.State.Health.Status}}' dreamhelp-postgres 2>$null
    $redisReady = docker inspect --format='{{.State.Health.Status}}' dreamhelp-redis 2>$null
} while (($pgReady -ne "healthy" -or $redisReady -ne "healthy") -and $waited -lt $maxWait)

if ($pgReady -eq "healthy") {
    Write-Host "  [OK] PostgreSQL :5432 healthy" -ForegroundColor Green
} else {
    Write-Host "  [!] PostgreSQL 未就绪" -ForegroundColor Yellow
}
if ($redisReady -eq "healthy") {
    Write-Host "  [OK] Redis :6379 healthy" -ForegroundColor Green
} else {
    Write-Host "  [!] Redis 未就绪" -ForegroundColor Yellow
}
Write-Host ""

# ═══ 2. 可选: 启动扩展服务 ═══
Write-Host "[2/3] 扩展服务 (可选):" -ForegroundColor Cyan
Write-Host "  当前仅启动核心服务 (PostgreSQL + Redis)"
Write-Host "  如需启动全部服务 (Milvus/ES/MinIO)，运行:" -ForegroundColor Yellow
Write-Host "  docker compose -f `"$ProjectDir\docker-compose.yml`" up -d" -ForegroundColor Yellow
Write-Host ""

# ═══ 3. 启动 WSL2 开发服务器 ═══
Write-Host "[3/3] 启动 WSL2 开发服务器..." -ForegroundColor Cyan
Write-Host "  WSL2 Ubuntu-22.04 中运行应用服务" -ForegroundColor Green
Write-Host ""

# 在新的 Windows Terminal 标签页中启动 WSL2 开发服务器
$wslScript = "~/dreamhelp-workspace/start-dev.sh"

# 检测是否在 Windows Terminal 中
if ($env:WT_SESSION) {
    # Windows Terminal: 新标签页
    wt -w 0 new-tab --title "DreamHelp Dev" wsl -d Ubuntu-22.04 -- bash -l $wslScript
    Write-Host "  已在新 Windows Terminal 标签页中启动" -ForegroundColor Green
} else {
    # 普通终端: 直接启动
    Start-Process wsl -ArgumentList "-d", "Ubuntu-22.04", "--", "bash", "-l", $wslScript
    Write-Host "  已在新窗口中启动" -ForegroundColor Green
}

Write-Host ""
Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Red
Write-Host "  Docker 基础设施已就绪!" -ForegroundColor Green
Write-Host "  WSL2 应用服务正在启动..." -ForegroundColor Green
Write-Host ""
Write-Host "  PostgreSQL:  localhost:5432" -ForegroundColor Cyan
Write-Host "  Redis:       localhost:6379" -ForegroundColor Cyan
Write-Host "  Web Portal:  http://localhost:3000  (WSL2)" -ForegroundColor Cyan
Write-Host "  Brain Core:  http://localhost:8000  (WSL2)" -ForegroundColor Cyan
Write-Host "  Gateway:     http://localhost:3100  (WSL2)" -ForegroundColor Cyan
Write-Host "  ═══════════════════════════════════════════" -ForegroundColor Red
Write-Host ""
