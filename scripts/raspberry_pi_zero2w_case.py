"""Parametric Raspberry Pi Zero 2 W snap-fit enclosure.

Two-piece FDM case driven by `projects/raspberry_pi_zero2w_case/parameters.json`.
Board envelope and connector centre-lines follow the official Zero 2 W
mechanical drawing (65 x 30 mm PCB, 3.5 mm mount offsets, dual micro-USB +
mini-HDMI on the long edge opposite the GPIO header).

Coordinate system (board mid-plane origin):
  +X along the long board axis (microSD on -X, CSI on +X)
  +Y toward the GPIO header
  +Z up, top copper facing +Z

Snap architecture (clearance fit when fully seated):
  - Base: external undercut groove near the rim (walls stay flush — no
    protruding ridge that forces an oversized lid)
  - Lid: close-fitting overhanging skirt (base OD + fit only), with inward
    beads that seat in the groove. Beads are Z-clear of the groove floor in
    the assembled pose so BREP fit checks stay non-interfering; the skirt
    flexes during insertion
  - Locating pins engage the four PCB mounting holes
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Cylinder,
    Locations,
    Mode,
    add,
    fillet,
)

from enclosure_common import (
    lid_print_orientation,
    mount_locations,
    require_numeric,
    require_positive,
    validate_mount_pitches,
)

REQUIRED_PARAMETERS = (
    "pcb_length",
    "pcb_width",
    "pcb_thickness",
    "pcb_corner_radius",
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
    "locating_pin_diameter",
    "lid_top_thickness",
    "lid_skirt_depth",
    "lid_skirt_thickness",
    "lid_fit_clearance",
    "snap_ridge_height",
    "snap_ridge_depth",
    "snap_bead_depth",
    "power_usb_center_x",
    "data_usb_center_x",
    "usb_opening_width",
    "usb_opening_height",
    "usb_opening_z",
    "hdmi_center_x",
    "hdmi_opening_width",
    "hdmi_opening_height",
    "hdmi_opening_z",
    "sd_opening_width",
    "sd_opening_height",
    "sd_opening_z",
    "csi_opening_width",
    "csi_opening_height",
    "csi_opening_z",
    "gpio_slot_center_x",
    "gpio_slot_center_y",
    "gpio_slot_length",
    "gpio_slot_width",
    "soc_center_x",
    "soc_center_y",
    "vent_hole_diameter",
    "vent_pitch",
)

# Short lip above the ridge so beads can seat under it.
_SNAP_LIP = 0.9
_SNAP_Z_CLEARANCE = 0.15


def validate_parameter_contract(parameters):
    """Reject incomplete or non-numeric project parameter mappings."""
    require_numeric(parameters, REQUIRED_PARAMETERS)
    require_positive(
        parameters,
        (
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
            "locating_pin_diameter",
            "lid_top_thickness",
            "lid_skirt_depth",
            "lid_skirt_thickness",
            "snap_ridge_height",
            "snap_ridge_depth",
            "snap_bead_depth",
            "usb_opening_width",
            "usb_opening_height",
            "hdmi_opening_width",
            "hdmi_opening_height",
            "sd_opening_width",
            "sd_opening_height",
            "csi_opening_width",
            "csi_opening_height",
            "gpio_slot_length",
            "gpio_slot_width",
            "vent_hole_diameter",
            "vent_pitch",
        ),
    )
    validate_mount_pitches(parameters)
    if parameters["lid_fit_clearance"] < 0:
        raise ValueError("lid_fit_clearance cannot be negative")
    if parameters["locating_pin_diameter"] >= parameters["mount_hole_diameter"]:
        raise ValueError("locating_pin_diameter must be smaller than mount_hole_diameter")


def _outer_size(parameters) -> tuple[float, float]:
    length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    return length, width


def _inner_size(parameters) -> tuple[float, float]:
    length = parameters["pcb_length"] + 2 * parameters["pcb_clearance"]
    width = parameters["pcb_width"] + 2 * parameters["pcb_clearance"]
    return length, width


def _ridge_z(parameters) -> float:
    return parameters["base_height"] - _SNAP_LIP - parameters["snap_ridge_height"]


def _south_ports(parameters):
    """Ports on the micro-USB / mini-HDMI edge (Y-)."""
    return (
        (
            parameters["power_usb_center_x"],
            parameters["usb_opening_width"],
            parameters["usb_opening_z"],
            parameters["usb_opening_height"],
        ),
        (
            parameters["data_usb_center_x"],
            parameters["usb_opening_width"],
            parameters["usb_opening_z"],
            parameters["usb_opening_height"],
        ),
        (
            parameters["hdmi_center_x"],
            parameters["hdmi_opening_width"],
            parameters["hdmi_opening_z"],
            parameters["hdmi_opening_height"],
        ),
    )


def build_base(parameters):
    """Build the snap-groove base with locating pins and port openings."""
    outer_length, outer_width = _outer_size(parameters)
    inner_length, inner_width = _inner_size(parameters)
    groove_depth = parameters["snap_ridge_depth"]
    groove_height = parameters["snap_ridge_height"]
    groove_z = _ridge_z(parameters)

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

    with BuildPart() as groove_builder:
        add(shell_builder.part)
        # External undercut ring: cut only the outer skin of the wall band.
        with BuildPart() as groove_cutter:
            with Locations((0, 0, groove_z)):
                Box(
                    outer_length + 2.0,
                    outer_width + 2.0,
                    groove_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                Box(
                    outer_length - 2.0 * groove_depth,
                    outer_width - 2.0 * groove_depth,
                    groove_height + 0.2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        add(groove_cutter.part, mode=Mode.SUBTRACT)

    with BuildPart() as mount_builder:
        add(groove_builder.part)
        with Locations(
            *(
                (x, y, parameters["floor_thickness"] - 0.2)
                for x, y in mount_locations(parameters)
            )
        ):
            Cylinder(
                parameters["standoff_diameter"] / 2,
                parameters["standoff_height"] + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        pin_z = parameters["floor_thickness"] + parameters["standoff_height"] - 0.15
        with Locations(*((x, y, pin_z) for x, y in mount_locations(parameters))):
            Cylinder(
                parameters["locating_pin_diameter"] / 2,
                parameters["pcb_thickness"] + 1.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    with BuildPart() as port_builder:
        add(mount_builder.part)
        for x_center, width, z_bottom, height in _south_ports(parameters):
            with Locations((x_center, -outer_width / 2, z_bottom)):
                Box(
                    width,
                    parameters["wall_thickness"] + 4.0,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with Locations((-outer_length / 2, 0.0, parameters["sd_opening_z"])):
            Box(
                parameters["wall_thickness"] + 4.0,
                parameters["sd_opening_width"],
                parameters["sd_opening_height"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        with Locations((outer_length / 2, 0.0, parameters["csi_opening_z"])):
            Box(
                parameters["wall_thickness"] + 4.0,
                parameters["csi_opening_width"],
                parameters["csi_opening_height"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as vent_builder:
        add(port_builder.part)
        for x in (-18.0, -6.0, 6.0, 18.0):
            with Locations((x, 0, -0.5)):
                Box(
                    2.4,
                    16.0,
                    parameters["floor_thickness"] + 1.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    return vent_builder.part


def build_lid(parameters):
    """Build an overhanging snap lid with GPIO access and SoC vents.

    Local coordinates: top plate at z >= 0; skirt hangs to negative Z so
    ``lid.moved((0, 0, base_height))`` telescopes over the base rim.
    """
    outer_length, outer_width = _outer_size(parameters)
    fit = parameters["lid_fit_clearance"]
    # Close fit over the flush base OD (same pattern as the Pi 4/5 lids).
    skirt_inner_length = outer_length + 2 * fit
    skirt_inner_width = outer_width + 2 * fit
    skirt_outer_length = skirt_inner_length + 2 * parameters["lid_skirt_thickness"]
    skirt_outer_width = skirt_inner_width + 2 * parameters["lid_skirt_thickness"]
    skirt_depth = parameters["lid_skirt_depth"]
    top_th = parameters["lid_top_thickness"]
    bead_depth = parameters["snap_bead_depth"]
    # Beads are slightly shorter than the groove so they seat with Z clearance.
    bead_height = max(0.4, parameters["snap_ridge_height"] - 2.0 * _SNAP_Z_CLEARANCE)

    # Centre beads in the base groove (world), expressed in lid-local Z.
    groove_z = _ridge_z(parameters)
    groove_mid = groove_z + parameters["snap_ridge_height"] / 2.0
    bead_z = groove_mid - parameters["base_height"] - bead_height / 2.0

    with BuildPart() as lid_builder:
        Box(
            skirt_outer_length,
            skirt_outer_width,
            top_th,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        fillet(
            lid_builder.edges().filter_by(Axis.Z),
            radius=min(parameters["outer_corner_radius"] + fit, 5.0),
        )
        with Locations((0, 0, -skirt_depth)):
            Box(
                skirt_outer_length,
                skirt_outer_width,
                skirt_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with Locations((0, 0, -skirt_depth - 0.05)):
            Box(
                skirt_inner_length,
                skirt_inner_width,
                skirt_depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as bead_builder:
        add(lid_builder.part)
        span_x = skirt_inner_length * 0.40
        span_y = skirt_inner_width * 0.40
        # +/- X walls — beads reach into the base undercut groove
        for sx in (+1.0, -1.0):
            with Locations(
                (
                    sx * (skirt_inner_length / 2.0 - bead_depth / 2.0),
                    0,
                    bead_z,
                )
            ):
                Box(
                    bead_depth,
                    span_y,
                    bead_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        # +/- Y walls
        for sy in (+1.0, -1.0):
            with Locations(
                (
                    0,
                    sy * (skirt_inner_width / 2.0 - bead_depth / 2.0),
                    bead_z,
                )
            ):
                Box(
                    span_x,
                    bead_depth,
                    bead_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

    with BuildPart() as feature_builder:
        add(bead_builder.part)
        with Locations(
            (
                parameters["gpio_slot_center_x"],
                parameters["gpio_slot_center_y"],
                -0.5,
            )
        ):
            Box(
                parameters["gpio_slot_length"],
                parameters["gpio_slot_width"],
                top_th + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
        vent_r = parameters["vent_hole_diameter"] / 2
        pitch = parameters["vent_pitch"]
        centres = [(0, 0), (-pitch, 0), (pitch, 0), (0, -pitch), (0, pitch)]
        with Locations(
            *(
                (
                    parameters["soc_center_x"] + dx,
                    parameters["soc_center_y"] + dy,
                    -0.5,
                )
                for dx, dy in centres
            )
        ):
            Cylinder(
                vent_r,
                top_th + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return feature_builder.part


def build_board_proxy(parameters):
    """Lightweight PCB fit-check interface (holes for locating pins)."""
    board_z = parameters["floor_thickness"] + parameters["standoff_height"]
    with BuildPart() as pcb_builder:
        with Locations((0, 0, board_z)):
            Box(
                parameters["pcb_length"],
                parameters["pcb_width"],
                parameters["pcb_thickness"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with Locations(
            *((x, y, board_z - 0.2) for x, y in mount_locations(parameters))
        ):
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
    lid_print = lid_print_orientation(lid, parameters)

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


def build_case(parameters):
    """Compatibility tuple for drawing and export scripts."""
    model = build_model(parameters)
    return (
        model["bodies"]["base"],
        model["bodies"]["lid"],
        model["bodies"]["lid_print"],
        model["interfaces"]["pcb_proxy"],
    )
