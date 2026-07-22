# Persistent projects

AI-editable CAD projects live here. Each directory is a complete contract:

```text
projects/<id>/
  project.json           # manifest, artifacts, rebuild policy
  parameters.json        # current values (mm)
  parameter_schema.json  # editable / locked / advanced metadata
  references.json        # provenance
  validation.json        # last accepted evidence
  revisions/             # immutable accept records
```

## Current pilots

| ID | Title |
| --- | --- |
| `raspberry_pi4_case` | Raspberry Pi 4 Model B enclosure |
| `raspberry_pi5_case` | Raspberry Pi 5 enclosure |
| `mounting_plate` | Slotted mounting plate |

Regenerate geometry and showcase copies from the repo root:

```bash
uv run --python 3.12 --with build123d --with build123d-drafting-helpers \
  --with jsonschema --with resvg-py \
  python scripts/export_artifacts.py --all
```

See [`docs/ai_cad_project_format.md`](../docs/ai_cad_project_format.md) for the
full lifecycle.
