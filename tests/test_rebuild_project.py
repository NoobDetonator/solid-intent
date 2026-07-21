"""Unit tests for rebuild comparison helpers (no OpenCASCADE required)."""

from __future__ import annotations

import rebuild_project as rebuild


def test_geometry_delta_computes_volume_and_topology():
    previous = {
        "volume_mm3": 100.0,
        "bbox_mm": [10.0, 20.0, 30.0],
        "topology": {"faces": 10, "edges": 20, "vertices": 12},
        "validate": "PASS",
    }
    current = {
        "volume_mm3": 110.5,
        "bbox_mm": [11.0, 20.0, 30.0],
        "topology": {"faces": 10, "edges": 22, "vertices": 12},
        "validate": "PASS",
    }
    delta = rebuild.geometry_delta(previous, current)
    assert delta["volume_mm3"] == 10.5
    assert delta["bbox_mm"] == [1.0, 0.0, 0.0]
    assert delta["topology_delta"] == {"faces": 0, "edges": 2, "vertices": 0}


def test_compare_validation_flags_interference_and_failures():
    previous = {
        "geometry": {
            "base": {
                "volume_mm3": 100.0,
                "bbox_mm": [1.0, 1.0, 1.0],
                "topology": {"faces": 1, "edges": 1, "vertices": 1},
            }
        }
    }
    candidate = {
        "geometry": {
            "base": {
                "validate": "FAIL",
                "single_solid": True,
                "brep_valid": True,
                "volume_mm3": 100.0,
                "bbox_mm": [1.0, 1.0, 1.0],
                "topology": {"faces": 1, "edges": 1, "vertices": 1},
            }
        },
        "interfaces": {
            "base_to_assembled_lid": {
                "status": "interfering",
                "intersection_volume_mm3": 2.0,
            }
        },
    }
    comparison = rebuild.compare_validation(previous, candidate)
    assert comparison["ok"] is False
    assert comparison["failed_bodies"] == ["base"]
    assert comparison["interfering_interfaces"] == ["base_to_assembled_lid"]


def test_compare_validation_passes_clean_candidate():
    candidate = {
        "geometry": {
            "base": {
                "validate": "PASS",
                "single_solid": True,
                "brep_valid": True,
                "volume_mm3": 100.0,
                "bbox_mm": [1.0, 1.0, 1.0],
                "topology": {"faces": 1, "edges": 1, "vertices": 1},
            }
        },
        "interfaces": {
            "base_to_pcb_proxy": {
                "status": "touching",
                "intersection_volume_mm3": 0.0,
            }
        },
    }
    comparison = rebuild.compare_validation(None, candidate)
    assert comparison["ok"] is True
    assert comparison["failed_bodies"] == []
    assert comparison["interfering_interfaces"] == []
