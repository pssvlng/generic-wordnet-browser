# Stage 1
FROM node:20-buster as build-step
WORKDIR /app
 
COPY . /app
RUN npm install
RUN npm run build
 
# Stage 2
FROM nginx:1.17.1-alpine
COPY --from=build-step /app/dist /usr/share/nginx/html