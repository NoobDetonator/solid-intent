"""Canonical geometry gates via build123d-mcp for exported project solids.

Local ``rebuild_project`` measures BREP metrics with build123d directly.
This harness imports the exported STEP bodies into a fresh MCP session and
runs ``validate`` + ``analyze_printability`` — the same gates the interactive
agent is expected to use before accepting a revision.

Usage:
    uv run --python 3.12 --with mcp --with build123d --with jsonschema \\
        python scripts/mcp_validate_project.py projects/raspberry_pi5_case
"""

from __future__ import annotations

import argparse
import asyncio
import json
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


def _parse_jsonish(text: str) -> Any:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"raw": text}


def _summarize_validate(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        if payload.get("passes_gate") is True:
            status = "PASS"
        elif payload.get("passes_gate") is False:
            status = "FAIL"
        else:
            status = str(
                payload.get("verdict") or payload.get("status") or payload.get("validate") or "UNKNOWN"
            ).upper()
        return {"status": status, "detail": payload}
    return {"status": "UNKNOWN", "detail": payload}


def _summarize_printability(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"status": "UNKNOWN", "detail": payload}
    status = str(payload.get("status") or payload.get("verdict") or "").upper()
    findings = payload.get("findings")
    if not status and isinstance(findings, list):
        severities = {str(item.get("severity", "")).lower() for item in findings if isinstance(item, dict)}
        if "error" in severities or "fail" in severities:
            status = "FAIL"
        elif "warning" in severities:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "PASS"
    if not status:
        status = "UNKNOWN"
    summary: dict[str, Any] = {"status": status}
    if isinstance(findings, list):
        summary["findings_count"] = len(findings)
        warnings = [
            item.get("message")
            for item in findings
            if isinstance(item, dict) and str(item.get("severity", "")).lower() == "warning"
        ]
        if warnings:
            summary["residual_warning"] = warnings[0]
        bridges = [
            item
            for item in findings
            if isinstance(item, dict) and str(item.get("kind", "")).lower() == "bridge"
        ]
        if bridges:
            summary["informational_bridges"] = len(bridges)
    for key in (
        "warnings",
        "residual_warning",
        "recommended_max_layer_height_mm",
        "informational_bridges",
        "overhangs",
        "note",
    ):
        if key in payload and key not in summary:
            summary[key] = payload[key]
    if len(summary) == 1:
        summary["detail"] = payload
    return summary


async def validate_project_mcp(project_path: Path) -> dict[str, Any]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    project = data_layer.load_project(project_path)
    artifacts = project.manifest.get("artifacts", {})
    bodies = [
        name
        for name in project.manifest["named_geometry"]["bodies"]
        if f"{name}_step" in artifacts
    ]
    if not bodies:
        raise SystemExit("No STEP artifacts declared for MCP validation.")

    step_files: list[tuple[str, Path]] = []
    for name in bodies:
        path = (project.root / artifacts[f"{name}_step"]).resolve()
        if not path.is_file():
            raise SystemExit(f"Missing STEP for '{name}': {path}")
        step_files.append((name, path))

    params = StdioServerParameters(
        command="uv",
        args=["tool", "run", "--python", "3.12", "build123d-mcp@latest"],
        cwd=str(REPO_ROOT),
    )

    geometry: dict[str, Any] = {}
    printability: dict[str, Any] = {}

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for name, path in step_files:
                imported = await session.call_tool(
                    "import_cad_file",
                    {"path": str(path), "name": name},
                )
                if getattr(imported, "isError", False):
                    raise SystemExit(f"MCP import failed for {name}: {_tool_text(imported)}")

                validated = await session.call_tool("validate", {"object_name": name})
                if getattr(validated, "isError", False):
                    raise SystemExit(f"MCP validate failed for {name}: {_tool_text(validated)}")
                geometry[name] = _summarize_validate(_parse_jsonish(_tool_text(validated)))

            for name in bodies:
                if name not in {"base", "lid_print"}:
                    continue
                printable = await session.call_tool(
                    "analyze_printability",
                    {"object_name": name},
                )
                if getattr(printable, "isError", False):
                    printability[name] = {
                        "status": "ERROR",
                        "note": _tool_text(printable)[:500],
                    }
                else:
                    printability[name] = _summarize_printability(
                        _parse_jsonish(_tool_text(printable))
                    )

    failed = [name for name, row in geometry.items() if str(row.get("status", "")).upper() != "PASS"]
    report = {
        "schema_version": 1,
        "project_id": project.manifest["project_id"],
        "executor": "build123d-mcp",
        "geometry_gates": geometry,
        "printability": printability,
        "failed_bodies": failed,
        "ok": not failed,
    }
    out = project.root / "mcp_validation_report.json"
    data_layer._atomic_write_json(out, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Path to projects/<id>")
    args = parser.parse_args()
    report = asyncio.run(validate_project_mcp(args.project))
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
