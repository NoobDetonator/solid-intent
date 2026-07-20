# Initial validation - 2026-07-20

## Passed

- `uv 0.11.29` is installed and executable.
- uv downloaded and selected CPython `3.12.13`.
- `uv tool run --python 3.12 build123d-mcp@latest --version` returned
  `build123d-mcp 0.3.79`.
- `uv tool install --python 3.12 build123d-mcp==0.3.79` completed and installed
  `C:\Users\HRBASSIST55\.local\bin\build123d-mcp.exe`.
- MCP stdio initialization and `tools/list` succeeded.
- The server exposed 36 tools, including `execute`, `render_view`, `measure`,
  `validate`, `health_check`, and `export`.
- Direct build123d/OpenCASCADE smoke test passed:
  - cold `import build123d`: 42.813 s
  - `Box(10, 20, 30)`: 0.018 s
  - measured kernel volume: 6000.0 mm^3

## Needs client-level retest

- The aggregate MCP `health_check` timed out after 150 seconds in the default
  worker mode.
- A subsequent `execute` attempt reported that the worker had restarted and
  the following `measure` call found no live session.
- `--in-process`, the server's documented fallback for sandboxed Windows MCP
  hosts, kept the process alive but did not complete either the aggregate
  health check or a minimal `execute` containing only `Box(10, 20, 30)` after
  more than 150 seconds.
- Launching the persistent executable directly, with the default worker and
  built-in sandbox, still timed out on that minimal `execute` at both the
  default 120-second limit and an explicitly raised 300-second limit.
- No PNG, STEP, or STL smoke artifacts were produced during this initial
  harness run.

The safe Codex project config is registered at `.codex/config.toml` with the
built-in Python sandbox, default worker isolation, a 120-second startup
timeout, and a 300-second tool timeout. Restart Codex and run
`prompts/smoke-test.md` from the real client. If the same failure repeats,
prefer a Linux dev container/WSL test or an upstream issue report over
persisting weaker sandbox settings.

## Post-restart Codex client validation

The real Codex MCP client loaded the project configuration successfully after
restart. The earlier external-harness failure did not reproduce in normal MCP
use.

- Resources and all 36 CAD tools were discovered.
- Persistent `execute` calls completed normally.
- A two-piece Raspberry Pi 5 enclosure was built incrementally.
- Numeric measurement, fit comparison, validity gates, and printability checks
  completed.
- Base and lid both passed exact validity checks as single watertight manifold
  solids.
- STEP and STL exports completed.
- SVG rendering completed, including a multi-object exploded view.
- PNG/VTK rendering still exceeded the 75-second tessellation budget, even for
  a single part. SVG is the validated preview fallback on this host.

## Raspberry Pi 4 case session

A later 32.7 MB, 108-solid Raspberry Pi 4 reference STEP import destabilized
the isolated worker. Subsequent worker starts failed with the server's Windows
sandbox subprocess error and explicitly recommended `--in-process`.

- `.codex/config.toml` now enables `--in-process` for this project.
- This mode removes the server's worker crash containment and per-operation
  timeouts; the Codex host sandbox still limits file-system access.
- The configuration was loaded successfully after a Codex client restart.
- As a one-session contingency, the Raspberry Pi 4 script was regenerated and
  checked directly with the installed build123d kernel.
- Base, lid, and PCB proxy were valid single solids; fit intersections were
  zero; exported STEP files passed a clean round-trip import.
- MCP exact validity gates passed for the Pi 4 base and lid as watertight,
  manifold, single solids.
- Fit checks reported zero PCB/base intersection and a touching, zero-overlap
  lid/base relationship after correcting the cap seating geometry.
- Four SVG previews rendered successfully through the MCP 3D pipeline.
- Printability analysis found only informational bridges on the print-oriented
  lid. The base requires layers no thicker than 0.20 mm and reports one local
  0.20 mm microfeature for physical review.
- STEP and STL files were re-exported through MCP after the lid correction.
