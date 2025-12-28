"""
分页查询工具模块 (Core Layer)

SoT Reference: API_SOT.md v9.3 §3.2 (分页规范)

本模块是 pagination 代码块，提供:
1. PaginationParams - 分页参数模型 (page, page_size, sort_by, sort_order)
2. get_pagination - FastAPI 依赖注入
3. paginate - SQLAlchemy 分页查询
4. paginate_with_cursor - 游标分页 (大数据集)
5. PaginatedResponse - 分页响应模型 (泛型)
6. PaginationMeta - 分页元信息
7. build_pagination_meta - 构建分页元信息
8. create_paginated_response - 创建分页响应

使用示例:
    from backend.core.pagination import (
        PaginationParams,
        get_pagination,
        paginate,
        create_paginated_response
    )

    @router.get("/items")
    def list_items(
        pagination: PaginationParams = Depends(get_pagination),
        db: Session = Depends(get_db)
    ):
        query = db.query(Item).filter(Item.is_active == True)
        items, total = paginate(query, pagination, Item)
        return success_response(
            data=create_paginated_response(items, total, pagination)
        )
"""

from typing import Any, Generic, List, Literal, Optional, Tuple, Type, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, inspect
from sqlalchemy.orm import Query as SAQuery

from backend.core.db import Base


T = TypeVar("T")


# ============================================
# 分页参数模型
# ============================================

class PaginationParams(BaseModel):
    """分页参数

    Attributes:
        page: 页码 (从1开始)
        page_size: 每页条数 (1-100)
        sort_by: 排序字段
        sort_order: 排序方向 (asc/desc)
    """
    model_config = ConfigDict(frozen=True)

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="排序方向")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """返回限制数"""
        return self.page_size


# ============================================
# FastAPI 依赖注入
# ============================================

def get_pagination(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="排序方向")
) -> PaginationParams:
    """
    分页参数依赖注入

    Usage:
        @router.get("/items")
        def list_items(
            pagination: PaginationParams = Depends(get_pagination),
            db: Session = Depends(get_db)
        ):
            items, total = paginate(db.query(Item), pagination, Item)
            return paginated_response(items=items, total=total, ...)
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )


# ============================================
# SQLAlchemy 分页查询
# ============================================

def paginate(
    query: SAQuery,
    params: PaginationParams,
    model: Optional[Type[Base]] = None
) -> Tuple[List[Any], int]:
    """
    执行分页查询

    Args:
        query: SQLAlchemy Query 对象
        params: 分页参数
        model: SQLAlchemy 模型类 (用于排序字段验证)

    Returns:
        (items, total) 元组

    Usage:
        query = db.query(DailyReport).filter(DailyReport.status == "pending")
        items, total = paginate(query, pagination, DailyReport)

    Note:
        - 使用子查询优化 COUNT 性能
        - 自动验证排序字段是否存在于模型
    """
    # 1. 获取总数 (使用子查询优化)
    total = query.count()

    # 2. 应用排序
    if params.sort_by:
        # 验证排序字段存在
        if model is not None:
            mapper = inspect(model)
            valid_columns = [c.key for c in mapper.columns]
            if params.sort_by not in valid_columns:
                # 字段不存在时忽略排序，而非抛出错误
                pass
            else:
                column = getattr(model, params.sort_by)
                if params.sort_order == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
        else:
            # 无模型时尝试直接排序 (可能失败)
            try:
                if params.sort_order == "desc":
                    query = query.order_by(params.sort_by + " DESC")
                else:
                    query = query.order_by(params.sort_by + " ASC")
            except Exception:
                pass

    # 3. 应用分页
    items = query.offset(params.offset).limit(params.limit).all()

    return items, total


def paginate_with_cursor(
    query: SAQuery,
    cursor_field: str,
    cursor_value: Optional[Any],
    limit: int = 20,
    direction: Literal["next", "prev"] = "next"
) -> Tuple[List[Any], Optional[Any], bool]:
    """
    游标分页 (适用于大数据集)

    Args:
        query: SQLAlchemy Query 对象
        cursor_field: 游标字段名 (通常是 id 或 created_at)
        cursor_value: 游标值
        limit: 每页条数
        direction: 翻页方向

    Returns:
        (items, next_cursor, has_more) 元组

    Usage:
        items, next_cursor, has_more = paginate_with_cursor(
            query, "id", last_id, limit=50
        )
    """
    # 获取模型类
    entity = query.column_descriptions[0]["entity"]
    cursor_column = getattr(entity, cursor_field)

    if cursor_value is not None:
        if direction == "next":
            query = query.filter(cursor_column > cursor_value)
        else:
            query = query.filter(cursor_column < cursor_value)

    # 多取一条用于判断是否有更多
    items = query.order_by(
        cursor_column.asc() if direction == "next" else cursor_column.desc()
    ).limit(limit + 1).all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = getattr(items[-1], cursor_field) if items else None

    return items, next_cursor, has_more


# ============================================
# 分页响应模型
# ============================================

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型 (泛型)

    用于 OpenAPI 文档生成

    Usage:
        @router.get("/items", response_model=ApiResponse[PaginatedResponse[ItemResponse]])
        def list_items(...):
            ...
    """
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginationMeta(BaseModel):
    """分页元信息 (用于 envelope.meta)"""
    model_config = ConfigDict(frozen=True)

    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


def build_pagination_meta(
    page: int,
    page_size: int,
    total: int
) -> PaginationMeta:
    """构建分页元信息"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


# ============================================
# 便捷函数
# ============================================

def create_paginated_response(
    items: List[Any],
    total: int,
    pagination: PaginationParams,
    message: str = "获取成功"
) -> dict:
    """
    创建分页响应数据 (符合 API envelope 规范)

    返回完整的 API 响应格式

    Usage:
        items, total = paginate(query, params, Model)
        return create_paginated_response(
            items=items,
            total=total,
            pagination=params,
            message="获取列表成功"
        )
    """
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if pagination.page_size > 0 else 0

    return {
        "success": True,
        "data": {
            "items": items,
            "meta": {
                "pagination": {
                    "page": pagination.page,
                    "page_size": pagination.page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": pagination.page < total_pages,
                    "has_prev": pagination.page > 1
                }
            }
        },
        "message": message
    }


# ============================================
# 默认值常量
# ============================================

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ============================================
# 导出列表
# ============================================

__all__ = [
    # 分页参数
    "PaginationParams",
    "get_pagination",

    # 分页查询
    "paginate",
    "paginate_with_cursor",

    # 响应模型
    "PaginatedResponse",
    "PaginationMeta",

    # 便捷函数
    "build_pagination_meta",
    "create_paginated_response",

    # 常量
    "DEFAULT_PAGE",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]
