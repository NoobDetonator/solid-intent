"""Unit tests for the persistent AI CAD project data layer.

These build hermetic fixture projects in ``tmp_path`` so they never depend on
the repository's real project or mutate tracked files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

import ai_cad_project as data_layer


PARAMETER_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["wall_thickness", "pcb_length"],
    "properties": {
        "wall_thickness": {
            "$ref": "#/$defs/editable_dimension",
            "title": "Wall thickness",
            "minimum": 1.2,
            "maximum": 5.0,
            "x-step": 0.1,
            "x-ui": {"group": "Base", "order": 20, "control": "slider"},
        },
        "pcb_length": {
            "$ref": "#/$defs/locked_dimension",
            "title": "PCB length",
            "minimum": 84.5,
            "maximum": 85.5,
            "x-ui": {"group": "Reference", "order": 10},
        },
    },
    "$defs": {
        "editable_dimension": {
            "type": "number",
            "x-unit": "mm",
            "x-user-editable": True,
            "x-semantic-change": False,
        },
        "locked_dimension": {
            "type": "number",
            "x-unit": "mm",
            "x-user-editable": False,
            "x-semantic-change": True,
            "x-lock-reason": "Controlled by reference hardware",
        },
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a self-contained valid project and return its root directory."""
    root = tmp_path / "sample_case"
    root.mkdir()

    model = root / "model.py"
    model.write_text("def build_model(parameters):\n    return {}\n", encoding="utf-8")

    _write_json(root / "parameter_schema.json", PARAMETER_SCHEMA)
    parameters = {"pcb_length": 85.0, "wall_thickness": 2.4}
    _write_json(root / "parameters.json", parameters)

    _write_json(
        root / "revisions" / "index.json",
        {"revisions": [{"revision": 1, "record": "0001.json"}]},
    )
    _write_json(
        root / "revisions" / "0001.json",
        {"revision": 1, "status": "accepted", "parameters_snapshot": parameters},
    )

    manifest = {
        "schema_version": 1,
        "format": "ai_cad_project",
        "project_id": "sample_case",
        "title": "Sample Case",
        "revision": 1,
        "units": "mm",
        "model": {"source": "model.py", "entrypoint": "build_model"},
        "parameter_values": "parameters.json",
        "parameter_schema": "parameter_schema.json",
        "references": "references.json",
        "validation": "validation.json",
        "revision_index": "revisions/index.json",
    }
    _write_json(root / "project.json", manifest)
    _write_json(root / "references.json", {"references": []})

    _write_json(
        root / "validation.json",
        {
            "accepted_revision": 1,
            "source_hashes_sha256": {
                "model": _sha256(model),
                "parameters": _sha256(root / "parameters.json"),
                "parameter_schema": _sha256(root / "parameter_schema.json"),
            },
        },
    )
    return root


def test_load_project_happy_path(project: Path) -> None:
    loaded = data_layer.load_project(project)
    assert loaded.manifest["project_id"] == "sample_case"
    assert loaded.parameters == {"pcb_length": 85.0, "wall_thickness": 2.4}
    assert loaded.model_source == (project / "model.py").resolve()


def test_load_project_rejects_unknown_format(project: Path) -> None:
    manifest = json.loads((project / "project.json").read_text())
    manifest["format"] = "something_else"
    _write_json(project / "project.json", manifest)
    with pytest.raises(ValueError, match="Unsupported project format"):
        data_layer.load_project(project)


def test_load_project_rejects_unknown_schema_version(project: Path) -> None:
    manifest = json.loads((project / "project.json").read_text())
    manifest["schema_version"] = 2
    _write_json(project / "project.json", manifest)
    with pytest.raises(ValueError, match="schema version"):
        data_layer.load_project(project)


def test_load_project_missing_model_source(project: Path) -> None:
    (project / "model.py").unlink()
    with pytest.raises(FileNotFoundError):
        data_layer.load_project(project)


def test_parameter_catalog_resolves_refs_and_sorts(project: Path) -> None:
    catalog = data_layer.parameter_catalog(data_layer.load_project(project))
    assert [item["name"] for item in catalog] == ["pcb_length", "wall_thickness"]

    by_name = {item["name"]: item for item in catalog}
    assert by_name["wall_thickness"]["user_editable"] is True
    assert by_name["wall_thickness"]["unit"] == "mm"
    assert by_name["wall_thickness"]["control"] == "slider"
    assert by_name["wall_thickness"]["semantic_change"] is False

    assert by_name["pcb_length"]["user_editable"] is False
    assert by_name["pcb_length"]["lock_reason"] == "Controlled by reference hardware"


def test_project_status_clean(project: Path) -> None:
    status = data_layer.project_status(data_layer.load_project(project))
    assert status["dirty"] is False
    assert status["changed_sources"] == []


def test_project_status_dirty_after_edit(project: Path) -> None:
    data_layer.set_parameter(project, "wall_thickness", 3.0)
    status = data_layer.project_status(data_layer.load_project(project))
    assert status["dirty"] is True
    assert "parameters" in status["changed_sources"]


def test_set_parameter_persists_editable(project: Path) -> None:
    result = data_layer.set_parameter(project, "wall_thickness", 3.0)
    assert result["changed"] is True
    assert result["requires_rebuild"] is True
    assert result["requires_ai_review"] is False  # x-semantic-change is False
    assert json.loads((project / "parameters.json").read_text())["wall_thickness"] == 3.0


def test_set_parameter_rejects_locked(project: Path) -> None:
    with pytest.raises(PermissionError, match="reference hardware"):
        data_layer.set_parameter(project, "pcb_length", 85.2)


def test_set_parameter_allow_locked_override(project: Path) -> None:
    result = data_layer.set_parameter(project, "pcb_length", 85.2, allow_locked=True)
    assert result["changed"] is True
    assert result["requires_ai_review"] is True  # locked defs are semantic


def test_set_parameter_unknown_key(project: Path) -> None:
    with pytest.raises(KeyError):
        data_layer.set_parameter(project, "does_not_exist", 1.0)


def test_set_parameter_out_of_range(project: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        data_layer.set_parameter(project, "wall_thickness", 99.0)
    # The rejected write must not have mutated the file.
    assert json.loads((project / "parameters.json").read_text())["wall_thickness"] == 2.4


def test_set_parameter_same_value_is_noop(project: Path) -> None:
    result = data_layer.set_parameter(project, "wall_thickness", 2.4)
    assert result["changed"] is False
    assert result["requires_rebuild"] is False
