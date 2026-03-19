.PHONY: dev build test lint clean docker-up docker-down setup

# ═══════════════════════════════════════════════════════════
# 梦帮小助 v3.0 · Makefile
# ═══════════════════════════════════════════════════════════

setup:
	pnpm install
	cp -n .env.example .env || true
	cd services/brain-core && python -m venv .venv && .venv/bin/pip install -r requirements.txt

dev:
	pnpm run dev

build:
	pnpm run build

test:
	pnpm run test

lint:
	pnpm run lint

clean:
	pnpm run clean

docker-up:
	docker compose up -d

docker-down:
	docker compose down

db-migrate:
	pnpm run db:migrate

db-seed:
	pnpm run db:seed
