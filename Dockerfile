FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY xray /usr/local/bin/xray
RUN chmod +x /usr/local/bin/xray && xray version

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
