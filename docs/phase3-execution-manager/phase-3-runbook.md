# ARES Phase 3 Runbook

Commands below assume PowerShell from `D:\major\Implementation`. Do not use the
root `.venv`; the canonical backend environment is `backend\.venv`.

## Prerequisites

- Python 3.10 or newer
- Docker Desktop running
- Node.js/npm for frontend verification

Check the actual interpreter and installed dependencies:

```powershell
.\backend\.venv\Scripts\python.exe --version
.\backend\.venv\Scripts\python.exe -m pip show fastapi pydantic pytest docker pywin32 charset-normalizer
.\backend\.venv\Scripts\python.exe -m pip check
```

`pip check` may report `charset-normalizer 3.5.2 is not supported on this
platform` in the current environment. This is recorded evidence, not an
instruction to upgrade packages blindly.

## Setup

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-Location ..
```

Verify Docker:

```powershell
docker info
docker run --rm hello-world
```

## Tests

Unit tests use mocks and do not require Docker:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\unit tests\test_health.py
```

Real integration tests are opt-in. They execute the dedicated multi-file
Python/Node project and controlled failure programs through `ExecutionManager`,
then remove their containers:

```powershell
$previousDockerGate = $env:ARES_RUN_DOCKER_TESTS
try {
    $env:ARES_RUN_DOCKER_TESTS = "1"
    backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py
} finally {
    if ($null -eq $previousDockerGate) {
        Remove-Item Env:ARES_RUN_DOCKER_TESTS -ErrorAction SilentlyContinue
    } else {
        $env:ARES_RUN_DOCKER_TESTS = $previousDockerGate
    }
}
```

The first run may pull the pinned images and therefore requires registry access.
The current verified run produced nine passing integration tests. These execute
the meaningful Python and Node.js fixtures through `ExecutionManager`, plus
nonzero-exit, runtime-error, timeout, workspace, output-limit, and cleanup
scenarios.

Run the manual real-execution demonstration:

```powershell
backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_execution_demo.py
```

Run the persistent multi-file demonstration:

```powershell
backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_multifile_demo.py
```

It registers `examples\workspaces\ares-multifile-demo`, reads its
`commands.txt`, executes both programs through ARES, and preserves the four
source files for inspection.

The original fixture demonstration remains available:

```powershell
backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_execution_demo.py
```

Run the full backend suite without Docker integration:

```powershell
backend\.venv\Scripts\python.exe -m pytest -q
```

Run the full backend suite with Docker integration and restore the gate:

```powershell
$previousDockerGate = $env:ARES_RUN_DOCKER_TESTS
try {
    $env:ARES_RUN_DOCKER_TESTS = "1"
    backend\.venv\Scripts\python.exe -m pytest -q
} finally {
    if ($null -eq $previousDockerGate) {
        Remove-Item Env:ARES_RUN_DOCKER_TESTS -ErrorAction SilentlyContinue
    } else {
        $env:ARES_RUN_DOCKER_TESTS = $previousDockerGate
    }
}
```

The positive integration tests use real Docker, not mocks. Unit tests use
mocks/temp directories and do not prove container execution.

## What the multi-file demo automates

The command below is an end-to-end demonstration, not just a local script
run. It prepares the example workspace, creates an `ExecutionManager`,
registers the workspace, reads the allowlisted commands, mounts the folder into
Docker at `/workspace`, executes both programs, collects structured results,
and prints stdout, stderr, exit codes, status, duration, truncation, and
cleanup information:

```powershell
backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_multifile_demo.py
```

It does not start Docker Desktop, install project dependencies, expose a
public API endpoint, or permit arbitrary shell commands. Docker Desktop must
already be running and the pinned images must be available locally or
downloadable.

## Exercising the manager

The manager is currently a Python API, not a public endpoint. From the
repository root:

```powershell
@'
from pathlib import Path
from backend.app.execution.config import ExecutionConfig
from backend.app.execution.contracts import ExecutionRequest
from backend.app.execution.manager import ExecutionManager

root = Path("examples/workspaces").resolve()
workspace = root / "python-example"
workspace.mkdir(parents=True, exist_ok=True)
manager = ExecutionManager(ExecutionConfig(workspace_root=root))
manager.register_workspace("python-example", workspace)
result = manager.execute(ExecutionRequest(
    workspace_id="python-example",
    command=["python", "--version"],
    runtime="python",
))
print(result.model_dump())
'@ | backend\.venv\Scripts\python.exe
```

The single-fixture output includes completed `2`, pending `1`, completion
`66.67%`, and intentional invalid-record handling. The Node fixture uses the same
calculation with Node.js standard-library assertions. Neither fixture uses
network access or third-party packages.

The multi-file demo uses four shared project files and reports total `4`,
completed `3`, pending `1`, and completion `75.00%` for both runtimes.

## Common failures

- Docker connection errors: start Docker Desktop and rerun `docker info`.
- Windows named-pipe errors such as `NpipeHTTPAdapter` missing or
  `Install pypiwin32 package to enable npipe:// support`: inspect
  `win32file`/`win32pipe` first:

  ```powershell
  .\backend\.venv\Scripts\python.exe -c "import win32file, win32pipe; print('Windows pipe modules: OK')"
  .\backend\.venv\Scripts\python.exe -c "import docker.api.client as c; print('NpipeHTTPAdapter available:', hasattr(c, 'NpipeHTTPAdapter'))"
  ```

  In the verified environment, reinstalling the already-required transitive
  `pywin32==312` wheel with
  the following command repaired the local virtual environment:

  ```powershell
  .\backend\.venv\Scripts\python.exe -m pip install --upgrade --force-reinstall --no-cache-dir --only-binary=:all: pywin32==312
  ```

  Do not add a separate application dependency or change Docker settings
  solely because of this local repair.
- Image preparation errors: verify registry access and the exact allowlisted
  image tag.
- Workspace errors: register a real directory below the configured root.
- Timeout: lower-risk commands should be split or given an appropriate bounded
  timeout; never remove timeout limits.
- `docker info` may report `DOCKER_INSECURE_NO_IPTABLES_RAW`; do not change
  Docker Desktop settings automatically. Treat it as a host-environment
  security warning requiring separate review.
- Containers use a shared host kernel. These controls reduce risk but are not
  an absolute security boundary.
- Frontend checks: run `Set-Location frontend; npm install; npm run build; npm run lint`.

Stop local servers with `Ctrl+C`. Containers created by the tests are removed
automatically; inspect `docker ps -a` only if a test is interrupted.
