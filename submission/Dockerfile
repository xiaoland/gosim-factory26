FROM rust:1.93-bookworm AS braid
WORKDIR /build/braid
COPY sources/braid/ ./
RUN cargo build --locked --release

FROM node:22.22.3-bookworm-slim AS node

FROM python:3.12-slim-bookworm AS runtime
ARG BACKEND=pi
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
WORKDIR /runtime
RUN if [ "$BACKEND" = pi ]; then package='@earendil-works/pi-coding-agent@0.85.1'; else package='@openai/codex@0.155.0'; fi; \
    npm install --save-exact "$package" && npm cache clean --force
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
