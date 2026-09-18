FROM docker.1ms.run/library/node:20-bookworm-slim AS frontend-builder

WORKDIR /frontend

# Keep dependency installation cacheable and reproducible from the lockfile.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

FROM docker.1ms.run/library/python:3.11-slim

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOME=/home/app \
    TZ=Asia/Shanghai

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && addgroup --system --gid "${APP_GID}" app \
    && adduser --system --uid "${APP_UID}" --ingroup app --home /home/app --shell /usr/sbin/nologin app \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app ./app
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app entrypoint.sh ./entrypoint.sh
COPY --chown=app:app start.sh ./start.sh
COPY --from=frontend-builder --chown=app:app /frontend/dist ./frontend/dist

RUN mkdir -p frontend/dist logs data static/uploads \
    && chown -R app:app /app /home/app \
    && chmod -R a-w /app/app /app/scripts /app/frontend \
    && chmod +x ./entrypoint.sh ./start.sh

# The bind-mounted data/log/upload directories remain writable; application
# code and the compiled SPA are read-only at runtime.
USER app

EXPOSE 5711

# Default CMD uses entrypoint.sh (init DB if missing, verify frontend/dist).
CMD ["sh", "./entrypoint.sh"]
