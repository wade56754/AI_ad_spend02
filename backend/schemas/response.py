"""
响应模型定义
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field(..., description="响应消息")
    code: str = Field(..., description="响应代码")
    request_id: str = Field(..., description="请求ID")
    timestamp: str = Field(..., description="时间戳")
    meta: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = Field(False, description="操作是否成功")
    data: None = Field(None, description="响应数据")
    message: str = Field(..., description="错误消息")
    code: str = Field(..., description="错误代码")
    request_id: str = Field(..., description="请求ID")
    timestamp: str = Field(..., description="时间戳")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    meta: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: List[Any] = Field(..., description="项目列表")
    pagination: PaginationMeta = Field(..., description="分页信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="时间戳")