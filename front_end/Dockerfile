# Étape 1 : build Vite. VITE_API_URL est lue AU BUILD (pas à l'exécution).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Étape 2 : fichiers statiques servis par nginx (aucun Node en production)
FROM nginx:1.27-alpine
# Templates rendus au démarrage par l'image nginx (envsubst) dans /etc/nginx/conf.d/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY securite.inc.template /etc/nginx/templates/securite.inc.template
# Origine de l'API autorisée par la CSP (connect-src), surchargeable à l'exécution
ENV API_ORIGIN=http://localhost:8000
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -q --spider http://127.0.0.1/ || exit 1
