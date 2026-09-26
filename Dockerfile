FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --include=dev
COPY frontend ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000

RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.0.0"

COPY requirements-render.txt .
RUN pip install -r requirements-render.txt

COPY src ./src
COPY checkpoints ./checkpoints
COPY data/sample_kitti ./data/sample_kitti
COPY data/semantic_kitti ./data/semantic_kitti
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 10000

CMD uvicorn src.backend.app:app --host 0.0.0.0 --port ${PORT}
