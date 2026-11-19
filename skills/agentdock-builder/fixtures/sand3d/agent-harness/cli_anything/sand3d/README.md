# CLI-Anything Sand3D

This one-shot CLI builds the mounting bracket from Sand3D's `docs/examples/bracket.py` and exports it through Sand3D to a real GLB. It uses the example's defaults: 80 × 40 × 6 mm plate, two 6.6 mm holes on a 50 mm pitch, 4 mm profile corners, and a 1 mm top fillet.

## Requirements and installation

Use Linux with a Sand3D-supported Python and Blender `bpy` version. Sand3D requires Python 3.11 with `bpy` 4.5 or Python 3.13 with `bpy` 5.2. Install the upstream Sand3D package and this harness in the same environment. AgentDock installs both from source in its fixture image.

## Usage

```bash
cli-anything-sand3d bracket
cli-anything-sand3d --json bracket --output /tmp/bracket.glb
cli-anything-sand3d --json bracket --w 80 --d 40 --t 6 --hole-d 6.6 --pitch 50
```

The default output is `./bracket.glb`. `--json` belongs before `bracket` and returns the absolute output path, format, byte count, and input dimensions. A failed command exits nonzero and writes the error to stderr. The command may overwrite an existing output file.

## Runtime verification

Run the AgentDock Sand3D fixture to check the exported plate with the independent GLB verifier. See `tests/TEST.md` for the validation commands.
