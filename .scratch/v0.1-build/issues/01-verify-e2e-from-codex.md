# 01 · Verify E2E from Codex

**What to build:** Package the pinned E2E checkout with its native CLI and Skills, then verify a deterministic browser task against a controlled local page.

**Blocked by:** None.

**Status:** Done.

- [x] One Codex request builds a rebuildable image, records its package identity and runs the public verifier.
- [x] A headless browser in that image runs the expected case against loopback with external networking disabled.
- [x] The verifier collects a new JSON report and independently confirms the configured case ran and passed.
- [x] A missing, malformed or wrong report fails verification, including when the container returns exit code zero.
- [x] A clean rebuild and second run produce independently inspectable evidence.

First live run: Linux ARM64, Docker 29.9.1, E2E 0.23.1. The selected Chromium smoke test passed. The verifier rejected a copy of the report with the selected test title changed while the successful exit status was preserved. See the [iteration retrospective](../../../docs/v0.1-iteration-01-retro.md).

A fresh Codex CLI session completed the documented build and run from the pinned source archive. The replay reused Docker build layers, ran a new browser container and wrote independent evidence. Both Docker commands needed scoped approval for the local Docker socket.
