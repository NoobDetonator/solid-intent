# SolidIntent

**From intent to validated parametric solids.**

<p align="center">
  <img src="docs/screenshots/solidintent_overview.png" alt="SolidIntent viewer showing the assembled Raspberry Pi 4 enclosure and its editable parameter inspector" width="100%">
</p>

<p align="center"><sub>Interactive project viewer backed by persistent parametric intent and MCP validation evidence.</sub></p>

SolidIntent is an AI-first, headless CAD workspace. The primary interface is a
conversation with an AI agent: the agent creates and edits parametric models,
while a transparent project format preserves parameters, references,
validation evidence, and revision history.

Geometry execution, rendering, measurement, validation, and export are handled
through `build123d-mcp`. Model scripts in `scripts/` contain only parametric
build123d geometry.

## Layout

- `scripts/` - canonical parametric regeneration sources
- `projects/` - persistent AI-editable project manifests and parameter state
- `specs/` - machine-readable design intent and acceptance targets
- `exports/` - generated STEP/STL/DXF/SVG files
- `renders/` - generated PNG/SVG review views
- `drawings/` - dimensioned SVG/DXF engineering drawings and MCP metadata
- `references/` - drawings, dimensions, and imported comparison geometry
- `docs/` - architecture decisions and technical studies
- `notes/` - test log and design decisions
- `prompts/` - reusable MCP-driven modeling and smoke-test prompts
- `environment/` - exact tool and package versions
- `smoke-output/` - artifacts from the initial environment validation
- `viewer/` - local React/Three.js project viewer and parameter editor

## Server command

The current upstream-recommended stdio launch command is:

```text
uv tool run --python 3.12 build123d-mcp@latest --in-process
```

Python 3.11-3.14 are supported; this workspace uses Python 3.12 as the
upstream conservative default. On this Windows Codex host, the isolated worker
became unable to spawn after a large reference STEP import. The project uses
the server-documented `--in-process` fallback and relies on the host-level
Codex sandbox. Restart the client after changing `.codex/config.toml`; see
`environment/validation.md` for the validation history and trade-off.

## Modeling loop

1. Call `version`, then `workflow_hints` at the start of a fresh client
   session. Run `health_check` once the basic `execute` smoke test succeeds.
2. Read `build123d://quickref` before writing model code.
3. Build incrementally with `execute`, assigning the final solid to `result`
   or registering named objects with `show()`.
4. Use `measure` after every important boolean; render only after the numeric
   checks pass.
5. Run `validate` immediately before export.
6. Export through the MCP `export` tool, never through custom file I/O.

See `prompts/smoke-test.md` for the first connected-client test.

## Reference policy

Use current official manufacturer CAD first, followed by exact physical
measurements, official reference drawings, third-party CAD, and finally photos.
Third-party assemblies are evidence, not automatic production truth. See
`references/README.md` and `AGENTS.md` for the complete workflow.

## Current projects

The Raspberry Pi 5 prototype case includes a parametric regeneration script,
machine-readable specification, STEP/STL exports, SVG previews, fit checks,
validity gates, and printability results. Connector openings remain prototype
geometry until checked against the current official Pi 5 STEP and a physical
board.

The Raspberry Pi 4 Model B case is a new board-specific design based on the
local dimensional drawing and detailed reference package. It includes separate
connector openings, microSD access, an external cap lid, GPIO access, and a
30 mm fan pattern. MCP SVG rendering, exact validity gates, fit checks, STEP/STL
exports, and printability analysis pass. The base printability report recommends
a maximum 0.20 mm layer height and flags one local 0.20 mm microfeature for
physical review.

The Pi 4 project also includes a combined A3 dimensioned drawing with plan,
front, side, and isometric views; ISO 7200 title block; SVG/DXF output; and an
MCP annotation sidecar for later machine inspection.

## Persistent AI CAD project pilot

`projects/raspberry_pi4_case/` is the first persistent project-format pilot.
Its manifest points to a `build_model(parameters)` entry point, schema-validates
42 parameters, exposes 26 user-editable controls, locks 16 reference-controlled
values, tracks accepted source hashes, and stores machine-readable validation
and revision records.

The workspace data layer can inspect the project, emit a UI-ready parameter
catalog, and atomically persist approved manual parameter edits. It never builds
or measures CAD; changed projects are rebuilt and accepted through the existing
build123d-mcp gates. See `docs/ai_cad_project_format.md` for the lifecycle and
future web-viewer boundary.

## Web viewer

The first SolidIntent viewer is implemented in `viewer/`. It opens the
persistent project manifest, loads generated STL bodies into an interactive 3D
canvas, presents editable and reference-controlled parameters separately, and
surfaces validation, provenance, revision, and dirty-state evidence.

```text
cd viewer
npm install
npm run dev
```

Open `http://127.0.0.1:4173`. Saving an allowed parameter updates
`parameters.json` atomically and marks the project as requiring an AI/MCP
rebuild. The viewer never regenerates, measures, validates, or exports geometry
itself.

### Viewer gallery

<table>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/solidintent_exploded.png" alt="Exploded enclosure view with schema-driven parameter controls">
    </td>
    <td width="50%">
      <img src="docs/screenshots/solidintent_validation.png" alt="Assembled enclosure view with exact geometry validation evidence">
    </td>
  </tr>
  <tr>
    <td align="center"><sub>Exploded body inspection and schema-driven parameters</sub></td>
    <td align="center"><sub>Accepted geometric evidence from build123d-mcp</sub></td>
  </tr>
</table>

## Credits and provenance

SolidIntent builds on the open-source
[`build123d-mcp`](https://github.com/pzfreo/build123d-mcp) project by
[`pzfreo`](https://github.com/pzfreo), distributed under the Apache License
2.0. The MCP server is installed as an external dependency; its source code is
not vendored in this repository.

The Raspberry Pi 4 pilot used Hasanain Shuja's
[`Raspberry Pi 4 Model B`](https://grabcad.com/library/raspberry-pi-4-model-b-1)
GrabCAD model as third-party dimensional and collision-reference evidence. The
downloaded package did not contain a licence file, so its native CAD files and
images are intentionally excluded from this repository. The enclosure itself
is a new parametric design and still requires physical connector verification.

See `THIRD_PARTY_NOTICES.md` and `references/README.md` for the complete
attribution and redistribution policy.
