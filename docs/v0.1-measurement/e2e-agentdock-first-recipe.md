# E2E smoke test Docker recipe

Run these commands from this directory with a Docker daemon that supports `linux/arm64`. The build needs access to the image registry, npm registry, Debian packages, and Playwright's browser download. The test container has no network access. No credentials are passed to either step. This recipe uses the fresh `./e2e` snapshot as its source and does not modify it.

The source's native Skill is `e2e/skills/e2e/SKILL.md`. Its `running` reference documents the CLI flags below. The AgentDock Builder Skill and `fixtures/e2e/{Dockerfile,build.sh,run.sh}` supplied the pinned build pattern; this recipe adapts that pattern to a source snapshot without Git metadata. The outer workflow supplies the independent verifier.

```bash
set -euo pipefail

evidence_dir="$(mktemp -d "$(pwd)/e2e-smoke-evidence.XXXXXX")"
context_dir="$(mktemp -d)"
trap 'rm -rf -- "$context_dir"' EXIT
mkdir -- "$context_dir/source"

# Stage a clean build context. In particular, do not ship the snapshot's
# existing .e2e replay cache, local dependencies, Git data, or local secrets.
tar -C ./e2e \
  --exclude='./.e2e' --exclude='*/.e2e' \
  --exclude='./node_modules' --exclude='*/node_modules' \
  --exclude='./.git' --exclude='*/.git' \
  --exclude='./.env' --exclude='./.env.*' \
  --exclude='*/.env' --exclude='*/.env.*' \
  -cf - . | tar -C "$context_dir/source" -xf -

shasum -a 256 ./e2e/pnpm-lock.yaml > "$evidence_dir/pnpm-lock.sha256"

cat > "$context_dir/Dockerfile" <<'DOCKERFILE'
FROM --platform=linux/arm64 node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    E2E_TELEMETRY_DISABLED=1 \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app
COPY source/ .
RUN npm install --global pnpm@12.3.4 \
    && pnpm install --frozen-lockfile \
    && pnpm --filter @e2e-dev/web exec playwright-core install chromium --with-deps --only-shell \
    && pnpm run build \
    && pnpm --filter @e2e-dev/web-benchmark run build \
    && chown -R node:node /app

USER node
WORKDIR /app/apps/web-benchmark
CMD ["node", "node_modules/e2e/dist/cli/bin.js", "run", "tests/smoke.e2e.ts", "--grep", "^home lists the scenarios and opens one$", "--target", "web", "--workers", "1", "--retries", "0", "--no-cache", "--max-duration", "90000", "--reporter", "json", "--trace=off", "--video=off"]
DOCKERFILE

docker build --platform linux/arm64 \
  --file "$context_dir/Dockerfile" \
  --iidfile "$evidence_dir/image-id" \
  "$context_dir"

status=0
docker run --rm --platform linux/arm64 --network none \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 2g --cpus 2 --pids-limit 256 \
  "$(cat "$evidence_dir/image-id")" \
  > "$evidence_dir/report.json" 2> "$evidence_dir/run.log" || status=$?
printf '%s\n' "$status" > "$evidence_dir/exit-status"
printf 'Evidence: %s\n' "$evidence_dir"
exit "$status"
```

The 90-second `--max-duration` is the upstream runner's application test cap; build and startup are outside that clock. `report.json` is the JSON reporter's stdout, and `exit-status` preserves the container result for the outer verifier. A passing process status alone does not replace that independent report check.
