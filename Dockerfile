# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY bin ./bin
COPY data ./data
COPY lib ./lib
COPY frp ./frp
COPY scripts ./scripts
COPY ktm.py config.py ./
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

EXPOSE 5000 7000
CMD ["python", "ktm.py"]
