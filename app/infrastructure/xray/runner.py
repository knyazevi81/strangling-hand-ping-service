import asyncio
import json
import os
import socket
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.domain.exceptions.exceptions import XrayNotFoundError, XrayStartError
from app.infrastructure.xray.config import build_xray_config
from app.domain.models.models import VlessKey


XRAY_CANDIDATES = [
    "xray",
    "./xray",
    "/usr/local/bin/xray",
    "/usr/bin/xray",
    "/opt/xray/xray",
]


def find_xray() -> str:
    for candidate in XRAY_CANDIDATES:
        try:
            r = subprocess.run(
                [candidate, "version"],
                capture_output=True,
                timeout=3,
            )
            if r.returncode == 0:
                return candidate
        except Exception:
            continue
    raise XrayNotFoundError()


def find_free_port(start: int = 11000, end: int = 13000) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Нет свободных портов в диапазоне")


async def wait_for_socks(port: int, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return True
        except OSError:
            await asyncio.sleep(0.15)
    return False


@asynccontextmanager
async def xray_process(key: VlessKey, xray_bin: str) -> AsyncGenerator[int, None]:
    """
    Контекстный менеджер — запускает xray и возвращает SOCKS5 порт.
    Гарантирует завершение процесса при выходе.
    """
    socks_port = find_free_port()
    cfg = build_xray_config(key, socks_port)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(cfg, f)
        config_path = f.name

    proc = subprocess.Popen(
        [xray_bin, "run", "-c", config_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        ready = await wait_for_socks(socks_port, timeout=8.0)
        if not ready:
            raise XrayStartError(8.0)
        yield socks_port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        if os.path.exists(config_path):
            os.remove(config_path)
