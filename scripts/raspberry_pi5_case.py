"""Parametric two-piece Raspberry Pi 5 prototype enclosure.

Dimensions are in millimetres. The PCB envelope and mounting pattern are based
on the official Raspberry Pi 5 mechanical drawing. Connector openings are
deliberately oversized for prototype access; verify them against a physical
board before production use.
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


# PCB and mounting pattern
PCB_LENGTH = 85.0
PCB_WIDTH = 56.0
MOUNT_PITCH_X = 58.0
MOUNT_PITCH_Y = 49.0
MOUNT_LEFT_INSET = 3.5
MOUNT_BOTTOM_INSET = 3.5
MOUNT_HOLE_DIAMETER = 2.8

# Base
CASE_CLEARANCE = 1.2
WALL_THICKNESS = 2.4
FLOOR_THICKNESS = 2.4
BASE_HEIGHT = 22.0
CORNER_RADIUS = 3.0
STANDOFF_RADIUS = 3.2
STANDOFF_HEIGHT = 4.0

# Lid
LID_TOP_THICKNESS = 2.4
LID_SKIRT_DEPTH = 3.0
LID_FIT_CLEARANCE = 0.3
LID_SKIRT_THICKNESS = 2.0


def build_case():
    outer_length = PCB_LENGTH + 2 * (CASE_CLEARANCE + WALL_THICKNESS)
    outer_width = PCB_WIDTH + 2 * (CASE_CLEARANCE + WALL_THICKNESS)
    inner_length = PCB_LENGTH + 2 * CASE_CLEARANCE
    inner_width = PCB_WIDTH + 2 * CASE_CLEARANCE

    hole_x_left = -PCB_LENGTH / 2 + MOUNT_LEFT_INSET
    hole_x_right = hole_x_left + MOUNT_PITCH_X
    hole_y_bottom = -PCB_WIDTH / 2 + MOUNT_BOTTOM_INSET
    hole_y_top = hole_y_bottom + MOUNT_PITCH_Y
    mount_locations = [
        (hole_x_left, hole_y_bottom),
        (hole_x_right, hole_y_bottom),
        (hole_x_left, hole_y_top),
        (hole_x_right, hole_y_top),
    ]

    # Rounded tray with a retained floor.
    with BuildPart() as shell_builder:
        Box(
            outer_length,
            outer_width,
            BASE_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        fillet(shell_builder.edges().filter_by(Axis.Z), radius=CORNER_RADIUS)
        with Locations((0, 0, FLOOR_THICKNESS)):
            Box(
                inner_length,
                inner_width,
                BASE_HEIGHT - FLOOR_THICKNESS + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    # Integrated PCB standoffs.
    post_locations = [
        (x, y, FLOOR_THICKNESS - 0.2) for x, y in mount_locations
    ]
    with BuildPart() as post_builder:
        add(shell_builder.part)
        with Locations(*post_locations):
            Cylinder(
                STANDOFF_RADIUS,
                STANDOFF_HEIGHT + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    # Through holes for M2.5 board screws.
    hole_locations = [(x, y, -1.0) for x, y in mount_locations]
    with BuildPart() as mounting_builder:
        add(post_builder.part)
        with Locations(*hole_locations):
            Cylinder(
                MOUNT_HOLE_DIAMETER / 2,
                FLOOR_THICKNESS + STANDOFF_HEIGHT + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    # Oversized universal connector access windows.
    with BuildPart() as window_builder:
        add(mounting_builder.part)
        for y in (-outer_width / 2, outer_width / 2):
            with Locations((0, y, 7.0)):
                Box(
                    70.0,
                    WALL_THICKNESS + 3.0,
                    11.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with Locations((-outer_length / 2, 0, 3.0)):
            Box(
                WALL_THICKNESS + 3.0,
                26.0,
                7.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    # Bottom ventilation, offset away from the mounting posts.
    vent_locations = [(-7.0, y, -1.0) for y in (-15, -9, -3, 3, 9, 15)]
    with BuildPart() as base_builder:
        add(window_builder.part)
        with Locations(*vent_locations):
            Box(
                32.0,
                3.0,
                FLOOR_THICKNESS + 2.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    # Friction-fit lid with an internal skirt.
    skirt_outer_length = inner_length - 2 * LID_FIT_CLEARANCE
    skirt_outer_width = inner_width - 2 * LID_FIT_CLEARANCE
    skirt_inner_length = skirt_outer_length - 2 * LID_SKIRT_THICKNESS
    skirt_inner_width = skirt_outer_width - 2 * LID_SKIRT_THICKNESS

    with BuildPart() as lid_builder:
        with Locations((0, 0, LID_SKIRT_DEPTH)):
            Box(
                outer_length,
                outer_width,
                LID_TOP_THICKNESS,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        fillet(lid_builder.edges().filter_by(Axis.Z), radius=CORNER_RADIUS)
        Box(
            skirt_outer_length,
            skirt_outer_width,
            LID_SKIRT_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Box(
            skirt_inner_length,
            skirt_inner_width,
            LID_SKIRT_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

    # Top ventilation.
    lid_vent_locations = [
        (0.0, y, LID_SKIRT_DEPTH - 0.5)
        for y in (-18, -12, -6, 0, 6, 12, 18)
    ]
    with BuildPart() as lid_vent_builder:
        add(lid_builder.part)
        with Locations(*lid_vent_locations):
            Box(
                55.0,
                3.0,
                LID_TOP_THICKNESS + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    base = base_builder.part
    lid = lid_vent_builder.part

    # Reflection places the decorative outer face on the print bed.
    lid_print = mirror(lid, about=Plane.XY)
    lid_print.move(Location((0, 0, LID_SKIRT_DEPTH + LID_TOP_THICKNESS)))

    return base, lid, lid_print


if __name__ == "__main__":
    base, lid, lid_print = build_case()
