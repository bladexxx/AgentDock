# AgentDock
AgentDock is an open-source platform that transforms existing applications into verified, reusable sandboxes, enabling AI agents to discover and use them on demand without manual integration.

## V0.1

See the [release contract](docs/v0.1-build-spec.md) and [local tickets](.scratch/v0.1-build/issues).

The E2E fixture uses the native CLI and upstream Skill from a pinned E2E Git checkout.
It needs Docker and Python 3.11 or newer. The container recipe pins its Node 26 Debian
base image by digest. The build downloads locked dependencies and Chromium. The test runs against the
benchmark app on loopback with external networking disabled.

```sh
image_id=$(bash fixtures/e2e/build.sh /path/to/e2e)
bash fixtures/e2e/run.sh "$image_id" /path/to/new-evidence-directory
python3 -B -m unittest discover -s tests
```

Use the [Builder Skill](skills/agentdock-builder/SKILL.md) for the same workflow in Codex.
