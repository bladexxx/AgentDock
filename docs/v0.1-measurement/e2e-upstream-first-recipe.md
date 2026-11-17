# Upstream web-benchmark smoke test in Docker

Run these commands from the directory containing the fresh `./e2e` snapshot. They prepare a disposable Docker build context, leaving `./e2e` untouched. The image build needs package-registry, Debian-package, and Playwright download access; the test container has no network interface beyond its own loopback. No registry credentials, model keys, GitHub tokens, host environment file, or secret mounts are supplied. The smoke test is deterministic and has no agent steps.

The commands require Docker Buildx with Linux arm64 support and Bash. The outer workflow supplies the independent verifier. This recipe itself has **not** been executed.

```bash
set -euo pipefail
recipe_context="$(mktemp -d)"
trap 'rm -rf "$recipe_context"' EXIT

# Copy the current source snapshot, including uncommitted source files, without
# modifying it or carrying local dependencies, output, VCS data, or secrets.
tar -C ./e2e \
  --exclude='*/.git' --exclude='*/node_modules' --exclude='*/.e2e' \
  --exclude='*/.next' --exclude='*/dist' \
  --exclude='*/.env' --exclude='*/.env.*' \
  --exclude='*/.npmrc' --exclude='*/.netrc' --exclude='*/.pypirc' \
  --exclude='*/.aws' --exclude='*/.ssh' --exclude='*/.config/gcloud' \
  --exclude='*/.azure' --exclude='*/.vault-token' \
  --exclude='*/id_rsa' --exclude='*/id_dsa' --exclude='*/id_ed25519' \
  --exclude='*/*.pem' --exclude='*/*.p12' \
  -cf - . | tar -C "$recipe_context" -xf -

cat > "$recipe_context/.dockerignore" <<'IGNORE'
.git
**/.git
**/node_modules
**/.e2e
**/.next
**/dist
**/.env
**/.env.*
**/.npmrc
**/.netrc
**/.pypirc
**/.aws
**/.ssh
**/.config/gcloud
**/.azure
**/.vault-token
**/id_rsa
**/id_dsa
**/id_ed25519
**/*.pem
**/*.p12
IGNORE

cat > "$recipe_context/Dockerfile" <<'DOCKERFILE'
# syntax=docker/dockerfile:1
FROM --platform=linux/arm64 node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1 AS build
WORKDIR /src
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NEXT_TELEMETRY_DISABLED=1 \
    E2E_TELEMETRY_DISABLED=1

# Node 26 does not bundle Corepack. Install the exact package-manager release.
RUN --mount=type=cache,target=/root/.npm npm install --global pnpm@12.3.4
COPY . .
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# The CLI, web engine, and configured GitHub reporter are workspace packages.
RUN pnpm --filter @e2e-dev/core run build && \
    pnpm --filter e2e run build && \
    pnpm --filter @e2e-dev/web run build && \
    pnpm --filter @e2e-dev/github run build
RUN pnpm --filter @e2e-dev/web exec playwright-core install --only-shell chromium
RUN pnpm --filter @e2e-dev/web-benchmark run build

FROM --platform=linux/arm64 node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1 AS runtime
WORKDIR /src
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    NEXT_TELEMETRY_DISABLED=1 \
    E2E_TELEMETRY_DISABLED=1 \
    CI=1
COPY --from=build --link /usr/local/lib/node_modules/pnpm /usr/local/lib/node_modules/pnpm
COPY --from=build --link /usr/local/bin/pnpm /usr/local/bin/pnpm
COPY --from=build --link --chown=1001:1001 /src /src
COPY --from=build --link --chown=1001:1001 /ms-playwright /ms-playwright

# Playwright resolves Debian's Chromium shared-library dependencies here,
# during image build. Runtime downloads are unnecessary.
RUN pnpm --dir /src/packages/web exec playwright-core install-deps chromium && \
    groupadd --gid 1001 e2e && useradd --uid 1001 --gid 1001 --create-home e2e
USER 1001:1001
WORKDIR /src/apps/web-benchmark
CMD ["node", "node_modules/e2e/dist/cli/bin.js", "run", "tests/smoke.e2e.ts:6", "--target", "web", "--workers", "1", "--retries", "0", "--no-cache", "--max-duration", "90000", "--reporter", "json"]
DOCKERFILE

docker buildx build \
  --platform linux/arm64 \
  --pull=false \
  --load \
  --tag e2e-web-smoke:upstream \
  "$recipe_context"

# JSON reporter writes one document to stdout. Preserve Docker's exit status.
docker run --rm --init --platform linux/arm64 --network none \
  --name e2e-web-smoke \
  e2e-web-smoke:upstream > smoke-report.json
```

`smoke-report.json` is the JSON reporter output. The runner also writes `.e2e/report.json` inside the disposable container. The CLI's `--max-duration 90000` caps test execution at 90 seconds; image building and pre-test app startup are outside that timer. The container reaches its own Next.js app on `127.0.0.1:4280` through loopback, even with `--network none`. A nonzero `docker run` status indicates that the smoke test or its setup failed.
