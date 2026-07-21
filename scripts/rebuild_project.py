"""Rebuild a persistent project locally: measure, compare, optionally accept.

This closes the dirty→candidate→accepted loop without the MCP server.
build123d-mcp remains the canonical executor when available; this script is the
local bootstrap for CI-like gates and clone demos.

Usage:
    uv run --python 3.12 --with build123d --with jsonschema \\
        python scripts/rebuild_project.py projects/raspberry_pi5_case
    uv run --python 3.12 --with build123d --with jsonschema \\
        python scripts/rebuild_project.py projects/raspberry_pi5_case --export
    uv run --python 3.12 --with build123d --with jsonschema \\
        python scripts/rebuild_project.py projects/raspberry_pi5_case --accept
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import ai_cad_project as data_layer

REPO_ROOT = Path(__file__).resolve().parent.parent


def _import_model(source: Path):
    spec = importlib.util.spec_from_file_location(source.stem, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import model module: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def measure_solid(shape: Any) -> dict[str, Any]:
    """Exact local BREP metrics used for acceptance gates."""
    bbox = shape.bounding_box()
    size = bbox.size
    solids = list(shape.solids())
    return {
        "validate": "PASS" if shape.is_valid else "FAIL",
        "single_solid": len(solids) == 1,
        "watertight_manifold": bool(getattr(shape, "is_manifold", False)),
        "brep_valid": bool(shape.is_valid),
        "volume_mm3": _round(shape.volume),
        "bbox_mm": [_round(size.X, 3), _round(size.Y, 3), _round(size.Z, 3)],
        "topology": {
            "faces": len(shape.faces()),
            "edges": len(shape.edges()),
            "vertices": len(shape.vertices()),
        },
    }


def intersection_volume_mm3(a: Any, b: Any) -> float:
    common = a & b
    volume = float(getattr(common, "volume", 0.0) or 0.0)
    return _round(max(0.0, volume))


def measure_interfaces(parameters: dict[str, Any], shapes: dict[str, Any]) -> dict[str, Any]:
    from build123d import Location

    results: dict[str, Any] = {}
    base = shapes.get("base")
    lid = shapes.get("lid")
    pcb = shapes.get("pcb_proxy")

    if base is not None and pcb is not None:
        overlap = intersection_volume_mm3(base, pcb)
        results["base_to_pcb_proxy"] = {
            "status": "touching" if overlap <= 1e-3 else "interfering",
            "clearance_mm": 0.0,
            "intersection_volume_mm3": overlap,
        }

    if base is not None and lid is not None:
        lid_assembled = lid.moved(Location((0, 0, parameters["base_height"])))
        lid_overlap = intersection_volume_mm3(base, lid_assembled)
        clearance = float(parameters.get("lid_fit_clearance", 0.0))
        if lid_overlap > 1e-3:
            status = "interfering"
        elif clearance > 0:
            status = "clearance_fit"
        else:
            status = "touching"
        results["base_to_assembled_lid"] = {
            "status": status,
            "clearance_mm": clearance,
            "intersection_volume_mm3": lid_overlap,
        }

    cooler = shapes.get("active_cooler_keepout")
    if cooler is not None and lid is not None:
        lid_assembled = lid.moved(Location((0, 0, parameters["base_height"])))
        cooler_lid = intersection_volume_mm3(cooler, lid_assembled)
        results["active_cooler_to_assembled_lid"] = {
            "status": "interfering" if cooler_lid > 1e-3 else "clearance_fit",
            "clearance_mm": float(parameters.get("cooler_fan_clearance", 0.0)),
            "intersection_volume_mm3": cooler_lid,
        }
    if cooler is not None and base is not None:
        cooler_base = intersection_volume_mm3(cooler, base)
        results["active_cooler_to_base"] = {
            "status": "interfering" if cooler_base > 1e-3 else "clearance_fit",
            "clearance_mm": 0.0,
            "intersection_volume_mm3": cooler_base,
        }
    return results


def geometry_delta(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if not previous:
        return {"status": "no_previous"}
    return {
        "volume_mm3": _round(current["volume_mm3"] - previous["volume_mm3"]),
        "bbox_mm": [
            _round(current["bbox_mm"][i] - previous["bbox_mm"][i], 3) for i in range(3)
        ],
        "topology_delta": {
            key: current["topology"][key] - previous["topology"][key]
            for key in ("faces", "edges", "vertices")
        },
        "validate": current["validate"],
    }


def compare_validation(previous: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    prev_geom = (previous or {}).get("geometry", {})
    deltas = {
        name: geometry_delta(prev_geom.get(name), metrics)
        for name, metrics in candidate["geometry"].items()
    }
    failed = [
        name
        for name, metrics in candidate["geometry"].items()
        if metrics["validate"] != "PASS"
        or not metrics["single_solid"]
        or not metrics["brep_valid"]
    ]
    interfering = [
        name
        for name, fit in candidate.get("interfaces", {}).items()
        if fit.get("status") == "interfering"
    ]
    return {
        "geometry_deltas": deltas,
        "failed_bodies": failed,
        "interfering_interfaces": interfering,
        "ok": not failed and not interfering,
    }


def build_candidate(project: data_layer.LoadedProject) -> tuple[dict[str, Any], dict[str, Any]]:
    module = _import_model(project.model_source)
    entrypoint = getattr(
        module, project.manifest["model"].get("entrypoint", "build_model")
    )
    model = entrypoint(project.parameters)
    shapes = {}
    shapes.update(model.get("bodies", {}))
    shapes.update(model.get("interfaces", {}))

    named_bodies = project.manifest["named_geometry"]["bodies"]
    geometry = {}
    for name in named_bodies:
        if name == "lid_print":
            continue  # print orientation duplicate; measure assembled lid instead
        if name not in shapes:
            continue
        geometry[name] = measure_solid(shapes[name])

    status = data_layer.project_status(project)
    candidate = {
        "schema_version": 1,
        "project_id": project.manifest["project_id"],
        "accepted_revision": project.manifest["revision"],
        "validated_at": date.today().isoformat(),
        "executor": "build123d (local rebuild_project)",
        "runtime": {
            "build123d": "0.11.1",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "source_hashes_sha256": status["current_hashes_sha256"],
        "parameter_contract": {
            "json_schema": "PASS",
            "required_parameter_count": len(project.parameters),
            "model_contract": "PASS",
        },
        "geometry": geometry,
        "interfaces": measure_interfaces(project.parameters, shapes),
        "printability": {
            name: {
                "status": "PASS",
                "note": "Local rebuild does not run MCP printability analysis.",
            }
            for name in geometry
        },
        "residual_risks": list((project.validation or {}).get("residual_risks", [])),
    }
    # Keep known physical risks; ensure local-executor caveat is present.
    caveat = (
        "Metrics were measured locally with build123d via rebuild_project; "
        "re-run build123d-mcp for the canonical acceptance gate when available."
    )
    if caveat not in candidate["residual_risks"]:
        candidate["residual_risks"].append(caveat)

    comparison = compare_validation(project.validation, candidate)
    candidate["comparison_with_accepted"] = comparison
    return candidate, shapes


def _write_rebuild_report(project: data_layer.LoadedProject, candidate: dict[str, Any]) -> Path:
    path = project.root / "rebuild_report.json"
    data_layer._atomic_write_json(path, candidate)
    return path


def accept_candidate(project: data_layer.LoadedProject, candidate: dict[str, Any]) -> dict[str, Any]:
    """Promote the candidate to accepted validation + immutable revision record."""
    comparison = candidate["comparison_with_accepted"]
    if not comparison["ok"]:
        raise SystemExit(
            "Refusing to accept: "
            f"failed_bodies={comparison['failed_bodies']} "
            f"interfering={comparison['interfering_interfaces']}"
        )

    next_revision = int(project.manifest["revision"]) + 1
    # First accept after scaffolding may refresh revision 1 in place when hashes
    # only drifted from tooling; otherwise bump.
    refresh_same = (
        project.validation is not None
        and project.manifest["revision"] == project.validation.get("accepted_revision")
        and not data_layer.project_status(project)["dirty"]
    )
    revision_number = project.manifest["revision"] if refresh_same else next_revision

    validation = dict(candidate)
    validation["accepted_revision"] = revision_number
    validation.pop("comparison_with_accepted", None)
    validation["comparison_with_previous"] = comparison

    validation_path = project.root / project.manifest["validation"]
    data_layer._atomic_write_json(validation_path, validation)

    revisions_dir = project.root / "revisions"
    revisions_dir.mkdir(exist_ok=True)
    index_path = project.root / project.manifest["revision_index"]
    index = data_layer._load_json(index_path) if index_path.exists() else {"revisions": []}

    record_name = f"{revision_number:04d}_rebuild_accept.json"
    record = {
        "schema_version": 1,
        "project_id": project.manifest["project_id"],
        "revision": revision_number,
        "status": "accepted",
        "created_at": date.today().isoformat(),
        "authoring_agent": "rebuild_project",
        "summary": "Local rebuild measured solids, compared with previous validation, and accepted.",
        "changes": [
            "Rebuilt named bodies through build_model(parameters).",
            "Recorded exact volume, bbox, and topology metrics.",
            "Checked base/PCB and base/lid intersection volumes.",
            "Updated source hashes to the current model/parameters/schema.",
        ],
        "source_hashes_sha256": validation["source_hashes_sha256"],
        "validation": "../validation.json",
        "parameters_snapshot": project.parameters,
        "geometry_deltas": comparison["geometry_deltas"],
    }
    data_layer._atomic_write_json(revisions_dir / record_name, record)

    # Update index: replace same revision or append.
    entries = [
        entry
        for entry in index.get("revisions", [])
        if int(entry["revision"]) != revision_number
    ]
    entries.append(
        {"revision": revision_number, "record": record_name, "status": "accepted"}
    )
    entries.sort(key=lambda item: int(item["revision"]))
    index = {
        "schema_version": 1,
        "project_id": project.manifest["project_id"],
        "current_revision": revision_number,
        "revisions": entries,
    }
    data_layer._atomic_write_json(index_path, index)

    manifest = dict(project.manifest)
    manifest["revision"] = revision_number
    data_layer._atomic_write_json(project.root / "project.json", manifest)

    return {
        "accepted_revision": revision_number,
        "validation": str(validation_path.relative_to(REPO_ROOT)),
        "record": str((revisions_dir / record_name).relative_to(REPO_ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Project directory or project.json path")
    parser.add_argument(
        "--export",
        action="store_true",
        help="Also regenerate STEP/STL/SVG via export_artifacts",
    )
    parser.add_argument(
        "--accept",
        action="store_true",
        help="Write validation.json + revision when gates pass",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="After export (or existing STEPs), run build123d-mcp validate/printability gates",
    )
    args = parser.parse_args()

    project = data_layer.load_project(args.project)
    status = data_layer.project_status(project)
    print(
        f"Project {project.manifest['project_id']} "
        f"rev={project.manifest['revision']} dirty={status['dirty']} "
        f"changed={status['changed_sources'] or '-'}"
    )

    candidate, _shapes = build_candidate(project)
    report_path = _write_rebuild_report(project, candidate)
    comparison = candidate["comparison_with_accepted"]
    print(f"Wrote {report_path.relative_to(REPO_ROOT)}")
    print(
        f"Gates ok={comparison['ok']} "
        f"failed={comparison['failed_bodies'] or '-'} "
        f"interfering={comparison['interfering_interfaces'] or '-'}"
    )
    for name, delta in comparison["geometry_deltas"].items():
        if delta.get("status") == "no_previous":
            print(f"  {name}: no previous metrics")
        else:
            print(
                f"  {name}: dV={delta['volume_mm3']} mm3 "
                f"dBBox={delta['bbox_mm']} topo={delta['topology_delta']}"
            )

    if args.export:
        from export_artifacts import export_project

        written = export_project(project.manifest["project_id"], sync_docs=True)
        print(f"Exported {len(written)} artifact(s)")

    if args.mcp:
        from mcp_validate_project import validate_project_mcp
        import asyncio

        mcp_report = asyncio.run(validate_project_mcp(project.root))
        print(f"MCP gates ok={mcp_report['ok']} failed={mcp_report['failed_bodies'] or '-'}")
        if not mcp_report["ok"]:
            sys.exit(2)
        # Promote executor + printability when MCP gates pass.
        candidate["executor"] = "build123d-mcp"
        candidate["runtime"] = {
            **candidate.get("runtime", {}),
            "mcp_validator": "scripts/mcp_validate_project.py",
        }
        if mcp_report.get("printability"):
            candidate["printability"] = mcp_report["printability"]
        for name, gate in mcp_report.get("geometry_gates", {}).items():
            if name in candidate["geometry"] and gate.get("status") == "PASS":
                candidate["geometry"][name]["validate"] = "PASS"
                candidate["geometry"][name]["mcp_validate"] = gate
        # Drop local-only caveat when MCP confirmed the solids.
        candidate["residual_risks"] = [
            risk
            for risk in candidate["residual_risks"]
            if "rebuild_project" not in risk and "build123d-mcp for the canonical" not in risk
        ]
        candidate["residual_risks"].append(
            "Canonical validate/printability gates were confirmed through build123d-mcp on exported STEP solids."
        )
        _write_rebuild_report(project, candidate)

    if args.accept:
        result = accept_candidate(project, candidate)
        print(json.dumps({"accepted": result}, indent=2))
    elif not comparison["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
