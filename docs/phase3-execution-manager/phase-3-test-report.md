# ARES Phase 3 Test Report

## Environment

- Date: 2026-10-29
- Branch: `feature/phase-3-execution-manager`
- OS: Windows
- Python: 3.13.13 from `backend\.venv`
- Docker context: `desktop-linux`
- Docker Engine: `28.3.2`
- Docker SDK: `7.1.0`
- Docker was available and used for the integration run.

## Completed validation

| Check | Command | Result |
|---|---|---|
| Focused contracts and health | `backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\unit\test_execution_contracts.py tests\test_health.py` | 9 passed, 0 failed |
| Focused adapter, manager, contracts, health | `backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\unit tests\test_health.py` | 18 passed, 0 failed |
| Targeted adapter/manager/contracts suite after hardening | `backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\unit\test_docker_adapter.py tests\phase3-execution-manager\unit\test_execution_manager.py tests\phase3-execution-manager\unit\test_execution_contracts.py` | 12 passed, 1 skipped, 0 failed |
| Real Docker runtimes and manager (initial baseline) | `$env:ARES_RUN_DOCKER_TESTS="1"; backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py` | 3 passed, 0 failed |
| Expanded real Docker suite after hardening | `$env:ARES_RUN_DOCKER_TESTS="1"; backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py` | 7 passed, 0 failed |
| Real fixture and manager integration suite | `$env:ARES_RUN_DOCKER_TESTS="1"; backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py` | 8 passed, 0 failed |
| Multi-file project integration suite | `$env:ARES_RUN_DOCKER_TESTS="1"; backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration\test_docker_execution.py` | 9 passed, 0 failed |
| Full backend suite (final) | `backend\.venv\Scripts\python.exe -m pytest -q` | 40 passed, 10 skipped, 0 failed |
| Full backend suite with Docker (final) | `$env:ARES_RUN_DOCKER_TESTS="1"; backend\.venv\Scripts\python.exe -m pytest -q` | 49 passed, 1 skipped, 0 failed |
| Frontend production build | `Set-Location frontend; npm run build` | Passed |
| Frontend lint | `Set-Location frontend; npm run lint` | Passed |
| Diff whitespace check | `git diff --check` | Passed |

The first real Docker attempt was blocked by the uncached Python image. After
the explicit image-preparation step pulled the pinned image, Python, Node.js,
and the registered-workspace manager tests passed. During this validation, a
live timeout probe reproduced a Docker SDK 7.1.0 Windows named-pipe
`requests.exceptions.ConnectionError` wrapping a timeout; the adapter was
hardened and the multi-file real-Docker suite then passed.

## Test provenance

The fixture integration tests execute the Python and Node.js programs through
`ExecutionManager`, using registered temporary workspaces and the real Docker
adapter. The exact expected stdout includes task calculations, percentage
formatting, and intentional invalid-record handling. A separate manual demo also executed both programs through the same manager
path. The multi-file manual demo printed `Python result: PASS`, `Node result:
PASS`, `Overall success: True`, and `ARES MULTI-FILE DEMO PASSED`.

The multi-file integration test additionally reads `commands.txt` through
`ProjectRunner`, verifies both programs consume the shared `tasks.json`, and
confirms the allowlisted command workflow succeeds.

The current non-Docker tests use mocked Docker objects or temporary
directories and do not prove daemon execution. One Windows symlink test is
skipped because directory symlink creation is unavailable in this environment.
The current 9 integration tests use the real Docker SDK and Docker Engine, run
the meaningful fixtures and controlled failure programs, and verify cleanup,
workspace persistence, timeout behavior, nonzero exits, runtime stderr, and
output limits.

Two pre-existing Starlette/httpx deprecation warnings are emitted by the health
test environment. They do not fail the suite. The final default backend run
skips the eight opt-in Docker tests plus the unavailable Windows symlink case.
The final Docker-enabled run passed all 49 runnable tests.

## Achieved behavior

The validated folder workflow now demonstrates that ARES can:

1. Use a host project folder under the approved workspace root.
2. Register that folder with the workspace manager.
3. Mount the registered folder into a temporary Docker container at
   `/workspace`.
4. Execute multiple files that share `tasks.json`.
5. Return structured results for each command.
6. Continue after a normal program failure while stopping for infrastructure
   failures, timeouts, validation failures, image failures, or cleanup
   failures.
7. Remove temporary containers after execution.

The implementation is complete for the current Phase 3 scope. Persistent
workspace lifecycle management, dependency installation, streaming log
collection, public execution endpoints, recovery, orchestration, and stronger
production isolation remain future work.

## Unverified or limited cases

Dependency installation, daemon-unavailable behavior against a live unavailable
daemon, image registry failure, and Windows-specific Docker security behavior
are covered by code paths or mocks but not all by live tests. The Docker host
warning `DOCKER_INSECURE_NO_IPTABLES_RAW`, if emitted, is an environment issue
and is not changed by ARES.

`pip check` currently reports `charset-normalizer 3.5.2 is not supported on
this platform`; no dependency change was made because the tested execution
paths passed.
