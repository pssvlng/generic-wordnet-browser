# Stage 1
FROM node:20-buster as build-step
WORKDIR /app
ARG BASE_HREF=/
ARG BACKEND_UPSTREAM=backend:5000
 
COPY . /app
RUN npm install
RUN npm run build -- --base-href "$BASE_HREF"
RUN sed "s@backend:5000@${BACKEND_UPSTREAM}@g" nginx.conf > /tmp/wordnet-nginx.conf
 
# Stage 2
FROM nginx:1.17.1-alpine
COPY --from=build-step /app/dist /usr/share/nginx/html
COPY --from=build-step /tmp/wordnet-nginx.conf /etc/nginx/conf.d/default.conf
