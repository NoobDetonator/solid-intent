"""Render assembled project solids to a VTK/PNG preview via build123d-mcp.

This complements the SVG→PNG technical views with a true tessellated 3D
raster from the MCP ``render_view`` path (VTK).

Usage:
    uv run --python 3.12 --with mcp --with jsonschema \\
        python scripts/mcp_render_vtk.py projects/raspberry_pi5_case
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

import ai_cad_project as data_layer

REPO_ROOT = Path(__file__).resolve().parent.parent


def _tool_text(result: Any) -> str:
    chunks: list[str] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()


async def render_assembled_vtk(project_path: Path) -> Path:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    project = data_layer.load_project(project_path)
    artifacts = project.manifest.get("artifacts", {})
    target_key = "assembled_vtk_png"
    if target_key not in artifacts:
        raise RuntimeError(f"Project does not declare {target_key} artifact.")
    out_path = (project.root / artifacts[target_key]).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bodies = [
        name
        for name in project.manifest["named_geometry"]["bodies"]
        if name != "lid_print" and f"{name}_step" in artifacts
    ]
    if not bodies:
        raise RuntimeError("No STEP bodies available for VTK render.")

    params = StdioServerParameters(
        command="uv",
        args=["tool", "run", "--python", "3.12", "build123d-mcp@latest"],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names: list[str] = []
            for name in bodies:
                step = (project.root / artifacts[f"{name}_step"]).resolve()
                if not step.is_file():
                    raise RuntimeError(f"Missing STEP for {name}: {step}")
                imported = await session.call_tool(
                    "import_cad_file",
                    {"path": str(step), "name": name},
                )
                if getattr(imported, "isError", False):
                    raise RuntimeError(f"import failed for {name}: {_tool_text(imported)}")
                names.append(name)

            # Prefer an assembled compound when base+lid are present.
            objects = ",".join(names)
            if "base" in names and "lid" in names:
                height = float(project.parameters.get("base_height", 0.0))
                assembled = await session.call_tool(
                    "execute",
                    {
                        "code": (
                            "from build123d import Compound, Location\n"
                            f"lid_up = lid.move(Location((0, 0, {height})))\n"
                            "assembled = Compound(children=[base, lid_up])\n"
                            "show(assembled, name='assembled')\n"
                        )
                    },
                )
                if not getattr(assembled, "isError", False):
                    objects = "assembled"

            rendered = await session.call_tool(
                "render_view",
                {
                    "direction": "iso",
                    "objects": objects,
                    "quality": "standard",
                    "format": "png",
                    "save_to": str(out_path),
                },
            )
            if getattr(rendered, "isError", False):
                # Last resort: render the first solid only.
                fallback = await session.call_tool(
                    "render_view",
                    {
                        "direction": "iso",
                        "objects": names[0],
                        "quality": "standard",
                        "format": "png",
                        "save_to": str(out_path),
                    },
                )
                if getattr(fallback, "isError", False):
                    raise RuntimeError(
                        f"render_view failed: {_tool_text(rendered)} / {_tool_text(fallback)}"
                    )

    if not out_path.is_file():
        raise RuntimeError(f"VTK PNG was not written to {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    path = asyncio.run(render_assembled_vtk(args.project))
    print(f"wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
