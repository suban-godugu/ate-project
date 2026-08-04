FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
ARG VITE_EMBED_BASE=/embed/test-opt/
ARG VITE_API_BASE_URL=/embed/test-opt/api-proxy/api/v1
ENV VITE_EMBED_BASE=$VITE_EMBED_BASE
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM node:22-bookworm-slim
WORKDIR /app
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/package-lock.json* ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/scripts ./scripts
EXPOSE 3043
CMD ["sh", "-c", "exec npm run start:render"]
