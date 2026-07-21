# Raspberry Pi Zero 2 W Snap-Fit Case

## Intent

Compact two-piece FDM enclosure for the Raspberry Pi Zero 2 W with a
flush ridge-groove snap fit (external undercut in the base, close-fitting
lid skirt with inward beads), locating pins into the four PCB mounting
holes, connector openings, GPIO lid access, and SoC ventilation.

## References

1. Official product brief mechanical drawing (65 × 30 mm, 3.5 mm hole offsets,
   port centre-lines 12.4 / 41.4 / 54.0 mm from the microSD edge).
2. Official Zero 2 W mechanical drawing PDF (form-factor confirmation).

## Assumptions

- Connector body heights for micro-USB, mini-HDMI, microSD, and CSI openings
  are assumed from typical Zero-family hardware; verify with physical plugs.
- Snap clearances (`lid_fit_clearance`, ridge/bead depths) need printer and
  filament calibration.
- GPIO header is treated as populated for the lid access slot.
- Antenna keep-out is not modelled as a separate solid.

## Physical verification needed

- Plug fit for power USB, data USB, and mini-HDMI.
- microSD insertion/removal with the board seated.
- CSI ribbon exit clearance.
- Snap engage/disengage force and long-term retention.
- Locating pin diameter vs hole tolerance after print shrinkage.
