FROM node:22.14-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["sh", "-c", "npx serve -s dist -l ${PORT:-3000} --no-clipboard"]