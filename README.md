# 梦帮小助 v3.2 · DREAMVFIA AI Assistant

> 企业智能版 · 赛博朋克主题 · **100 技能 · 5 工具 · 5 智能体 · 3 LLM · 70+ API · 61 页面 · 9 容器 · 150+ 测试 · LLM 网关 · RAG Reranker** · v3.2.0

## 项目架构

```
dreamhelp-v3/
├── apps/
│   └── web-portal/          # Next.js 15 前端（赛博朋克 UI）
├── services/
│   ├── gateway/              # NestJS 10 API 网关（Fastify + WebSocket）
│   └── brain-core/           # Python FastAPI AI 核心（Agent + RAG + LLM）
├── packages/
│   ├── design-system/        # 赛博朋克设计 Token + TailwindCSS 预设
│   ├── database/             # Prisma ORM + PostgreSQL
│   ├── ts-sdk/               # TypeScript 类型定义
│   ├── auth/                 # JWT 认证共享库
│   ├── logger/               # Pino 日志
│   └── config/               # Zod 环境变量验证
└── docker-compose.yml        # 本地一键启动 (7 容器)
```

## 核心能力

| 模块 | 说明 |
|------|------|
| **多智能体** | ReAct (工具调用) · Code (编程) · Writing (写作) · Analysis (分析) · **PlanExecute (规划执行)** + 关键词/LLM 智能路由 |
| **100 技能** | 日常 15 · 办公 15 · 编程 15 · 文档 13 · 娱乐 12 · 图像 12 · 音频 10 · 视频 8 |
| **记忆系统** | 短期会话记忆 + 长期用户画像 (LLM 自动提取) + RAG 知识检索 |
| **RAG 检索** | 3 模式: 内存 TF-IDF · Milvus 向量 · 混合(Milvus+ES BM25+RRF) + **Cross-Encoder Reranker** |
| **多模型** | MiniMax M2.5 · OpenAI GPT-4o · DeepSeek Chat — 用户可切换 |
| **主动唤醒** | 定时任务引擎 + 空闲检测 + 早晚问候 + 个性化消息 |
| **Admin 面板** | 用户/会话/分析/智能体/技能/审计/系统/组织/工作人员 9 大管理页 |
| **媒体处理** | Pillow 图像 12技能 · pydub 音频 10技能 · ffmpeg 视频 8技能 |
| **语音** | STT: faster-whisper / OpenAI API 双引擎 · TTS: Edge-TTS / MiniMax 双引擎 (12 音色) |
| **LLM 网关** | 统一中间件: RateLimiter → SemanticCache → CircuitBreaker → Router(cost/latency/fallback) |
| **安全** | JWT 认证 · PBKDF2 密码 · Rate Limiting · 安全 Headers · CORS |

## 快速开始

### 前置要求

- **Node.js** ≥ 20 · **pnpm** ≥ 9 · **Python** ≥ 3.12 · **Docker** + Compose

### 1. 安装依赖

```bash
pnpm install
cd services/brain-core && pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 JWT_SECRET, MINIMAX_API_KEY 等
```

### 3. 启动基础设施

```bash
docker compose up -d postgres redis
# 或启动全部: docker compose up -d
```

### 4. 初始化数据库

```bash
pnpm db:migrate
pnpm db:seed
```

### 5. 启动开发服务

```bash
# 前端
pnpm --filter web-portal dev          # :3000

# AI 核心
cd services/brain-core
uvicorn src.main:app --reload --port 8000

# 网关 (可选)
pnpm --filter gateway dev             # :3001
```

### 6. Docker 一键部署

```bash
docker compose up -d
# 启动 7 个容器: postgres, redis, milvus, es, minio, web-portal, brain-core
```

### 7. 访问

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| AI 服务 | http://localhost:8000/health |
| Health Check | http://localhost:3000/api/health |
| MinIO 控制台 | http://localhost:9001 |

## API 路由一览 (40+)

### 认证 `/api/auth/*`
`POST login` · `POST register` · `GET me` · `POST logout` · `PUT password` · `POST forgot-password` · `POST reset-password` · `POST verify-email` · `POST resend-verify` · `GET captcha`

### 对话 `/api/chat/*`
`POST completions` · `GET/POST sessions` · `GET/DELETE sessions/[id]` · `GET messages`

