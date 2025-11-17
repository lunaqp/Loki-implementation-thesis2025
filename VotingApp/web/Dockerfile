# Build stage
FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# serve with nginx
#FROM nginx:1.27-alpine
FROM nginx:1.27
COPY --from=build /app/dist /usr/share/nginx/html
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Optional single-page app fallback?
EXPOSE 80