ARG NODE_IMAGE=node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1
FROM ${NODE_IMAGE} AS dependencies

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
# Use the reviewed lockfile to retrieve packages before copying application source.
COPY source/pnpm-lock.yaml source/pnpm-workspace.yaml ./
RUN npm install --global pnpm@12.3.4
RUN pnpm fetch --config.fetch-timeout=600000 --ignore-scripts \
    && node node_modules/.pnpm/playwright-core@1.65.1/node_modules/playwright-core/cli.js \
        install chromium --with-deps --only-shell

FROM dependencies
COPY source/ .
RUN --network=none pnpm install --offline --frozen-lockfile \
    && pnpm run build \
    && pnpm --filter @e2e-dev/web-benchmark run build \
    && chown -R node:node /app

USER node
WORKDIR /app/apps/web-benchmark
CMD ["node", "node_modules/e2e/dist/cli/bin.js", "run", "tests/smoke.e2e.ts", "--target", "web", "--workers", "1", "--retries", "0", "--no-cache", "--max-duration", "90000", "--reporter", "json", "--trace=off", "--video=off"]
