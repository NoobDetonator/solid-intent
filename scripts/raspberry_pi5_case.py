"""Parametric two-piece Raspberry Pi 5 prototype enclosure project model.

The geometry is driven by an explicit parameter mapping. The canonical values
live in ``projects/raspberry_pi5_case/parameters.json``; this module contains
no independent dimensional defaults. All dimensions are millimetres.

PCB outline and mounting pattern come from the official Raspberry Pi 5
mechanical drawing. Connector opening centres/heights are taken from that
same approximate reference drawing (not a manufacturer STEP keep-out solid).
Active Cooler / fan clearance is not modelled — verify against physical
hardware before production use.
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
    board_z,
    inner_envelope,
    lid_print_orientation,
    mount_locations,
    outer_envelope,
    require_numeric,
    require_positive,
    validate_mount_pitches,
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
    "usb_c_center_x",
    "usb_c_opening_width",
    "usb_c_z",
    "usb_c_height",
    "micro_hdmi_0_center_x",
    "micro_hdmi_1_center_x",
    "micro_hdmi_opening_width",
    "micro_hdmi_z",
    "micro_hdmi_height",
    "usb_2_center_y",
    "usb_3_center_y",
    "usb_opening_width",
    "usb_z",
    "usb_height",
    "ethernet_center_y",
    "ethernet_opening_width",
    "ethernet_z",
    "ethernet_height",
    "microsd_center_y",
    "microsd_opening_width",
    "microsd_z",
    "microsd_height",
    "gpio_slot_center_x",
    "gpio_slot_center_y",
    "gpio_slot_length",
    "gpio_slot_width",
    "base_vent_length",
    "base_vent_width",
    "lid_vent_length",
    "lid_vent_width",
)


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
            "lid_top_thickness",
            "lid_skirt_depth",
            "lid_skirt_thickness",
            "usb_c_opening_width",
            "usb_c_height",
            "micro_hdmi_opening_width",
            "micro_hdmi_height",
            "usb_opening_width",
            "usb_height",
            "ethernet_opening_width",
            "ethernet_height",
            "microsd_opening_width",
            "microsd_height",
            "gpio_slot_length",
            "gpio_slot_width",
            "base_vent_length",
            "base_vent_width",
            "lid_vent_length",
            "lid_vent_width",
        ),
    )
    validate_mount_pitches(parameters)
    if parameters["lid_fit_clearance"] < 0:
        raise ValueError("lid_fit_clearance cannot be negative")


def _south_ports(parameters):
    """Power / video edge (−Y). Pi 5 has no 3.5 mm audio jack."""
    return (
        (
            parameters["usb_c_center_x"],
            parameters["usb_c_opening_width"],
            parameters["usb_c_z"],
            parameters["usb_c_height"],
        ),
        (
            parameters["micro_hdmi_0_center_x"],
            parameters["micro_hdmi_opening_width"],
            parameters["micro_hdmi_z"],
            parameters["micro_hdmi_height"],
        ),
        (
            parameters["micro_hdmi_1_center_x"],
            parameters["micro_hdmi_opening_width"],
            parameters["micro_hdmi_z"],
            parameters["micro_hdmi_height"],
        ),
    )


def _east_ports(parameters):
    return (
        (
            parameters["usb_2_center_y"],
            parameters["usb_opening_width"],
            parameters["usb_z"],
            parameters["usb_height"],
        ),
        (
            parameters["usb_3_center_y"],
            parameters["usb_opening_width"],
            parameters["usb_z"],
            parameters["usb_height"],
        ),
        (
            parameters["ethernet_center_y"],
            parameters["ethernet_opening_width"],
            parameters["ethernet_z"],
            parameters["ethernet_height"],
        ),
    )


def build_base(parameters):
    """Build the ventilated base with PCB standoffs and connector openings."""
    outer_length, outer_width = outer_envelope(parameters)
    inner_length, inner_width = inner_envelope(parameters)

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
            *((x, y, parameters["floor_thickness"] - 0.2) for x, y in mount_locations(parameters))
        ):
            Cylinder(
                parameters["standoff_diameter"] / 2,
                parameters["standoff_height"] + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    with BuildPart() as mounting_builder:
        add(standoff_builder.part)
        with Locations(*((x, y, -1.0) for x, y in mount_locations(parameters))):
            Cylinder(
                parameters["mount_hole_diameter"] / 2,
                parameters["floor_thickness"] + parameters["standoff_height"] + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as south_cut_builder:
        add(mounting_builder.part)
        for x_center, width, z_bottom, height in _south_ports(parameters):
            with Locations((x_center, -outer_width / 2, z_bottom)):
                Box(
                    width,
                    parameters["wall_thickness"] + 4.0,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    with BuildPart() as east_cut_builder:
        add(south_cut_builder.part)
        for y_center, width, z_bottom, height in _east_ports(parameters):
            with Locations((outer_length / 2, y_center, z_bottom)):
                Box(
                    parameters["wall_thickness"] + 4.0,
                    width,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    with BuildPart() as microsd_cut_builder:
        add(east_cut_builder.part)
        with Locations((-outer_length / 2, parameters["microsd_center_y"], parameters["microsd_z"])):
            Box(
                parameters["wall_thickness"] + 4.0,
                parameters["microsd_opening_width"],
                parameters["microsd_height"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as base_builder:
        add(microsd_cut_builder.part)
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
    """Build a friction-fit lid with GPIO access and top ventilation."""
    outer_length, outer_width = outer_envelope(parameters)
    inner_length, inner_width = inner_envelope(parameters)

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

    with BuildPart() as gpio_builder:
        add(lid_builder.part)
        with Locations(
            (
                parameters["gpio_slot_center_x"],
                parameters["gpio_slot_center_y"],
                parameters["lid_skirt_depth"] - 0.5,
            )
        ):
            Box(
                parameters["gpio_slot_length"],
                parameters["gpio_slot_width"],
                parameters["lid_top_thickness"] + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as lid_vent_builder:
        add(gpio_builder.part)
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
    """PCB + official-drawing connector keep-out envelopes for fit checks."""
    z0 = board_z(parameters)
    half_length = parameters["pcb_length"] / 2
    half_width = parameters["pcb_width"] / 2
    protrusion = parameters["pcb_clearance"] + parameters["wall_thickness"] + 0.5

    with BuildPart() as pcb_builder:
        with Locations((0, 0, z0)):
            Box(
                parameters["pcb_length"],
                parameters["pcb_width"],
                parameters["pcb_thickness"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with Locations(*((x, y, z0 - 0.2) for x, y in mount_locations(parameters))):
            Cylinder(
                parameters["mount_hole_diameter"] / 2,
                parameters["pcb_thickness"] + 0.4,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        for x_center, width, z_bottom, height in _south_ports(parameters):
            with Locations((x_center, -(half_width + protrusion / 2), z_bottom)):
                Box(
                    width,
                    protrusion,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

        for y_center, width, z_bottom, height in _east_ports(parameters):
            with Locations((half_length + protrusion / 2, y_center, z_bottom)):
                Box(
                    protrusion,
                    width,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

        with Locations(
            (
                -(half_length + protrusion / 2),
                parameters["microsd_center_y"],
                parameters["microsd_z"],
            )
        ):
            Box(
                protrusion,
                parameters["microsd_opening_width"],
                parameters["microsd_height"],
                align=(Align.CENTER, Align.CENTER, Align.MIN),
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
