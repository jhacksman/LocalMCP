FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

ENV PORT=8010
ENV LOG_LEVEL=info
ENV TOTAL_VRAM_GB=64
ENV UNLOAD_TIMEOUT_MINUTES=30

EXPOSE 8010

CMD ["node", "dist/index.js"]
