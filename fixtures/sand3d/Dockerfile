# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.11-slim-bookworm@sha256:e8c69d86735f6df3efa06b324694fe51f0422785f83a3bd463052636c2421944
FROM ${PYTHON_IMAGE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libx11-6 libxi6 libxkbcommon0 libxrender1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --timeout 120 --no-cache-dir \
    'certifi==2026.10.23' 'charset-normalizer==3.5.2' 'click==8.3.3' 'cython==3.3.1' \
    'idna==3.20' 'numpy==1.26.4' 'requests==2.34.2' 'setuptools==82.0.1' \
    'urllib3==2.8.0' 'wheel==0.46.3' 'zstandard==0.25.0'

RUN --mount=type=bind,source=wheel,target=/wheel \
    wheel=bpy-4.5.16-cp311-cp311-manylinux_2_28_x86_64.whl \
    && sha=8c16462bdedd3feade101a417a84409ccbb264a5080b9f2ccf088f0cea1650de \
    && if [ -f "/wheel/$wheel" ]; then \
        echo "$sha  /wheel/$wheel" | sha256sum -c - && input="/wheel/$wheel"; \
    else \
        input="https://files.pythonhosted.org/packages/b6/1b/4b02e891f744284e25d1eb1535253bc18c79e1bc3ff2702cbeb1a01750d8/$wheel#sha256=$sha"; \
    fi \
    && pip install --timeout 120 --no-cache-dir --no-deps "$input"

# The bpy wheel links against these X11 libraries even in headless mode.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libsm6 libice6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY source/ /app/source/
COPY agent-harness/ /app/agent-harness/
RUN --network=none pip install --no-cache-dir --no-build-isolation --no-deps /app/source /app/agent-harness \
    && pip check

ARG PYTHON_IMAGE
ARG SAND3D_REVISION
ARG SAND3D_SKILL_SHA256
LABEL org.opencontainers.image.source="https://github.com/Sandflow-ai/sand3d" \
      org.opencontainers.image.revision="${SAND3D_REVISION}" \
      org.opencontainers.image.base.name="${PYTHON_IMAGE}" \
      io.agentdock.cli-anything.revision="34f519533bc175d2fe287ab8316b0dd99bb9cc43" \
      io.agentdock.sand3d.cli-version="0.1.0" \
      io.agentdock.sand3d.skill-sha256="${SAND3D_SKILL_SHA256}"

ENV HOME=/tmp PYTHONUNBUFFERED=1
USER 65532:65532
WORKDIR /tmp
ENTRYPOINT ["cli-anything-sand3d"]
CMD ["--help"]
