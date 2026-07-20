"""Load, inspect, and edit persistent AI CAD project parameters.

This module is the workspace data layer. It never creates or measures geometry;
rebuilds and acceptance gates remain the responsibility of build123d-mcp.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema


PROJECT_FORMAT = "ai_cad_project"


@dataclass(frozen=True)
class LoadedProject:
    """Validated project metadata and current parameter state."""

    root: Path
    manifest: dict[str, Any]
    parameters: dict[str, Any]
    parameter_schema: dict[str, Any]
    validation: dict[str, Any] | None

    @property
    def model_source(self) -> Path:
        return (self.root / self.manifest["model"]["source"]).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as source:
        value = json.load(source)
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(value, destination, indent=2, ensure_ascii=False)
        destination.write("\n")
    os.replace(temporary, path)


def load_project(project_path: str | Path) -> LoadedProject:
    """Load and validate a project manifest, schema, and current values."""
    candidate = Path(project_path).resolve()
    root = candidate.parent if candidate.is_file() else candidate
    manifest_path = candidate if candidate.is_file() else root / "project.json"
    manifest = _load_json(manifest_path)

    if manifest.get("format") != PROJECT_FORMAT:
        raise ValueError(
            f"Unsupported project format: {manifest.get('format')!r}; "
            f"expected {PROJECT_FORMAT!r}"
        )
    if manifest.get("schema_version") != 1:
        raise ValueError(
            f"Unsupported project schema version: {manifest.get('schema_version')!r}"
        )

    parameter_path = root / manifest["parameter_values"]
    schema_path = root / manifest["parameter_schema"]
    parameters = _load_json(parameter_path)
    parameter_schema = _load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(parameter_schema)
    jsonschema.validate(parameters, parameter_schema)

    validation_path = root / manifest["validation"]
    validation = _load_json(validation_path) if validation_path.exists() else None
    model_source = (root / manifest["model"]["source"]).resolve()
    if not model_source.is_file():
        raise FileNotFoundError(f"Model source does not exist: {model_source}")

    return LoadedProject(
        root=root,
        manifest=manifest,
        parameters=parameters,
        parameter_schema=parameter_schema,
        validation=validation,
    )


def _resolved_property(schema: dict[str, Any], name: str) -> dict[str, Any]:
    raw = dict(schema["properties"][name])
    reference = raw.pop("$ref", None)
    if reference is None:
        return raw
    prefix = "#/$defs/"
    if not reference.startswith(prefix):
        raise ValueError(f"Unsupported local schema reference: {reference}")
    inherited = dict(schema["$defs"][reference[len(prefix) :]])
    inherited_ui = dict(inherited.pop("x-ui", {}))
    raw_ui = dict(raw.pop("x-ui", {}))
    return {
        **inherited,
        **raw,
        "x-ui": {**inherited_ui, **raw_ui},
    }


def parameter_catalog(project: LoadedProject) -> list[dict[str, Any]]:
    """Return UI-ready controls sorted by group order metadata."""
    controls = []
    for name, value in project.parameters.items():
        definition = _resolved_property(project.parameter_schema, name)
        ui = definition.get("x-ui", {})
        controls.append(
            {
                "name": name,
                "label": definition.get("title", name),
                "value": value,
                "type": definition.get("type"),
                "unit": definition.get("x-unit"),
                "minimum": definition.get("minimum"),
                "maximum": definition.get("maximum"),
                "step": definition.get("x-step"),
                "user_editable": definition.get("x-user-editable", False),
                "semantic_change": definition.get("x-semantic-change", True),
                "lock_reason": definition.get("x-lock-reason"),
                "group": ui.get("group", "General"),
                "order": ui.get("order", 9999),
                "control": ui.get("control", "number"),
                "advanced": ui.get("advanced", False),
                "warning": ui.get("warning"),
            }
        )
    return sorted(controls, key=lambda item: (item["order"], item["name"]))


def project_status(project: LoadedProject) -> dict[str, Any]:
    """Report whether source and parameters still match accepted validation."""
    parameter_path = project.root / project.manifest["parameter_values"]
    schema_path = project.root / project.manifest["parameter_schema"]
    current_hashes = {
        "model": _sha256(project.model_source),
        "parameters": _sha256(parameter_path),
        "parameter_schema": _sha256(schema_path),
    }
    accepted_hashes = (
        project.validation.get("source_hashes_sha256", {})
        if project.validation
        else {}
    )
    changed = [
        name
        for name, value in current_hashes.items()
        if value != accepted_hashes.get(name)
    ]
    return {
        "project_id": project.manifest["project_id"],
        "revision": project.manifest["revision"],
        "accepted_revision": (
            project.validation.get("accepted_revision")
            if project.validation
            else None
        ),
        "dirty": bool(changed),
        "changed_sources": changed,
        "current_hashes_sha256": current_hashes,
        "accepted_hashes_sha256": accepted_hashes,
    }


def set_parameter(
    project_path: str | Path,
    name: str,
    value: Any,
    *,
    allow_locked: bool = False,
) -> dict[str, Any]:
    """Persist one schema-valid parameter edit and mark the project dirty."""
    project = load_project(project_path)
    if name not in project.parameters:
        raise KeyError(f"Unknown parameter: {name}")

    definition = _resolved_property(project.parameter_schema, name)
    editable = definition.get("x-user-editable", False)
    if not editable and not allow_locked:
        reason = definition.get("x-lock-reason", "Parameter is locked")
        raise PermissionError(f"Cannot edit '{name}': {reason}")

    updated = dict(project.parameters)
    previous = updated[name]
    if previous == value:
        return {
            "project_id": project.manifest["project_id"],
            "parameter": name,
            "previous": previous,
            "current": value,
            "changed": False,
            "requires_rebuild": False,
            "requires_ai_review": False,
            "status": project_status(project),
        }
    updated[name] = value
    jsonschema.validate(updated, project.parameter_schema)

    parameter_path = project.root / project.manifest["parameter_values"]
    _atomic_write_json(parameter_path, updated)
    reloaded = load_project(project.root)
    return {
        "project_id": project.manifest["project_id"],
        "parameter": name,
        "previous": previous,
        "current": value,
        "changed": True,
        "requires_rebuild": True,
        "requires_ai_review": definition.get("x-semantic-change", True),
        "status": project_status(reloaded),
    }


def _parse_cli_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect one project")
    inspect_parser.add_argument("project")

    catalog_parser = subparsers.add_parser(
        "parameters", help="Emit the parameter-editor catalog"
    )
    catalog_parser.add_argument("project")

    set_parser = subparsers.add_parser("set", help="Persist one parameter edit")
    set_parser.add_argument("project")
    set_parser.add_argument("name")
    set_parser.add_argument("value")
    set_parser.add_argument("--allow-locked", action="store_true")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "inspect":
        project = load_project(args.project)
        result = {
            "manifest": project.manifest,
            "status": project_status(project),
        }
    elif args.command == "parameters":
        project = load_project(args.project)
        result = {
            "project_id": project.manifest["project_id"],
            "parameters": parameter_catalog(project),
        }
    else:
        result = set_parameter(
            args.project,
            args.name,
            _parse_cli_value(args.value),
            allow_locked=args.allow_locked,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
