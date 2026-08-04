# Use Debian slim — Alpine often fails Next.js builds (sharp / native deps).
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json ./
# package-lock may be missing if Root Directory is wrong; prefer ci when present.
COPY package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

FROM node:22-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS=--max-old-space-size=1536
ARG NEXT_PUBLIC_AUTH_ENABLED=false
ARG NEXT_PUBLIC_API_BASE_URL=/api/v1
ARG ATE_API_PROXY=http://127.0.0.1:8000
ENV NEXT_PUBLIC_AUTH_ENABLED=$NEXT_PUBLIC_AUTH_ENABLED
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV ATE_API_PROXY=$ATE_API_PROXY
ENV BACKEND_URL=$ATE_API_PROXY
ENV NEXT_EMBED_BASE_PATH=/embed/failure
ENV NEXT_PUBLIC_EMBED_BASE_PATH=/embed/failure
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["sh", "-c", "exec npm run start -- -H 0.0.0.0 -p ${PORT:-3000}"]
