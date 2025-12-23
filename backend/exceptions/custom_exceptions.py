"""
统一异常体系
Version: 2.0
Author: Claude协作开发

重构说明:
- 集成 backend/core/error_codes.py 的 ErrorCode 对象
- 支持从 ErrorCode 类属性或字符串错误码初始化
- 保持向后兼容性
"""

from typing import Optional, Any, Union
from backend.core.error_codes import (
    ErrorCode,
    get_error_code,
    AuthErrorCodes,
    BusinessErrorCodes,
    SystemErrorCodes,
    DatabaseErrorCodes,
    ValidationErrorCodes,
    StateErrorCodes,
    TrendErrorCodes,
    ProfitErrorCodes,
)


class BaseCustomException(Exception):
    """
    统一异常基类

    支持两种初始化方式:
    1. 传入 ErrorCode 对象: raise BaseCustomException(error=AuthErrorCodes.TOKEN_INVALID)
    2. 传入字符串错误码: raise BaseCustomException(message="错误", error_code="AUTH_401")
    """

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        # 优先使用 ErrorCode 对象
        if error is not None:
            self.error_code = error.code
            self.message = message or error.message
            self.status_code = status_code or error.status_code
        elif error_code is not None:
            # 从 ERROR_CODE_MAP 查找
            ec = get_error_code(error_code)
            self.error_code = error_code
            self.message = message or ec.message
            self.status_code = status_code or ec.status_code
        else:
            self.error_code = "SYS_001"
            self.message = message or "系统内部错误"
            self.status_code = status_code or 500

        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class BusinessLogicError(BaseCustomException):
    """
    业务逻辑错误

    用于可预期的业务规则违反，如:
    - 资源不存在
    - 状态转换非法
    - 金额不足
    """

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "BIZ_001",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
            error=error,
        )


class ResourceNotFoundError(BaseCustomException):
    """
    资源不存在错误

    默认错误码: BIZ_002 (资源不存在)
    """

    def __init__(
        self,
        message: str = "资源不存在",
        error_code: str = "BIZ_002",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details,
            error=error or BusinessErrorCodes.RESOURCE_NOT_FOUND,
        )


class PermissionDeniedError(BaseCustomException):
    """
    权限不足错误

    默认错误码: AUTH_500 (权限不足)
    """

    def __init__(
        self,
        message: str = "权限不足",
        error_code: str = "AUTH_500",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details,
            error=error or AuthErrorCodes.PERMISSION_DENIED,
        )


class ResourceConflictError(BaseCustomException):
    """
    资源冲突错误

    默认错误码: BIZ_003 (资源已存在)
    """

    def __init__(
        self,
        message: str = "资源已存在",
        error_code: str = "BIZ_003",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409,
            details=details,
            error=error or BusinessErrorCodes.RESOURCE_ALREADY_EXISTS,
        )


class ValidationError(BaseCustomException):
    """
    数据验证错误

    默认错误码: VALIDATION_001 (必填字段缺失)
    """

    def __init__(
        self,
        message: str = "验证失败",
        error_code: str = "VALIDATION_001",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
            error=error or ValidationErrorCodes.REQUIRED_FIELD_MISSING,
        )


class AuthenticationError(BaseCustomException):
    """
    认证错误

    默认错误码: AUTH_401 (无效的认证令牌)
    """

    def __init__(
        self,
        message: str = "认证失败",
        error_code: str = "AUTH_401",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
            error=error or AuthErrorCodes.TOKEN_INVALID,
        )


class SecurityError(BaseCustomException):
    """
    安全错误

    默认错误码: AUTH_500 (权限不足)
    """

    def __init__(
        self,
        message: str = "安全验证失败",
        error_code: str = "AUTH_500",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details,
            error=error or AuthErrorCodes.PERMISSION_DENIED,
        )


class RateLimitError(BaseCustomException):
    """
    限流错误

    默认错误码: SYS_004 (请求过于频繁)
    """

    def __init__(
        self,
        message: str = "请求过于频繁",
        error_code: str = "SYS_004",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=429,
            details=details,
            error=error or SystemErrorCodes.RATE_LIMIT_EXCEEDED,
        )


class ExternalServiceError(BaseCustomException):
    """
    外部服务错误

    默认错误码: SYS_002 (服务暂时不可用)
    """

    def __init__(
        self,
        message: str = "外部服务不可用",
        error_code: str = "SYS_002",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details,
            error=error or SystemErrorCodes.SERVICE_UNAVAILABLE,
        )


class ConfigurationError(BaseCustomException):
    """
    配置错误

    默认错误码: SYS_001 (系统内部错误)
    """

    def __init__(
        self,
        message: str = "配置错误",
        error_code: str = "SYS_001",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
            error=error or SystemErrorCodes.INTERNAL_ERROR,
        )


class StateTransitionError(BaseCustomException):
    """
    状态转换错误

    默认错误码: STATE_400 (非法状态流转)
    """

    def __init__(
        self,
        message: str = "非法状态流转",
        error_code: str = "STATE_400",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
            error=error or StateErrorCodes.FORBIDDEN_TRANSITION,
        )


class TrendRiskError(BaseCustomException):
    """
    趋势风控错误

    默认错误码: TREND_002 (风控复核未完成)
    """

    def __init__(
        self,
        message: str = "风控复核未完成",
        error_code: str = "TREND_002",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
            error=error or TrendErrorCodes.REVIEW_REQUIRED,
        )


class DatabaseError(BaseCustomException):
    """
    数据库错误

    默认错误码: DB_002 (数据库查询失败)
    """

    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: str = "DB_002",
        details: Optional[Any] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
            error=error or DatabaseErrorCodes.QUERY_FAILED,
        )


# ==============================================
# 便捷工厂函数
# ==============================================

def raise_not_found(resource_type: str, resource_id: Any) -> None:
    """抛出资源不存在错误"""
    raise ResourceNotFoundError(
        message=f"{resource_type} [{resource_id}] 不存在",
        details={"resource_type": resource_type, "resource_id": resource_id},
    )


def raise_permission_denied(action: str, resource: Optional[str] = None) -> None:
    """抛出权限不足错误"""
    msg = f"无权执行操作: {action}"
    if resource:
        msg += f" (资源: {resource})"
    raise PermissionDeniedError(
        message=msg,
        details={"action": action, "resource": resource},
    )


def raise_validation_error(field: str, reason: str) -> None:
    """抛出验证错误"""
    raise ValidationError(
        message=f"字段 [{field}] 验证失败: {reason}",
        error=ValidationErrorCodes.VALIDATION_ERROR,
        details={"field": field, "reason": reason},
    )


def raise_state_transition_error(
    current_state: str,
    target_state: str,
    reason: Optional[str] = None,
) -> None:
    """抛出状态转换错误"""
    msg = f"状态从 [{current_state}] 转换到 [{target_state}] 非法"
    if reason:
        msg += f": {reason}"
    raise StateTransitionError(
        message=msg,
        details={
            "current_state": current_state,
            "target_state": target_state,
            "reason": reason,
        },
    )
