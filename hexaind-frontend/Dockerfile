FROM node:16 AS build

RUN npm install --location=global @angular/cli@16.2.4

WORKDIR /usr/local/src/hexaind_frontend

ENV NODE_OPTIONS="--max-old-space-size=4096" \
    NPM_CACHE_DIR=/var/cache/npm

RUN npm config set save false \
    && npm config set cache ${NPM_CACHE_DIR}

RUN --mount=type=cache,id=frontend-requirements,target=${NPM_CACHE_DIR} \
    --mount=type=bind,source=package.json,target=package.json,readonly \
    --mount=type=bind,source=package-lock.json,target=package-lock.json,readonly \
    npm install

RUN --mount=type=bind,source=package.json,target=package.json,readonly \
    --mount=type=bind,source=src,target=src,readwrite \
    --mount=type=bind,source=angular.json,target=angular.json,readonly \
    --mount=type=bind,source=tsconfig.json,target=tsconfig.json,readonly \
    --mount=type=bind,source=tsconfig.app.json,target=tsconfig.app.json,readonly \
    --mount=type=bind,source=tsconfig.spec.json,target=tsconfig.spec.json,readonly \
    npm run build-prod

FROM nginx:alpine-slim

RUN chown nginx:nginx -R /usr/share/nginx/html /var/cache/nginx /etc/nginx /var/log/nginx

RUN touch /var/run/nginx.pid && chown nginx:nginx  /var/run/nginx.pid

COPY ./contrib/nginx.conf /etc/nginx/conf.d/default.conf

COPY ./update_environment.sh /docker-entrypoint.d/40-update-environment.sh

COPY --from=build  --chown=nginx:nginx /var/dist /usr/share/nginx/html

USER nginx
