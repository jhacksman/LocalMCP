FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

ENV PORT=8015
ENV LOG_LEVEL=info
ENV MODEL_ID=stabilityai/stable-diffusion-xl-base-1.0
ENV MODEL_CACHE_DIR=./model_cache
ENV VRAM_USAGE_GB=16
ENV ENABLE_4BIT_QUANTIZATION=true
ENV ENABLE_CPU_OFFLOAD=true
ENV MAX_IMAGE_WIDTH=1024
ENV MAX_IMAGE_HEIGHT=1024

EXPOSE 8015

CMD ["node", "dist/index.js"]
