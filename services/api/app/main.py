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
        description=(
            "Transport driver and route management platform — FastAPI backend.\n\n"
            "**Authentication:** All endpoints (except `/auth/login`) require a Bearer token.\n"
            "Obtain a token via `POST /auth/login` then pass it as `Authorization: Bearer <token>`.\n\n"
            "**Roles:** `super_admin` has full access. `admin` has read access to drivers/routes."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "auth", "description": "Login, token refresh, and logout."},
            {"name": "drivers", "description": "Driver CRUD, activation/deactivation."},
            {"name": "routes", "description": "Route management and waypoint editing."},
            {"name": "allocations", "description": "Assign drivers to routes and confirm allocations."},
            {"name": "meta", "description": "Health check and API info."},
        ],
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
    from app.routers import auth as auth_router
    from app.routers import drivers as drivers_router
    from app.routers import routes as routes_router
    from app.routers import allocations as allocations_router

    app.include_router(auth_router.router)
    app.include_router(drivers_router.router)
    app.include_router(routes_router.router)
    app.include_router(allocations_router.router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "environment": settings.environment}

    # ── Root info endpoint ────────────────────────────────────────────────────
    @app.get("/", tags=["meta"])
    def root():
        """API info and endpoint map."""
        return {
            "name": "Greencore API",
            "version": "0.1.0",
            "description": "Transport driver and route management platform.",
            "environment": settings.environment,
            "status": "ok",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
            "endpoints": {
                "auth": {
                    "description": "Authentication — login, token refresh, logout.",
                    "routes": [
                        {"method": "POST", "path": "/auth/login",   "auth": False, "summary": "Obtain access + refresh tokens"},
                        {"method": "POST", "path": "/auth/refresh",  "auth": True,  "summary": "Refresh access token"},
                        {"method": "POST", "path": "/auth/logout",   "auth": True,  "summary": "Revoke refresh token"},
                    ],
                },
                "drivers": {
                    "description": "Driver management — CRUD and status control.",
                    "routes": [
                        {"method": "GET",   "path": "/drivers",                     "auth": True, "summary": "List drivers (paginated)"},
                        {"method": "POST",  "path": "/drivers",                     "auth": True, "summary": "Create a new driver"},
                        {"method": "GET",   "path": "/drivers/{id}",               "auth": True, "summary": "Get driver by ID"},
                        {"method": "PATCH", "path": "/drivers/{id}",               "auth": True, "summary": "Partial update driver"},
                        {"method": "POST",  "path": "/drivers/{id}/deactivate",    "auth": True, "summary": "Deactivate driver"},
                        {"method": "POST",  "path": "/drivers/{id}/reactivate",    "auth": True, "summary": "Reactivate driver"},
                    ],
                },
                "routes": {
                    "description": "Route management — stops, waypoints, and scheduling.",
                    "routes": [
                        {"method": "GET",    "path": "/routes",              "auth": True, "summary": "List routes"},
                        {"method": "POST",   "path": "/routes",              "auth": True, "summary": "Create a route"},
                        {"method": "GET",    "path": "/routes/{id}",         "auth": True, "summary": "Get route by ID"},
                        {"method": "PATCH",  "path": "/routes/{id}",         "auth": True, "summary": "Update route details"},
                        {"method": "DELETE", "path": "/routes/{id}",         "auth": True, "summary": "Delete route"},
                    ],
                },
                "allocations": {
                    "description": "Driver-route allocations — assign and confirm.",
                    "routes": [
                        {"method": "GET",  "path": "/allocations",              "auth": True, "summary": "List allocations"},
                        {"method": "POST", "path": "/allocations",              "auth": True, "summary": "Create allocation"},
                        {"method": "GET",  "path": "/allocations/{id}",         "auth": True, "summary": "Get allocation by ID"},
                        {"method": "POST", "path": "/allocations/{id}/confirm", "auth": True, "summary": "Confirm allocation"},
                        {"method": "POST", "path": "/allocations/{id}/cancel",  "auth": True, "summary": "Cancel allocation"},
                    ],
                },
            },
        }

    return app


# Module-level app instance for uvicorn / gunicorn.
app = create_app()
