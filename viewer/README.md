# SolidIntent viewer

Local web inspector for persistent AI CAD projects. Three.js shows generated
STL artifacts; `build123d-mcp` remains the authority for geometry, measure,
validate, and export.

## Run

Requires Node.js 20+, projects under `../projects/`, and STL files at the paths
in each `project.json` artifacts map.

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173) (binds `127.0.0.1`; set
`PORT` to change).

```bash
npm run build
npm start
```

## Capabilities

- Discover `project.json` manifests and load body STLs
- Toggle bodies, exploded placement, transparency, camera fit
- Inspect SVG previews and dimensioned drawings
- Edit schema-approved parameters; lock reference-controlled values
- Persist parameters atomically; show clean/dirty from SHA-256 hashes
- Surface validation metrics, residual risks, references, revisions
- Copy a rebuild prompt or run **Rebuild & accept** via the local API

## Authority boundary

The viewer edits declared intent in `parameters.json`. It does not invent
engineering measurements or silently accept revisions. After a save, rebuild
through `build123d-mcp` (or `scripts/rebuild_project.py`), compare with the
accepted revision, validate exports, then record a new revision.
