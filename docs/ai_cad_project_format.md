# Project format

## Purpose

An AI CAD project is the persistent, editable document used by an AI-operated
CAD workflow. Natural-language requests remain the primary interface. A future
web viewer may expose approved parameters, but it is not a second CAD kernel.

The project format is transparent JSON plus Python source. STEP, STL, SVG, and
DXF are derived artifacts and never replace the editable project definition.

## Project contract

`project.json` declares:

- Project identity and schema version.
- Model source and callable entry point.
- Parameter values and validation schema.
- Stable body and interface names.
- Reference and validation records.
- Artifact locations and rebuild policy.

The model entry point has this conceptual signature:

```python
def build_model(parameters):
    return {
        "bodies": {"base": ..., "lid": ..., "lid_print": ...},
        "interfaces": {"pcb_proxy": ...},
    }
```

The entry point receives the complete persisted parameter mapping. It must not
silently substitute independent dimensional defaults.

## Parameter classes

The JSON Schema uses extension metadata understood by the project manager and
future viewer:

- `x-unit` - engineering unit displayed to the user.
- `x-step` - preferred editor increment without floating-point `multipleOf`
  validation problems.
- `x-user-editable` - whether the user may change the value directly.
- `x-semantic-change` - whether changing it requires AI design judgment.
- `x-lock-reason` - why a reference-controlled value is locked.
- `x-ui` - group, order, control type, advanced flag, and warnings.

Reference dimensions and connector centres are locked by default. Enclosure
clearances, thicknesses, and selected interface dimensions are user-editable.

## Lifecycle states

```text
clean accepted revision
        |
        | parameter or model edit
        v
dirty / rebuild required
        |
        | build123d-mcp rebuild + comparison + validation
        v
candidate revision
    |              |
    | pass         | fail
    v              v
accepted       rejected / restore
```

Hashes in `validation.json` determine whether the working project still matches
the accepted revision. A parameter edit is saved immediately but does not
become an accepted revision until the CAD gates pass.

## AI open workflow

1. Load `project.json` through `scripts/ai_cad_project.py`.
2. Validate `parameters.json` against `parameter_schema.json`.
3. Check source hashes against `validation.json`.
4. Read references, residual risks, and the latest revision record.
5. Reconstruct the model through build123d-mcp when the project is dirty or the
   user requests a geometry operation.
6. Use stable names from `named_geometry` for comparisons and exports.

## Parameter edit workflow

1. The user or viewer chooses an `x-user-editable` parameter.
2. The project manager validates and atomically writes the new value.
3. The project becomes dirty because its parameter hash differs from the
   accepted validation record.
4. The AI rebuilds the project through build123d-mcp.
5. Compare the candidate with the accepted revision using exact envelope,
   volume, topology, interface, and validity evidence.
6. Re-run printability and drawing generation when affected.
7. On success, create a revision record and update accepted hashes.

Locked values require an explicit semantic change led by the AI and human
review of the controlling reference.

## Workspace data-layer commands

Inspect a project:

```text
python scripts/ai_cad_project.py inspect projects/raspberry_pi4_case
```

Emit the parameter-editor catalog:

```text
python scripts/ai_cad_project.py parameters projects/raspberry_pi4_case
```

Persist an editable value:

```text
python scripts/ai_cad_project.py set projects/raspberry_pi4_case wall_thickness 3.0
```

The `set` command performs no CAD operation. It reports `requires_rebuild=true`;
the AI must perform the MCP rebuild and acceptance workflow.

## Viewer boundary

The web viewer in `viewer/` reads the manifest, parameter catalog, validation
report, and lightweight tessellated artifacts. It edits approved parameter
values and prepares AI rebuild requests. It must never become the authority for dimensions,
interference, mass, or validity. Those results come from build123d-mcp and are
stored in the accepted validation report.

The implemented first viewer milestone provides:

- Project and revision selector.
- Interactive model visibility and exploded state.
- Grouped parameter controls generated from the schema.
- Clean/dirty/validating/accepted status.
- Validation findings and artifact downloads.
- A copyable AI rebuild request after dimensional changes.