"""FastAPI application factory and entrypoint for the ApplyPilot API.

The application is fully synchronous: route handlers are plain ``def`` functions
and the database layer uses the SQLAlchemy 2.0 sync engine/session.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from applypilot.api.routes import api_router
from applypilot.core.config import get_settings
from applypilot.core.logging import configure_logging, get_logger


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    app = FastAPI(title=settings.app_name)

    # Allow the configured web origin plus the conventional local dev origin,
    # de-duplicated while preserving order.
    allowed_origins = list(dict.fromkeys([settings.web_url, "http://localhost:3000"]))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    logger.info(
        "ApplyPilot API initialised (env=%s, llm_provider=%s, provider_is_local=%s)",
        settings.app_env,
        settings.llm_provider,
        settings.provider_is_local,
    )
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("applypilot.main:app", host="0.0.0.0", port=8000, reload=False)
