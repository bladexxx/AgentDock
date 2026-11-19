---
name: agentdock-builder
description: Build and check an Application Sandbox Package. Use for AgentDock packaging requests for the supported E2E browser and Sand3D modeling fixtures.
---

# Build an Application Sandbox Package

## Permission boundary

Use the reviewed fixture recipes and configured Docker/BuildKit daemon.
Dependency retrieval needs network access to the public endpoints in those
recipes. Source builds and fixture runs use Docker's `--network=none`. The
recipe receives a staged Git archive and explicit fixture inputs. Pass no
host workspace mounts, credentials, proxy settings, SSH forwarding, secret
mounts, or Docker sockets to build steps or runtime containers. Stop and report
any required restriction the configured environment cannot enforce.

Keep the host receipt created by the build script. Pass it with the local image
ID to the runner, which checks the artifact independently and records the
receipt's source, CLI and Skill provenance.

## Build the E2E package

1. Use the reviewed E2E checkout provided by the developer. Use its native CLI and Skill at the source commit selected by the fixture recipe.
2. Use a working Docker daemon and the recipe's pinned Node 26 Debian image. The build requires access to the dependency registries and browser distribution endpoints. If the sandbox denies access to Docker, use the agent's normal approval mechanism for the specific build or run command.
3. Resolve `BUILDER_SKILL_DIR` to the directory containing this `SKILL.md`. Run `bash "$BUILDER_SKILL_DIR/fixtures/e2e/build.sh" E2E_CHECKOUT NEW_BUILD_RECEIPT`. It builds from the fixture's pinned Git commit and writes the host receipt and prints the local image ID.
4. Run `bash "$BUILDER_SKILL_DIR/fixtures/e2e/run.sh" IMAGE_ID BUILD_RECEIPT NEW_EVIDENCE_DIRECTORY`. It runs the browser fixture with loopback and records package identity, report, exit status, logs and artifact check in the evidence directory.
5. Report the source commit, base image digest, local image ID, native Skill path and evidence location. Report missing prerequisites and failures as incomplete verification.

## Build the Sand3D package

1. Use the reviewed Sand3D checkout provided by the developer. The fixture uses its native Python API. CLI-Anything generated the console entry point and companion Skill because the pinned Sand3D source has no application CLI. For a rebuild, use the checked-in pair and pinned provenance.
2. Use Docker with Linux amd64 support. The build needs network access to the base-image, Debian and Python package registries. The verifier runs with network disabled and gives the container no host mounts.
3. Resolve `BUILDER_SKILL_DIR` to the directory containing this `SKILL.md`. Run `bash "$BUILDER_SKILL_DIR/fixtures/sand3d/build.sh" SAND3D_CHECKOUT NEW_BUILD_RECEIPT`. It archives the pinned Git revision, packages the command and matching Skill, and writes the host receipt and prints the local image ID. If the registry download stalls, set `SAND3D_BPY_WHEEL` to a local copy of the exact Blender wheel. The recipe checks the same pinned SHA-256 in both cases.
4. Run `bash "$BUILDER_SKILL_DIR/fixtures/sand3d/run.sh" IMAGE_ID BUILD_RECEIPT NEW_EVIDENCE_DIRECTORY`. It runs the command from the generated Skill on the real application, saves the bracket GLB and package identity, and checks the geometry with the bundled independent verifier.
5. Report the source and CLI-Anything revisions, base image digest, local image ID, platform, Skill path and evidence location. Report missing prerequisites and failures as incomplete verification.
