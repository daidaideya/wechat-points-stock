FROM docker.1ms.run/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

WORKDIR /app

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY entrypoint.sh ./entrypoint.sh
COPY start.sh ./start.sh

# frontend/dist is NOT baked into the image by default — docker-compose mounts
# ./frontend/dist. For a self-contained image, build the SPA first and:
#   docker build --build-arg INCLUDE_FRONTEND=1 ...
# or copy dist into the context before build.
RUN mkdir -p frontend/dist logs data static/uploads \
    && chmod +x ./entrypoint.sh ./start.sh

EXPOSE 5711

# Default CMD uses entrypoint.sh (init DB if missing, require frontend/dist).
CMD ["sh", "./entrypoint.sh"]
