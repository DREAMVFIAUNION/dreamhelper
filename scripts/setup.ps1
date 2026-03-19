# 梦帮小助 v3.0 · Windows 项目初始化脚本
Write-Host "═══════════════════════════════════════" -ForegroundColor Red
Write-Host "  DREAMVFIA · 梦帮小助 v3.0 Setup" -ForegroundColor Red
Write-Host "═══════════════════════════════════════" -ForegroundColor Red

# 1. 检查 pnpm
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host "[!] pnpm not found. Installing..." -ForegroundColor Yellow
    npm install -g pnpm
}

# 2. 安装依赖
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Cyan
pnpm install

# 3. 复制环境变量
Write-Host "[2/4] Setting up environment..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from .env.example" -ForegroundColor Green
}

# 4. Python 虚拟环境
Write-Host "[3/4] Setting up Python environment..." -ForegroundColor Cyan
Push-Location services/brain-core
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\pip install -r requirements.txt
Pop-Location

# 5. 启动 Docker
Write-Host "[4/4] Starting Docker services..." -ForegroundColor Cyan
docker compose up -d

Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host "  Run 'pnpm dev' to start development" -ForegroundColor Gray
