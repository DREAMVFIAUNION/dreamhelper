# ═══════════════════════════════════════════════════════════
# 梦帮小助 brain-core — Multi-stage Dockerfile
# ═══════════════════════════════════════════════════════════

# Stage 1: Dependencies
FROM python:3.12-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 LTS (for GitNexus MCP via npx)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

# Node.js runtime (for GitNexus MCP)
COPY --from=deps /usr/bin/node /usr/bin/node
COPY --from=deps /usr/bin/npx /usr/bin/npx
COPY --from=deps /usr/lib/node_modules /usr/lib/node_modules

COPY --from=deps /install /usr/local

COPY src/ ./src/
COPY prompts/ ./prompts/

RUN chown -R appuser:appgroup /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUTF8=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
