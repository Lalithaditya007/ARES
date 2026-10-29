# Phase 3: Execution Manager

This folder contains the complete Phase 3 documentation for the ARES Docker
sandbox and execution-manager implementation.

## What Phase 3 delivers

- Typed execution requests and structured results.
- Explicit registration of local workspaces below an approved root.
- Pinned, allowlisted Python and Node.js Docker runtimes.
- Docker execution with disabled networking, non-root containers, dropped
  capabilities, resource limits, timeouts, output limits, and cleanup.
- A restricted multi-file project runner that reads `commands.txt` and
  dispatches only `python main.py` and `node app.js`.
- Unit tests, real Docker integration tests, and reproducible manual demos.

## Documentation map

- [Implementation guide](./phase-3-implementation.md): architecture,
  lifecycle, contracts, workflow, security controls, and limitations.
- [Runbook](./phase-3-runbook.md): setup, PowerShell commands, tests,
  troubleshooting, and manual execution.
- [Test report](./phase-3-test-report.md): environment, evidence, observed
  results, warnings, and unverified cases.
- [Decisions](./phase-3-decisions.md): design choices and intentionally
  deferred functionality.
- [Project changelog](../PROJECT_CHANGELOG.md): chronological project history
  including the Phase 3 work.

## Quickest end-to-end test

From `D:\major\Implementation`, with Docker Desktop running:

```powershell
.\backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_multifile_demo.py
```

The demo registers the example folder, mounts it at `/workspace`, executes the
Python and Node.js programs through `ExecutionManager`, collects their results,
and reports whether the complete workflow succeeded.
