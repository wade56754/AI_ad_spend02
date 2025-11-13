"""
自定义异常类
Version: 1.0
Author: Claude协作开发
"""

from typing import Optional, Any


class BaseCustomException(Exception):
    """自定义异常基类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class BusinessLogicError(BaseCustomException):
    """业务逻辑错误"""

    def __init__(self, message: str, error_code: str = "BIZ_ERROR", details: Optional[Any] = None):
        super().__init__(message, error_code, 400, details)


class ResourceNotFoundError(BaseCustomException):
    """资源不存在错误"""

    def __init__(self, message: str, error_code: str = "SYS_004", details: Optional[Any] = None):
        super().__init__(message, error_code, 404, details)


class PermissionDeniedError(BaseCustomException):
    """权限不足错误"""

    def __init__(self, message: str, error_code: str = "SYS_003", details: Optional[Any] = None):
        super().__init__(message, error_code, 403, details)


class ResourceConflictError(BaseCustomException):
    """资源冲突错误"""

    def __init__(self, message: str, error_code: str = "SYS_005", details: Optional[Any] = None):
        super().__init__(message, error_code, 409, details)


class ValidationError(BaseCustomException):
    """数据验证错误"""

    def __init__(self, message: str, error_code: str = "SYS_001", details: Optional[Any] = None):
        super().__init__(message, error_code, 422, details)


class AuthenticationError(BaseCustomException):
    """认证错误"""

    def __init__(self, message: str, error_code: str = "SYS_002", details: Optional[Any] = None):
        super().__init__(message, error_code, 401, details)


class SecurityError(BaseCustomException):
    """安全错误"""

    def __init__(self, message: str, error_code: str = "SEC_ERROR", details: Optional[Any] = None):
        super().__init__(message, error_code, 403, details)


class RateLimitError(BaseCustomException):
    """限流错误"""

    def __init__(self, message: str, error_code: str = "SYS_429", details: Optional[Any] = None):
        super().__init__(message, error_code, 429, details)


class ExternalServiceError(BaseCustomException):
    """外部服务错误"""

    def __init__(self, message: str, error_code: str = "SYS_503", details: Optional[Any] = None):
        super().__init__(message, error_code, 503, details)


class ConfigurationError(BaseCustomException):
    """配置错误"""

    def __init__(self, message: str, error_code: str = "SYS_CONFIG", details: Optional[Any] = None):
        super().__init__(message, error_code, 500, details)