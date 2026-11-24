FROM node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --no-fund --no-audit
COPY frontend ./
RUN npm run build
FROM nginx:1.28-alpine@sha256:a8b39bd9cf0f83869a2162827a0caf6137ddf759d50a171451b335cecc87d236
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
