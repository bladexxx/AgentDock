# 02 · Verify Sand3D from Codex

**What to build:** Package the pinned Sand3D source for headless modeling in Linux.

**Blocked by:** 01 · Verify E2E from Codex.

**Status:** Done.

- [x] CLI-Anything generates a small CLI and matching Skill based on Sand3D's native Python API.
- [x] The packaged command uses Sand3D and Blender to export a bracket GLB.
- [x] The independent verifier checks the GLB and expected mesh without an interactive desktop.

The Linux amd64 image passed a live export, a wrong-width regression and a clean archive replay. See [the Sand3D fixture evidence](../../../docs/v0.1-sand3d-evidence.md) for timings and CLI-Anything provenance.
