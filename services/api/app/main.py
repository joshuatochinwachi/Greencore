"""
Greencore FastAPI application factory.

Security:
- CORS locked to known origins from settings (Section 9.6).
- Rate limiting on auth endpoints via slowapi.
- No public sign-up endpoint (Section 9.1).

Error responses always use the standard shape from Section 14.8:
  { "error": "machine_readable_code", "message": "Human-readable explanation.", "field_errors": {...} }
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import auth as auth_router

logger = logging.getLogger("greencore")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    settings = get_settings()
    logger.info(
        "Greencore API starting",
        extra={"environment": settings.environment},
    )
    yield
    logger.info("Greencore API shutting down.")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Greencore API",
        description="Transport driver and route management platform — FastAPI backend.",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS (Section 9.6) ────────────────────────────────────────────────────
    # Driver app uses bearer token auth, not cookies — CSRF surface is minimal.
    # Admin dashboard origins are explicitly listed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Standard error handlers ───────────────────────────────────────────────
    # Produces the Section 14.8 error shape for validation failures.
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        field_errors = {}
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
            field_errors[field] = err["msg"]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "One or more fields failed validation.",
                "field_errors": field_errors,
            },
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router)

    # Phase 1 routers — registered here once built:
    # from app.routers import drivers, routes, allocations, shifts, deliveries
    # app.include_router(drivers.router)
    # ...

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["meta"], include_in_schema=not settings.is_production)
    def health():
        return {"status": "ok", "environment": settings.environment}

    return app


# Module-level app instance for uvicorn / gunicorn.
app = create_app()
