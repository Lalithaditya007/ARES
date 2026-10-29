# ARES

ARES — **An Agentic AI Execution Management Platform for Reliable Autonomous Software Engineering**.

ARES is a research-oriented platform for executing software-engineering tasks through specialized agents, running code in controlled environments, detecting failures, recovering from them, verifying results, and reusing validated recovery experiences through the Adaptive Execution Knowledge Engine (AEKE).

## Current scope

The repository is currently in **Phase 3 Docker sandbox and execution-manager implementation**. Phase 3 adds the foundational, local Docker execution infrastructure while preserving the Phase 2 backend and frontend skeleton.

The current implementation includes:

- A FastAPI backend with a health endpoint
- A React/Vite frontend skeleton
- A basic pytest health check
- Development configuration and setup documentation
- Docker Engine verification
- A typed execution contract and execution manager
- Controlled local workspaces and allowlisted Python/Node runtime images
- Docker SDK execution with bounded output, timeouts, resource limits, and cleanup
- A restricted multi-file project runner for registered workspaces

The agents, execution sandbox, Recovery Engine, AEKE, orchestration workflows, and other domain features are planned for future implementation phases. They are not yet implemented.

## Technology stack

- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI, Uvicorn
- **Testing:** pytest
- **Execution foundation:** Docker
- **Planned technologies:** LangGraph, Ollama, PostgreSQL, and semantic retrieval

The architecture is intended to remain independent of any particular LLM model or GPU.

## Development setup

See [docs/development-setup.md](docs/development-setup.md) for prerequisites and full setup instructions.

The backend environment is created at `backend/.venv`. The root `.venv` is not used by this project.

### Backend

From the repository root, use the backend virtual environment:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The API health check is available at `http://127.0.0.1:8000/health`.

### Frontend

From the `frontend` directory:

```powershell
npm install
npm run dev
```

### Tests

From the repository root:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q
```

### Frontend verification

From the `frontend` directory:

```powershell
npm run build
npm run lint
```

### Docker verification

With Docker Desktop running:

```powershell
docker info
docker run --rm hello-world
```

See the [ARES master handover](docs/ARES_MASTER_HANDOVER.md) first for the
authoritative project status and file inventory. The focused [Phase 3
execution-manager documentation](docs/phase3-execution-manager/README.md)
covers the implementation guide, runbook, decisions, test report, observed
results, and current limitations.
