#!/bin/bash
# ═══════════════════════════════════════════════════════════
# 梦帮小助 v3.0 · WSL2 本地开发服务器启动脚本
# ═══════════════════════════════════════════════════════════

set -e

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

PROJECT_DIR="/mnt/d/DREAMVFIA Assistant/dreamhelp-v3"

echo -e "${RED}╔═══════════════════════════════════════════╗${NC}"
echo -e "${RED}║   DREAMVFIA · 梦帮小助 v3.0 Dev Server   ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════╝${NC}"
echo ""

# ═══ 1. 检查 Docker 基础设施 ═══
echo -e "${CYAN}[1/4] 检查 Docker 基础设施...${NC}"

check_port() {
    local name=$1
    local port=$2
    if python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost',$port)); s.close()" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $name (port $port): ONLINE"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (port $port): OFFLINE"
        return 1
    fi
}

PG_OK=0; REDIS_OK=0
check_port "PostgreSQL" 5432 && PG_OK=1
check_port "Redis" 6379 && REDIS_OK=1

if [ "$PG_OK" -eq 0 ] || [ "$REDIS_OK" -eq 0 ]; then
    echo -e "${YELLOW}  提示: 请先在 Windows PowerShell 中运行:${NC}"
    echo -e "${YELLOW}  docker compose -f \"$PROJECT_DIR/docker-compose.yml\" up -d postgres redis${NC}"
    echo ""
    read -p "按 Enter 重试，或输入 skip 跳过: " retry
    if [ "$retry" != "skip" ]; then
        check_port "PostgreSQL" 5432
        check_port "Redis" 6379
    fi
fi
echo ""

# ═══ 2. 环境变量 ═══
echo -e "${CYAN}[2/4] 加载环境变量...${NC}"
export DATABASE_URL="postgresql://dreamhelp:dev_password@localhost:5432/dreamhelp"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="dev-secret-dreamvfia-2026"
export NODE_ENV="development"
export BRAIN_CORE_URL="http://localhost:8000"
export GATEWAY_URL="http://localhost:3100"
echo "  DATABASE_URL = postgresql://...@localhost:5432/dreamhelp"
echo "  REDIS_URL    = redis://localhost:6379"
echo "  NODE_ENV     = development"
echo ""

# ═══ 3. 选择启动模式 ═══
echo -e "${CYAN}[3/4] 选择启动模式:${NC}"
echo "  1) 全部启动 (web-portal + brain-core + gateway)"
echo "  2) 仅前端 (web-portal Next.js :3000)"
echo "  3) 仅后端 (brain-core FastAPI :8000)"
echo "  4) 仅网关 (gateway NestJS :3100)"
echo "  5) 前端 + 后端 (无网关)"
echo ""
read -p "输入选择 [1-5, 默认 1]: " choice
choice=${choice:-1}
echo ""

# ═══ 进程 PID 记录 ═══
PIDS=()

start_web() {
    echo -e "${GREEN}[启动] web-portal (Next.js) -> http://localhost:3000${NC}"
    cd "$PROJECT_DIR/apps/web-portal"
    pnpm dev &
    PIDS+=($!)
    echo "  PID: ${PIDS[-1]}"
    cd "$PROJECT_DIR"
}

start_brain() {
    echo -e "${GREEN}[启动] brain-core (FastAPI) -> http://localhost:8000${NC}"
    cd "$PROJECT_DIR/services/brain-core"
    if [ ! -d ".venv" ]; then
        echo "  创建 Python 虚拟环境..."
        python3 -m venv .venv
    fi
    source .venv/bin/activate
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt 2>/dev/null || true
    fi
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    PIDS+=($!)
    echo "  PID: ${PIDS[-1]}"
    cd "$PROJECT_DIR"
}

start_gateway() {
    echo -e "${GREEN}[启动] gateway (NestJS) -> http://localhost:3100${NC}"
    cd "$PROJECT_DIR/services/gateway"
    pnpm dev &
    PIDS+=($!)
    echo "  PID: ${PIDS[-1]}"
    cd "$PROJECT_DIR"
}

# ═══ 4. 启动服务 ═══
echo -e "${CYAN}[4/4] 启动服务...${NC}"
case $choice in
    1) start_brain; start_gateway; start_web ;;
    2) start_web ;;
    3) start_brain ;;
    4) start_gateway ;;
    5) start_brain; start_web ;;
    *) echo "无效选择"; exit 1 ;;
esac

echo ""
echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  所有服务已启动!${NC}"
echo ""
echo -e "  ${CYAN}门户首页:${NC}  http://localhost:3000"
echo -e "  ${CYAN}工作台:${NC}    http://localhost:3000/overview"
echo -e "  ${CYAN}AI核心:${NC}    http://localhost:8000"
echo -e "  ${CYAN}API文档:${NC}   http://localhost:8000/docs"
echo -e "  ${CYAN}网关:${NC}      http://localhost:3100"
echo -e "  ${CYAN}PostgreSQL:${NC} localhost:5432"
echo -e "  ${CYAN}Redis:${NC}     localhost:6379"
echo ""
echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "按 ${YELLOW}Ctrl+C${NC} 停止所有服务"
echo ""

# 捕获退出信号，清理所有子进程
cleanup() {
    echo ""
    echo -e "${YELLOW}停止所有服务...${NC}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    echo -e "${GREEN}已停止${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# 等待所有子进程
wait
