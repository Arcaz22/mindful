from fastapi import FastAPI

from app.core.settings import get_settings
from app.core.logging import configure_logging
from app.core.middleware.error_handler import ErrorHandlingMiddleware
from app.core.middleware.request_id import RequestIdMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.interfaces.http.routers import router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="FM Boilerplate",
        version="0.1.0",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app


app = create_app()
