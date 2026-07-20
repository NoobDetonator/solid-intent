# Reference Library

Reference packages are immutable evidence. Preserve their original filenames
and record how each file should be used before deriving production geometry.

## Trust order

1. Current official manufacturer CAD or production drawing.
2. Exact physical measurements from the hardware revision being enclosed.
3. Official approximate/reference drawings.
4. Third-party CAD assemblies.
5. Photos and rendered images.

## Raspberry Pi 4 Model B package study

Package: `raspberry-pi-4-model-b-1.snapshot.3/`

Original model: **Raspberry Pi 4 Model B** by **Hasanain Shuja**  
Source: <https://grabcad.com/library/raspberry-pi-4-model-b-1>

No licence or provenance file is present in the package. Treat it as internal
reference material and do not redistribute its native CAD or images until the
source and licence are confirmed.

The package directory is excluded from version control. A contributor who has
obtained the reference directly from its source may place it at the path above;
SolidIntent remains usable without redistributing that package.

### Best uses by file type

| Type | Best use | Limitations |
|---|---|---|
| PDF dimension sheet | Extract board envelope, mounting pattern, corner radius, connector offsets, and Z envelopes | Dated 2019; not an official Raspberry Pi 5 production datum |
| STEP assembly | Collision, keep-out, connector access, and visual cross-checks | 32.7 MB, 108 solids, 10,487 faces; too heavy for every iteration |
| Parasolid `.x_b` | High-fidelity archival/interchange source | Not directly supported by the current MCP import tool |
| SolidWorks assembly/parts | Editable upstream source and component provenance | Requires SolidWorks or a compatible converter |
| Orthographic images | Semantic identification and human review | Perspective/scale cannot establish production dimensions |

### Measured STEP inventory

- Import name: `rpi4_reference`
- Bounding box in source coordinates: 88.99 x 19.9 x 58.4 mm
- Solids: 108
- Faces: 10,487
- Edges: 29,395
- Vertices: 19,174
- STEP product records: 38
- Volume: 18,782.1512 mm^3

The model is oriented with the board plane in XZ and component height along Y.
Normalize orientation before comparing it with enclosure models built in the
usual XY board plane.

### Recommended derived artifact

For repeated enclosure work, derive a lightweight board interface model with:

- PCB outline and mounting holes.
- Connector keep-out boxes.
- GPIO and active-cooler keep-out volumes.
- Underside component and microSD clearance.
- Named interface objects for fit checks.

Keep the detailed STEP for final collision review. Use the lightweight proxy in
the normal AI iteration loop.

## Raspberry Pi generation rule

The Raspberry Pi 4 package is a workflow example and a Pi 4 reference only.
Do not use its connector positions or component heights for Raspberry Pi 5.
For Pi 5 production geometry, use the current official Pi 5 STEP plus a
physical-board check.
