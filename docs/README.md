# Documentation

Curated engineering and product docs for SolidIntent.

## Start here

| Doc | Description |
| --- | --- |
| [../README.md](../README.md) | Product overview, tour, and quick start |
| [../PRODUCT.md](../PRODUCT.md) | Purpose, users, and positioning |
| [../DESIGN.md](../DESIGN.md) | Visual system and interaction principles |
| [ai_cad_architecture.md](ai_cad_architecture.md) | Runtime layers and ownership boundaries |
| [ai_cad_project_format.md](ai_cad_project_format.md) | Persistent project contract and lifecycle |
| [../AGENTS.md](../AGENTS.md) | Rules for AI agents working in this repo |

## Brand & visuals

| Path | Description |
| --- | --- |
| [brand/solidintent_logo.png](brand/solidintent_logo.png) | Wordmark, white on transparent (dark UI) |
| [brand/solidintent_logo_readme.png](brand/solidintent_logo_readme.png) | Wordmark, dark on transparent (light UI / README) |
| [brand/solidintent_logo.svg](brand/solidintent_logo.svg) | Lightweight geometric mark (no background fill) |
| [screenshots/](screenshots/) | README hero frames |
| [showcase/](showcase/) | Synced assembled, exploded, and dimensioned previews |
| [design/](design/) | Palette and early viewer direction studies |

## Showcase convention

`docs/showcase/` mirrors selected files from `renders/` and `drawings/` for
README review. Prefer PNG for README embeds and keep the matching SVG next to
it for zoomable line art. Regenerate with:

```bash
uv run --python 3.12 --with build123d --with build123d-drafting-helpers \
  --with jsonschema --with resvg-py \
  python scripts/export_artifacts.py --all
```
