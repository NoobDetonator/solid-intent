# SolidIntent viewer

The SolidIntent viewer is a local web interface for persistent AI CAD projects.
It is deliberately not a browser CAD kernel: Three.js displays generated STL
artifacts, while build123d-mcp remains the authority for geometry creation,
measurement, validation, printability analysis, and export.

## Run locally

Requirements:

- Node.js 20 or newer
- A SolidIntent project under `../projects/`
- Generated STL artifacts at the paths declared by the project manifest

```text
npm install
npm run dev
```

Open `http://127.0.0.1:4173`.

Production build and local serving:

```text
npm run build
npm start
```

The server binds to `127.0.0.1` by default. Set `PORT` to change the local
port.

## Current capabilities

- Discover local `project.json` manifests.
- Load base and lid STL artifacts in an interactive Three.js canvas.
- Toggle bodies, exploded placement, transparency, and camera fit.
- Inspect SVG technical previews and the dimensioned drawing sheet.
- Group and search the schema-defined parameter catalog.
- Separate editable parameters from reference-controlled values.
- Enforce locked status and numeric ranges in the local API.
- Atomically persist approved parameter changes.
- Derive clean/dirty state from accepted SHA-256 source hashes.
- Display validation metrics, residual physical risks, references, and revision
  history.
- Copy a precise rebuild request for the AI agent after parameters change.

## Authority boundary

The viewer may edit declared intent in `parameters.json`. It must not calculate
engineering measurements, claim geometric validity, or accept a revision.
After any saved change, an AI agent rebuilds through build123d-mcp, compares the
candidate with the accepted revision, validates every exported solid, and then
records a new revision.
