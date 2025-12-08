from datetime import datetime, timezone
from typing import Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.core.config import get_settings
from backend.core.db import get_engine
from backend.core.response import fail, ok, success_response, error_response, StandardResponse
from backend.core.error_codes import SystemErrorCodes, ValidationErrorCodes
# 导入核心路由模块
from backend.routers import (
    health,
    projects,
    authentication,
    ad_accounts,
    ad_spend,
    channels,
    topup,  # ✅ 充值管理API (已修复)
    daily_reports,  # ✅ 日报管理API (已修复)
    suppliers,  # ✅ 供应商管理API (full_pipeline v2)
    settlements,  # ✅ 结算管理API (full_pipeline v2)
    transfers,  # ✅ 死号余额迁移API (新增)
    ledger,  # ✅ 财务总账API (启用 - finance_profit bugfix)
    finance_profit,  # ✅ 财务利润API (从 ledger 迁出)
    import_jobs,  # ✅ 数据导入API (已实现ImportJob模型)
    reconciliation,  # ✅ 对账管理API (新启用)
    reports,  # ✅ 报表管理API (v2.0 - 完整重构)
    # 暂时注释掉缺失依赖的路由,以便测试运行:
    # ai_monitoring,  # AI监控API
    # supabase_auth,  # 使用authentication代替
    # ai_analytics,  # 待完善
    # project_templates,  # 待完善
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
app.include_router(health.router, prefix=API_V1_PREFIX)  # 健康检查
app.include_router(projects.router, prefix=API_V1_PREFIX)  # 项目管理
app.include_router(authentication.router, prefix=API_V1_PREFIX)  # 用户认证
app.include_router(ad_spend.router, prefix=API_V1_PREFIX)  # 广告消耗
app.include_router(ad_accounts.router, prefix=API_V1_PREFIX)  # 广告账户
app.include_router(channels.router, prefix=API_V1_PREFIX)  # 渠道管理
app.include_router(topup.router, prefix=API_V1_PREFIX)  # 充值管理
app.include_router(daily_reports.router, prefix=API_V1_PREFIX)  # 日报管理 ✅ 新启用
app.include_router(suppliers.router, prefix=API_V1_PREFIX)  # 供应商管理 ✅ full_pipeline v2
app.include_router(settlements.router, prefix=API_V1_PREFIX)  # 结算管理 ✅ full_pipeline v2
app.include_router(transfers.router, prefix=API_V1_PREFIX)  # 死号余额迁移 ✅ 新增
app.include_router(ledger.router, prefix=API_V1_PREFIX)  # 财务总账 ✅ 启用 (finance_profit bugfix)
app.include_router(finance_profit.router, prefix=API_V1_PREFIX)  # 财务利润 ✅ 从 ledger 迁出
app.include_router(import_jobs.router, prefix=API_V1_PREFIX)  # 数据导入 ✅ 已实现ImportJob模型
app.include_router(reconciliation.router, prefix=API_V1_PREFIX)  # 对账管理 ✅ 新启用
app.include_router(reports.router, prefix=API_V1_PREFIX)  # 报表管理 ✅ v2.0 完整重构
# 暂时注释掉缺失依赖的路由,以便测试运行:
# app.include_router(ai_monitoring.router, prefix=API_V1_PREFIX)  # AI监控


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


# 注意：/api/v1/health 端点已通过 health.router 注册，无需重复定义


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


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理 Pydantic 验证错误，返回符合 SoT 约定的 StandardResponse 格式

    SoT Ref: ERROR_CODES_SOT.md v2.1 第 1.3 节 (Envelope 格式)
    错误码: VALIDATION_001 (必填字段缺失) / VALIDATION_002 (格式无效)
    """
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        error_type = first_error.get("type", "")
        error_msg = first_error.get("msg", "参数验证失败")
        loc = first_error.get("loc", [])
        field_name = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else str(loc[0]) if loc else "unknown"

        if "missing" in error_type or "required" in error_type:
            code = ValidationErrorCodes.REQUIRED_FIELD_MISSING.code
            message = f"必填字段缺失: {field_name}"
        else:
            code = ValidationErrorCodes.INVALID_FORMAT.code
            message = f"格式无效: {field_name} - {error_msg}"
    else:
        code = ValidationErrorCodes.INVALID_FORMAT.code
        message = "参数验证失败"

    return error_response(
        code=code,
        message=message,
        status_code=422
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
    message = str(exc) if settings.debug else "Internal server error"
    return fail(code=SystemErrorCodes.INTERNAL_ERROR.code, message=message, status_code=SystemErrorCodes.INTERNAL_ERROR.status_code)



 
