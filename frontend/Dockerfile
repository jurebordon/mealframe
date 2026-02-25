# ---- Base stage ----
FROM node:20-alpine AS base

WORKDIR /app

# ---- Dependencies stage ----
FROM base AS deps

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --ignore-scripts; else npm install --ignore-scripts; fi

# ---- Development stage ----
FROM deps AS dev

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# ---- Build stage ----
FROM deps AS builder

COPY . .

# Build arguments baked into the client bundle
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_GOOGLE_SCRIPT_URL
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_GOOGLE_SCRIPT_URL=${NEXT_PUBLIC_GOOGLE_SCRIPT_URL}
ENV NEXT_PUBLIC_SITE_URL=${NEXT_PUBLIC_SITE_URL}

RUN npm run build

# ---- Production stage ----
FROM base AS prod

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
