# AI Codebase Understanding Engine — Full-Stack Platform

A production-grade SaaS platform where developers submit GitHub repositories and receive deep AI-powered analysis: architecture explanations, interactive dependency graphs, bug detection, refactoring suggestions, and RAG-powered Q&A chat.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser / Client                      │
│              React + Vite SPA (port 3000)               │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / WebSocket
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Nginx Reverse Proxy                     │
│   /         →  Frontend (port 3000)                    │
│   /engine   →  FastAPI Backend (port 8000)             │
└───────────┬──────────────────────────┬──────────────────┘
            │                          │
            ▼                          ▼
┌──────────────────┐       ┌───────────────────────────────┐
│  React + Vite    │       │  FastAPI + Python 3.11        │
│  Frontend        │       │  All routes at /engine/*      │
│                  │       │                               │
│  Pages:          │       │  Auth: JWT + bcrypt           │
│  / Landing       │       │  Repo ingestion (GitPython)   │
│  /login          │       │  Parser (AST + regex)         │
│  /register       │       │  Embedding (ChromaDB)         │
│  /dashboard      │       │  RAG Q&A (OpenAI)             │
│  /repo/:id       │       │  Bug detection (static+LLM)   │
│    Overview tab  │       │  Refactor suggestions         │
│    Issues tab    │       │  WebSocket progress           │
│    Refactor tab  │       └───────────┬───────────────────┘
│    Graph tab     │                   │
│    Q&A tab       │    ┌──────────────┼──────────────────┐
└──────────────────┘    ▼              ▼                   ▼
              ┌──────────────┐ ┌──────────┐ ┌────────────────┐
              │  PostgreSQL  │ │  Redis   │ │   ChromaDB     │
              │  users       │ │  cache + │ │   vector store │
              │  repos       │ │  Celery  │ └────────────────┘
              │  issues      │ └──────────┘
              │  refactors   │
              └──────────────┘
```

### Design Patterns
| Pattern | Location |
|---|---|
| **Factory** | `parsers/factory.py` — selects Python/JS parser by file extension |
| **Visitor** | `parsers/python_parser.py` — walks Python AST nodes |
| **Strategy** | `domain/interfaces.py` — `ICodeParser`, `ILLMClient` |
| **Repository** | `infrastructure/database/repositories/` — DB abstraction layer |
| **Dependency Injection** | FastAPI `Depends()` for auth, DB sessions |
| **Clean Architecture** | Domain → Services → Infrastructure, no inward dependencies |

---

## Features

| Feature | Description |
|---|---|
| **JWT Auth** | Register / login / protected routes with bcrypt password hashing |
| **Repo Analysis** | Clone, parse, embed any public GitHub repository |
| **Architecture Summary** | LLM-generated overview of codebase structure |
| **Dependency Graph** | Interactive ReactFlow visualization (zoom, pan, filter) |
| **Bug Detection** | Static (AST complexity, type hints) + semantic (LLM) issue finder |
| **Refactoring Suggestions** | God Class, Feature Envy, design pattern advice with effort badges |
| **RAG Q&A** | Ask questions about the code — answers cite source file chunks |
| **Real-time Progress** | WebSocket stream of analysis stages |

---

## Project Structure

```
/
├── artifacts/
│   ├── codebase-engine/            # Python FastAPI backend
│   │   ├── api/
│   │   │   ├── routes/             # REST endpoints + WebSocket
│   │   │   │   ├── auth.py         # register, login, /me
│   │   │   │   ├── analyze.py      # POST /analyze-repo
│   │   │   │   ├── summary.py      # GET /repo-summary
│   │   │   │   ├── graph.py        # GET /dependency-graph
│   │   │   │   ├── qa.py           # POST /ask
│   │   │   │   ├── issues.py       # GET /issues
│   │   │   │   ├── refactor.py     # GET /refactor
│   │   │   │   ├── user_repos.py   # GET /my-repos, DELETE /repo/:id
│   │   │   │   └── progress.py     # WS /ws/progress/:id
│   │   │   └── middleware/
│   │   ├── core/                   # Config, logging, exceptions
│   │   ├── domain/                 # Models + interfaces (ports)
│   │   ├── infrastructure/         # DB, vector store, graph, cache
│   │   ├── services/               # Business logic + AuthService
│   │   ├── parsers/                # AST parsers (Python, JS)
│   │   ├── workers/                # Celery background tasks
│   │   ├── tests/                  # 18 unit + integration tests
│   │   ├── docker-compose.yml      # Full stack orchestration
│   │   ├── nginx.conf              # Reverse proxy config
│   │   └── Dockerfile
│   │
│   └── codebase-ui/                # React + Vite frontend
│       └── src/
│           ├── pages/
│           │   ├── Home.tsx        # Landing page
│           │   ├── Login.tsx       # Auth form
│           │   ├── Register.tsx    # Sign-up form
│           │   ├── Dashboard.tsx   # Repo list + submit form
│           │   └── RepoDetails.tsx # 5-tab analysis view
│           ├── components/
│           │   ├── layout/         # Navbar
│           │   └── ui/             # shadcn/ui components
│           └── lib/
│               ├── api.ts          # Axios API client (all endpoints)
│               └── auth-store.ts   # Zustand JWT auth state
```

---

## API Reference

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/engine/auth/register` | — | Create account, returns JWT |
| `POST` | `/engine/auth/login` | — | Get JWT token |
| `GET` | `/engine/auth/me` | Bearer | Get current user profile |

### Repository Analysis
| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/engine/analyze-repo` | optional | Submit GitHub repo for analysis |
| `GET` | `/engine/repo-summary` | — | List all repos |
| `GET` | `/engine/repo-summary/{id}` | — | Repo status + summary |
| `GET` | `/engine/my-repos` | Bearer | List user's own repos |
| `DELETE` | `/engine/repo/{id}` | Bearer | Delete repo (owner only) |

### Analysis Results
| Method | Path | Description |
|---|---|---|
| `GET` | `/engine/dependency-graph/{id}` | Node-link graph (filterable by type/size) |
| `GET` | `/engine/issues/{id}` | Code issues (filter by severity, file) |
| `GET` | `/engine/refactor/{id}` | Refactoring suggestions (filter by effort) |
| `POST` | `/engine/ask` | RAG Q&A — answer + source file citations |

### Real-time
| Protocol | Path | Description |
|---|---|---|
| WebSocket | `/engine/ws/progress/{id}` | Analysis progress events |

---

## Running Locally

### Docker Compose (recommended)

Starts everything: Nginx, Frontend, FastAPI, Celery, PostgreSQL, Redis.

```bash
cd artifacts/codebase-engine
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY and a JWT_SECRET
docker compose up -d
```

- Frontend: http://localhost
- API docs: http://localhost/engine/docs
- Celery monitoring (optional): `docker compose --profile monitoring up -d`
- Neo4j graph DB (optional): `docker compose --profile neo4j up -d`

### Without Docker

```bash
# Backend
cd artifacts/codebase-engine
pip install -r requirements.txt
PYTHONPATH=. python main.py     # port 8000

# Frontend (from repo root)
pnpm install
pnpm --filter @workspace/codebase-ui run dev   # port varies
```

---

## Environment Variables

### Backend (`.env` in `artifacts/codebase-engine/`)

```env
# Required for LLM features
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Required for JWT auth (change in production!)
JWT_SECRET=your-long-random-secret

# Database (defaults to SQLite if unset)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
```

### Frontend

```env
VITE_API_BASE=/engine
```

---

## Analysis Pipeline

```
POST /engine/analyze-repo
        │
        ▼
  RepoIngestionService        ← Clone via GitPython
        │
        ▼
  ParserService (Factory)     ← Python AST / JS regex parser
        │
        ▼
  EmbeddingService            ← Chunk code → ChromaDB vectors
        │
        ▼
  BugDetectionService         ← Static (AST) + LLM semantic rules
        │
        ▼
  RefactorService             ← Design pattern + LLM suggestions
        │
        ▼
  SummaryService              ← LLM architecture narrative
        │
        ▼
  status = "complete" ✓       ← WebSocket notifies frontend
```

---

## Running Tests

```bash
cd artifacts/codebase-engine
PYTHONPATH=. pytest tests/ -v
```

18 unit tests, all run with no external dependencies (in-memory SQLite + mocked LLM).

---

## Extending the Engine

### Add a New Language Parser

1. Create `parsers/go_parser.py` extending `BaseParser`
2. Implement `supported_extensions`, `language`, `_parse_content`
3. Register in `parsers/parser_factory.py`

### Add a New Bug Rule

Add a `_check_*` method to `BugDetectionService` and call it from `detect_static_issues`.

### Switch to Neo4j

Set `NEO4J_URI` in your environment — `get_graph_store()` switches automatically.
