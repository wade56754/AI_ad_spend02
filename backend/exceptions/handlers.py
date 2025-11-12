"""
全局异常处理器
统一处理应用中的各种异常
"""
import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.response import error_response
from types import SimpleNamespace
from datetime import datetime
import uuid


def create_error_response(code: str, message: str, details: dict | None = None) -> SimpleNamespace:
    """兼容旧代码的错误响应构造器，返回带有 .dict() 方法的对象。
    最终由本模块使用 JSONResponse(status_code=..., content=...).
    """
    payload = {
        "success": False,
        "data": None,
        "message": message,
        "code": code,
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
    }
    if details is not None:
        payload["details"] = details
    return SimpleNamespace(dict=lambda: payload)

# 配置日志
logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常类"""
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationException(AppException):
    """验证异常"""
    def __init__(self, message: str = "参数验证失败", details: dict = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(AppException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(AppException):
    """授权异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ResourceNotFoundException(AppException):
    """资源未找到异常"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(AppException):
    """资源冲突异常"""
    def __init__(self, message: str = "资源冲突"):
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class BusinessRuleException(AppException):
    """业务规则异常"""
    def __init__(self, message: str = "违反业务规则", details: dict = None):
        super().__init__(
            code="BUSINESS_RULE_ERROR",
            message=message,
            details=details
        )


class ExternalServiceException(AppException):
    """外部服务异常"""
    def __init__(self, message: str = "外部服务错误", service_name: str = None):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service_name": service_name} if service_name else None
        )


class RateLimitException(AppException):
    """限流异常"""
    def __init__(self, message: str = "请求过于频繁", retry_after: int = None):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after} if retry_after else None
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理应用自定义异常"""
    # 记录错误日志
    logger.error(
        f"App exception: {exc.code} - {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )

    # 返回错误响应
    return error_response(
        message=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """处理参数验证异常"""
    # 提取验证错误详情
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
    else:
        errors = exc.errors()

    # 格式化错误信息
    details = {
        "validation_errors": [
            {
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            }
            for error in errors
        ]
    }

    # 记录错误日志
    logger.warning(
        f"Validation error: {len(errors)} errors",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "details": details,
        }
    )

    # 返回错误响应
    return error_response(
        message="参数验证失败",
        code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """处理HTTP异常"""
    # 映射HTTP状态码到错误码
    error_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
        status.HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    # 记录错误日志
    logger.warning(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "path": request.url.path,
            "method": request.method,
        }
    )

    # 返回错误响应
    return error_response(
        message=str(exc.detail),
        code=error_code,
        status_code=exc.status_code,
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """处理数据库异常"""
    # 获取错误详情
    error_msg = str(exc)

    # 记录错误日志
    logger.error(
        f"Database error: {error_msg}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        }
    )

    # 判断异常类型
    if isinstance(exc, IntegrityError):
        # 违反数据库约束
        error_response = create_error_response(
            code="INTEGRITY_ERROR",
            message="数据完整性错误",
            details={"error": error_msg}
        )
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        # 其他数据库错误
        error_response = create_error_response(
            code="DATABASE_ERROR",
            message="数据库操作失败",
            details={"error": error_msg} if logger.isEnabledFor(logging.DEBUG) else None
        )
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的通用异常"""
    # 记录错误日志
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        }
    )

    # 返回通用错误响应
    error_response = create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="服务器内部错误"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


def register_exception_handlers(app: FastAPI):
    """注册所有异常处理器"""
    # 应用自定义异常
    app.add_exception_handler(AppException, app_exception_handler)

    # FastAPI验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # HTTP异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # 通用异常（必须最后注册）
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered")
