"""Unit tests for shared enclosure helpers."""

from __future__ import annotations

import enclosure_common as common


def test_mount_locations_are_symmetric():
    parameters = {
        "pcb_length": 85.0,
        "pcb_width": 56.0,
        "mount_edge_offset": 3.5,
        "mount_pitch_x": 58.0,
        "mount_pitch_y": 49.0,
    }
    points = common.mount_locations(parameters)
    assert len(points) == 4
    xs = sorted({round(x, 3) for x, _ in points})
    ys = sorted({round(y, 3) for _, y in points})
    assert xs == [-39.0, 19.0]
    assert ys == [-24.5, 24.5]


def test_outer_envelope_includes_clearance_and_walls():
    length, width = common.outer_envelope(
        {
            "pcb_length": 85.0,
            "pcb_width": 56.0,
            "pcb_clearance": 1.2,
            "wall_thickness": 2.4,
        }
    )
    assert length == 85.0 + 2 * (1.2 + 2.4)
    assert width == 56.0 + 2 * (1.2 + 2.4)
