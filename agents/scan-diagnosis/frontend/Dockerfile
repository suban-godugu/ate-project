FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json ./
COPY package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

FROM node:22-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS=--max-old-space-size=1536
ARG NEXT_EMBED_BASE_PATH=/embed/scan
ARG NEXT_PUBLIC_API_BASE=/embed/scan
ARG ATE_API_PROXY=http://127.0.0.1:8031
ENV NEXT_EMBED_BASE_PATH=$NEXT_EMBED_BASE_PATH
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_API_BASE_URL=/api
ENV ATE_API_PROXY=$ATE_API_PROXY
ENV BACKEND_URL=$ATE_API_PROXY
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
EXPOSE 3030
CMD ["sh", "-c", "exec npx next start -H 0.0.0.0 -p ${PORT:-3030}"]
