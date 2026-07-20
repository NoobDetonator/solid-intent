# Connected MCP smoke test

Use build123d-mcp for every CAD operation in this test.

1. Call `version` and `workflow_hints`; report each result.
2. Read `build123d://quickref`, then reset the session and execute a simple
   `Box(10, 20, 30)` first. Stop if this does not return within five minutes.
3. Call `health_check` only after the simple execute succeeds.
4. Incrementally create a 60 mm x 40 mm x 6 mm mounting plate with two 5 mm
   through-holes whose centers are 40 mm apart.
5. Register the finished solid as `mounting_plate` with `show()`.
6. Measure it using the aluminum material preset. Verify the bounding box,
   volume, topology, and mass are plausible.
7. Render ISO, top, and front PNG views into `renders/`.
8. Run `validate`; do not export unless it passes.
9. Export STEP and STL into `exports/`.
10. Report the exact output paths and a concise table of measured metrics.

If the server reports `Worker was not running`, stop and report it. The
documented `--in-process` fallback also stalled in this host's initial harness,
so do not persist that flag without a controlled client-level retest.
