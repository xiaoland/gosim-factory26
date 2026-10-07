FROM node:20.19.3-bookworm-slim AS build
WORKDIR /src
COPY app/ /src/
RUN cd frontend && npm ci && npm run build
RUN cd backend && npm ci --omit=dev
RUN rm -rf frontend/node_modules backend/node_modules/.cache backend/node_modules/.npm \
    backend/src/**/*.test.* backend/test backend/tests
RUN mkdir -p /out && tar -czf /out/app-runtime.tar.gz frontend backend

FROM scratch
COPY --from=build /out/app-runtime.tar.gz /app-runtime.tar.gz
