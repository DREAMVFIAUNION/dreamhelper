# DreamHelper

```text
██████╗ ██████╗ ███████╗ █████╗ ███╗   ███╗██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗ 
██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗
██║  ██║██████╔╝█████╗  ███████║██╔████╔██║███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝
██║  ██║██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗
██████╔╝██║  ██║███████╗██║  ██║██║ ╚═╝ ██║██║  ██║███████╗███████╗██║     ███████╗██║  ██║
╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                                           
```

<p align="center">
  <strong>DREAMVFIA AI Assistant | Cyberpunk Theme | 100+ Skills | 5 Agents | Local GPU Accelerated</strong>
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=28&pause=1000&color=00FF00&center=true&vCenter=true&width=760&lines=DreamHelper;DREAMVFIA+AI+Assistant;v3.7.0+Enterprise+Edition;100%2B+Skills+%7C+5+Agents+%7C+Local+GPU+Power" alt="Typing SVG" />
</p>

<p align="center">
  <a href="https://github.com/DREAMVFIAUNION/dreamhelper-v3">
    <img src="https://img.shields.io/github/stars/DREAMVFIAUNION/dreamhelper-v3?style=flat&color=00ff00" alt="stars">
  </a>
  <a href="https://github.com/DREAMVFIAUNION/dreamhelper-v3">
    <img src="https://img.shields.io/github/forks/DREAMVFIAUNION/dreamhelper-v3?style=flat&color=00ff00" alt="forks">
  </a>
  <a href="https://github.com/DREAMVFIAUNION/dreamhelper-v3/releases">
    <img src="https://img.shields.io/github/v/release/DREAMVFIAUNION/dreamhelper-v3?color=00ff00&label=Version" alt="release">
  </a>
  <img src="https://img.shields.io/badge/License-PROPRIETARY-00ff00" alt="license">
  <img src="https://img.shields.io/badge/Docker-7+Containers-00ff00" alt="docker">
  <img src="https://img.shields.io/badge/Python-3.12+-00ff00" alt="python">
  <img src="https://img.shields.io/badge/Next.js-15-00ff00" alt="nextjs">
</p>

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a> |
  <a href="#system-architecture"><strong>Architecture</strong></a> |
  <a href="#api-endpoints"><strong>API</strong></a> |
  <a href="#skills-overview"><strong>Skills</strong></a>
</p>

---

## Overview

DREAMVFIA is an enterprise-grade AI assistant platform built around a **Next.js frontend**, **NestJS gateway**, and **Python FastAPI brain core**. It combines conversational AI, multimodal processing, knowledge retrieval, workflow execution, and a large built-in skill ecosystem into one deployable system.

### Highlights at a glance

| Area | What you get |
|------|---------------|
| Multi-agent runtime | ReAct, Code, Writing, Analysis, and PlanExecute agents |
| Skill ecosystem | 100+ built-in skills across daily, office, coding, document, image, audio, and video workflows |
| AI capabilities | RAG knowledge base, tool calling, multimodal understanding, workflow automation |
| Infra | PostgreSQL, Redis, Milvus, Elasticsearch, MinIO, WebSocket, local GPU support |
| Product UX | Cyberpunk-themed UI, realtime chat, session persistence, admin features |

---

## Demo Videos

| Demo | Preview |
|------|---------|
| YouTube Shorts Demo | <a href="https://youtube.com/shorts/sBnOLkFhz-I?si=4K-JQQNdQtD3DQ2Z"><img src="https://img.youtube.com/vi/sBnOLkFhz-I/0.jpg" width="280" alt="YouTube Shorts Demo" /></a> |
| YouTube Full Demo | <a href="https://www.youtube.com/watch?v=Yct5YYgZeJU&t=277s"><img src="https://img.youtube.com/vi/Yct5YYgZeJU/0.jpg" width="280" alt="YouTube Full Demo" /></a> |

---

## Key Features

