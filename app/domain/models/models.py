from __future__ import annotations
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel


class PingStatus(StrEnum):
    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"


class VlessKey(BaseModel):
    """Value object — распарсенный VLESS ключ."""
    uri: str
    name: str
    host: str
    port: int
    uuid: str
    security: str       # reality | tls | none
    sni: str
    fingerprint: str
    public_key: str
    short_id: str
    spider_x: str
    network_type: str   # tcp | grpc | ws
    flow: str
    encryption: str


class PingResult(BaseModel):
    """Результат пинга одного ключа."""
    uri: str
    name: str
    host: str
    port: int
    security: str
    status: PingStatus
    min_ms: Optional[float] = None
    avg_ms: Optional[float] = None
    max_ms: Optional[float] = None
    loss: int = 0
    total: int = 0
    error: Optional[str] = None


class PingRequest(BaseModel):
    """Запрос на пинг списка ключей."""
    keys: list[str]             # raw vless:// URIs
    count: int = 3              # попыток на ключ
    timeout: float = 8.0       # таймаут одной попытки
    test_url: str = "http://www.gstatic.com/generate_204"
