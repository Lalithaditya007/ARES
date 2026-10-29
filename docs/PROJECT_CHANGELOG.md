# ARES Project Changelog

## Project and phase overview

ARES is a research-oriented execution-management platform. Phase 3 provides
the local Docker execution foundation only. Future agents must call the
Execution Manager rather than controlling Docker directly.

## Baseline before Phase 3

Before Phase 3, the repository contained a FastAPI health endpoint, a React/Vite
skeleton, a pytest health test, setup documentation, and Docker availability
checks. There was no execution contract, workspace registry, Docker SDK
adapter, or execution manager.

## Files added

- `backend/app/execution/contracts.py`, `config.py`, `workspace.py`,
  `runtime_policy.py`, `docker_adapter.py`, `manager.py`, `project_runner.py`,
  and `__init__.py`
- `tests/phase3-execution-manager/unit/`: execution contracts, Docker adapter,
  manager, and project-runner tests
- `tests/phase3-execution-manager/integration/test_docker_execution.py`
- `tests/phase3-execution-manager/fixtures/execution/`: deterministic Python
  and Node.js programs
- `tests/phase3-execution-manager/manual/phase3_execution_demo.py`
- `tests/phase3-execution-manager/manual/phase3_multifile_demo.py`
- `docs/phase3-execution-manager/README.md`,
  `phase3-execution-manager/phase-3-implementation.md`,
  `phase3-execution-manager/phase-3-runbook.md`,
  `phase3-execution-manager/phase-3-test-report.md`, and
  `phase3-execution-manager/phase-3-decisions.md`
- `docs/ARES_MASTER_HANDOVER.md`: authoritative technical handover and file
  inventory

## Files modified

- `backend/requirements.txt`: added `docker==7.1.0`
- `README.md`: linked and described the current Phase 3 capability
- `README.md`: linked the master handover as the primary documentation entry

## Significant modules

`ExecutionRequest`/`ExecutionResult` define typed inputs and outcomes.
`WorkspaceManager` registers only existing directories under an approved root.
`RuntimePolicy` selects the configured Python or Node image.
`DockerAdapter` owns Docker SDK calls, resource controls, timeout handling,
bounded returned output, and cleanup. `ExecutionManager` owns the caller-facing
orchestration flow.

## Architecture and execution flow

`Agent (future) -> ExecutionManager -> DockerAdapter -> Docker SDK -> Docker
Engine -> temporary container -> structured result`.

The current manager is a Python API and is intentionally not exposed as a
public network endpoint.

## Safety and resource-control decisions

Execution mounts only a registered workspace at `/workspace`, read-write.
Containers are non-root (`1000:1000`), network-disabled, capability-dropped,
protected by `no-new-privileges`, and limited to 512 MiB, one CPU, and 256
processes by default. No privileged mode, host devices, Docker socket, host
namespace, or broad host mount is configured. Docker remains a shared-kernel
boundary, not an absolute security boundary.

## Environment and dependency fixes

The verified environment is Windows with Python 3.13.13, Docker Desktop using
the `desktop-linux` context, Docker Engine 28.3.2, and Docker SDK 7.1.0.
Docker SDK Windows named-pipe imports required a local force-reinstall of the
existing `pywin32==312` wheel. No direct pywin32 requirement was added.
`pip check` still reports `charset-normalizer 3.5.2 is not supported on this
platform`; no blind package change was made because execution passed.
Docker also reports `DOCKER_INSECURE_NO_IPTABLES_RAW`; host settings were not
changed.

## Verified test commands and results

On 2026-10-29, from `D:\major\Implementation`:

| Command | Result |
|---|---|
| `.\backend\.venv\Scripts\python.exe -m pytest -q` | 40 passed, 10 skipped, 2 warnings |
| `$env:ARES_RUN_DOCKER_TESTS="1"; .\backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py` | 9 passed |
| `$env:ARES_RUN_DOCKER_TESTS="1"; .\backend\.venv\Scripts\python.exe -m pytest -q` | 49 passed, 1 skipped, 2 warnings |
| Focused adapter/manager/contracts suite | 12 passed, 1 skipped |
| `Set-Location frontend; npm run build` | Passed |
| `Set-Location frontend; npm run lint` | Passed |

The nine integration tests use the real Docker daemon and verify meaningful
Python and Node execution through the manager, exact output, runtime errors,
nonzero exits, timeout cleanup, workspace read/write persistence, and output
truncation. Unit tests use mocks and temporary directories.

## Known warnings and limitations

- Two existing Starlette/httpx-related deprecation warnings remain.
- Output truncation occurs after log retrieval and is not a streaming memory
  limit.
- Workspace registration is process-local and does not provide race-free
  filesystem isolation against every possible symlink/filesystem race.
- Dependency installation, persistent execution history, public APIs, recovery,
  Kubernetes, and production hardening are deferred.

## Outstanding issues

- Decide whether to add bounded streaming log collection.
- Define a persistent workspace lifecycle and cleanup policy.
- Evaluate stronger isolation if the threat model exceeds Docker's shared
  kernel.
- Resolve or explicitly accept the local `pip check` charset warning.

## Planned work by future phase

- **Proposed Phase 4:** LangGraph orchestration and planning/coding agents,
  routed through the Execution Manager.
- **Proposed Phase 5:** testing, failure analysis, bounded recovery, and
  verification workflows.
- **Proposed Phase 6:** PostgreSQL execution history and AEKE retrieval.
- **Proposed Phase 7:** dashboard, observability, authentication, and metrics.
- **Later hardening:** quotas, concurrency, audit logging, stronger isolation,
  and production deployment controls.

These are proposed roadmap groupings, not implemented functionality.

## Developer onboarding and troubleshooting

Use `backend\.venv\Scripts\python.exe`, run `docker info`, and enable
`ARES_RUN_DOCKER_TESTS=1` only for real integration tests. See
`docs/phase3-execution-manager/phase-3-runbook.md` for named-pipe diagnostics, image-pull failures,
workspace errors, timeout behavior, and safe cleanup.

## Chronological change log

### Phase 3 implementation

- Added typed execution contracts and structured status/error mapping.
- Added registered workspace and allowlisted runtime policy.
- Added Docker SDK adapter and `docker==7.1.0`.
- Added resource controls, disabled networking, output limits, timeout
  handling, cleanup, and test coverage.
- Added Python/Node real-Docker integration tests.
- Added deterministic Python and Node.js task-summary fixtures and the
  manager-based `tests/phase3-execution-manager/manual/phase3_execution_demo.py`.
- Added the registered multi-file host project under
  `examples/workspaces/ares-multifile-demo/` and the restricted
  `ProjectRunner` for exact `commands.txt` allowlisting.
- Verified the multi-file project through nine real-Docker integration tests
  and the persistent manual demonstration.
- Reproduced exact fixture output through Docker; Python and Node both returned
  status `succeeded` and exit code `0`.
- Hardened Windows Docker SDK timeout handling after reproducing the wrapped
  named-pipe `ConnectionError` behavior.
- Updated implementation, runbook, decisions, test report, and README
  documentation with verified evidence and limitations.
- Added the master technical handover with current verification results,
  architecture, complete Phase 3 inventory, troubleshooting, deferred scope,
  and release instructions.
