import asyncio
import time
from collections.abc import AsyncGenerator

import httpx

from app.domain.models.models import PingResult, PingStatus, VlessKey
from app.domain.exceptions.exceptions import (
    InvalidVlessUriError,
    XrayNotFoundError,
    XrayStartError,
)
from app.infrastructure.xray.parser import parse_vless_uri
from app.infrastructure.xray.runner import find_xray, xray_process


async def ping_single_key(
    uri: str,
    count: int,
    timeout: float,
    test_url: str,
) -> PingResult:
    """
    Пингует один VLESS ключ.
    Запускает xray, делает count HTTP запросов через SOCKS5,
    возвращает агрегированный результат.
    """
    # 1. Парсим URI
    try:
        key: VlessKey = parse_vless_uri(uri)
    except InvalidVlessUriError as e:
        return PingResult(
            uri=uri, name=uri[:50], host="?", port=0,
            security="?", status=PingStatus.ERROR,
            total=count, loss=count, error=str(e),
        )

    result = PingResult(
        uri=uri, name=key.name, host=key.host,
        port=key.port, security=key.security,
        status=PingStatus.ERROR, total=count, loss=count,
    )

    # 2. Находим xray
    try:
        xray_bin = find_xray()
    except XrayNotFoundError as e:
        result.error = str(e)
        return result

    # 3. Запускаем xray и измеряем задержки
    delays: list[float] = []

    try:
        async with xray_process(key, xray_bin) as socks_port:
            proxy_url = f"socks5://127.0.0.1:{socks_port}"
            transport = httpx.AsyncHTTPTransport(proxy=proxy_url)

            async with httpx.AsyncClient(
                transport=transport,
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as client:
                for _ in range(count):
                    try:
                        t0 = time.perf_counter()
                        r = await client.get(test_url)
                        elapsed = (time.perf_counter() - t0) * 1000
                        if r.status_code in (200, 204):
                            delays.append(round(elapsed, 1))
                    except Exception:
                        pass
                    await asyncio.sleep(0.3)

    except XrayStartError as e:
        result.error = str(e)
        result.status = PingStatus.TIMEOUT
        return result
    except Exception as e:
        result.error = str(e)
        return result

    # 4. Агрегируем
    if delays:
        result.status = PingStatus.OK
        result.min_ms = min(delays)
        result.avg_ms = round(sum(delays) / len(delays), 1)
        result.max_ms = max(delays)
        result.loss = count - len(delays)
    else:
        result.status = PingStatus.TIMEOUT
        result.loss = count
        result.error = "Все попытки провалились"

    return result


async def ping_keys_stream(
    uris: list[str],
    count: int,
    timeout: float,
    test_url: str,
    concurrency: int = 5,
) -> AsyncGenerator[PingResult, None]:
    """
    Пингует ключи параллельно с ограничением concurrency.
    Yields результаты по мере готовности.
    """
    semaphore = asyncio.Semaphore(concurrency)
    queue: asyncio.Queue[PingResult] = asyncio.Queue()

    async def _ping_with_sem(uri: str) -> None:
        async with semaphore:
            result = await ping_single_key(uri, count, timeout, test_url)
            await queue.put(result)

    tasks = [asyncio.create_task(_ping_with_sem(uri)) for uri in uris]

    completed = 0
    total = len(uris)

    while completed < total:
        result = await queue.get()
        completed += 1
        yield result

    # Ждём завершения всех задач
    await asyncio.gather(*tasks, return_exceptions=True)
