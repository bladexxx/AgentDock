# Sand3D harness: bracket GLB

## Source analysis

Sand3D is a Python geometry library backed by Blender's `bpy`. Its public verbs are exported from `src/sand3d/__init__.py`. The first program in `README.md` and `docs/examples/bracket.py` build the same bracket: an 80 × 40 × 6 mm plate from `rect` and `extrude`, two 6.6 mm holes on a 50 mm pitch with `grid` and `hole`, and a 1 mm fillet on the top edges. `s3d.export(root, path)` writes `.glb` through Blender's glTF exporter and converts the program's millimetres to metres.

## Paired CLI design

`cli-anything-sand3d bracket` builds that bracket in one fresh process and exports a GLB. It accepts an output path and the five example dimensions. The default path is `./bracket.glb`. `--json` emits one summary object.

The harness calls Sand3D's public modeling verbs directly. The CLI checks the GLB header and declared file length after export. AgentDock independently verifies the installed command's GLB output.
