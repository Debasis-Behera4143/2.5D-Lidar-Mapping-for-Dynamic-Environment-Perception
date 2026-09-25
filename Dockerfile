FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src ./src
COPY checkpoints ./checkpoints
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
