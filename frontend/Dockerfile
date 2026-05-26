FROM node:18-alpine

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm install

RUN npm install -g vue-tsc vite

COPY frontend/ .

RUN vue-tsc --noEmit || true && vite build

FROM nginx:alpine

COPY --from=0 /app/frontend/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/nginx.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]