from datetime import datetime
from typing import Any, Dict, Optional, TypeVar, Generic
import uuid

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel


T = TypeVar('T')


class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式类"""
    success: bool
    data: Optional[T] = None
    message: str
    code: str
    request_id: str
    timestamp: str

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: str = "OK",
        status_code: int = 200,
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """成功响应"""
        content = {
            "success": True,
            "data": jsonable_encoder(data),
            "message": message,
            "code": code,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }

        if meta:
            content["meta"] = meta

        return JSONResponse(
            status_code=status_code,
            content=content
        )

    @staticmethod
    def error(
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """错误响应"""
        content = {
            "success": False,
            "data": None,
            "message": message,
            "code": code,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }

        if details:
            content["details"] = details

        if meta:
            content["meta"] = meta

        return JSONResponse(
            status_code=status_code,
            content=content
        )

    @staticmethod
    def paginated(
        data: Any,
        page: int,
        page_size: int,
        total: int,
        message: str = "获取成功",
        code: str = "OK"
    ) -> JSONResponse:
        """分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

        return StandardResponse.success(
            data=data,
            message=message,
            code=code,
            meta={"pagination": pagination}
        )


# 保持向后兼容的函数
def ok(data: Any = None, status_code: int = 200, meta: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """兼容旧版本的ok函数"""
    return StandardResponse.success(
        data=data,
        status_code=status_code,
        meta=meta
    )


def fail(code: str, message: str, status_code: int = 400, meta: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """兼容旧版本的fail函数"""
    return StandardResponse.error(
        message=message,
        code=code,
        status_code=status_code,
        meta=meta
    )


# 推荐使用的新函数
def success_response(data: Any = None, message: str = "操作成功", code: str = "OK", **kwargs) -> JSONResponse:
    """成功响应函数"""
    # 直接构建成功响应内容，避免 Pydantic Generic 类的问题
    content = {
        "success": True,
        "data": jsonable_encoder(data),
        "message": message,
        "code": code,
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    }

    # 处理额外参数
    if "status_code" in kwargs:
        status_code = kwargs.pop("status_code")
    else:
        status_code = 200

    if kwargs:
        content.update(kwargs)

    return JSONResponse(
        status_code=status_code,
        content=content
    )


def error_response(message: str, code: str = "INTERNAL_ERROR", status_code: int = 400, details: Optional[Dict[str, Any]] = None, **kwargs) -> JSONResponse:
    """
    错误响应函数
    
    符合 API_SOT.md v9.0 第 4.3 节 Envelope 格式：
    {
      "success": false,
      "error": {
        "code": "...",
        "message": "...",
        "details": {...}
      },
      "request_id": "...",
      "timestamp": "..."
    }
    """
    error_obj = {
        "code": code,
        "message": message
    }
    
    if details:
        error_obj["details"] = details
    
    content = {
        "success": False,
        "error": error_obj,
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if kwargs:
        content.update(kwargs)
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def paginated_response(data: Any = None, items: Any = None, page: int = 1, page_size: int = 20, total: int = 0, **kwargs) -> JSONResponse:
    """分页响应函数"""
    # 支持 items 和 data 两种参数名（向后兼容）
    actual_data = items if items is not None else data
    
    # 直接实现分页逻辑，避免 Pydantic V2 的 @staticmethod 问题
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    # 直接构建响应内容，不依赖 StandardResponse.success()
    content = {
        "success": True,
        "data": jsonable_encoder(actual_data),
        "message": "获取成功",
        "code": "OK",
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "meta": {"pagination": pagination}
    }
    
    return JSONResponse(
        status_code=200,
        content=content
    )


# 新增的Pydantic模型类，用于API响应
class ApiResponse(BaseModel, Generic[T]):
    """API响应模型"""
    success: bool
    data: Optional[T] = None
    message: str
    code: str
    request_id: Optional[str] = None
    timestamp: Optional[str] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: list
    total: int
    page: int
    size: int
    pages: int


