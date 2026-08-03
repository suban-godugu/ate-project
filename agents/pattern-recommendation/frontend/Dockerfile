FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY . .
ARG VITE_EMBED_BASE=/embed/pattern-rec/
ARG VITE_API_BASE_URL=/embed/pattern-rec/api-proxy
ENV VITE_EMBED_BASE=$VITE_EMBED_BASE
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3041
CMD sh -c "serve -s dist -l ${PORT:-3041}"
