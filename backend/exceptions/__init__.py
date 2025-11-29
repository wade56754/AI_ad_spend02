"""
异常处理模块
"""
from .handlers import (
    AppException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ConflictException,
    BusinessRuleException,
    ExternalServiceException,
    RateLimitException,
    register_exception_handlers,
)

__all__ = [
    "AppException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "ResourceNotFoundException",
    "ConflictException",
    "BusinessRuleException",
    "ExternalServiceException",
    "RateLimitException",
    "register_exception_handlers",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "PermissionError",
]

# 添加别名以保持兼容性
ValidationError = ValidationException
AuthenticationError = AuthenticationException
NotFoundError = ResourceNotFoundException
PermissionError = AuthorizationException