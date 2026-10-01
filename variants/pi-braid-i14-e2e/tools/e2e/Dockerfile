FROM node:24.10.0-bookworm-slim AS dependencies
WORKDIR /e2e
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts && npm cache clean --force

FROM python:3.12-slim-bookworm
COPY --from=dependencies /usr/local/bin/node /usr/local/bin/node
COPY --from=dependencies /e2e /e2e
WORKDIR /e2e
ENV PLAYWRIGHT_BROWSERS_PATH=/e2e/browsers
RUN node node_modules/playwright/cli.js install chromium --with-deps --no-shell
RUN node node_modules/playwright/cli.js install chromium --only-shell
COPY finish.py /build/finish.py
RUN python /build/finish.py
