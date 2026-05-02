# AI Codebase Understanding Engine

A production-grade, scalable system that analyses any GitHub repository and provides deep insights powered by static analysis and LLM reasoning.

## Features

| Feature | Description |
|---|---|
| **Repository Ingestion** | Clone any public GitHub repo, detect languages, count files/LOC |
| **AST Parsing** | Extract classes, functions, imports, call graphs using the `ast` module |
| **Dependency Graph** | Build and query a directed graph (files → classes → functions) |
| **Vector Embeddings** | Chunk code files, embed with ChromaDB, enable semantic search |
| **Developer Q&A (RAG)** | Answer natural-language questions using retrieved code context + LLM |
| **Architecture Summary** | LLM-generated architecture overview from file-level summaries |
| **Bug Detection** | Static rules (complexity, type hints, circular imports) + LLM semantic detection |
| **Refactoring Suggestions** | Code-smell detection (God Class, Feature Envy) + LLM pattern recommendations |
| **Async Processing** | Celery + Redis for background analysis of large repositories |
| **Caching** | Redis-backed response caching with in-memory fallback |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI (API Layer)                       │
│  POST /analyze-repo  GET /repo-summary/:id  GET /dependency-    │
│  graph/:id  POST /ask  GET /issues/:id  GET /refactor/:id        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Service Layer                               │
│  RepoIngestionService  →  ParserService  →  EmbeddingService    │
│  AnalysisService  →  BugDetectionService  →  RefactorService    │
│  GraphService  →  RAGService  →  AnalysisPipeline               │
└──────┬──────────────────────────────────────────────┬───────────┘
       │ Repository Pattern                            │ Strategy Pattern
┌──────▼──────────────────┐            ┌──────────────▼────────────┐
│    Infrastructure Layer  │            │      Parser Layer          │
│  PostgreSQL (metadata)   │            │  ParserFactory (Factory)   │
│  ChromaDB (vectors)      │            │  PythonParser  (Visitor)   │
│  NetworkX/Neo4j (graph)  │            │  JavaScriptParser          │
│  Redis (cache/queue)     │            └────────────────────────────┘
└──────────────────────────┘
```

### Design Patterns Applied

| Pattern | Where |
|---|---|
| **Factory** | `ParserFactory` → selects correct parser by file extension |
| **Visitor** | `_ASTVisitor` → traverses Python AST nodes |
| **Strategy** | `ICodeParser` / `ILLMClient` → swappable implementations |
| **Repository** | `IRepositoryStore` / `IIssueStore` / `IRefactorStore` → DB abstraction |
| **Clean Architecture** | Domain → Services → Infrastructure, no inward dependencies |

---

## Setup Instructions

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone / navigate to this directory
cd artifacts/codebase-engine

# 2. Copy environment config
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# 3. Start all services
docker compose up -d

# 4. Check health
curl http://localhost:8000/health
```

To also start Neo4j:
```bash
docker compose --profile neo4j up -d
```

To monitor Celery workers:
```bash
docker compose --profile monitoring up -d
```

### Option B: Local Development

**Prerequisites:** Python 3.11+, (optional) PostgreSQL, (optional) Redis

```bash
cd artifacts/codebase-engine

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — DATABASE_URL can be left blank for SQLite

# Start the server
python main.py
# or: uvicorn main:app --reload --port 8000
```

**Start Celery worker (optional, for background processing):**
```bash
celery -A workers.celery_app worker --loglevel=info
```

---

## API Reference

### POST `/analyze-repo`
Submit a GitHub repository for analysis. Returns immediately; poll for status.

```json
{
  "github_url": "https://github.com/tiangolo/fastapi",
  "branch": "master",
  "force_reanalysis": false
}
```

**Response `202`:**
```json
{
  "repo_id": "uuid",
  "status": "cloning",
  "message": "Analysis started. Use GET /repo-summary/{id} to track progress."
}
```

---

### GET `/repo-summary/{repo_id}`
Get analysis status and results.

**Response `200`:**
```json
{
  "repo_id": "uuid",
  "github_url": "https://github.com/...",
  "status": "complete",
  "languages": ["python"],
  "file_count": 312,
  "total_lines": 48291,
  "architecture_summary": "## Architecture Overview\n...",
  "created_at": "2025-01-01T00:00:00",
  "completed_at": "2025-01-01T00:05:00"
}
```

---

### GET `/dependency-graph/{repo_id}`
Retrieve the code dependency graph.

Query parameters:
- `node_type` — filter by `file` | `class` | `function`
- `max_nodes` — cap result size (default: 500)

---

### POST `/ask`
Ask a natural-language question about the codebase (RAG).

```json
{
  "repo_id": "uuid",
  "question": "How does authentication work in this codebase?",
  "max_chunks": 5
}
```

**Response `200`:**
```json
{
  "repo_id": "uuid",
  "question": "How does authentication...",
  "answer": "Authentication is handled by...",
  "source_chunks": [
    {
      "file_path": "auth/middleware.py",
      "start_line": 42,
      "end_line": 68,
      "content": "...",
      "score": 0.92
    }
  ]
}
```

---

### GET `/issues/{repo_id}`
Get detected code issues.

Query parameters:
- `severity` — `critical` | `high` | `medium` | `low` | `info`
- `file_path` — substring filter

---

### GET `/refactor/{repo_id}`
Get refactoring suggestions.

Query parameters:
- `effort` — `low` | `medium` | `high`
- `file_path` — substring filter

---

## Running Tests

```bash
cd artifacts/codebase-engine
pytest tests/ -v
```

Unit tests run with no external dependencies (in-memory SQLite + mocked LLM).

---

## Environment Variables

See `.env.example` for full reference. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | SQLite | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for cache and Celery |
| `NEO4J_URI` | *(unset)* | Enable Neo4j graph DB (optional) |
| `OPENAI_API_KEY` | *(unset)* | Your OpenAI key, or use Replit AI Integrations |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model for completions |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage path |
| `REPOS_BASE_DIR` | `./data/repos` | Cloned repository storage |

---

## Extending the Engine

### Add a New Language Parser

1. Create `parsers/go_parser.py` extending `BaseParser`
2. Implement `supported_extensions`, `language`, and `_parse_content`
3. Register in `parsers/parser_factory.py`:
   ```python
   factory.register(GoParser())
   ```

### Add a New Analysis Rule

Add a method to `BugDetectionService._check_*` and call it from `detect_static_issues`.

### Switch to Neo4j

Set `NEO4J_URI` in your environment — the `get_graph_store()` factory switches automatically.
