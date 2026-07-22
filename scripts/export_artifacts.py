"""Regenerate project CAD artifacts: STEP/STL meshes and SVG technical views.

Canonical geometry authority remains build123d-mcp. This script is the local
bootstrap so clones can populate ``exports/``, ``renders/``, and drawings
without the MCP server.

Usage:
    uv run --python 3.12 --with build123d --with build123d-drafting-helpers \\
        python scripts/export_artifacts.py
    uv run --python 3.12 --with build123d --with build123d-drafting-helpers \\
        python scripts/export_artifacts.py raspberry_pi5_case
    uv run --python 3.12 --with build123d --with build123d-drafting-helpers \\
        python scripts/export_artifacts.py --all
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = REPO_ROOT / "projects"
SHOWCASE_DIR = REPO_ROOT / "docs" / "showcase"

# Dark strokes for white-paper / README readability.
LAYER_COLORS = {
    "base": ((0.12, 0.22, 0.30), (0.62, 0.68, 0.72)),
    "lid": ((0.50, 0.18, 0.18), (0.75, 0.62, 0.62)),
    "pcb_proxy": ((0.12, 0.42, 0.18), (0.62, 0.72, 0.62)),
}
ISO_CAMERA = (110.0, 110.0, 95.0)
ISO_UP = (0.0, 0.0, 1.0)
EXPLODED_LID_Z = 28.0


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
    shapes: dict[str, Any] = {}
    shapes.update(model.get("bodies", {}))
    shapes.update(model.get("interfaces", {}))
    return shapes


def _write_technical_svg(
    target: Path,
    parts: list[tuple[str, Any]],
    *,
    look_at: tuple[float, float, float] = (0.0, 0.0, 10.0),
) -> None:
    from build123d import Color, Compound, ExportSVG, LineType

    svg = ExportSVG(margin=4)
    for name, shape in parts:
        visible_rgb, hidden_rgb = LAYER_COLORS.get(
            name, ((0.15, 0.15, 0.15), (0.65, 0.65, 0.65))
        )
        visible, hidden = shape.project_to_viewport(ISO_CAMERA, ISO_UP, look_at)
        vis_layer = f"{name}_visible"
        hid_layer = f"{name}_hidden"
        svg.add_layer(
            vis_layer,
            line_color=Color(*visible_rgb),
            line_weight=0.4,
        )
        svg.add_layer(
            hid_layer,
            line_color=Color(*hidden_rgb),
            line_weight=0.22,
            line_type=LineType.HIDDEN,
        )
        svg.add_shape(Compound(children=list(visible)), layer=vis_layer)
        if hidden:
            svg.add_shape(Compound(children=list(hidden)), layer=hid_layer)
    target.parent.mkdir(parents=True, exist_ok=True)
    svg.write(str(target))


def _export_svg_previews(
    project_id: str,
    project_dir: Path,
    manifest: dict[str, Any],
    shapes: dict[str, Any],
) -> list[Path]:
    from build123d import Location

    written: list[Path] = []
    artifacts = manifest.get("artifacts", {})
    body_names = [
        name
        for name in manifest.get("named_geometry", {}).get("bodies", [])
        if name in shapes and name != "lid_print"
    ]
    if not body_names:
        return written

    primary = shapes[body_names[0]]
    try:
        bb = primary.bounding_box()
        look_z = (bb.max.Z + bb.min.Z) / 2
    except Exception:
        look_z = 12.0
    look_at = (0.0, 0.0, look_z)

    assembled_key = "assembled_preview"
    if assembled_key in artifacts:
        target = (project_dir / artifacts[assembled_key]).resolve()
        parts = [(name, shapes[name]) for name in body_names]
        # Prefer familiar layer colors when present; otherwise dark stroke.
        _write_technical_svg(target, parts, look_at=look_at)
        written.append(target)
        print(f"  wrote {target.relative_to(REPO_ROOT)} ({target.stat().st_size} bytes)")

    exploded_key = "exploded_preview"
    if exploded_key in artifacts and "lid" in shapes and "base" in shapes:
        target = (project_dir / artifacts[exploded_key]).resolve()
        lid_up = shapes["lid"].moved(Location((0, 0, EXPLODED_LID_Z)))
        parts = [("base", shapes["base"]), ("lid", lid_up)]
        if "pcb_proxy" in shapes:
            parts.insert(1, ("pcb_proxy", shapes["pcb_proxy"]))
        _write_technical_svg(target, parts, look_at=(0.0, 0.0, look_z + EXPLODED_LID_Z / 2))
        written.append(target)
        print(f"  wrote {target.relative_to(REPO_ROOT)} ({target.stat().st_size} bytes)")

    return written


def _export_dimensioned_drawing(project_id: str, project_dir: Path, manifest: dict[str, Any]) -> list[Path]:
    if "dimensioned_drawing" not in manifest.get("artifacts", {}):
        return []

    drawing_modules = {
        "raspberry_pi4_case": "raspberry_pi4_case_drawing",
        "raspberry_pi5_case": "raspberry_pi5_case_drawing",
        "raspberry_pi_zero2w_case": "raspberry_pi_zero2w_case_drawing",
    }
    module_name = drawing_modules.get(project_id)
    if module_name is None:
        return []

    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    module = __import__(module_name)
    svg_path, dxf_path, _issues = module.generate_drawing()
    written = [Path(svg_path), Path(dxf_path)]
    dims_path = Path(svg_path).with_suffix(".dims.json")
    if dims_path.exists():
        written.append(dims_path)
    for path in written:
        print(f"  wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size} bytes)")
    return written


def _sync_showcase(written: list[Path]) -> None:
    """Copy regenerated SVG/PNG review assets into docs/showcase for the README."""
    SHOWCASE_DIR.mkdir(parents=True, exist_ok=True)
    for path in written:
        if path.suffix.lower() not in {".svg", ".png"}:
            continue
        if path.parent.name not in {"renders", "drawings"}:
            continue
        # Skip DXF sidecar previews that are not the dimensioned sheet PNG.
        if path.name.endswith("_preview.png"):
            dest = SHOWCASE_DIR / path.name.replace("_preview", "")
        else:
            dest = SHOWCASE_DIR / path.name
        shutil.copy2(path, dest)
        print(f"  synced docs/showcase/{dest.name}")


def export_project(project_id: str, *, sync_docs: bool = True) -> list[Path]:
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
            continue
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

    written.extend(_export_svg_previews(project_id, project_dir, manifest, shapes))
    written.extend(_export_dimensioned_drawing(project_id, project_dir, manifest))
    written.extend(_export_png_previews(written))
    written.extend(_export_vtk_png(project_id, project_dir, manifest))

    if sync_docs:
        _sync_showcase(written)
    return written


def _export_vtk_png(project_id: str, project_dir: Path, manifest: dict[str, Any]) -> list[Path]:
    """Optional MCP VTK raster of the assembled solids."""
    if "assembled_vtk_png" not in manifest.get("artifacts", {}):
        return []
    try:
        from mcp_render_vtk import render_assembled_vtk
        import asyncio

        path = asyncio.run(render_assembled_vtk(project_dir))
        print(f"  wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size} bytes)")
        return [path]
    except BaseException as exc:  # noqa: BLE001 - keep export resilient (incl. SystemExit)
        print(f"  skip VTK PNG: {exc}", file=sys.stderr)
        return []


def _export_png_previews(svg_paths: list[Path]) -> list[Path]:
    """Rasterise SVG technical views to PNG via resvg (MCP render_drawing path)."""
    import re

    try:
        import resvg_py
    except ImportError:
        print("  skip PNG: resvg-py not installed", file=sys.stderr)
        return []

    written: list[Path] = []
    for svg_path in svg_paths:
        if svg_path.suffix.lower() != ".svg":
            continue
        if svg_path.parent.name not in {"renders", "drawings"}:
            continue
        png_path = svg_path.with_suffix(".png")
        svg_text = svg_path.read_text(encoding="utf-8")
        # build123d ExportSVG uses mm width/height; resvg wants unitless/px sizes.
        svg_text = re.sub(
            r'width="([0-9.]+)mm"',
            lambda match: f'width="{max(1, int(float(match.group(1)) * 3.7795275591))}"',
            svg_text,
            count=1,
        )
        svg_text = re.sub(
            r'height="([0-9.]+)mm"',
            lambda match: f'height="{max(1, int(float(match.group(1)) * 3.7795275591))}"',
            svg_text,
            count=1,
        )
        try:
            png_bytes = resvg_py.svg_to_bytes(svg_text, zoom=2.0, background="white")
        except Exception as exc:  # noqa: BLE001 - keep export resilient
            print(f"  skip PNG for {svg_path.name}: {exc}", file=sys.stderr)
            continue
        png_path.write_bytes(png_bytes)
        written.append(png_path)
        print(f"  wrote {png_path.relative_to(REPO_ROOT)} ({png_path.stat().st_size} bytes)")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "project",
        nargs="?",
        default="raspberry_pi4_case",
        help="Project id under projects/ (default: raspberry_pi4_case)",
    )
    parser.add_argument("--all", action="store_true", help="Export every project")
    parser.add_argument(
        "--no-docs",
        action="store_true",
        help="Do not copy SVG/PNG into docs/showcase",
    )
    args = parser.parse_args()
    projects = (
        sorted(path.name for path in PROJECTS_ROOT.iterdir() if (path / "project.json").is_file())
        if args.all
        else [args.project]
    )
    total = 0
    for project_id in projects:
        print(f"Regenerating artifacts for '{project_id}'...")
        written = export_project(project_id, sync_docs=not args.no_docs)
        total += len(written)
        if not written:
            print(f"No artifacts were written for '{project_id}'.", file=sys.stderr)
    if total == 0:
        sys.exit(1)
    print(f"Done: {total} artifact(s).")


if __name__ == "__main__":
    main()
