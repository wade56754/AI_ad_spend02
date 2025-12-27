from datetime import datetime, timezone
from typing import Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.core.config import get_settings
from backend.core.db import get_engine
from backend.core.response import (
    fail,
    ok,
    success_response,
    error_response,
    StandardResponse,
)
from backend.core.error_codes import SystemErrorCodes, ValidationErrorCodes
from backend.exceptions.custom_exceptions import BaseCustomException

# 导入核心路由模块
from backend.routers import (
    health,
    projects,
    project_members,  # ✅ 项目成员管理API (MASTER.md v4.4 §2.4)
    authentication,
    users,  # ✅ 用户管理API (API_SOT v9.0 §5)
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
    agents,  # ✅ Agent Platform API (新增)
    spend,  # ✅ 消耗导入API (Financial SoT Phase 2)
    dashboard,  # ✅ CEO驾驶舱API (Phase C - MASTER.md v4.4 §6.5)
    weekly_briefs,  # ✅ 周度简报API (B3-weekly-brief.md)
    weekly_reports,  # ✅ 周报管理API (TASK-WEEKLY-002)
    fund,  # ✅ 资金总览API (A2-fund-overview.md)
    finance_v2,  # ✅ 财务管理V2 (资金总览+项目盈亏重构)
    profit,  # ✅ 利润模块API (TASK-PROFIT-001)
    # 暂时注释掉缺失依赖的路由,以便测试运行:
    # ai_monitoring,  # AI监控API
    # supabase_auth,  # 使用authentication代替
    # ai_analytics,  # 待完善
    # project_templates,  # 待完善
)


settings = get_settings()

# 禁用 redirect_slashes 避免 307 重定向导致 Authorization header 丢失
app = FastAPI(title=settings.app_name, debug=settings.debug, redirect_slashes=False)

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
app.include_router(
    project_members.router, prefix=API_V1_PREFIX
)  # 项目成员管理 ✅ MASTER.md v4.4
app.include_router(authentication.router, prefix=API_V1_PREFIX)  # 用户认证
app.include_router(
    users.router, prefix=API_V1_PREFIX
)  # 用户管理 ✅ 新增 (API_SOT v9.0 §5)
app.include_router(ad_spend.router, prefix=API_V1_PREFIX)  # 广告消耗
app.include_router(ad_accounts.router, prefix=API_V1_PREFIX)  # 广告账户
app.include_router(channels.router, prefix=API_V1_PREFIX)  # 渠道管理
app.include_router(topup.router, prefix=API_V1_PREFIX)  # 充值管理
app.include_router(daily_reports.router, prefix=API_V1_PREFIX)  # 日报管理 ✅ 新启用
app.include_router(
    suppliers.router, prefix=API_V1_PREFIX
)  # 供应商管理 ✅ full_pipeline v2
app.include_router(
    settlements.router, prefix=API_V1_PREFIX
)  # 结算管理 ✅ full_pipeline v2
app.include_router(transfers.router, prefix=API_V1_PREFIX)  # 死号余额迁移 ✅ 新增
app.include_router(
    ledger.router, prefix=API_V1_PREFIX
)  # 财务总账 ✅ 启用 (finance_profit bugfix)
app.include_router(
    finance_profit.router, prefix=API_V1_PREFIX
)  # 财务利润 ✅ 从 ledger 迁出
app.include_router(
    import_jobs.router, prefix=API_V1_PREFIX
)  # 数据导入 ✅ 已实现ImportJob模型
app.include_router(reconciliation.router, prefix=API_V1_PREFIX)  # 对账管理 ✅ 新启用
# app.include_router(
#     reconciliation_control.router, prefix=API_V1_PREFIX
# )  # 对账中控 (待实现 - OpenSpec: add-reconciliation-control-center)
app.include_router(reports.router, prefix=API_V1_PREFIX)  # 报表管理 ✅ v2.0 完整重构
app.include_router(agents.router, prefix=API_V1_PREFIX)  # Agent Platform ✅ 新增
app.include_router(
    spend.router, prefix=API_V1_PREFIX
)  # 消耗导入 ✅ Financial SoT Phase 2
app.include_router(
    dashboard.router, prefix=API_V1_PREFIX
)  # CEO驾驶舱 ✅ Phase C - MASTER.md v4.4 §6.5
app.include_router(
    weekly_briefs.router, prefix=API_V1_PREFIX
)  # 周度简报 ✅ B3-weekly-brief.md
app.include_router(
    weekly_reports.router, prefix=API_V1_PREFIX
)  # 周报管理 ✅ TASK-WEEKLY-002
app.include_router(fund.router, prefix=API_V1_PREFIX)  # 资金总览 ✅ A2-fund-overview.md
app.include_router(
    finance_v2.router
)  # 财务管理V2 ✅ 资金总览+项目盈亏重构 (已包含 /api/v1 前缀)
app.include_router(profit.router, prefix=API_V1_PREFIX)  # 利润模块 ✅ TASK-PROFIT-001
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
            details={"checks": {"database": "error"}},
        )

    return success_response(
        data={"status": "ok", "checks": {"database": "ok"}},
        message="Readiness check passed",
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


@app.exception_handler(BaseCustomException)
async def handle_custom_exception(_: Request, exc: BaseCustomException) -> JSONResponse:
    """
    处理自定义业务异常，返回符合 SoT 约定的 StandardResponse 格式

    SoT Ref: ERROR_CODES_SOT.md v2.1 第 1.3 节 (Envelope 格式)

    支持的异常类型:
    - BusinessLogicError (400)
    - ResourceNotFoundError (404)
    - PermissionDeniedError (403)
    - ResourceConflictError (409)
    - ValidationError (422)
    - AuthenticationError (401)
    - StateTransitionError (400)
    - 其他 BaseCustomException 子类
    """
    return error_response(
        code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
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
        field_name = (
            ".".join(str(x) for x in loc[1:])
            if len(loc) > 1
            else str(loc[0]) if loc else "unknown"
        )

        if "missing" in error_type or "required" in error_type:
            code = ValidationErrorCodes.REQUIRED_FIELD_MISSING.code
            message = f"必填字段缺失: {field_name}"
        else:
            code = ValidationErrorCodes.INVALID_FORMAT.code
            message = f"格式无效: {field_name} - {error_msg}"
    else:
        code = ValidationErrorCodes.INVALID_FORMAT.code
        message = "参数验证失败"

    return error_response(code=code, message=message, status_code=422)


@app.exception_handler(Exception)
async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
    import traceback
    import sys

    error_msg = (
        f"Unexpected exception: {type(exc).__name__}: {exc}\n{traceback.format_exc()}"
    )
    print(error_msg, file=sys.stderr, flush=True)
    message = str(exc) if settings.debug else "Internal server error"
    return fail(
        code=SystemErrorCodes.INTERNAL_ERROR.code,
        message=message,
        status_code=SystemErrorCodes.INTERNAL_ERROR.status_code,
    )