### 知识库 `/api/knowledge/*`
`GET list` · `POST upload` · `POST upload/file` · `GET/DELETE [id]`

### Dashboard `/api/dashboard/*`
`GET stats` · `GET analytics`

### Admin `/api/admin/*`
`GET stats` · `GET users` · `GET sessions` · `GET analytics` · `POST auth/login`

### 用户 `/api/user/*`
`GET export` · `DELETE chats`

### RAG `/api/v1/rag/*`
`POST ingest` · `POST query` · `GET stats`

### LLM 网关 `/api/llm/*` (v3.2 新增)
`GET gateway/stats` · `GET models` · `GET providers`

### 多模态 `/api/multimodal/*`
`POST stt` · `POST tts` · `GET status`

### 其他
`GET /api/health` · `GET /api/skills` · `POST /api/proactive/heartbeat` · `GET /api/proactive/messages`

## 技能列表 (100 个)

### 日常类 (15)
calculator · unit_converter · password_generator · bmi_calculator · random_generator · countdown_timer · color_converter · morse_code · zodiac_lookup · calorie_calculator · tip_calculator · decision_maker · datetime_calc · habit_tracker · dice_roller

### 办公类 (15)
todo_manager · pomodoro_timer · json_formatter · cron_parser · expense_tracker · csv_analyzer · email_template · meeting_minutes · yaml_processor · schedule_planner · time_tracker · invoice_generator · kanban_board · gantt_chart · contact_manager

### 编程类 (15)
base64_codec · url_codec · hash_generator · uuid_generator · jwt_decoder · sql_formatter · json_validator · ip_calculator · html_entity_codec · env_parser · code_formatter · code_minifier · file_hasher · diff_patch · regex_tester

### 文档类 (13)
markdown_processor · text_statistics · text_diff · regex_builder · template_engine · csv_to_table · json_to_csv · xml_parser · html_cleaner · text_encryptor · text_translator_dict · word_counter · text_summarizer

### 娱乐类 (12)
coin_flipper · fortune_teller · name_generator · lorem_ipsum · ascii_art · number_trivia · emoji_art · maze_generator · sudoku_solver · anagram_solver · word_game · rock_paper_scissors

### 图像类 (12)
image_resize · image_crop · image_rotate · image_watermark · image_compress · image_format_convert · image_metadata · image_thumbnail · image_collage · image_filter · image_color_palette · qrcode_generator

### 音频类 (10)
audio_info · audio_convert · audio_trim · audio_merge · audio_volume · audio_split · audio_fade · audio_speed · audio_reverse · audio_silence_detect

### 视频类 (8)
video_info · video_thumbnail · video_trim · video_merge · video_to_gif · video_extract_audio · video_resize · video_rotate

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 15 + React 19 + TailwindCSS + Framer Motion + Lucide Icons |
| 网关 | NestJS 10 + Fastify + WebSocket |
| AI 核心 | Python 3.12 + FastAPI + Pydantic + Pillow + pydub + ffmpeg + httpx |
| 数据库 | PostgreSQL 17 + Prisma ORM + Redis 8 |
| 向量库 | Milvus 2.4 + Elasticsearch 8 |
| 部署 | Docker Compose (7 容器) |
| 测试 | Vitest (前端) + Pytest (后端) + Playwright (E2E) — 150+ 测试 |
| CI/CD | GitHub Actions (lint → test → build → docker) |

## 测试

```bash
# 前端 API 测试
cd apps/web-portal && npx vitest run

# 后端测试 (100技能 + 核心模块)
cd services/brain-core && pytest tests/ -v

# E2E 测试
cd apps/web-portal && npx playwright test
```

## 项目文档

- [开发方案 v3.0](../梦帮小助_AI助手开发方案v3.0_企业智能版.md)
- [项目结构框架（上）](../梦帮小助_项目结构框架_上.md)
- [项目结构框架（下）](../梦帮小助_项目结构框架_下.md)
- [UI 设计方案](../梦帮小助_前端WebUI设计方案_赛博朋克版_上.md)
- [100 技能开发手册](../梦帮小助_100技能开发手册_Part1_核心引擎与日常办公.md)

## License

UNLICENSED · © 2026 DREAMVFIA UNION
