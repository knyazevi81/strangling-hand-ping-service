import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.application.use_cases.ping import ping_keys_stream, ping_single_key
from app.infrastructure.xray.runner import find_xray
from app.domain.exceptions.exceptions import XrayNotFoundError
from app.presentation.fastapi.schemas.schemas import (
    PingRequestSchema,
    PingResultSchema,
    PingDoneSchema,
)

router = APIRouter(tags=["ping"])


# ── WebSocket — стриминг результатов по мере готовности ───────────────────────

@router.websocket("/ws/ping")
async def ws_ping(websocket: WebSocket) -> None:
    """
    WebSocket эндпоинт для пинга VLESS ключей.

    Клиент отправляет JSON:
    {
        "keys": ["vless://...", ...],
        "count": 3,
        "timeout": 8.0,
        "concurrency": 5
    }

    Сервер стримит результаты по мере готовности:
    {"uri": "...", "status": "ok", "avg_ms": 42, ...}
    ...
    {"done": true, "total": 5}
    """
    await websocket.accept()

    try:
        raw = await websocket.receive_text()
        try:
            req = PingRequestSchema.model_validate_json(raw)
        except Exception as e:
            await websocket.send_text(
                json.dumps({"error": f"Невалидный запрос: {e}"})
            )
            await websocket.close()
            return

        total = len(req.keys)

        async for result in ping_keys_stream(
            uris=req.keys,
            count=req.count,
            timeout=req.timeout,
            test_url=req.test_url,
            concurrency=req.concurrency,
        ):
            payload = PingResultSchema(**result.model_dump())
            await websocket.send_text(payload.model_dump_json())

        # Финальное сообщение — сигнал завершения
        done = PingDoneSchema(total=total)
        await websocket.send_text(done.model_dump_json())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass


# ── REST — синхронный пинг одного ключа (удобно для тестов) ──────────────────

@router.post("/ping/one", response_model=PingResultSchema)
async def ping_one(uri: str, count: int = 3, timeout: float = 8.0) -> PingResultSchema:
    """Пинг одного ключа — удобно для отладки."""
    result = await ping_single_key(
        uri=uri,
        count=count,
        timeout=timeout,
        test_url="http://www.gstatic.com/generate_204",
    )
    return PingResultSchema(**result.model_dump())


# ── Health check ──────────────────────────────────────────────────────────────

@router.get("/health")
async def health() -> dict:
    try:
        xray_bin = find_xray()
        return {"status": "ok", "xray": xray_bin}
    except XrayNotFoundError:
        return {
            "status": "degraded",
            "xray": None,
            "message": "xray не найден",
        }
