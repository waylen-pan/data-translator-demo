FROM node:20-slim AS build

WORKDIR /app

# 先拷贝依赖清单以便缓存命中
COPY package.json package-lock.json ./
RUN npm ci

# 再拷贝源码并构建
COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
