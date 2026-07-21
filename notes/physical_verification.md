# Physical verification checklist

This workspace uses **official approximate mechanical drawings**, not
manufacturer production STEP keep-out solids. Before releasing a printable
enclosure revision, verify the following against the exact hardware revision
on the bench.

## Raspberry Pi 5 enclosure

Reference drawings:

- [Raspberry Pi 5 mechanical drawing](https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf)
- [Active Cooler mechanical drawing](https://pip-assets.raspberrypi.com/categories/993-raspberry-pi-active-cooler/documents/RP-008187-DS-1-raspberry-pi-active-cooler-mechanical-drawing.pdf)

No redistributable manufacturer STEP of the board or Active Cooler is shipped
in this repository. Connector and cooler envelopes in
`projects/raspberry_pi5_case` are **drawing-derived boxes**.

### Fit checks to perform on hardware

1. USB-C, dual micro-HDMI, USB-A, Ethernet, and microSD plug clearance through
   the base openings (including strain-relief boots).
2. GPIO header / HAT stack height against the lid slot and skirt.
3. Official Active Cooler installed: confirm the aluminium body and blower do
   not collide with the lid, and that the modelled `cooler_fan_clearance`
   matches the printer/material stack.
4. Lid friction fit with the accepted `lid_fit_clearance` for the target
   filament and printer.
5. If MCP printability reports a ~0.2 mm microfeature warning, print with
   layer height ≤ 0.2 mm and inspect the thin wall/opening edges.

### Raspberry Pi 4 enclosure

Same discipline: openings come from the project parameter contract and must be
checked against the physical board and plugs before production use.
