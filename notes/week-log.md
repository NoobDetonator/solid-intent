# Hands-on CAD test log

## Day 1 - environment and primitives

- Goal: Validate the full MCP loop with a Raspberry Pi 5 prototype enclosure.
- Model: Two-piece ventilated case with PCB standoffs and friction-fit lid.
- Numeric checks: Base 92.2 x 63.2 x 22 mm; lid 92.2 x 63.2 x 5.4 mm.
- Render observations: SVG rendering passed; Windows PNG tessellation timed out.
- Validation/export result: Base and lid PASS; STEP and STL exported.
- Follow-up: Verify connector windows and lid fit against a physical board.

## Day 2 - sketches and constraints

- Goal: Study a detailed Raspberry Pi 4 reference package and formalize the
  workspace reference workflow.
- Model: Imported third-party Pi 4 STEP assembly as `rpi4_reference`.
- Numeric checks: 108 solids, 10,487 faces, 32.7 MB STEP, source bbox
  88.99 x 19.9 x 58.4 mm.
- Render observations: Orthographic and isometric source images are useful for
  semantic review but not production dimensions.
- Validation/export result: Reference catalog and trust hierarchy documented.
- Follow-up: Obtain the current official Pi 5 STEP and derive a lightweight
  keep-out proxy for repeated enclosure checks.

## Day 3 - booleans and feature selection

- Goal: Create a Raspberry Pi 4 Model B enclosure from the local dimensional
  drawing and detailed reference package without reusing the Pi 5 geometry.
- Model: Board-specific ventilated base, four standoffs, discrete connector
  openings, microSD access, external cap lid, GPIO slot, and 30 mm fan grille.
- Numeric checks: Closed envelope 96.1 x 67.1 x 26.4 mm; base volume
  25,570.501 mm3; lid volume 15,166.765 mm3; zero PCB/base and lid/base
  intersection volume in the intended assembled positions. Lid and base touch
  at the seating interface with no overlap.
- Render observations: MCP generated assembled, exploded, base isometric, and
  lid top SVG previews through the 3D pipeline. A combined A3 technical drawing
  adds six projected views, primary dimensions, feature callouts, hidden lines,
  and an ISO 7200 title block. Drawing lint has no errors or warnings.
- Validation/export result: Exact MCP validity gates passed for the base and
  lid as watertight manifold single solids. MCP re-exported STEP and STL after
  the seating correction. The lid print orientation has informational bridges
  only; the base recommends a maximum 0.20 mm layer height and flags one local
  0.20 mm microfeature.
- Follow-up: Tune connector and 0.15 mm-per-side lid clearances against a
  physical Pi 4 board, target FDM material, and printer calibration.

## Day 4 - fillets, chamfers, and shells

- Goal:
- Model:
- Numeric checks:
- Render observations:
- Validation/export result:
- Follow-up:

## Day 5 - assemblies and clearances

- Goal:
- Model:
- Numeric checks:
- Render observations:
- Validation/export result:
- Follow-up:

## Day 6 - imported references and comparison

- Goal:
- Model:
- Numeric checks:
- Render observations:
- Validation/export result:
- Follow-up:

## Day 7 - robust parametric part

- Goal:
- Model:
- Numeric checks:
- Render observations:
- Validation/export result:
- Follow-up:
