from typing import Optional
from pydantic import BaseModel, Field


class PingRequestSchema(BaseModel):
    keys: list[str] = Field(min_length=1, max_length=50)
    count: int = Field(default=3, ge=1, le=10)
    timeout: float = Field(default=8.0, ge=1.0, le=30.0)
    test_url: str = "http://www.gstatic.com/generate_204"
    concurrency: int = Field(default=5, ge=1, le=10)


class PingResultSchema(BaseModel):
    uri: str
    name: str
    host: str
    port: int
    security: str
    status: str
    min_ms: Optional[float] = None
    avg_ms: Optional[float] = None
    max_ms: Optional[float] = None
    loss: int = 0
    total: int = 0
    error: Optional[str] = None


class PingDoneSchema(BaseModel):
    done: bool = True
    total: int
