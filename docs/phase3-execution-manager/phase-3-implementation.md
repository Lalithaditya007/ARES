# ARES Phase 3 Implementation

## Scope

Phase 3 adds the foundational local Docker execution infrastructure. It does not
implement planning, coding, testing, debugging, recovery, AEKE, LangGraph,
PostgreSQL, the dashboard, or production deployment.

## Architecture

Callers create an `ExecutionRequest` and pass it to `ExecutionManager`. The
manager validates the registered workspace and approved runtime image, asks the
Docker SDK adapter to prepare the image, and executes the argument-list command.
The adapter returns an `ExecutionResult`; callers do not need Docker-specific
objects.

The implementation lives in `backend/app/execution/`:

- `contracts.py`: Pydantic request/result models, statuses, error categories,
  and bounded UTF-8 output.
- `config.py`: workspace root, approved images, and resource limits.
- `workspace.py`: explicit workspace registration and resolved-path containment.
- `runtime_policy.py`: Python and Node image allowlist enforcement.
- `docker_adapter.py`: Docker SDK lifecycle, sandbox settings, logs, timeout,
  and cleanup.
- `manager.py`: stable orchestration boundary for future ARES agents.
- `project_runner.py`: restricted `commands.txt` parser and sequential
  dispatcher for the dedicated multi-file demo workflow.
- `tests/phase3-execution-manager/fixtures/execution/`: deterministic
  standard-library Python and
  Node.js programs used by real Docker tests.
- `tests/phase3-execution-manager/manual/phase3_execution_demo.py`: reproducible
  manager-based terminal demonstration.

## Contracts and lifecycle

Requests contain a registered `workspace_id`, argument-list `command`, explicit
runtime family, optional approved image, timeout, and output limit. Extra fields
are rejected, so callers cannot submit mounts, host paths, privileged mode,
devices, or arbitrary environment variables.

The lifecycle is:

1. Resolve a previously registered workspace.
2. Select the configured image for Python or Node.js.
3. Ping Docker and explicitly prepare the approved image (a missing image is
   pulled only during an explicit execution).
4. Create a temporary container with only the workspace mounted at
   `/workspace`.
5. Run as UID/GID `1000:1000`, with networking disabled, all Linux capabilities
   dropped, `no-new-privileges`, memory/CPU/PID limits, and a timeout.
6. Collect stdout and stderr, then apply a 256 KiB-per-stream default cap
   (maximum 10 MiB) plus an explicit truncation flag.
7. Stop timed-out containers and remove the container in a `finally` path.

Successful commands, nonzero commands, timeouts, validation/workspace failures,
image preparation failures, container failures, and cleanup failures have
separate statuses. A command failure is not treated as a Docker failure.

The Docker SDK timeout is a transport read timeout on the installed Windows
named-pipe path. Docker SDK 7.1.0 can surface it as a
`requests.exceptions.ConnectionError` wrapping a timeout, so the adapter
recognizes both direct and wrapped timeout forms, stops the container, and
continues cleanup. Other transport failures remain container/connection
failures.

## Workspace lifecycle

The application does not clone repositories or accept arbitrary host paths in a
request. A trusted local caller explicitly registers a directory beneath the
configured workspace root. Registration resolves the path and uses
`os.path.commonpath` to reject traversal and symlink escapes. The registered
directory is mounted read-write so later recovery edits can persist.

The current registry is process-local. A future phase can persist registrations
and add copy-on-write workspace creation.

The real integration tests copy the fixtures into temporary registered
workspaces before calling `ExecutionManager.execute()`. The manager, rather
than the tests, selects and prepares the configured runtime image.

## Multi-file project workflow

`examples/workspaces/ares-multifile-demo/` is a dedicated host project
containing `main.py`, `app.js`, the shared `tasks.json`, and `commands.txt`.
Both programs independently read the same JSON file, validate task records,
calculate totals, and handle an intentional invalid-record case.

`ProjectRunner` reads `commands.txt` only from the registered workspace. Its
grammar accepts blank lines, full-line comments, and exactly:

```text
python main.py
node app.js
```

It rejects extra arguments, absolute or traversal paths, shell operators,
redirection, command chaining, shell launchers, and all unknown commands. It
converts accepted lines to argument lists and executes them sequentially
through `ExecutionManager`; a nonzero program result is recorded and execution
continues, while timeout, validation, image, Docker, or cleanup failures stop
the workflow. Overall success requires every recognized command to succeed.

## Runtime and dependencies

The initial approved images are:

- `python:3.10.19-slim-bookworm`
- `node:22.14.0-bookworm-slim`

The image must be the configured image for the selected runtime. The host does
not need Python or Node.js to execute project commands. Runtime detection and
dependency installation from project manifests are intentionally not automatic
yet; callers must provide a validated command. This avoids silently executing
untrusted installation scripts or guessing an ambiguous project runtime.

## Security limitations

The implementation does not use privileged mode, host devices, the Docker
socket, host namespaces, or broad host mounts. Networking is disabled for project execution by default. Output truncation
limits the returned strings after Docker log retrieval; it is not a streaming
memory bound, so a future implementation should add bounded log streaming if
untrusted output volume becomes a concern.
Docker Desktop and the shared host kernel remain part of the trust boundary;
these controls reduce risk but are not a perfect security boundary. The
`DOCKER_INSECURE_NO_IPTABLES_RAW` host warning, if present, must be reviewed
outside this application and is not changed automatically.

## Known limitations

- The process-local workspace registry is not persistent.
- Dependency installation, caching, credentials, and lockfile workflows are
  deferred.
- Only the configured Python and Node image versions are supported.
- Docker integration tests require Docker Desktop and network access when an
  image is not cached.
- The selected image must support UID/GID `1000:1000`; this is verified for the
  configured Python and Node images by the integration suite.
- Windows Docker named-pipe support depends on a working `pywin32` installation.
- The backend does not expose the execution manager as a public HTTP endpoint.
