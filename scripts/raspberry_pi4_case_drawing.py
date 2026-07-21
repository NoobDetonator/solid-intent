"""Generate the dimensioned Raspberry Pi 4 enclosure drawing.

Run from the project root (or via ``scripts/export_artifacts.py``). Writes an
A3 SVG, DXF, and ``.dims.json`` annotation sidecar under ``drawings/``.
"""

from json import load
from pathlib import Path

from build123d import (
    Align,
    Color,
    Compound,
    ExportDXF,
    ExportSVG,
    LineType,
    Location,
    Rectangle,
)
from build123d_drafting import (
    Dimension,
    Leader,
    Note,
    TitleBlock,
    annotate,
    draft_preset,
    lint_drawing,
    set_page,
)

from raspberry_pi4_case import (
    BASE_VENT_LENGTH,
    BASE_VENT_WIDTH,
    BASE_VENT_X_POSITIONS,
    build_case,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETER_PATH = (
    PROJECT_ROOT / "projects" / "raspberry_pi4_case" / "parameters.json"
)
PAGE_WIDTH = 420.0
PAGE_HEIGHT = 297.0
DRAWING_SCALE = 1.0
SVG_PATH = str(PROJECT_ROOT / "drawings" / "raspberry_pi4_case_dimensioned.svg")
DXF_PATH = str(PROJECT_ROOT / "drawings" / "raspberry_pi4_case_dimensioned.dxf")
DIMS_PATH = str(PROJECT_ROOT / "drawings" / "raspberry_pi4_case_dimensioned.dims.json")


def _jsonable(value):
    """Convert drafting metadata into plain JSON values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "X") and hasattr(value, "Y"):
        return [float(value.X), float(value.Y)]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _annotation_record(name: str, item) -> dict:
    record = {"type": type(item).__name__}
    label = getattr(item, "label", None)
    if label is not None:
        record["label_str"] = str(label)
    measured = getattr(item, "measured_length", None)
    if measured is not None:
        record["measured_length"] = float(measured)
    for field in ("label_bbox", "dim_level_y", "segments"):
        if hasattr(item, field):
            record[field] = _jsonable(getattr(item, field))
    return record


def _write_dims_sidecar(named_annotations: list[tuple[str, object]]) -> None:
    from json import dump

    payload = {name: _annotation_record(name, item) for name, item in named_annotations}
    with open(DIMS_PATH, "w", encoding="utf-8") as handle:
        dump(payload, handle, indent=2)
        handle.write("\n")


def load_project_parameters():
    """Load the current persisted project parameter values."""
    with PARAMETER_PATH.open("r", encoding="utf-8") as parameter_file:
        return load(parameter_file)


def dimension_label(value):
    """Format a millimetre value consistently for the drawing."""
    return f"{value:.1f}"


def project_view(shape, camera, up, look_at, position):
    """Project and position visible and hidden line compounds."""
    visible, hidden = shape.project_to_viewport(camera, up, look_at)
    placed_visible = Compound(children=list(visible)).locate(
        Location((position[0], position[1], 0))
    )
    placed_hidden = (
        Compound(children=list(hidden)).locate(
            Location((position[0], position[1], 0))
        )
        if hidden
        else None
    )
    return placed_visible, placed_hidden


def generate_drawing(parameters=None):
    """Generate the combined A3 base-and-lid engineering drawing."""
    if parameters is None:
        parameters = load_project_parameters()

    base, lid, _, _ = build_case(parameters)
    draft = draft_preset(font_size=2.5, decimal_precision=1)
    set_page(PAGE_WIDTH, PAGE_HEIGHT, margin=10.0)

    base_outer_length = parameters["pcb_length"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    base_outer_width = parameters["pcb_width"] + 2 * (
        parameters["pcb_clearance"] + parameters["wall_thickness"]
    )
    base_height = parameters["base_height"]
    lid_outer_length = base_outer_length + 2 * (
        parameters["lid_fit_clearance"] + parameters["lid_skirt_thickness"]
    )
    lid_outer_width = base_outer_width + 2 * (
        parameters["lid_fit_clearance"] + parameters["lid_skirt_thickness"]
    )
    lid_height = parameters["lid_skirt_depth"] + parameters["lid_top_thickness"]

    base_plan_center = (70.0, 205.0)
    base_front_center = (70.0, 105.0)
    lid_plan_center = (290.0, 105.0)
    lid_front_center = (290.0, 52.0)

    def base_plan_point(x, y):
        return (base_plan_center[0] + x, base_plan_center[1] + y, 0)

    def base_front_point(x, z):
        return (
            base_front_center[0] + x,
            base_front_center[1] + z - base_height / 2,
            0,
        )

    def lid_plan_point(x, y):
        return (lid_plan_center[0] + x, lid_plan_center[1] + y, 0)

    def lid_front_point(x, z):
        return (
            lid_front_center[0] + x,
            lid_front_center[1] + z - lid_height / 2,
            0,
        )

    mount_left = -parameters["pcb_length"] / 2 + parameters["mount_edge_offset"]
    mount_right = mount_left + parameters["mount_pitch_x"]
    mount_bottom = -parameters["pcb_width"] / 2 + parameters["mount_edge_offset"]
    mount_top = mount_bottom + parameters["mount_pitch_y"]

    base_look = (0.0, 0.0, base_height / 2)
    base_front = project_view(
        base,
        (0.0, -160.0, base_height / 2),
        (0, 0, 1),
        base_look,
        base_front_center,
    )
    base_side = project_view(
        base, (160.0, 0.0, 12.0), (0, 0, 1), base_look, (180.0, 105.0)
    )
    base_plan = project_view(
        base, (0.0, 0.0, 180.0), (0, 1, 0), base_look, (70.0, 205.0)
    )
    base_iso = project_view(
        base, (100.0, 100.0, 112.0), (0, 0, 1), base_look, (305.0, 215.0)
    )

    lid_look = (0.0, 0.0, lid_height / 2)
    lid_plan = project_view(
        lid, (0.0, 0.0, 150.0), (0, 1, 0), lid_look, (290.0, 105.0)
    )
    lid_front = project_view(
        lid,
        (0.0, -150.0, lid_height / 2),
        (0, 0, 1),
        lid_look,
        lid_front_center,
    )
    view_pairs = [
        base_front,
        base_side,
        base_plan,
        base_iso,
        lid_plan,
        lid_front,
    ]

    annotations = []
    named_annotations: list[tuple[str, object]] = []

    def add_annotation(item, name):
        annotations.append(item)
        named_annotations.append((name, item))
        annotate(item, name)

    add_annotation(
        Dimension(
            base_plan_point(-base_outer_length / 2, -base_outer_width / 2),
            base_plan_point(base_outer_length / 2, -base_outer_width / 2),
            "below",
            10.0,
            draft,
            label=dimension_label(base_outer_length),
        ),
        "base_dim_length",
    )
    add_annotation(
        Dimension(
            base_plan_point(-base_outer_length / 2, -base_outer_width / 2),
            base_plan_point(-base_outer_length / 2, base_outer_width / 2),
            "left",
            10.0,
            draft,
            label=dimension_label(base_outer_width),
        ),
        "base_dim_width",
    )
    add_annotation(
        Dimension(
            base_plan_point(mount_left, mount_top),
            base_plan_point(mount_right, mount_top),
            "above",
            9.0,
            draft,
            label=dimension_label(parameters["mount_pitch_x"]),
        ),
        "base_mount_pitch_x",
    )
    add_annotation(
        Dimension(
            base_plan_point(mount_right, mount_bottom),
            base_plan_point(mount_right, mount_top),
            "right",
            9.0,
            draft,
            label=dimension_label(parameters["mount_pitch_y"]),
        ),
        "base_mount_pitch_y",
    )
    add_annotation(
        Dimension(
            base_front_point(-base_outer_length / 2, 0.0),
            base_front_point(-base_outer_length / 2, base_height),
            "left",
            10.0,
            draft,
            label=dimension_label(base_height),
        ),
        "base_dim_height",
    )
    add_annotation(
        Leader(
            base_plan_point(mount_right, mount_top),
            (121.0, 246.0, 0),
            f"4x DIA {parameters['screw_clearance_diameter']:.1f} THRU",
            draft,
        ),
        "base_hole_callout",
    )
    add_annotation(
        Leader(
            (70.0, 205.0, 0),
            (121.0, 215.0, 0),
            (
                f"{len(BASE_VENT_X_POSITIONS)}x "
                f"{BASE_VENT_WIDTH:.1f} x {BASE_VENT_LENGTH:.1f} VENT SLOTS"
            ),
            draft,
        ),
        "base_vent_callout",
    )

    add_annotation(
        Dimension(
            lid_plan_point(-lid_outer_length / 2, -lid_outer_width / 2),
            lid_plan_point(lid_outer_length / 2, -lid_outer_width / 2),
            "below",
            8.0,
            draft,
            label=dimension_label(lid_outer_length),
        ),
        "lid_dim_length",
    )
    add_annotation(
        Dimension(
            lid_plan_point(lid_outer_length / 2, -lid_outer_width / 2),
            lid_plan_point(lid_outer_length / 2, lid_outer_width / 2),
            "right",
            8.0,
            draft,
            label=dimension_label(lid_outer_width),
        ),
        "lid_dim_width",
    )
    add_annotation(
        Dimension(
            lid_plan_point(
                parameters["fan_center_x"] - parameters["fan_hole_pitch"] / 2,
                parameters["fan_center_y"] - parameters["fan_hole_pitch"] / 2,
            ),
            lid_plan_point(
                parameters["fan_center_x"] + parameters["fan_hole_pitch"] / 2,
                parameters["fan_center_y"] - parameters["fan_hole_pitch"] / 2,
            ),
            "below",
            7.0,
            draft,
            label=dimension_label(parameters["fan_hole_pitch"]),
        ),
        "lid_fan_pitch_x",
    )
    add_annotation(
        Dimension(
            lid_plan_point(
                parameters["fan_center_x"] + parameters["fan_hole_pitch"] / 2,
                parameters["fan_center_y"] - parameters["fan_hole_pitch"] / 2,
            ),
            lid_plan_point(
                parameters["fan_center_x"] + parameters["fan_hole_pitch"] / 2,
                parameters["fan_center_y"] + parameters["fan_hole_pitch"] / 2,
            ),
            "right",
            7.0,
            draft,
            label=dimension_label(parameters["fan_hole_pitch"]),
        ),
        "lid_fan_pitch_y",
    )
    add_annotation(
        Dimension(
            lid_plan_point(
                parameters["gpio_slot_center_x"]
                - parameters["gpio_slot_length"] / 2,
                parameters["gpio_slot_center_y"],
            ),
            lid_plan_point(
                parameters["gpio_slot_center_x"]
                + parameters["gpio_slot_length"] / 2,
                parameters["gpio_slot_center_y"],
            ),
            "above",
            8.0,
            draft,
            label=dimension_label(parameters["gpio_slot_length"]),
        ),
        "lid_gpio_length",
    )
    add_annotation(
        Dimension(
            lid_front_point(-lid_outer_length / 2, 0.0),
            lid_front_point(-lid_outer_length / 2, lid_height),
            "left",
            8.0,
            draft,
            label=dimension_label(lid_height),
        ),
        "lid_dim_height",
    )
    add_annotation(
        Dimension(
            lid_front_point(lid_outer_length / 2, 0.0),
            lid_front_point(
                lid_outer_length / 2,
                parameters["lid_skirt_depth"],
            ),
            "right",
            8.0,
            draft,
            label=dimension_label(parameters["lid_skirt_depth"]),
        ),
        "lid_skirt_depth",
    )
    add_annotation(
        Leader(
            lid_plan_point(
                parameters["fan_center_x"] - parameters["fan_hole_pitch"] / 2,
                parameters["fan_center_y"] - parameters["fan_hole_pitch"] / 2,
            ),
            (350.0, 145.0, 0),
            f"4x DIA {parameters['fan_screw_diameter']:.1f} - 30 mm FAN",
            draft,
            text_side="right",
        ),
        "lid_fan_callout",
    )
    add_annotation(
        Leader(
            lid_plan_point(
                parameters["gpio_slot_center_x"],
                parameters["gpio_slot_center_y"],
            ),
            (245.0, 145.0, 0),
            "GPIO SLOT "
            f"{parameters['gpio_slot_length']:.1f} x "
            f"{parameters['gpio_slot_width']:.1f}",
            draft,
        ),
        "lid_gpio_callout",
    )

    notes = (
        ("BASE - PLAN", (55.0, 252.0, 0), "base_plan_label"),
        ("BASE - FRONT", (50.0, 124.0, 0), "base_front_label"),
        ("BASE - SIDE", (165.0, 124.0, 0), "base_side_label"),
        ("BASE - ISOMETRIC", (280.0, 274.0, 0), "base_iso_label"),
        ("LID - PLAN", (275.0, 151.0, 0), "lid_plan_label"),
        ("LID - FRONT", (275.0, 60.0, 0), "lid_front_label"),
        ("ALL DIMENSIONS IN mm", (105.0, 30.0, 0), "general_note_1"),
        (
            "PROTOTYPE - VERIFY CONNECTOR CUTOUTS ON PHYSICAL BOARD",
            (105.0, 24.0, 0),
            "general_note_2",
        ),
        (
            "GENERAL WALL/FLOOR: "
            f"{parameters['wall_thickness']:.1f}/"
            f"{parameters['floor_thickness']:.1f} | LID CLEARANCE: "
            f"{parameters['lid_fit_clearance']:.2f} PER SIDE",
            (105.0, 18.0, 0),
            "general_note_3",
        ),
    )
    for text, position, name in notes:
        add_annotation(Note(text, position, draft), name)

    title_block = TitleBlock(
        "RPI4 CASE - BASE AND LID",
        "RPI4-CASE-001",
        scale="1:1",
        material="FDM POLYMER",
        general_tolerance="ISO 2768-m",
        designed_by="AI CAD WORKSPACE",
        date="2026-07-20",
        revision="A",
        legal_owner="PERSONAL PROJECT",
        width=170.0,
        draft=draft,
        drawing_scale=1.0,
    ).locate(Location((240.0, 10.0, 0)))
    add_annotation(title_block, "case_title_block")

    border = Rectangle(
        PAGE_WIDTH - 20.0,
        PAGE_HEIGHT - 20.0,
        align=(Align.MIN, Align.MIN),
    ).locate(Location((10.0, 10.0, 0)))

    issues = lint_drawing(
        annotations,
        drawing_scale=DRAWING_SCALE,
        page_bbox=(0.0, 0.0, PAGE_WIDTH, PAGE_HEIGHT),
        view_shapes=[pair[0] for pair in view_pairs],
    )
    actionable = [issue for issue in issues if issue.severity != "info"]
    if actionable:
        messages = "; ".join(
            f"{issue.severity}:{issue.code}:{issue.message}" for issue in actionable
        )
        raise ValueError(f"Drawing lint failed: {messages}")

    part_color = Color(0.05, 0.05, 0.05)
    hidden_color = Color(0.55, 0.55, 0.55)
    dimension_color = Color(0.0, 0.20, 0.70)
    border_color = Color(0.15, 0.15, 0.15)

    svg = ExportSVG(margin=0)
    svg.add_layer("border", line_color=border_color, line_weight=0.35)
    svg.add_layer("part", line_color=part_color, line_weight=0.45)
    svg.add_layer(
        "hidden",
        line_color=hidden_color,
        line_weight=0.20,
        line_type=LineType.HIDDEN,
    )
    svg.add_layer(
        "dimensions",
        line_color=dimension_color,
        fill_color=dimension_color,
        line_weight=0.08,
    )
    svg.add_shape(border, layer="border")
    for visible, hidden in view_pairs:
        svg.add_shape(visible, layer="part")
        if hidden is not None:
            svg.add_shape(hidden, layer="hidden")
    for annotation in annotations:
        svg.add_shape(annotation, layer="dimensions")
    svg.write(SVG_PATH)

    dxf = ExportDXF()
    dxf.add_layer("border", line_weight=0.35)
    dxf.add_layer("part", line_weight=0.50)
    dxf.add_layer("hidden", line_weight=0.25)
    dxf.add_layer("dimensions", line_weight=0.13)
    dxf.add_shape(border, layer="border")
    for visible, hidden in view_pairs:
        dxf.add_shape(visible, layer="part")
        if hidden is not None:
            dxf.add_shape(hidden, layer="hidden")
    for annotation in annotations:
        dxf.add_shape(annotation, layer="dimensions")
    dxf.write(DXF_PATH)
    _write_dims_sidecar(named_annotations)

    return SVG_PATH, DXF_PATH, issues


if __name__ == "__main__":
    generate_drawing()
