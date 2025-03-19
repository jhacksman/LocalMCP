FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

ENV PORT=8012
ENV LOG_LEVEL=info
ENV TEMP_DIR=./temp
ENV OCR_WORKER_THREADS=2
ENV PDF_WORKER_THREADS=2
ENV VRAM_USAGE_GB=1

EXPOSE 8012

CMD ["node", "dist/index.js"]
