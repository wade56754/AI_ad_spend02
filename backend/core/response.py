from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


class StandardResponse:
    """标准响应格式类"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: str = "SUCCESS",
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
        code: str = "SUCCESS"
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
def success_response(data: Any = None, message: str = "操作成功", code: str = "SUCCESS", **kwargs) -> JSONResponse:
    """成功响应函数"""
    return StandardResponse.success(data=data, message=message, code=code, **kwargs)


def error_response(message: str, code: str = "INTERNAL_ERROR", status_code: int = 400, **kwargs) -> JSONResponse:
    """错误响应函数"""
    return StandardResponse.error(message=message, code=code, status_code=status_code, **kwargs)


def paginated_response(data: Any, page: int, page_size: int, total: int, **kwargs) -> JSONResponse:
    """分页响应函数"""
    return StandardResponse.paginated(data=data, page=page, page_size=page_size, total=total, **kwargs)


