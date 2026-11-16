# 01 · Verify E2E from Codex

**What to build:** Package the pinned E2E checkout with its native CLI and Skills, then verify a deterministic browser task against a controlled local page.

**Blocked by:** None.

**Status:** In progress.

- [ ] One Codex request builds a rebuildable image, records its package identity and runs the public verifier.
- [ ] A headless browser in that image runs the expected case against loopback with external networking disabled.
- [ ] The verifier collects a new JSON report and independently confirms the configured case ran and passed.
- [ ] A missing, malformed or wrong report fails verification, including when the container returns exit code zero.
- [ ] A clean rebuild and second run produce independently inspectable evidence.
