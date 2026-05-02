# Workspace

## Overview

Full-stack SaaS platform for AI-powered codebase analysis. pnpm monorepo (TypeScript) + Python FastAPI backend + React+Vite frontend.

## Stack

### Frontend — AI Codebase Platform (`artifacts/codebase-ui/`)
- **Framework**: React 18 + Vite + TypeScript
- **Routing**: wouter
- **State**: Zustand (auth store with JWT in localStorage)
- **Data fetching**: @tanstack/react-query
- **HTTP client**: Axios with auth interceptor (`src/lib/api.ts`)
- **UI**: shadcn/ui components + Tailwind CSS
- **Graph**: @xyflow/react (ReactFlow) for dependency graph
- **Toasts**: sonner
- **Preview path**: `/` (port 19556 in dev)

### Backend — AI Codebase Engine (`artifacts/codebase-engine/`)
- **Framework**: FastAPI + Uvicorn (port 8000)
- **Route prefix**: `/engine` (all routes)
- **Auth**: JWT (python-jose) + bcrypt password hashing
- **Database**: PostgreSQL + SQLAlchemy ORM (SQLite fallback)
  - Tables: `users`, `repositories`, `file_analyses`, `code_issues`, `refactor_suggestions`
- **Vector DB**: ChromaDB (persistent, local sentence-transformer embeddings)
- **Graph DB**: NetworkX (in-process) with optional Neo4j adapter
- **Cache**: Redis with in-memory fallback
- **Task queue**: Celery + Redis (FastAPI BackgroundTasks in dev)
- **LLM**: OpenAI (via Replit AI Integrations proxy or direct API key)
- **WebSocket**: `/engine/ws/progress/{repo_id}` for real-time progress

### TypeScript API (`artifacts/api-server/`)
- **Framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Route prefix**: `/api`
- **Port**: 8080

## Key Commands

### Frontend
- `pnpm --filter @workspace/codebase-ui run dev` — start Vite dev server

### Python Backend
- `cd artifacts/codebase-engine && PYTHONPATH=. python main.py` — start FastAPI (port 8000)
- `cd artifacts/codebase-engine && PYTHONPATH=. pytest tests/ -v` — run 18 unit tests
- `cd artifacts/codebase-engine && celery -A workers.celery_app worker` — Celery worker
- `cd artifacts/codebase-engine && docker compose up -d` — full stack with Docker

### TypeScript
- `pnpm run typecheck` — full typecheck
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks + Zod schemas
- `pnpm --filter @workspace/db run push` — push DB schema (dev only)

## Architecture: Routing (Proxy)

```
/ (root)     →  React frontend (port 19556)
/engine      →  Python FastAPI (port 8000)
/api         →  TypeScript Express (port 8080)
```

## Frontend Pages

| Route | Page | Auth |
|---|---|---|
| `/` | Landing page | Public |
| `/login` | Login form | Public (redirects if authed) |
| `/register` | Registration form | Public (redirects if authed) |
| `/dashboard` | Repo list + submit new repo | Protected |
| `/repo/:id` | Analysis view (5 tabs) | Protected |

## Python API Endpoints (all prefixed `/engine`)

### Auth
- `POST /auth/register` — create account, returns JWT
- `POST /auth/login` — returns JWT
- `GET /auth/me` — current user (Bearer)

### Repos
- `POST /analyze-repo` — submit GitHub URL
- `GET /repo-summary` — list all repos
- `GET /repo-summary/{id}` — status + summary
- `GET /my-repos` — user's repos (Bearer)
- `DELETE /repo/{id}` — delete repo (Bearer, owner only)

### Analysis
- `GET /dependency-graph/{id}` — node-link graph
- `GET /issues/{id}` — code issues (filter by severity/file)
- `GET /refactor/{id}` — refactoring suggestions
- `POST /ask` — RAG Q&A with source citations

### Real-time
- `WS /ws/progress/{id}` — analysis progress events

## Auth Flow
- JWT stored in localStorage via `useAuthStore` (Zustand)
- `loadFromStorage()` called on app mount to restore session
- Axios interceptor injects `Authorization: Bearer <token>` on every request
- Protected routes redirect to `/login?returnTo=<path>` if unauthenticated
- After login/register: `setUser(tokenResponse)` → redirect to `/dashboard`

## Clean Architecture (Python Backend)

```
api/          FastAPI routes
core/         Config, logging, exceptions
domain/       Models + interfaces (ports)
services/     Business logic (AuthService, RepoIngestionService, RAGService, etc.)
infrastructure/  DB adapters (Postgres, ChromaDB, NetworkX/Neo4j, Redis)
parsers/      AST parsers — Factory + Visitor patterns
workers/      Celery async tasks
tests/        18 unit + integration tests
```

## Docker (Production)

`artifacts/codebase-engine/docker-compose.yml` orchestrates:
- **nginx** — reverse proxy (port 80): `/engine` → FastAPI, `/` → Frontend
- **frontend** — Vite production build (port 3000)
- **api** — FastAPI (port 8000)
- **worker** — Celery worker
- **postgres** — PostgreSQL 16
- **redis** — Redis 7
- Optional profiles: `neo4j`, `monitoring` (Flower)

## Environment Variables

### Python Backend
- `OPENAI_API_KEY` — for LLM features
- `JWT_SECRET` — JWT signing secret (change in production!)
- `DATABASE_URL` — PostgreSQL (falls back to SQLite)
- `REDIS_URL` — Redis for cache + Celery
- `LLM_MODEL` — default `gpt-4o-mini`
- `NEO4J_URI` — optional, activates Neo4j graph store

### Frontend
- `VITE_API_BASE` — API base path (default `/engine`)
