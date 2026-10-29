# ARES Phase 3 Decisions

## Workspace mounting

Use an explicitly registered local workspace mounted at `/workspace` rather
than cloning or copying arbitrary repositories. A read-write mount preserves
approved edits for later recovery attempts while the registration root prevents
unbounded host access. Copy-on-write snapshots and persistent registrations are
future work.

## Runtime image policy

Only pinned Python and Node image tags configured in `ExecutionConfig` are
accepted. The request may repeat the configured image but cannot replace it
with an arbitrary image. This makes runtime selection auditable and avoids
silently using `latest`.

## Dependency preparation

Dependency installation is deferred. The current phase executes validated
commands only; it does not guess package managers, run lifecycle scripts, or
handle credentials. A future implementation should use lockfiles, a separate
network-enabled preparation container, bounded logs, and an explicit network
policy before code execution.

## Network and resource limits

Project containers have networking disabled, a 512 MiB memory limit, one CPU,
and a 256-process limit by default. A 120-second request timeout and 256 KiB
per-stream output limit prevent unbounded work. Image preparation is a separate
explicit operation and may require registry access.

## Container lifecycle

Containers are created through the Docker SDK, started, waited on, logged, and
removed in a cleanup path. Timeouts stop the container before removal. Cleanup
failure is returned as a distinct status instead of being silently ignored.
The installed Docker SDK can wrap named-pipe wait timeouts in a requests
`ConnectionError`; the adapter recognizes the wrapped timeout while preserving
other transport failures as errors.

## Output handling

The result contract caps each returned output stream independently at 256 KiB
by default, with a maximum request limit of 10 MiB. This is a result-size
policy applied after log retrieval, not a hard memory bound. Streaming log
collection is deferred.

## Restricted project runner

The multi-file workflow uses a small reusable `ProjectRunner`, not shell
evaluation. `commands.txt` is an allowlist input for exactly `python main.py`
and `node app.js`; it is converted to argument lists and dispatched through
the existing manager. This provides a realistic project workflow without
introducing arbitrary command execution or a second Docker orchestration layer.

## Environment repairs

The application depends on Docker SDK 7.1.0, whose Windows transport uses
`pywin32`. The verified developer environment required a local force-reinstall
of its existing `pywin32==312` wheel before named-pipe imports worked. This is
an environment repair, not a new direct cross-platform dependency decision.
The same environment reports a `pip check` warning for
`charset-normalizer 3.5.2`; no package change was made because ARES tests and
Docker execution passed.

## Deliberately deferred

Persistence, copy-on-write workspaces, dependency caches, secret injection,
public HTTP execution endpoints, recovery policies, agent integration,
Kubernetes, and production hardening are outside Phase 3.
