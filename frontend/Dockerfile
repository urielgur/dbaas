FROM node:20-alpine AS build

ARG VITE_API_URL
ARG VITE_DEMO_USERNAME
ARG VITE_DEMO_PASSWORD
ARG VITE_DEMO_MODE

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
