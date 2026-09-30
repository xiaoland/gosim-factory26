FROM node:24.10.0-bookworm-slim AS node
WORKDIR /runtime
COPY harness/npm/package.json harness/npm/package-lock.json ./
RUN npm ci --legacy-peer-deps && npm cache clean --force

FROM python:3.12-slim-bookworm AS runtime
ARG BACKEND=pi
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
WORKDIR /runtime
COPY --from=node /runtime/package.json /runtime/package-lock.json ./
COPY --from=node /runtime/node_modules ./node_modules
RUN apt-get update && apt-get install -y --no-install-recommends procps ripgrep sudo patch && rm -rf /var/lib/apt/lists/*
ENV PLAYWRIGHT_BROWSERS_PATH=/runtime/.playwright
RUN ./node_modules/.bin/playwright install chromium --with-deps --no-shell
RUN mkdir /runtime/python && \
    if [ "$BACKEND" = codex ]; then \
      python -m pip install --target /runtime/python 'litellm[proxy]==1.102.0'; fi && \
    PYTHONPATH=/runtime/python python -m pip freeze --path /runtime/python > /runtime/python-requirements.lock
COPY --from=node /usr/local/bin/node /runtime/bin/node
# Application native addon, separate from the Node 24 harness dependencies.
ADD --checksum=sha256:a16b1df74f095e47b6404b4af1c237d2aca75f431d8f4d1f498419263632ed03 \
    https://github.com/WiseLibs/better-sqlite3/releases/download/v11.10.0/better-sqlite3-v11.10.0-node-v115-linux-x64.tar.gz \
    /runtime/native-prebuilds/better-sqlite3-v11.10.0-node-v115-linux-x64.tar.gz
COPY harness/npm/patches/ /build/patches/
RUN patch --batch --fuzz=0 -p1 -d /runtime/node_modules/pi-background-bash -i /build/patches/pi-background-bash-1.0.5.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/pi-subagents -i /build/patches/pi-subagents-0.56.0-completion-boundary.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/pi-subagents -i /build/patches/pi-subagents-0.56.0-model-exclusion-boundary.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/pi-subagents -i /build/patches/pi-subagents-0.56.0-open-tools.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/pi-subagents -i /build/patches/pi-subagents-0.56.0-acceptance-off.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/@earendil-works/pi-coding-agent -i /build/patches/pi-coding-agent-0.85.1-braid-boundary.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/@upstash/context7-pi -i /build/patches/context7-pi-0.1.2.patch && \
    patch --batch --fuzz=0 -p1 -d /runtime/node_modules/@ff-labs/pi-fff -i /build/patches/pi-fff-0.11.0.patch
COPY build.py /build/build.py
RUN python /build/build.py "$BACKEND"

FROM rust:1.93-bookworm AS braid
WORKDIR /build/braid
COPY sources/braid/ ./
RUN cargo build --locked --release

FROM runtime AS team
COPY --from=braid /build/braid/target/release/braid /runtime/bin/braid
