# syntax=docker/dockerfile:1
# Build context is the REPO ROOT (the Next app is the `web` pnpm workspace package).
FROM node:22-slim

ENV NEXT_TELEMETRY_DISABLED=1

# Pin pnpm via corepack so it matches the committed pnpm-lock.yaml.
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate

WORKDIR /app

# Install workspace deps first for layer caching. Copy every file the frozen
# install needs, preserving the web/ path so the workspace resolves.
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json ./
COPY web/package.json ./web/package.json
RUN pnpm install --frozen-lockfile

# Copy the web sources (tsconfig extends ../tsconfig.base.json) and build.
COPY web ./web
RUN pnpm --filter @wtw/web build

EXPOSE 3000

CMD ["pnpm", "--filter", "@wtw/web", "start"]
