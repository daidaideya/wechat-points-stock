FROM docker.1ms.run/library/node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM docker.1ms.run/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY entrypoint.sh ./entrypoint.sh
COPY start.sh ./start.sh
COPY migrate_note.py ./migrate_note.py
COPY --from=frontend-builder /frontend/dist ./frontend/dist

RUN mkdir -p logs data static/uploads \
    && chmod +x ./entrypoint.sh ./start.sh

EXPOSE 5711

CMD ["sh", "./entrypoint.sh"]
