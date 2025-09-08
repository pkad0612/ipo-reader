# backend/Dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr poppler-utils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV TRANSFORMERS_CACHE=/tmp/hf \
    HF_HOME=/tmp/hf \
    SENTENCE_TRANSFORMERS_HOME=/tmp/sent \
    DATA_DIR=/data \
    PORT=7860

RUN mkdir -p /data /tmp/hf /tmp/sent && chmod -R 777 /data /tmp

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy *only* backend code so /app/main.py exists
COPY backend /app

EXPOSE 7860
CMD sh -c 'python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}'
