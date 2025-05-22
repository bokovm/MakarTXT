FROM node:18 as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

# Явно копируем исходники
COPY src ./src
COPY public/ ./public
COPY *.js *.json ./
COPY index.html . 
COPY vite.config.js .

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html