- **5 specialized agents** for reasoning, coding, writing, analysis, and planning workflows
- **100+ built-in skills** covering productivity, coding, documents, media, and automation
- **Local GPU acceleration** for high-performance AI inference and multimodal workloads
- **RAG knowledge system** backed by Milvus + Elasticsearch for semantic and keyword retrieval
- **Multimodal capabilities** including STT, TTS, document parsing, and vision processing
- **Realtime architecture** with WebSocket support and persistent chat sessions
- **Enterprise-oriented stack** with gateway, auth, caching, storage, and structured service boundaries
- **Cyberpunk product experience** with animated UI and dark-mode-first styling

### Agent System

| Agent | Capability | Use Case |
|-------|------------|----------|
| ReAct | Tool calling + reasoning | Multi-step task execution |
| Code | Code generation / execution | Software development |
| Writing | Structured content creation | Content generation |
| Analysis | Data analysis and insights | Business intelligence |
| PlanExecute | Planning and execution loops | Complex task orchestration |

### Product Experience

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=14&pause=500&color=00FF00&background=0D1117&lines=Neon+Glow+Effects;Dark+Mode+First;Animated+Components;Cyberpunk+Visual+Language" alt="product experience">
</p>

---

<a id="system-architecture"></a>

## System Architecture

```mermaid
flowchart TD
    A[Next.js 15 Frontend
React 19 + TailwindCSS]
    B[NestJS Gateway
Fastify + WebSocket]
    C[Brain Core
FastAPI + Python]
    D[PostgreSQL
Prisma ORM]
    E[Redis
Cache + Pub/Sub]
    F[Milvus
Vector Search]
    G[Elasticsearch
Full-text Search]
    H[MinIO
Object Storage]
    I[Local GPU
Model Compute]

    A --> B
    B --> C
    B --> D
    B --> E
    C --> F
    C --> G
    C --> H
    C --> I
```

### Architecture layers

| Layer | Responsibility |
|-------|----------------|
| Frontend | Chat UI, product surfaces, interaction flows, cyberpunk-themed experience |
| Gateway | Auth, transport, WebSocket communication, channel access, API orchestration |
| Brain Core | Agent runtime, tools, workflows, multimodal processing, RAG, memory |
| Data & Infra | PostgreSQL, Redis, Milvus, Elasticsearch, MinIO, GPU execution |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TailwindCSS, Framer Motion |
| Gateway | NestJS 10, Fastify, WebSocket |
| AI Core | Python 3.12, FastAPI, Pydantic |
| Database | PostgreSQL 17, Prisma ORM, Redis 8 |
| Search | Milvus 2.4, Elasticsearch 8 |
| Deploy | Docker Compose (7 Containers) |
| Testing | Vitest, Pytest, Playwright |

---

<a id="skills-overview"></a>

## 100+ Skills Overview

| Category | Count | Example Skills |
|----------|-------|----------------|
| Daily | 15 | `calculator`, `unit_converter`, `password_generator`, `bmi_calculator` |
| Office | 15 | `todo_manager`, `pomodoro_timer`, `csv_analyzer`, `invoice_generator` |
| Coding | 15 | `base64_codec`, `url_codec`, `jwt_decoder`, `sql_formatter`, `code_formatter` |
| Document | 13 | `markdown_processor`, `text_statistics`, `text_summarizer`, `word_counter` |
| Entertainment | 12 | `fortune_teller`, `name_generator`, `ascii_art`, `sudoku_solver` |
| Image | 12 | `image_resize`, `image_watermark`, `image_filter`, `image_collage` |
| Audio | 10 | `audio_convert`, `audio_trim`, `audio_merge`, `audio_volume` |
| Video | 8 | `video_thumbnail`, `video_trim`, `video_merge`, `video_to_gif` |

> The skill system is designed to auto-route user requests to the right tool chain for practical everyday and professional workflows.

---

<a id="quick-start"></a>

## Quick Start

