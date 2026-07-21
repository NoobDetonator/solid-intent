"""Shared helpers for Raspberry Pi enclosure project models.

Keeps mount-pattern math and print-orientation transforms identical across
Pi 4 / Pi 5 scripts so board revisions cannot silently diverge on those
contracts.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence


def mount_locations(parameters: dict[str, Any]) -> tuple[tuple[float, float], ...]:
    """Return the four PCB mounting-hole centres (board-centred XY)."""
    left = -parameters["pcb_length"] / 2 + parameters["mount_edge_offset"]
    right = left + parameters["mount_pitch_x"]
    bottom = -parameters["pcb_width"] / 2 + parameters["mount_edge_offset"]
    top = bottom + parameters["mount_pitch_y"]
    return ((left, bottom), (right, bottom), (left, top), (right, top))


def outer_envelope(parameters: dict[str, Any]) -> tuple[float, float]:
    """Return outer shell length/width including clearance and walls."""
    length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    return length, width


def inner_envelope(parameters: dict[str, Any]) -> tuple[float, float]:
    """Return cavity length/width (PCB plus edge clearance)."""
    length = parameters["pcb_length"] + 2 * parameters["pcb_clearance"]
    width = parameters["pcb_width"] + 2 * parameters["pcb_clearance"]
    return length, width


def board_z(parameters: dict[str, Any]) -> float:
    """Z of the PCB bottom face above the enclosure origin."""
    return parameters["floor_thickness"] + parameters["standoff_height"]


def require_numeric(parameters: dict[str, Any], names: Iterable[str]) -> None:
    missing = [name for name in names if name not in parameters]
    if missing:
        raise ValueError(f"Missing project parameters: {', '.join(missing)}")
    for name in names:
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Parameter '{name}' must be numeric, got {type(value).__name__}")


def require_positive(parameters: dict[str, Any], names: Sequence[str]) -> None:
    invalid = [name for name in names if parameters[name] <= 0]
    if invalid:
        raise ValueError(f"Parameters must be greater than zero: {', '.join(invalid)}")


def validate_mount_pitches(parameters: dict[str, Any]) -> None:
    if parameters["mount_pitch_x"] >= parameters["pcb_length"]:
        raise ValueError("mount_pitch_x must be smaller than pcb_length")
    if parameters["mount_pitch_y"] >= parameters["pcb_width"]:
        raise ValueError("mount_pitch_y must be smaller than pcb_width")


def lid_print_orientation(lid: Any, parameters: dict[str, Any]) -> Any:
    """Mirror the assembled lid into the preferred FDM print orientation."""
    from build123d import Location, Plane, mirror

    printed = mirror(lid, about=Plane.XY)
    printed.move(
        Location((0, 0, parameters["lid_skirt_depth"] + parameters["lid_top_thickness"]))
    )
    return printed
