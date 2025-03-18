FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

ENV PORT=8005
ENV LOG_LEVEL=info
ENV VECTOR_DB_PATH=./data
ENV EMBEDDING_MODEL=all-MiniLM-L6-v2
ENV VRAM_USAGE_GB=2

EXPOSE 8005

CMD ["node", "dist/index.js"]
