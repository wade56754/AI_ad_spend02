"""
统一的响应格式模块
遵循项目规范中的API响应格式
"""
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    success: bool
    data: Optional[T] = None
    message: str
    code: str
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    """错误详情模型"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: ErrorDetail
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = True
    data: List[T]
    message: str = "操作成功"
    code: str = "SUCCESS"
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pagination: PaginationMeta


def create_response(
    data: T = None,
    message: str = "操作成功",
    code: str = "SUCCESS",
    success: bool = True
) -> BaseResponse[T]:
    """创建标准响应"""
    return BaseResponse[T](
        success=success,
        data=data,
        message=message,
        code=code
    )


def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details
        )
    )


def create_paginated_response(
    data: List[T],
    page: int,
    size: int,
    total: int,
    message: str = "获取成功",
    code: str = "SUCCESS"
) -> PaginatedResponse[T]:
    """创建分页响应"""
    pages = (total + size - 1) // size
    return PaginatedResponse[T](
        data=data,
        message=message,
        code=code,
        pagination=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
    )


# 常用的响应快捷方法
def success(data: T = None, message: str = "操作成功") -> BaseResponse[T]:
    """成功响应"""
    return create_response(data=data, message=message)


def created(data: T = None, message: str = "创建成功") -> BaseResponse[T]:
    """创建成功响应"""
    return create_response(data=data, message=message, code="CREATED")


def updated(data: T = None, message: str = "更新成功") -> BaseResponse[T]:
    """更新成功响应"""
    return create_response(data=data, message=message, code="UPDATED")


def deleted(message: str = "删除成功") -> BaseResponse[None]:
    """删除成功响应"""
    return create_response(data=None, message=message, code="DELETED")


def not_found(message: str = "资源不存在") -> ErrorResponse:
    """404错误响应"""
    return create_error_response(
        code="NOT_FOUND",
        message=message
    )


def validation_error(message: str = "参数验证失败") -> ErrorResponse:
    """验证错误响应"""
    return create_error_response(
        code="VALIDATION_ERROR",
        message=message
    )


def permission_denied(message: str = "权限不足") -> ErrorResponse:
    """权限拒绝响应"""
    return create_error_response(
        code="PERMISSION_DENIED",
        message=message
    )


def server_error(message: str = "服务器内部错误") -> ErrorResponse:
    """服务器错误响应"""
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message=message
    )


def unauthorized(message: str = "未授权访问") -> ErrorResponse:
    """未授权响应"""
    return create_error_response(
        code="UNAUTHORIZED",
        message=message
    )