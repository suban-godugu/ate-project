FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .

ARG NEXT_EMBED_BASE_PATH=/embed/scan-debug-rec
ARG NEXT_PUBLIC_EMBED_BASE_PATH=/embed/scan-debug-rec
ARG NEXT_PUBLIC_API_MODE=live
ENV NEXT_EMBED_BASE_PATH=$NEXT_EMBED_BASE_PATH
ENV NEXT_PUBLIC_EMBED_BASE_PATH=$NEXT_PUBLIC_EMBED_BASE_PATH
ENV NEXT_PUBLIC_API_MODE=$NEXT_PUBLIC_API_MODE

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3042

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3042

CMD sh -c "npm run start -- -H 0.0.0.0 -p ${PORT:-3042}"
