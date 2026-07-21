"""Regenerate neutral CAD artifacts (STL/STEP) for a persistent project.

This is a convenience entry point for local previews. The canonical geometry
pipeline is ``build123d-mcp`` (see ``AGENTS.md``); this script simply loads a
project's parameters, rebuilds its named bodies through the project model
entry point, and writes the mesh/BREP artifacts declared in ``project.json``.

Usage:
    uv run --python 3.12 --with build123d python scripts/export_artifacts.py
    uv run --python 3.12 --with build123d python scripts/export_artifacts.py raspberry_pi4_case
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = REPO_ROOT / "projects"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _import_model(source: Path):
    spec = importlib.util.spec_from_file_location(source.stem, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import model module: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _collect_shapes(model: dict[str, Any]) -> dict[str, Any]:
    """Flatten the model's bodies and interfaces into a single name map."""
    shapes: dict[str, Any] = {}
    shapes.update(model.get("bodies", {}))
    shapes.update(model.get("interfaces", {}))
    return shapes


def export_project(project_id: str) -> list[Path]:
    from build123d import export_step, export_stl

    project_dir = PROJECTS_ROOT / project_id
    manifest = _load_json(project_dir / "project.json")
    parameters = _load_json(project_dir / manifest["parameter_values"])

    model_source = (project_dir / manifest["model"]["source"]).resolve()
    module = _import_model(model_source)
    entrypoint = getattr(module, manifest["model"].get("entrypoint", "build_model"))
    model = entrypoint(parameters)
    shapes = _collect_shapes(model)

    written: list[Path] = []
    exporters = {"stl": export_stl, "step": export_step}
    for key, relative_path in manifest.get("artifacts", {}).items():
        suffix = key.rsplit("_", 1)[-1]
        exporter = exporters.get(suffix)
        if exporter is None:
            continue  # previews (svg) and drawings are generated elsewhere
        body_name = key[: -(len(suffix) + 1)]
        shape = shapes.get(body_name)
        if shape is None:
            print(f"  skip {key}: no body named '{body_name}' in the model", file=sys.stderr)
            continue
        target = (project_dir / relative_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        exporter(shape, str(target))
        written.append(target)
        print(f"  wrote {target.relative_to(REPO_ROOT)} ({target.stat().st_size} bytes)")

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project",
        nargs="?",
        default="raspberry_pi4_case",
        help="Project id under projects/ (default: raspberry_pi4_case)",
    )
    args = parser.parse_args()
    print(f"Regenerating artifacts for '{args.project}'...")
    written = export_project(args.project)
    if not written:
        print("No STL/STEP artifacts were written.", file=sys.stderr)
        sys.exit(1)
    print(f"Done: {len(written)} artifact(s).")


if __name__ == "__main__":
    main()
