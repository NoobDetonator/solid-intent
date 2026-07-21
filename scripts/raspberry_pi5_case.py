"""Parametric two-piece Raspberry Pi 5 prototype enclosure project model.

The geometry is driven by an explicit parameter mapping. The canonical values
live in ``projects/raspberry_pi5_case/parameters.json``; this module contains
no independent dimensional defaults. All dimensions are millimetres.

The PCB envelope and mounting pattern come from the official Raspberry Pi 5
mechanical drawing. Connector windows are deliberately oversized for prototype
access; verify them against a physical board before production use.
"""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    add,
    fillet,
    mirror,
)


# Floor and lid vent patterns (shared with the dimensioned drawing callouts).
BASE_VENT_Y_POSITIONS = (-15.0, -9.0, -3.0, 3.0, 9.0, 15.0)
BASE_VENT_X = -7.0
LID_VENT_Y_POSITIONS = (-18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0)

REQUIRED_PARAMETERS = (
    "pcb_length",
    "pcb_width",
    "pcb_thickness",
    "mount_pitch_x",
    "mount_pitch_y",
    "mount_edge_offset",
    "mount_hole_diameter",
    "pcb_clearance",
    "wall_thickness",
    "floor_thickness",
    "base_height",
    "outer_corner_radius",
    "standoff_diameter",
    "standoff_height",
    "lid_top_thickness",
    "lid_skirt_depth",
    "lid_skirt_thickness",
    "lid_fit_clearance",
    "side_window_width",
    "side_window_height",
    "side_window_z",
    "end_window_width",
    "end_window_height",
    "end_window_z",
    "base_vent_length",
    "base_vent_width",
    "lid_vent_length",
    "lid_vent_width",
)


def validate_parameter_contract(parameters):
    """Reject incomplete or non-numeric project parameter mappings."""
    missing = [name for name in REQUIRED_PARAMETERS if name not in parameters]
    if missing:
        raise ValueError(f"Missing project parameters: {', '.join(missing)}")

    for name in REQUIRED_PARAMETERS:
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Parameter '{name}' must be numeric, got {type(value).__name__}")

    positive = (
        "pcb_length",
        "pcb_width",
        "pcb_thickness",
        "mount_pitch_x",
        "mount_pitch_y",
        "mount_hole_diameter",
        "wall_thickness",
        "floor_thickness",
        "base_height",
        "standoff_diameter",
        "standoff_height",
        "lid_top_thickness",
        "lid_skirt_depth",
        "lid_skirt_thickness",
        "side_window_width",
        "side_window_height",
        "end_window_width",
        "end_window_height",
        "base_vent_length",
        "base_vent_width",
        "lid_vent_length",
        "lid_vent_width",
    )
    invalid = [name for name in positive if parameters[name] <= 0]
    if invalid:
        raise ValueError(f"Parameters must be greater than zero: {', '.join(invalid)}")

    if parameters["mount_pitch_x"] >= parameters["pcb_length"]:
        raise ValueError("mount_pitch_x must be smaller than pcb_length")
    if parameters["mount_pitch_y"] >= parameters["pcb_width"]:
        raise ValueError("mount_pitch_y must be smaller than pcb_width")
    if parameters["lid_fit_clearance"] < 0:
        raise ValueError("lid_fit_clearance cannot be negative")


def _mount_locations(parameters):
    left = -parameters["pcb_length"] / 2 + parameters["mount_edge_offset"]
    right = left + parameters["mount_pitch_x"]
    bottom = -parameters["pcb_width"] / 2 + parameters["mount_edge_offset"]
    top = bottom + parameters["mount_pitch_y"]
    return ((left, bottom), (right, bottom), (left, top), (right, top))


