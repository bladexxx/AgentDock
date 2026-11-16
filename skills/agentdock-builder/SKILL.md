---
name: agentdock-builder
description: Build and check an Application Sandbox Package. Use for AgentDock packaging requests for the supported E2E browser fixture.
---

# Build the E2E package

1. Use the reviewed E2E checkout provided by the developer. Use its native CLI and Skill at the source commit selected by the fixture recipe.
2. Use a working Docker daemon and the recipe's pinned Node 26 Debian image. The build requires access to the dependency registries and browser distribution endpoints. Pass no credentials to the build.
3. From AgentDock, run `bash fixtures/e2e/build.sh E2E_CHECKOUT`. It builds from the fixture's pinned Git commit and prints the local image ID.
4. Run `bash fixtures/e2e/run.sh IMAGE_ID NEW_EVIDENCE_DIRECTORY`. It runs the browser fixture with loopback and records package identity, report, exit status, logs and artifact check in the evidence directory.
5. Report the source commit, base image digest, local image ID, native Skill path and evidence location. Report missing prerequisites and failures as incomplete verification.
