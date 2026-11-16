ARG NODE_IMAGE=node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1
FROM ${NODE_IMAGE}

ARG E2E_REVISION
ARG E2E_SKILL_TREE
ARG NODE_IMAGE
LABEL org.opencontainers.image.source="https://github.com/e2e-inc/e2e" \
      org.opencontainers.image.revision="${E2E_REVISION}" \
      org.opencontainers.image.base.name="${NODE_IMAGE}" \
      io.agentdock.e2e.skill-tree="${E2E_SKILL_TREE}"

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
CMD ["node", "node_modules/e2e/dist/cli/bin.js", "run", "tests/smoke.e2e.ts", "--target", "web", "--workers", "1", "--retries", "0", "--no-cache", "--max-duration", "90000", "--reporter", "json", "--trace=off", "--video=off"]