def build_base(parameters):
    """Build the ventilated base with PCB standoffs and prototype windows."""
    outer_length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    outer_width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    inner_length = parameters["pcb_length"] + 2 * parameters["pcb_clearance"]
    inner_width = parameters["pcb_width"] + 2 * parameters["pcb_clearance"]

    with BuildPart() as shell_builder:
        Box(
            outer_length,
            outer_width,
            parameters["base_height"],
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        fillet(
            shell_builder.edges().filter_by(Axis.Z),
            radius=parameters["outer_corner_radius"],
        )
        with Locations((0, 0, parameters["floor_thickness"])):
            Box(
                inner_length,
                inner_width,
                parameters["base_height"] - parameters["floor_thickness"] + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as standoff_builder:
        add(shell_builder.part)
        with Locations(
            *((x, y, parameters["floor_thickness"] - 0.2) for x, y in _mount_locations(parameters))
        ):
            Cylinder(
                parameters["standoff_diameter"] / 2,
                parameters["standoff_height"] + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    with BuildPart() as mounting_builder:
        add(standoff_builder.part)
        with Locations(*((x, y, -1.0) for x, y in _mount_locations(parameters))):
            Cylinder(
                parameters["mount_hole_diameter"] / 2,
                parameters["floor_thickness"] + parameters["standoff_height"] + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as window_builder:
        add(mounting_builder.part)
        for y in (-outer_width / 2, outer_width / 2):
            with Locations((0, y, parameters["side_window_z"])):
                Box(
                    parameters["side_window_width"],
                    parameters["wall_thickness"] + 3.0,
                    parameters["side_window_height"],
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with Locations((-outer_length / 2, 0, parameters["end_window_z"])):
            Box(
                parameters["wall_thickness"] + 3.0,
                parameters["end_window_width"],
                parameters["end_window_height"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as base_builder:
        add(window_builder.part)
        with Locations(*((BASE_VENT_X, y, -1.0) for y in BASE_VENT_Y_POSITIONS)):
            Box(
                parameters["base_vent_length"],
                parameters["base_vent_width"],
                parameters["floor_thickness"] + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return base_builder.part


def build_lid(parameters):
    """Build a friction-fit lid with an internal skirt and top ventilation."""
    outer_length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    outer_width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    inner_length = parameters["pcb_length"] + 2 * parameters["pcb_clearance"]
    inner_width = parameters["pcb_width"] + 2 * parameters["pcb_clearance"]

    skirt_outer_length = inner_length - 2 * parameters["lid_fit_clearance"]
    skirt_outer_width = inner_width - 2 * parameters["lid_fit_clearance"]
    skirt_inner_length = skirt_outer_length - 2 * parameters["lid_skirt_thickness"]
    skirt_inner_width = skirt_outer_width - 2 * parameters["lid_skirt_thickness"]

    with BuildPart() as lid_builder:
        with Locations((0, 0, parameters["lid_skirt_depth"])):
            Box(
                outer_length,
                outer_width,
                parameters["lid_top_thickness"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        fillet(
            lid_builder.edges().filter_by(Axis.Z),
            radius=parameters["outer_corner_radius"],
        )
        Box(
            skirt_outer_length,
            skirt_outer_width,
            parameters["lid_skirt_depth"],
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Box(
            skirt_inner_length,
            skirt_inner_width,
            parameters["lid_skirt_depth"],
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

    with BuildPart() as lid_vent_builder:
        add(lid_builder.part)
        with Locations(
            *((0.0, y, parameters["lid_skirt_depth"] - 0.5) for y in LID_VENT_Y_POSITIONS)
        ):
            Box(
                parameters["lid_vent_length"],
                parameters["lid_vent_width"],
                parameters["lid_top_thickness"] + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return lid_vent_builder.part


def build_board_proxy(parameters):
    """Build the lightweight PCB fit-check interface body.

    ``mount_hole_diameter`` is the nominal PCB hole and is only consumed here,
    by the fit-check proxy.
    """
    board_z = parameters["floor_thickness"] + parameters["standoff_height"]
    with BuildPart() as pcb_builder:
        with Locations((0, 0, board_z)):
            Box(
                parameters["pcb_length"],
                parameters["pcb_width"],
                parameters["pcb_thickness"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with Locations(*((x, y, board_z - 0.2) for x, y in _mount_locations(parameters))):
            Cylinder(
                parameters["mount_hole_diameter"] / 2,
                parameters["pcb_thickness"] + 0.4,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return pcb_builder.part


def build_model(parameters):
    """Build named project bodies from the persisted parameter mapping."""
    validate_parameter_contract(parameters)
    base = build_base(parameters)
    lid = build_lid(parameters)
    pcb_proxy = build_board_proxy(parameters)

    lid_print = mirror(lid, about=Plane.XY)
    lid_print.move(
        Location((0, 0, parameters["lid_skirt_depth"] + parameters["lid_top_thickness"]))
    )

    return {
        "bodies": {
            "base": base,
            "lid": lid,
            "lid_print": lid_print,
        },
        "interfaces": {
            "pcb_proxy": pcb_proxy,
        },
    }
