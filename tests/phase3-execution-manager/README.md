# Phase 3 Tests

This folder contains the tests, fixtures, and manual demonstrations for the
Phase 3 Docker sandbox and Execution Manager.

## Structure

- `unit/`: mocked and local tests for contracts, workspace handling, runtime
  policy, Docker adapter behavior, the manager, and the restricted project
  runner.
- `integration/`: opt-in tests that use the real Docker SDK and Docker Engine.
- `fixtures/`: deterministic Python and Node.js programs copied into temporary
  registered workspaces.
- `manual/`: visible end-to-end demonstrations.

Run the unit tests with:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\unit
```

Run the real Docker integration tests with:

```powershell
$previousDockerGate = $env:ARES_RUN_DOCKER_TESTS
try {
    $env:ARES_RUN_DOCKER_TESTS = "1"
    .\backend\.venv\Scripts\python.exe -m pytest -q tests\phase3-execution-manager\integration
} finally {
    if ($null -eq $previousDockerGate) {
        Remove-Item Env:ARES_RUN_DOCKER_TESTS -ErrorAction SilentlyContinue
    } else {
        $env:ARES_RUN_DOCKER_TESTS = $previousDockerGate
    }
}
```

Run the folder-sending demonstration with:

```powershell
.\backend\.venv\Scripts\python.exe tests\phase3-execution-manager\manual\phase3_multifile_demo.py
```
