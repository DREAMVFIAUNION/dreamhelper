#!/bin/bash
# 梦帮小助 v3.0 · 项目初始化脚本

set -e

echo "═══════════════════════════════════════"
echo "  DREAMVFIA · 梦帮小助 v3.0 Setup"
echo "═══════════════════════════════════════"

# 1. 安装依赖
echo "[1/4] Installing dependencies..."
pnpm install

# 2. 环境变量
echo "[2/4] Setting up environment..."
[ ! -f .env ] && cp .env.example .env && echo "  Created .env"

# 3. Python 虚拟环境
echo "[3/4] Setting up Python environment..."
cd services/brain-core
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ../..

# 4. Docker
echo "[4/4] Starting Docker services..."
docker compose up -d

echo ""
echo "✓ Setup complete! Run 'pnpm dev' to start."
