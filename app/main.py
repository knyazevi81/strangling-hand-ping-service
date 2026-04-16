from fastapi import FastAPI
from app.presentation.fastapi.routers.ping import router as ping_router


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Ping Service",
        description="VLESS key latency measurement microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    _app.include_router(ping_router)

    return _app


app = create_app()
