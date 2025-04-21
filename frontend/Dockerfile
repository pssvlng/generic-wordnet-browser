# Stage 1

FROM node:20-buster as build-step

RUN mkdir -p /app

WORKDIR /app

ENV NODE_OPTIONS=--max-old-space-size=2048

COPY package.json /app

RUN npm install

RUN npm update

COPY . /app

RUN npm run build --omit=dev
 

# Stage 2

FROM nginx:1.17.1-alpine

COPY --from=build-step /app/dist /usr/share/nginx/html