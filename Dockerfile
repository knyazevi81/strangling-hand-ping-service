FROM python:3.13-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем xray из официального релиза
ARG XRAY_VERSION=1.8.24
ARG TARGETARCH=amd64
RUN curl -fsSL \
    "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-${TARGETARCH}.zip" \
    -o /tmp/xray.zip \
    && unzip /tmp/xray.zip xray -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/xray \
    && rm /tmp/xray.zip \
    && xray version

# Python зависимости
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi>=0.135.0" \
    "uvicorn[standard]>=0.35.0" \
    "httpx[socks]>=0.28.0" \
    "websockets>=13.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0"

COPY . .

EXPOSE 8088

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
