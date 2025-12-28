"""
统一异常模块 (Core Layer)

SoT Reference: API_SOT.md v9.3 §4 (响应格式规范)
SoT Reference: ERROR_CODES_SOT.md v2.1 (错误码定义)

本模块是 response-envelope 代码块的一部分，提供:
1. BusinessError - 业务异常基类 (推荐使用)
2. 各类型化异常 - 便于捕获和处理
3. 工厂函数 - 快速抛出常见异常

使用示例:
    from backend.core.exceptions import BusinessError, raise_not_found
    from backend.core.error_codes import BusinessErrorCodes

    # 方式 1: 使用 ErrorCode 对象
    raise BusinessError(error=BusinessErrorCodes.INVALID_OPERATION)

    # 方式 2: 使用错误码字符串
    raise BusinessError(message="自定义消息", error_code="BIZ_001")

    # 方式 3: 使用工厂函数
    raise_not_found("Project", project_id)
"""

from typing import Any, Dict, Optional

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
    ReconciliationErrorCodes,
    FeeErrorCodes,
)


# ============================================
# 异常基类
# ============================================

class BusinessError(Exception):
    """
    业务异常基类 (推荐使用)

    支持两种初始化方式:
    1. 传入 ErrorCode 对象: raise BusinessError(error=BusinessErrorCodes.RESOURCE_NOT_FOUND)
    2. 传入字符串错误码: raise BusinessError(message="错误", error_code="BIZ_002")

    Attributes:
        code: 错误码字符串 (如 "BIZ_001")
        message: 错误消息
        status_code: HTTP 状态码
        details: 额外详情 (可选)

    SoT 对齐:
        - 错误码必须来自 ERROR_CODES_SOT.md
        - 响应格式: {"success": false, "error": {"code": "...", "message": "..."}}
    """

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        # 优先使用 ErrorCode 对象
        if error is not None:
            self.code = error.code
            self.message = message or error.message
            self.status_code = status_code or error.status_code
        elif error_code is not None:
            # 从 ERROR_CODE_MAP 查找
            ec = get_error_code(error_code)
            self.code = error_code
            self.message = message or ec.message
            self.status_code = status_code or ec.status_code
        else:
            # 默认: 系统内部错误
            self.code = "SYS_001"
            self.message = message or "系统内部错误"
            self.status_code = status_code or 500

        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为响应字典格式"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result

    def to_response(self) -> Dict[str, Any]:
        """转换为完整响应格式 (符合 API_SOT.md §4)"""
        return {
            "success": False,
            "error": self.to_dict(),
        }


# ============================================
# 类型化异常
# ============================================

class AuthError(BusinessError):
    """认证/授权错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "AUTH_401",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
            error=error or AuthErrorCodes.TOKEN_INVALID,
        )


class PermissionError(BusinessError):
    """权限不足错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "AUTH_500",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details,
            error=error or AuthErrorCodes.PERMISSION_DENIED,
        )


class NotFoundError(BusinessError):
    """资源不存在错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "BIZ_002",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details,
            error=error or BusinessErrorCodes.RESOURCE_NOT_FOUND,
        )


class ConflictError(BusinessError):
    """资源冲突错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "BIZ_003",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409,
            details=details,
            error=error or BusinessErrorCodes.RESOURCE_ALREADY_EXISTS,
        )


class ValidationError(BusinessError):
    """数据验证错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "VALIDATION_001",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details,
            error=error or ValidationErrorCodes.REQUIRED_FIELD_MISSING,
        )


class StateTransitionError(BusinessError):
    """状态转换错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "STATE_400",
        current_state: Optional[str] = None,
        target_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        if details is None:
            details = {}
        if current_state:
            details["current_state"] = current_state
        if target_state:
            details["target_state"] = target_state

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
            error=error or StateErrorCodes.FORBIDDEN_TRANSITION,
        )


class DatabaseError(BusinessError):
    """数据库错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "DB_002",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
            error=error or DatabaseErrorCodes.QUERY_FAILED,
        )


class RateLimitError(BusinessError):
    """限流错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "SYS_004",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=429,
            details=details,
            error=error or SystemErrorCodes.RATE_LIMIT_EXCEEDED,
        )


class ExternalServiceError(BusinessError):
    """外部服务错误"""

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: str = "SYS_002",
        details: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorCode] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details,
            error=error or SystemErrorCodes.SERVICE_UNAVAILABLE,
        )


# ============================================
# 工厂函数 (快速抛出常见异常)
# ============================================

def raise_not_found(resource_type: str, resource_id: Any) -> None:
    """
    抛出资源不存在错误

    Args:
        resource_type: 资源类型 (如 "Project", "User")
        resource_id: 资源ID

    Raises:
        NotFoundError
    """
    raise NotFoundError(
        message=f"{resource_type} [{resource_id}] 不存在",
        details={"resource_type": resource_type, "resource_id": str(resource_id)},
    )


def raise_permission_denied(action: str, resource: Optional[str] = None) -> None:
    """
    抛出权限不足错误

    Args:
        action: 操作名称
        resource: 资源标识 (可选)

    Raises:
        PermissionError
    """
    msg = f"无权执行操作: {action}"
    if resource:
        msg += f" (资源: {resource})"
    raise PermissionError(
        message=msg,
        details={"action": action, "resource": resource},
    )


def raise_validation_error(field: str, reason: str) -> None:
    """
    抛出验证错误

    Args:
        field: 字段名
        reason: 验证失败原因

    Raises:
        ValidationError
    """
    raise ValidationError(
        message=f"字段 [{field}] 验证失败: {reason}",
        error=ValidationErrorCodes.VALIDATION_ERROR,
        details={"field": field, "reason": reason},
    )


def raise_state_error(
    current_state: str,
    target_state: str,
    reason: Optional[str] = None,
) -> None:
    """
    抛出状态转换错误

    Args:
        current_state: 当前状态
        target_state: 目标状态
        reason: 错误原因 (可选)

    Raises:
        StateTransitionError
    """
    msg = f"状态从 [{current_state}] 转换到 [{target_state}] 非法"
    if reason:
        msg += f": {reason}"
    raise StateTransitionError(
        message=msg,
        current_state=current_state,
        target_state=target_state,
        details={"reason": reason} if reason else None,
    )


def raise_conflict(resource_type: str, identifier: str) -> None:
    """
    抛出资源冲突错误

    Args:
        resource_type: 资源类型
        identifier: 冲突标识

    Raises:
        ConflictError
    """
    raise ConflictError(
        message=f"{resource_type} [{identifier}] 已存在",
        details={"resource_type": resource_type, "identifier": identifier},
    )


# ============================================
# 向后兼容别名
# ============================================

# 从 backend/exceptions/custom_exceptions.py 重导出
# 保持向后兼容性
BusinessLogicError = BusinessError
ResourceNotFoundError = NotFoundError
PermissionDeniedError = PermissionError
ResourceConflictError = ConflictError


# ============================================
# 导出列表
# ============================================

__all__ = [
    # 基类
    "BusinessError",

    # 类型化异常
    "AuthError",
    "PermissionError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "StateTransitionError",
    "DatabaseError",
    "RateLimitError",
    "ExternalServiceError",

    # 工厂函数
    "raise_not_found",
    "raise_permission_denied",
    "raise_validation_error",
    "raise_state_error",
    "raise_conflict",

    # 向后兼容别名
    "BusinessLogicError",
    "ResourceNotFoundError",
    "PermissionDeniedError",
    "ResourceConflictError",
]
