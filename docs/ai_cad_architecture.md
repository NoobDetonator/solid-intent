# AI CAD Workbench Architecture

## Product position

This workspace is an AI-operated mechanical prototyping workbench. It is not a
general replacement for a mature interactive CAD system. Its strongest use
cases are enclosures, brackets, adapters, fixtures, flanges, turned parts,
small assemblies, and repeatable parametric edits.

## Core architecture

```text
Request / drawing / reference CAD
              |
              v
Structured design intent and assumptions
              |
              v
build123d-mcp persistent CAD session
              |
              v
Measure -> Compare -> Validate -> Printability
              |
              v
Human review and physical verification
              |
              v
Regeneration source + STEP + STL + report
```

## Responsibilities

### build123d-mcp

- Execute parametric build123d code.
- Maintain geometric session state and snapshots.
- Measure exact BREP geometry.
- Detect common mechanical features.
- Render engineering previews.
- Check fit, alignment, interference, and printability.
- Validate and export CAD artifacts.

### Workspace layer

- Preserve reference provenance.
- Store declared design intent separately from generated geometry.
- Track assumptions and unresolved dimensions.
- Keep regeneration scripts reviewable and versionable.
- Define acceptance gates and regression targets.
- Present generated artifacts to the user.

### Human review

- Resolve ambiguous design intent.
- Confirm manufacturing method and tolerances.
- Verify interfaces against exact physical hardware.
- Approve safety-critical or production use.

## Recommended operating environment

Prefer a pinned Linux container or WSL environment for repeatable automation.
The current Windows host successfully executes and exports CAD through the real
Codex MCP client, but PNG/VTK rendering exceeded its time budget. SVG is the
current reliable preview fallback.

## Model lifecycle

1. Inventory reference files without modifying them.
2. Extract a written and machine-readable specification.
3. Create a lightweight interface/keep-out model when the reference CAD is
   too detailed for repeated analysis.
4. Build the manufactured part incrementally.
5. Check every important boolean numerically.
6. Compare against the interface model.
7. Validate and analyze the print orientation.
8. Export and record residual warnings.

## Near-term roadmap

1. Complete a 15-20 part evaluation set.
2. Pin and containerize the working environment.
3. Add reusable spec and acceptance-report generation.
4. Add lightweight reference proxies for common electronics boards.
5. Add geometric regression tests between revisions.
6. Add a fast artifact viewer without replacing the MCP measurement pipeline.

