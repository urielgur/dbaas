# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

DBaaS Manager is a metadata aggregation platform that unifies GitLab project inventory with ArgoCD deployment status across multiple Kubernetes clusters. It has no direct database control — it reads from GitLab (Chart.yaml files) and ArgoCD APIs, merges them, and presents a unified view.

## Commands

### Backend

```bash
cd backend
pip install -e ".[dev]"           # Install with dev dependencies
uvicorn app.main:app --reload     # Dev server (port 8000)
pytest                            # All tests
pytest tests/test_foo.py::test_bar  # Single test
ruff check app/                   # Lint
mypy app/                         # Type check
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # Vite dev server (port 5173)
npm run build     # Production build
npm run lint      # ESLint
```

### Docker

```bash
docker-compose up --build
# Backend: http://localhost:8000 (API at /api/v1)
# Frontend: http://localhost:3000
```

## Architecture

### Data Flow

```
GitLab (subgroup tree → Chart.yaml) ─┐
                                      ├→ ScanOrchestrator → StorageBackend → API → Frontend
ArgoCD (multi-cluster apps)          ┘        ↑
                                        ScanScheduler (background interval)
```

### Backend (`backend/app/`)

- **`collectors/`** — `GitLabCollector` walks subgroup tree via BFS, fetches `Chart.yaml` from each project. `ArgoCDCollector` queries multiple ArgoCD instances in parallel.
- **`scanner/scan_orchestrator.py`** — Runs both collectors concurrently (`asyncio.gather`), matches results using the key `{last_namespace_segment}-{db_name}`, persists `DatabaseRecord` objects.
- **`storage/`** — Abstract `StorageBackend` with `JsonStorageBackend` and `MongoStorageBackend`. Selected via `STORAGE_BACKEND` env var.
- **`registry/`** — `DBTypeRegistry` is a plugin system for database types (elasticsearch, mongodb, postgresql). Add a new type under `registry/types/`.
- **`auth/`** — Abstract `AuthProvider` with `LocalAuthProvider` (JSON file-backed). JWT tokens via `tokens.py`.
- **`api/`** — Three routers: `auth`, `databases`, `scan`. All mounted under `/api/v1`.
- **`config.py`** — All configuration via `pydantic-settings` (env vars).
- **`dependencies.py`** — FastAPI `Depends()` providers for storage, collectors, auth.

### Frontend (`frontend/src/`)

- **`api/`** — axios client with JWT auth interceptor; typed wrappers for each endpoint.
- **`hooks/`** — React Query hooks (`useDatabases`, `useScan`, `useDbTypes`, `useUrlFilters`).
- **`components/`** — Table-centric UI; `fields/` contains renderers for ArgoCD links, sync/health badges, etc.
- Filters and pagination are URL-based (query params) and server-side.

### ArgoCD App Key Convention

The matching key between GitLab and ArgoCD is: `{last_namespace_segment}-{db_name}` (e.g., namespace `ops/logs/prod` + db name `my-db` → key `prod-my-db`). This is the critical join logic — get it wrong and databases show as unmatched.

### Storage

- JSON backend: atomic writes via `tempfile + os.replace`. Files at `data/databases.json` and `data/users.json`.
- MongoDB backend: Motor async driver; database selected via `STORAGE_MONGO_DATABASE`.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `GITLAB_URL` | GitLab instance URL |
| `GITLAB_TOKEN` | Personal access token |
| `GITLAB_PARENT_GROUP_ID` | Root group ID to start BFS scan |
| `ARGOCD_INSTANCES` | JSON array: `[{"cluster_name":…, "url":…, "token":…}]` |
| `STORAGE_BACKEND` | `"json"` or `"mongodb"` |
| `AUTH_SECRET_KEY` | Required — JWT signing key |
| `AUTH_BOOTSTRAP_ADMIN_USERNAME/PASSWORD` | Seeds initial admin on first run |
| `SCAN_INTERVAL_SECONDS` | Background scan interval; `0` disables |

See `.env.example` for the full list.

## Extensibility Points

- **New DB type**: Add a file under `backend/app/registry/types/` and register it in `db_type_registry.py`.
- **New auth provider**: Implement the `AuthProvider` abstract class and wire it in `dependencies.py`.
- **New storage backend**: Implement `StorageBackend` abstract class.
