# Workspace

## Overview

pnpm workspace monorepo using TypeScript, plus a standalone Python FastAPI service for AI-powered codebase analysis.

## Stack

### TypeScript / Node.js (existing)
- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

### Python (AI Codebase Understanding Engine)
- **Python version**: 3.11
- **API framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL (asyncpg/SQLAlchemy) with SQLite fallback
- **Vector DB**: ChromaDB (persistent, local sentence-transformer embeddings)
- **Graph DB**: NetworkX (in-process) with optional Neo4j adapter
- **Cache**: Redis with in-memory fallback
- **Task queue**: Celery + Redis (optional; FastAPI BackgroundTasks used in dev)
- **LLM**: OpenAI (via Replit AI Integrations proxy)
- **Location**: `artifacts/codebase-engine/`

## Key Commands

### TypeScript
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

### Python (AI Codebase Engine)
- `cd artifacts/codebase-engine && PYTHONPATH=. python main.py` — start FastAPI server (port 8000)
- `cd artifacts/codebase-engine && PYTHONPATH=. pytest tests/ -v` — run all tests
- `cd artifacts/codebase-engine && celery -A workers.celery_app worker` — start Celery worker
- `cd artifacts/codebase-engine && docker compose up -d` — start full stack with Docker

## Architecture: AI Codebase Understanding Engine

### Clean Architecture Layers

```
api/          FastAPI routes (analyze, summary, graph, qa, issues, refactor)
core/         Config, logging, exceptions
domain/       Models (Repository, FileAnalysis, CodeIssue, etc.), interfaces (ports)
services/     Business logic (RepoIngestionService, ParserService, RAGService, etc.)
infrastructure/  DB adapters (Postgres, ChromaDB, NetworkX/Neo4j, Redis)
parsers/      AST parsers with Factory + Visitor patterns
workers/      Celery tasks for async processing
tests/        Unit + integration tests
```

### Design Patterns
- **Factory Pattern**: `ParserFactory` — selects correct parser by file extension
- **Visitor Pattern**: `_ASTVisitor` — traverses Python AST nodes
- **Strategy Pattern**: `ICodeParser` / `ILLMClient` — swappable implementations
- **Repository Pattern**: `IRepositoryStore` / `IIssueStore` / `IRefactorStore`

### API Endpoints
- `POST /analyze-repo` — submit GitHub URL for analysis
- `GET /repo-summary/{id}` — status + architecture summary
- `GET /dependency-graph/{id}` — node-link graph (filterable)
- `POST /ask` — RAG Q&A over the codebase
- `GET /issues/{id}` — detected bugs (static + semantic)
- `GET /refactor/{id}` — refactoring suggestions

### Workflow
- **AI Codebase Engine** runs at port 8000

## Environment Variables (Python service)
- `DATABASE_URL` — PostgreSQL URL (falls back to SQLite)
- `REDIS_URL` — Redis for cache + Celery
- `NEO4J_URI` — optional, activates Neo4j graph store
- `AI_INTEGRATIONS_OPENAI_API_KEY` / `AI_INTEGRATIONS_OPENAI_BASE_URL` — Replit proxy
- `OPENAI_API_KEY` — direct OpenAI key (alternative)
- `LLM_MODEL` — default `gpt-4o-mini`
