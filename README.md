# ping-service

Микросервис для измерения латентности VLESS ключей.  
Запускает xray локально, подключается через SOCKS5, измеряет задержку.

## Архитектура

```
Фронт
  ↕ WebSocket /api/v1/ping/ws
Бэкенд Savebit (api.savebit.ru)
  - проверяет JWT токен
  - берёт личные подписки пользователя из БД
  - передаёт URI в ping-service
  ↕ WebSocket ws://host.docker.internal:8088/ws/ping
Ping Service (порт 8088)
  - запускает xray процесс для каждого ключа
  - измеряет задержку через SOCKS5
  - стримит результаты по мере готовности
```

## Структура

```
app/
├── domain/
│   ├── models/models.py          — VlessKey, PingResult, PingRequest
│   └── exceptions/exceptions.py — доменные исключения
├── application/
│   └── use_cases/ping.py         — ping_single_key, ping_keys_stream
├── infrastructure/
│   └── xray/
│       ├── parser.py             — парсер vless:// URI
│       ├── config.py             — генератор xray конфига
│       └── runner.py             — запуск xray процесса
└── presentation/
    └── fastapi/
        ├── routers/ping.py       — WebSocket + REST эндпоинты
        └── schemas/schemas.py    — Pydantic схемы
```

## Деплой

```bash
docker compose up -d
```

Проверка:
```bash
curl http://localhost:8088/health
```

## Интеграция с бэкендом Savebit

Скопируй `backend_ping_router.py` в бэкенд как:
```
app/presentation/fastapi/routers/ping.py
```

Добавь в `main.py`:
```python
from app.presentation.fastapi.routers.ping import router as ping_router
_app.include_router(ping_router, prefix="/api/v1")
```

Добавь зависимость в бэкенд:
```bash
# В pyproject.toml бэкенда добавь:
"websockets>=13.0"
```

## WebSocket протокол

**Клиент → Бэкенд (первое сообщение):**
```json
{"token": "eyJhbGci..."}
```

**Бэкенд → Клиент (стрим результатов):**
```json
{"uri": "vless://...", "name": "...", "status": "ok", "avg_ms": 42.1, "min_ms": 38.0, "max_ms": 47.3, "loss": 0, "total": 3}
{"uri": "vless://...", "name": "...", "status": "timeout", "avg_ms": null, "loss": 3, "total": 3}
{"done": true, "total": 2}
```

## Эндпоинты ping-service

| Метод | Путь | Описание |
|-------|------|----------|
| WS | `/ws/ping` | Стриминг результатов |
| POST | `/ping/one?uri=vless://...` | Пинг одного ключа |
| GET | `/health` | Статус + наличие xray |
| GET | `/docs` | Swagger UI |
