# AI CAD Workspace Instructions

## Language

- Write source code, filenames, specifications, reports, comments, and project
  documentation in English.
- User-facing conversation may be in Brazilian Portuguese.

## CAD execution policy

- Use `build123d-mcp` for geometry creation, modification, measurement,
  rendering, comparison, validation, printability analysis, and export.
- Do not implement custom renderers or measurement pipelines when an MCP tool
  already provides the capability.
- Read `build123d://quickref` before writing unfamiliar build123d operations.
- Build incrementally. After every boolean, use `measure` and confirm that
  volume or topology changed as intended.
- Use stable object names with `show()` and preserve canonical objects by
  copying them before presentation-only transformations.
- Run `validate` before every final export.
- For FDM parts, analyze the intended print orientation before delivering STL.

## Reference precedence

Use mechanical evidence in this order:

1. Current official manufacturer CAD or production drawing.
2. Measurements from the exact physical hardware revision.
3. Current official approximate/reference drawings.
4. Trusted third-party CAD assemblies.
5. Product photos and rendered images.

Never silently transfer connector positions or component heights between board
generations. Record assumptions and unresolved dimensions in the project spec.

## Artifact conventions

- Parametric regeneration sources: `scripts/`
- Machine-readable design intent: `projects/<id>/` (parameters, schema, validation)
- Generated neutral CAD and meshes: `exports/`
- Generated previews: `renders/` (committed SVG technical views)
- Dimensioned drawings: `drawings/` (SVG + DXF + `.dims.json`)
- README review copies: `docs/showcase/` (synced by `export_artifacts.py`)
- External source material: `references/`
- Architecture and studies: `docs/`
- Test notes: `notes/`
- Persistent AI-editable projects: `projects/`

Use lowercase snake_case for generated artifact filenames. Preserve original
filenames inside imported reference packages.

## AI CAD project lifecycle

- Open `projects/<id>/project.json` before editing a persistent project.
- Treat `parameters.json` and the model entry point as the editable source of
  truth; STEP/STL/SVG/DXF are derived artifacts.
- Validate parameters against `parameter_schema.json` before rebuilding.
- Do not edit a parameter marked `x-user-editable: false` without explicit
  semantic design review and evidence from its controlling reference.
- A parameter or source edit makes the project dirty. Rebuild, compare with the
  accepted revision, and run all applicable gates before accepting it.
- Preserve stable body and interface names declared by the manifest.
- Do not advance the manifest revision or validation hashes until all required
  gates pass. Record rejected probes without promoting their parameter values.

## Definition of done

A delivered model must include:

1. Named parameters with millimetre units.
2. A clean regeneration script.
3. Numeric envelope and topology checks.
4. Fit/interference checks for relevant interfaces.
5. `validate` PASS for every exported solid.
6. STEP for interchange and STL for printable parts.
7. At least one preview, with SVG accepted when PNG rendering is unavailable.
8. Assumptions, reference provenance, and physical-verification needs.

## Cursor Cloud specific instructions

Two runnable components. See `README.md` (Quick start) and `viewer/README.md`
for the canonical commands; notes below cover only non-obvious caveats.

### Web viewer (primary app)

- Run it with `npm run dev` from `viewer/` (dependencies live in `viewer/`, not
 the repo root). It serves at `http://127.0.0.1:4173`, binding `127.0.0.1`
 only; set `PORT` to change the port.
- `npm run dev` is a custom Express server (`viewer/server/index.ts` via `tsx`)
 that mounts Vite in middleware mode and exposes the `/api/...` project
 endpoints. It is not a plain `vite dev` server.
- There is no separate lint script. The closest gate is `npm run build`, which
 runs `tsc --noEmit` for both tsconfigs and then `vite build`.

### Generated CAD artifacts

- `exports/` (STEP/STL) and `smoke-output/` are gitignored and ship empty.
- `renders/*.svg` technical previews are generated and committed; regenerate
  with `scripts/export_artifacts.py`.
- `drawings/` holds the dimensioned A3 sheet (SVG/DXF/`.dims.json`).
- `docs/showcase/` stores README copies synced by the export script.
- The viewer 3D canvas needs STL files under `exports/`; SVG sheets appear in
  the Drawings evidence panel once present.
- Local bootstrap:
  `uv run --python 3.12 --with build123d --with build123d-drafting-helpers python scripts/export_artifacts.py --all`

### build123d-mcp CAD server (Python)

- Installed and run via `uv` (already on `PATH` at `~/.local/bin`):
 `uv tool run --python 3.12 build123d-mcp@latest`. It is an external MCP CAD
 server, not vendored here.
- The first `import build123d` in a fresh process is slow (~40s cold) because
 of the OpenCASCADE kernel; subsequent operations are fast.
- The data layer CLI `scripts/ai_cad_project.py` (`inspect`/`parameters`/`set`)
 needs `jsonschema`; run it inside the build123d env, e.g.
 `uv run --python 3.12 --with build123d python scripts/ai_cad_project.py ...`.
