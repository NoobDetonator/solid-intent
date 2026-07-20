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
- Machine-readable design intent: `specs/`
- Generated neutral CAD and meshes: `exports/`
- Generated previews: `renders/`
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
