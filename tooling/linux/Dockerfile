FROM rust:1.93-bookworm AS resource-monitor
WORKDIR /build/resource-monitor
COPY sources/resource-monitor/ ./
RUN cargo build --locked --release

FROM node:24.10.0-bookworm-slim AS node
WORKDIR /runtime
COPY harness/npm/package.json harness/npm/package-lock.json ./
RUN npm ci --legacy-peer-deps && npm cache clean --force

FROM python:3.12-slim-bookworm AS runtime
ARG BACKEND=pi
ARG RUNTIME_PROFILE=full
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
WORKDIR /runtime
COPY --from=node /runtime/package.json /runtime/package-lock.json ./
COPY --from=node /runtime/node_modules ./node_modules
RUN apt-get update && apt-get install -y --no-install-recommends procps ripgrep sudo patch && rm -rf /var/lib/apt/lists/*
ENV PLAYWRIGHT_BROWSERS_PATH=/runtime/.playwright FACTORY26_RUNTIME_PROFILE=${RUNTIME_PROFILE}
RUN if [ "$RUNTIME_PROFILE" = full ]; then \
      ./node_modules/.bin/playwright install chromium --with-deps --no-shell; \
    else \
      mkdir -p /runtime/.playwright; \
    fi
RUN mkdir /runtime/python && \
    if [ "$BACKEND" = codex ]; then \
      python -m pip install --target /runtime/python 'litellm[proxy]==1.102.0'; fi && \
    PYTHONPATH=/runtime/python python -m pip freeze --path /runtime/python > /runtime/python-requirements.lock
COPY --from=node /usr/local/bin/node /runtime/bin/node
COPY harness/npm/patches/ /build/patches/
COPY harness/npm/native-managed.mjs harness/npm/v8-observation.mjs /runtime/
COPY --from=resource-monitor /build/resource-monitor/target/release/factory26-resource-monitor /runtime/bin/factory26-resource-monitor
COPY apply-native-patches.sh /build/apply-native-patches.sh
RUN sh /build/apply-native-patches.sh
COPY build.py /build/build.py
COPY browser_runtime.py /build/browser_runtime.py
RUN python /build/build.py "$BACKEND"

FROM rust:1.93-bookworm AS braid
WORKDIR /build/braid
COPY sources/braid/ ./
RUN cargo build --locked --release

FROM runtime AS team
COPY --from=braid /build/braid/target/release/braid /runtime/bin/braid