### Prerequisites

```bash
Node.js >= 20
pnpm >= 9
Python >= 3.12
Docker + Docker Compose
```

### 1. Clone Project

```bash
git clone https://github.com/DREAMVFIAUNION/dreamhelper-v3.git
cd dreamhelper-v3
```

### 2. Install Dependencies

```bash
# Frontend dependencies
pnpm install

# AI Core dependencies
cd services/brain-core
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your config
```

### 4. Start Docker Services

```bash
docker compose up -d postgres redis milvus es minio
```

### 5. Initialize Database

```bash
pnpm db:migrate
pnpm db:seed
```

### 6. Start Development

```bash
# Frontend (http://localhost:3000)
pnpm --filter web-portal dev

# AI Core (http://localhost:8000)
cd services/brain-core
uvicorn src.main:app --reload --port 8000

# Gateway (Optional) (http://localhost:3001)
pnpm --filter gateway dev
```

### 7. One-Click Start (Docker)

```bash
docker compose up -d
# Visit http://localhost:3000
```

---

<a id="api-endpoints"></a>

## API Endpoints

| Module | Endpoint | Purpose |
|--------|----------|---------|
| Auth | `POST /api/auth/login` | User login |
| Auth | `POST /api/auth/register` | User registration |
| Auth | `POST /api/auth/logout` | User logout |
| Auth | `PUT /api/auth/password` | Change password |
| Chat | `POST /api/chat/completion` | AI chat completion |
| Chat | `GET/POST /api/chat/session` | Session management |
| Knowledge | `POST /api/knowledge/upload` | Upload documents |
| Knowledge | `GET /api/knowledge/list` | List knowledge items |
| Multimodal | `POST /api/multimodal/stt` | Speech to text |
| Multimodal | `POST /api/multimodal/tts` | Text to speech |

---

## Feature Demos

### AI Chat

```python
# User Input
user: "Write a poem about starlight"

# AI Response
Stars twinkle in the deep night sky,
Milky Way reflects a dreamy eye.
Vast universe so endless and bright,
Gazing up, my thoughts take flight.
```

### Image Processing

```bash
# User: "Add watermark to this image"
# Auto calls image_watermark skill
# Returns processed image
```

### Data Analysis

```bash
# User: "Analyze this sales data"
# AI auto calls csv_analyzer
# Returns visualization report
```

---

## Connect With Us

<p align="center">
  <a href="https://github.com/DREAMVFIAUNION">
    <img src="https://img.shields.io/badge/GitHub-DREAMVFIAUNION-00ff00?style=for-the-badge&logo=github" alt="github">
  </a>
</p>

---

## Project Stats

<p align="center">

![GitHub Stars](https://img.shields.io/github/stars/DREAMVFIAUNION/dreamhelper-v3)
![GitHub Forks](https://img.shields.io/github/forks/DREAMVFIAUNION/dreamhelper-v3)
![Contributors](https://img.shields.io/github/contributors/DREAMVFIAUNION/dreamhelper-v3)
![Last Commit](https://img.shields.io/github/last-commit/DREAMVFIAUNION/dreamhelper-v3)

</p>

---

## Contributing

Welcome to submit Issues and Pull Requests.

```bash
# 1. Fork the project
# 2. Create feature branch
git checkout -b feature/AmazingFeature
# 3. Commit changes
git commit -m 'Add some AmazingFeature'
# 4. Push branch
git push origin feature/AmazingFeature
# 5. Open Pull Request
```

---

## License

```text
Copyright (c) 2026 DREAMVFIA UNION
All Rights Reserved
```

---

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=12&pause=1000&color=00FF00&center=true&vCenter=true&width=420&lines=Made+by+DREAMVFIA+UNION;Building+the+Future+of+AI+Assistants" alt="footer">
</p>

<p align="center">
  <sub>Copyright 2026 DREAMVFIA UNION | Built for the future of AI assistants</sub>
</p>
