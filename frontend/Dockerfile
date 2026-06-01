FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

ENV NODE_ENV=production
ENV PORT=5173

WORKDIR /app

COPY server.mjs .
COPY --from=build /app/dist ./dist

EXPOSE 5173

CMD ["node", "server.mjs"]
