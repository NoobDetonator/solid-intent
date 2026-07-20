"""Parametric Raspberry Pi 4 Model B enclosure project model.

The geometry is driven by an explicit parameter mapping. The canonical values
live in `projects/raspberry_pi4_case/parameters.json`; this module contains no
independent dimensional defaults. All dimensions are millimetres.
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
    "screw_clearance_diameter",
    "lid_top_thickness",
    "lid_skirt_depth",
    "lid_skirt_thickness",
    "lid_fit_clearance",
    "usb_c_center_x",
    "usb_c_opening_width",
    "micro_hdmi_0_center_x",
    "micro_hdmi_1_center_x",
    "micro_hdmi_opening_width",
    "audio_center_x",
    "audio_opening_width",
    "usb_2_center_y",
    "usb_3_center_y",
    "usb_opening_width",
    "ethernet_center_y",
    "ethernet_opening_width",
    "microsd_center_y",
    "microsd_opening_width",
    "gpio_slot_center_x",
    "gpio_slot_center_y",
    "gpio_slot_length",
    "gpio_slot_width",
    "fan_center_x",
    "fan_center_y",
    "fan_hole_pitch",
    "fan_screw_diameter",
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
        "screw_clearance_diameter",
        "lid_top_thickness",
        "lid_skirt_depth",
        "lid_skirt_thickness",
        "usb_c_opening_width",
        "micro_hdmi_opening_width",
        "audio_opening_width",
        "usb_opening_width",
        "ethernet_opening_width",
        "microsd_opening_width",
        "gpio_slot_length",
        "gpio_slot_width",
        "fan_hole_pitch",
        "fan_screw_diameter",
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


def _south_ports(parameters):
    return (
        (
            "usb_c",
            parameters["usb_c_center_x"],
            parameters["usb_c_opening_width"],
            5.2,
            6.0,
        ),
        (
            "micro_hdmi_0",
            parameters["micro_hdmi_0_center_x"],
            parameters["micro_hdmi_opening_width"],
            5.4,
            5.8,
        ),
        (
            "micro_hdmi_1",
            parameters["micro_hdmi_1_center_x"],
            parameters["micro_hdmi_opening_width"],
            5.4,
            5.8,
        ),
        (
            "audio",
            parameters["audio_center_x"],
            parameters["audio_opening_width"],
            5.2,
            8.2,
        ),
    )


def _east_ports(parameters):
    return (
        (
            "usb_2",
            parameters["usb_2_center_y"],
            parameters["usb_opening_width"],
            5.4,
            17.4,
        ),
        (
            "usb_3",
            parameters["usb_3_center_y"],
            parameters["usb_opening_width"],
            5.4,
            17.4,
        ),
        (
            "ethernet",
            parameters["ethernet_center_y"],
            parameters["ethernet_opening_width"],
            5.4,
            15.2,
        ),
    )


def build_base(parameters):
    """Build the ventilated base with PCB standoffs and port openings."""
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
            *(
                (x, y, parameters["floor_thickness"] - 0.2)
                for x, y in _mount_locations(parameters)
            )
        ):
            Cylinder(
                parameters["standoff_diameter"] / 2,
                parameters["standoff_height"] + 0.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    with BuildPart() as mounting_builder:
        add(standoff_builder.part)
        with Locations(
            *((x, y, -0.5) for x, y in _mount_locations(parameters))
        ):
            Cylinder(
                parameters["screw_clearance_diameter"] / 2,
                parameters["floor_thickness"]
                + parameters["standoff_height"]
                + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    with BuildPart() as south_cut_builder:
        add(mounting_builder.part)
        for _, x_center, width, z_bottom, height in _south_ports(parameters):
            with Locations((x_center, -outer_width / 2, z_bottom)):
                Box(
                    width,
                    parameters["wall_thickness"] + 2.0,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    with BuildPart() as east_cut_builder:
        add(south_cut_builder.part)
        for _, y_center, width, z_bottom, height in _east_ports(parameters):
            with Locations((outer_length / 2, y_center, z_bottom)):
                Box(
                    parameters["wall_thickness"] + 2.0,
                    width,
                    height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

    with BuildPart() as microsd_cut_builder:
        add(east_cut_builder.part)
        with Locations(
            (
                -outer_length / 2,
                parameters["microsd_center_y"],
                2.6,
            )
        ):
            Box(
                parameters["wall_thickness"] + 2.0,
                parameters["microsd_opening_width"],
                5.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    vent_x_positions = (-20.0, -14.0, -8.0, -2.0, 4.0, 10.0, 16.0)
    with BuildPart() as base_builder:
        add(microsd_cut_builder.part)
        with Locations(*((x, 0, -0.5) for x in vent_x_positions)):
            Box(
                3.0,
                28.0,
                parameters["floor_thickness"] + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return base_builder.part


def build_lid(parameters):
    """Build an external cap lid with GPIO and 30 mm fan interfaces."""
    base_outer_length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    base_outer_width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    skirt_inner_length = base_outer_length + 2 * parameters["lid_fit_clearance"]
    skirt_inner_width = base_outer_width + 2 * parameters["lid_fit_clearance"]
    skirt_outer_length = skirt_inner_length + 2 * parameters["lid_skirt_thickness"]
    skirt_outer_width = skirt_inner_width + 2 * parameters["lid_skirt_thickness"]

    with BuildPart() as lid_builder:
        with Locations((0, 0, parameters["lid_skirt_depth"])):
            Box(
                skirt_outer_length,
                skirt_outer_width,
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

    fan_slots = (
        (-12.0, 12.0),
        (-8.0, 22.0),
        (-4.0, 27.0),
        (0.0, 28.0),
        (4.0, 27.0),
        (8.0, 22.0),
        (12.0, 12.0),
    )
    with BuildPart() as fan_builder:
        add(gpio_builder.part)
        for y_offset, slot_length in fan_slots:
            with Locations(
                (
                    parameters["fan_center_x"],
                    parameters["fan_center_y"] + y_offset,
                    parameters["lid_skirt_depth"] - 0.5,
                )
            ):
                Box(
                    slot_length,
                    2.6,
                    parameters["lid_top_thickness"] + 1.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        with Locations(
            *(
                (
                    parameters["fan_center_x"] + dx,
                    parameters["fan_center_y"] + dy,
                    parameters["lid_skirt_depth"] - 0.5,
                )
                for dx in (
                    -parameters["fan_hole_pitch"] / 2,
                    parameters["fan_hole_pitch"] / 2,
                )
                for dy in (
                    -parameters["fan_hole_pitch"] / 2,
                    parameters["fan_hole_pitch"] / 2,
                )
            )
        ):
            Cylinder(
                parameters["fan_screw_diameter"] / 2,
                parameters["lid_top_thickness"] + 1.0,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return fan_builder.part


def build_board_proxy(parameters):
    """Build the lightweight PCB fit-check interface body."""
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
            *(
                (x, y, board_z - 0.2)
                for x, y in _mount_locations(parameters)
            )
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

    lid_print = mirror(lid, about=Plane.XY)
    lid_print.move(
        Location(
            (
                0,
                0,
                parameters["lid_skirt_depth"] + parameters["lid_top_thickness"],
            )
        )
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


def build_case(parameters):
    """Compatibility tuple for drawing and export scripts."""
    model = build_model(parameters)
    return (
        model["bodies"]["base"],
        model["bodies"]["lid"],
        model["bodies"]["lid_print"],
        model["interfaces"]["pcb_proxy"],
    )
