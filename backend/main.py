from datetime import datetime, timezone
from typing import Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.core.config import get_settings
from backend.core.db import get_engine
from backend.core.response import fail, ok
from backend.routers import ad_accounts, ad_spend, channels, import_jobs, projects, reconciliations, reports, topups

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_V1_PREFIX = "/api/v1"

app.include_router(projects.router, prefix=API_V1_PREFIX)
app.include_router(channels.router, prefix=API_V1_PREFIX)
app.include_router(ad_accounts.router, prefix=API_V1_PREFIX)
app.include_router(ad_spend.router, prefix=API_V1_PREFIX)
app.include_router(reconciliations.router, prefix=API_V1_PREFIX)
app.include_router(reports.router, prefix=API_V1_PREFIX)
app.include_router(topups.router, prefix=API_V1_PREFIX)
app.include_router(import_jobs.router, prefix=API_V1_PREFIX)


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Return service health status (Kubernetes compatible)."""
    from backend.core.response import success_response
    return success_response(
        data={
            "status": "ok",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
        message="Health check passed",
    )


@app.get("/readyz")
async def readyz() -> JSONResponse:
    """Readiness probe including database connectivity (Kubernetes compatible)."""
    from backend.core.response import success_response, error_response
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        message = str(exc) if settings.debug else "Readiness check failed"
        return error_response(
            message=message,
            code="READY_CHECK_FAILED",
            status_code=503,
            details={"checks": {"database": "error"}}
        )

    return success_response(
        data={"status": "ok", "checks": {"database": "ok"}},
        message="Readiness check passed"
    )


@app.get("/api/v1/health")
async def health_api() -> JSONResponse:
    """API version health check for consistency with documentation."""
    from backend.core.response import success_response
    return success_response(
        data={
            "status": "ok",
            "service": "ai-ad-spend-backend",
            "version": "v2.1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
        message="API health check passed",
    )


@app.api_route("/api/health", methods=["GET", "OPTIONS"])
async def health_root() -> JSONResponse:
    """Compatibility health check for tests expecting flat JSON under /api/health."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": "v2.1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
    )


def _extract_error(detail: object, status_code: int) -> Tuple[str, str]:
    default_code = f"HTTP_{status_code}"
    if isinstance(detail, dict):
        code = detail.get("code") or default_code
        message = detail.get("message") or detail.get("detail") or str(detail)
        return str(code), str(message)
    if detail is None:
        return default_code, ""
    return default_code, str(detail)


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    code, message = _extract_error(exc.detail, exc.status_code)
    return fail(code=code, message=message, status_code=exc.status_code)


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
    message = str(exc) if settings.debug else "Internal server error"
    return fail(code="HTTP_500", message=message, status_code=500)



