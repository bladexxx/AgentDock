---
name: cli-anything-sand3d
description: Export a two-hole mounting bracket as a GLB through the Sand3D Python API and Blender. Use with AgentDock's headless Sand3D package.
---

# Export a Sand3D bracket

The package includes `cli-anything-sand3d`. Show its commands with `cli-anything-sand3d --help`.

- `bracket` — Export the upstream example's two-hole mounting bracket.

```bash
cli-anything-sand3d --json bracket --output /tmp/bracket.glb
```

The default bracket has an 80 × 40 × 6 mm plate, two 6.6 mm holes on a 50 mm pitch, 4 mm profile corners and a 1 mm top fillet. Use `bracket --help` for dimension options. The default output is `./bracket.glb`. An existing output file may be overwritten.

Place `--json` before `bracket` to request a machine-readable summary. Check the process status and pass the GLB to AgentDock's independent artifact verifier when verifying the default bracket.
