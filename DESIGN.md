# SolidIntent Design System

## Direction

SolidIntent is a dark, restrained technical instrument. The interface uses a
persistent three-zone workspace: project context on the left, a dominant 3D
canvas in the centre, and task-specific evidence or controls on the right.
Complexity is revealed through selection rather than a permanent CAD toolbar.

The approved visual references are:

- `docs/design/solidintent_palette.png`
- `docs/design/viewer_direction_a.png`

Brand wordmark assets (white mark):

- `docs/brand/solidintent_logo.png` — white on transparent (canonical)
- `docs/brand/solidintent_logo_white.png` — compact white on transparent
- `docs/brand/solidintent_logo_readme.png` — white mark on graphite banner for README
- `viewer/src/assets/solidintent_logo.png` — header lockup (white, transparent)

## Color

Use OKLCH tokens only.

```css
--graphite-950: oklch(0.10 0 0);
--graphite-900: oklch(0.13 0.004 160);
--graphite-850: oklch(0.16 0.008 160);
--graphite-800: oklch(0.21 0.010 160);
--graphite-700: oklch(0.30 0.012 160);
--ink-primary: oklch(0.94 0.006 160);
--ink-secondary: oklch(0.76 0.012 160);
--ink-muted: oklch(0.66 0.012 160);
--action: oklch(0.68 0.18 250);
--action-hover: oklch(0.73 0.17 250);
--validated: oklch(0.72 0.14 160);
--warning: oklch(0.78 0.14 78);
--danger: oklch(0.67 0.18 25);
```

Color is semantic. Blue means action, selection, or focus. Green means a
completed validity gate. Amber means attention or unresolved verification.
Coral means error or geometry that no longer matches saved parameters. State
must also be communicated with text or an icon.

## Typography

- Interface: Geist Sans variable.
- Engineering values: Geist Mono variable.
- UI scale: 0.75rem metadata, 0.875rem secondary, 1rem body, 1.125rem section
  heading, 1.25rem screen heading.
- Body text is never below 1rem. Compact metadata may use 0.75rem or 0.875rem
  when it is not required to complete a task.
- Use tabular numerals for dimensions, revisions, hashes, and topology values.
- Do not use emoji, decorative display fonts, or all-caps labels as recurring
  section scaffolding.

## Spacing and geometry

- Base spacing unit: 4px.
- Scale: 4, 8, 12, 16, 24, 32, 48px.
- Related control rows use 8-12px gaps; distinct sections use 24-32px.
- Controls use 6-8px radii. Panels use at most 12px.
- Depth in dark mode comes from lighter surfaces and hairline dividers, not
  wide blurred shadows.
- Desktop workspace: 56px header, 220-240px context rail, flexible canvas,
  344-384px inspector.

## Components

- Header: project identity, revision, validation state, and no unrelated global
  navigation.
- Context rail: body visibility plus evidence destinations.
- Canvas: real 3D artifacts, fit/exploded/body/transparency controls, and a
  functional axis helper.
- Inspector: visible labels, search, editable/locked filters, grouped parameter
  rows, accepted/current comparisons, and explicit save feedback.
- Evidence views: validation, references, and revisions use aligned definition
  lists and compact tables rather than nested cards.
- Status: short label plus explanatory sentence when action is required.

## Motion

- State transitions: 150-220ms with ease-out-quart.
- Motion explains selection, panel changes, saving, and model transforms only.
- Respect `prefers-reduced-motion`; model transitions and interface animations
  become immediate.

## Responsive behavior

- Desktop: three persistent zones.
- Tablet: compact navigation rail, canvas and inspector side-by-side where
  possible; inspector may occupy a second row in portrait.
- Mobile: canvas first, navigation becomes a horizontal tab strip, and the
  inspector follows the canvas as normal document flow.
- All pointer targets are at least 44 by 44px on coarse-pointer devices.

## Accessibility

Target WCAG 2.2 AA. Provide full keyboard paths, visible focus rings, semantic
landmarks and labels, screen-reader status announcements, 200% zoom support,
and contrast of at least 4.5:1 for body text and 3:1 for UI components.
