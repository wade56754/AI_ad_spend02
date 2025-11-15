from datetime import datetime, timezone
from typing import Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from core.config import get_settings
from core.db import get_engine
from core.response import fail, ok, success_response, StandardResponse
# 导入核心路由模块（暂时排除有问题的模块）
from routers import (
    projects,
    authentication,
    # supabase_auth,  # 暂时跳过
    # ai_analytics,  # 暂时跳过
    # project_templates,  # 暂时跳过
    ad_accounts,
    ad_spend,
    channels,
    topup,  # ✅ 已修复装饰器问题，重新启用
    # import_jobs,  # 暂时跳过
    # reconciliations,  # 暂时跳过
    # reports,  # 暂时跳过
    # daily_reports,  # 暂时跳过
    # reconciliation,  # 暂时跳过
    # ad_account,  # 暂时跳过
    ledger,  # 新增财务总账API
    reconciliation_extended,  # 新增对账管理API
    ai_monitoring,  # 新增AI监控API
)



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

# 注册核心API路由
app.include_router(projects.router, prefix=API_V1_PREFIX)
app.include_router(authentication.router, prefix=API_V1_PREFIX)
app.include_router(ad_spend.router, prefix=API_V1_PREFIX)
app.include_router(ad_accounts.router, prefix=API_V1_PREFIX)
app.include_router(channels.router, prefix=API_V1_PREFIX)
app.include_router(topup.router, prefix=API_V1_PREFIX)  # ✅ 充值管理API (已修复)
app.include_router(ledger.router, prefix=API_V1_PREFIX)  # 新增财务总账API
app.include_router(reconciliation_extended.router, prefix=API_V1_PREFIX)  # 新增对账管理API
app.include_router(ai_monitoring.router, prefix=API_V1_PREFIX)  # 新增AI监控API
# 其他路由暂时跳过，待修复导入问题后再启用


@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Return service health status (Kubernetes compatible)."""
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
    from core.response import success_response, error_response
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
    from core.response import success_response
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



 
