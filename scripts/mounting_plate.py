"""Parametric slotted mounting plate.

A deliberately small non-enclosure project used to prove the persistent AI CAD
project contract outside Raspberry Pi cases. All dimensions are millimetres.
"""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Cylinder,
    Locations,
    Mode,
    fillet,
)


REQUIRED_PARAMETERS = (
    "plate_length",
    "plate_width",
    "plate_thickness",
    "corner_radius",
    "slot_length",
    "slot_width",
    "slot_pitch_x",
    "edge_offset_x",
    "edge_offset_y",
)


def validate_parameter_contract(parameters):
    missing = [name for name in REQUIRED_PARAMETERS if name not in parameters]
    if missing:
        raise ValueError(f"Missing project parameters: {', '.join(missing)}")
    for name in REQUIRED_PARAMETERS:
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Parameter '{name}' must be numeric, got {type(value).__name__}")
        if value <= 0:
            raise ValueError(f"Parameter '{name}' must be greater than zero")
    if parameters["slot_length"] <= parameters["slot_width"]:
        raise ValueError("slot_length must be greater than slot_width")
    if parameters["corner_radius"] * 2 >= min(parameters["plate_length"], parameters["plate_width"]):
        raise ValueError("corner_radius is too large for the plate envelope")


def _slot_centers(parameters):
    left = -parameters["plate_length"] / 2 + parameters["edge_offset_x"]
    right = left + parameters["slot_pitch_x"]
    y = -parameters["plate_width"] / 2 + parameters["edge_offset_y"]
    return ((left, y), (right, y))


def build_plate(parameters):
    """Build a rectangular plate with two rounded slots."""
    slot_span = parameters["slot_length"] - parameters["slot_width"]
    half = slot_span / 2
    radius = parameters["slot_width"] / 2
    thickness = parameters["plate_thickness"] + 1.0

    with BuildPart() as plate:
        Box(
            parameters["plate_length"],
            parameters["plate_width"],
            parameters["plate_thickness"],
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        fillet(plate.edges().filter_by(Axis.Z), radius=parameters["corner_radius"])
        for x, y in _slot_centers(parameters):
            with Locations((x, y, -0.5)):
                Box(
                    slot_span,
                    parameters["slot_width"],
                    thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
            with Locations(((x - half, y, -0.5), (x + half, y, -0.5))):
                Cylinder(
                    radius,
                    thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
    return plate.part


def build_model(parameters):
    validate_parameter_contract(parameters)
    return {"bodies": {"plate": build_plate(parameters)}, "interfaces": {}}
