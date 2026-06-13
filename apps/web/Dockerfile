# syntax=docker/dockerfile:1
#
# ApplyPilot web (Next.js 16 App Router) image.
# Build context is the REPO ROOT so the pnpm workspace resolves correctly.
#   docker build -f apps/web/Dockerfile -t applypilot-web:local .
#
# Relies on Next.js `output: "standalone"` (set in next.config.ts) with
# outputFileTracingRoot pinned to the monorepo root, so the standalone bundle
# preserves the apps/web/ path layout.

# ---------- base ----------
FROM node:24-alpine AS base
RUN corepack enable
WORKDIR /app

# ---------- deps ----------
# Install workspace dependencies using only the manifests for cache efficiency.
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# ---------- builder ----------
FROM base AS builder
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# Reuse installed node_modules (pnpm uses relative symlinks, preserved by COPY).
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY . .
RUN pnpm --filter web build

# ---------- runner ----------
FROM base AS runner
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app

# Run as an unprivileged user.
RUN addgroup -g 1001 -S nodejs \
    && adduser -u 1001 -S nextjs -G nodejs

# Standalone server bundle + static assets + public dir.
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/public ./apps/web/public

USER nextjs
EXPOSE 3000

CMD ["node", "apps/web/server.js"]
