FROM node:22.14-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 8080

CMD ["sh", "-c", "npx serve -s dist -l tcp://0.0.0.0:${PORT:-8080} --no-clipboard"]