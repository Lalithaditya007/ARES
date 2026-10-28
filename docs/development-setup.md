# ARES Development Setup

This guide prepares a teammate's machine to work with the current ARES Phase 2 project skeleton.

Phase 2 provides the development environment only. The agents, AEKE, recovery engine, database schema, and Docker sandbox execution logic are planned for later phases.

## Prerequisites

Install the following tools before cloning the repository:

- Git
- Python 3.10 or newer
- Node.js and npm
- Docker Desktop
- A code editor such as VS Code

The environment used to verify this repository contains Python 3.10.11, Node.js 22.13.1, npm 11.7.0, and Docker 28.3.2.

## Clone the Repository

```text
git clone https://github.com/Lalithaditya007/ARES.git
cd ARES
```

## Configuration

Create a local environment file from the example:

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

Do not commit `.env`. It is ignored by Git. Never place real passwords, API keys, or tokens in `.env.example`.

## Backend Setup

The Python virtual environment must be created inside `backend/.venv`. It is separate from the frontend's Node.js dependencies.
The root `.venv` is not used by this project; use `backend/.venv` for all backend commands.

### Windows PowerShell

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, allow it only for the current terminal process and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

When activated, the terminal prompt normally includes `(.venv)`.

## Run the Backend

Keep the virtual environment activated and run:

```text
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`.

Verify the health endpoint from a second terminal:

### Windows PowerShell

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### macOS/Linux

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Stop the backend with `Ctrl+C` when finished.

## Frontend Setup

The frontend uses Node.js/npm and does not use the Python virtual environment.

Open a separate terminal at the project root and run:

```text
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173/`.

Stop the frontend with `Ctrl+C` when finished.

## Docker Verification

Start Docker Desktop before running Docker commands. Verify the Docker engine with:

```text
docker info
docker run --rm hello-world
```

The second command should print `Hello from Docker!`. Phase 2 only verifies Docker availability; it does not implement the ARES sandbox.

## Run Tests

Activate the backend virtual environment, move to the project root, and run:

```text
python -m pytest -q
```

The current Phase 2 test verifies the FastAPI health endpoint.

## Useful Git Checks

From the project root:

```text
git status
git branch --show-current
git pull --rebase origin main
```

Before pushing work, make sure tests pass and no `.env`, `.venv`, `node_modules`, or build output is staged.

## Team Workflow

1. Pull the latest `main` before starting work.
2. Create a feature branch for changes.
3. Make a focused change.
4. Run the relevant tests and checks.
5. Commit with a clear message.
6. Push the feature branch and open a pull request.

Example:

```text
git pull --rebase origin main
git switch -c feature/short-description
git add <files>
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Avoid committing directly to `main` for normal team work.
