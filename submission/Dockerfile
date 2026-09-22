FROM rust:1.93-bookworm AS braid
WORKDIR /build/braid
COPY sources/braid/ ./
RUN cargo build --locked --release

FROM node:24.10.0-bookworm-slim AS node
WORKDIR /runtime
COPY harness/npm/package.json harness/npm/package-lock.json ./
RUN npm ci && npm cache clean --force

FROM python:3.12-slim-bookworm AS runtime
ARG BACKEND=pi
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
WORKDIR /runtime
COPY --from=node /runtime/package.json /runtime/package-lock.json ./
COPY --from=node /runtime/node_modules ./node_modules
RUN apt-get update && apt-get install -y --no-install-recommends sudo && rm -rf /var/lib/apt/lists/*
RUN HOME=/runtime ./node_modules/.bin/agent-browser install --with-deps
COPY sources/svc/ /build/svc/
RUN python -m pip wheel --wheel-dir /wheels /build/svc/cli && \
    if [ "$BACKEND" = codex ]; then \
      python -m pip install --find-links=/wheels --target /runtime/python sustainable-vibe-coding 'litellm[proxy]==1.102.0'; \
    else python -m pip install --no-index --find-links=/wheels --target /runtime/python sustainable-vibe-coding; fi && \
    PYTHONPATH=/runtime/python python -m pip freeze --path /runtime/python > /runtime/python-requirements.lock
COPY --from=braid /build/braid/target/release/braid /runtime/bin/braid
COPY --from=node /usr/local/bin/node /runtime/bin/node
COPY build.py /build/build.py
RUN python /build/build.py "$BACKEND"
