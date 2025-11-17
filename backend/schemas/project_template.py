"""
项目模板相关的 Schema 定义
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ProjectTemplateCreateRequest(BaseModel):
    """创建项目模板请求"""
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    category: str = Field("custom", max_length=50, description="模板分类")
    default_budget: Optional[Decimal] = Field(None, ge=0, description="默认预算")
    default_currency: str = Field("CNY", max_length=10, description="默认货币")
    default_duration_days: Optional[int] = Field(None, gt=0, le=365, description="默认持续天数")
    account_types: Optional[List[str]] = Field(default_factory=list, description="账户类型列表")
    default_roles: Optional[List[str]] = Field(default_factory=list, description="默认角色列表")
    checklist: Optional[List[str]] = Field(default_factory=list, description="检查清单")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    is_active: bool = Field(True, description="是否激活")


class ProjectTemplateUpdateRequest(BaseModel):
    """更新项目模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    category: Optional[str] = Field(None, max_length=50, description="模板分类")
    default_budget: Optional[Decimal] = Field(None, ge=0, description="默认预算")
    default_currency: Optional[str] = Field(None, max_length=10, description="默认货币")
    default_duration_days: Optional[int] = Field(None, gt=0, le=365, description="默认持续天数")
    account_types: Optional[List[str]] = Field(None, description="账户类型列表")
    default_roles: Optional[List[str]] = Field(None, description="默认角色列表")
    checklist: Optional[List[str]] = Field(None, description="检查清单")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ProjectTemplateResponse(BaseModel):
    """项目模板响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    category: str
    default_budget: Optional[Decimal]
    default_currency: str
    default_duration_days: Optional[int]
    config: Optional[str]  # JSON 字符串
    is_active: bool
    use_count: int
    last_used_at: Optional[datetime]
    created_by: int
    created_by_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int]


class ProjectTemplateListResponse(BaseModel):
    """项目模板列表响应"""
    items: List[ProjectTemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectTemplateApplyRequest(BaseModel):
    """应用项目模板请求"""
    project_name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    client_name: str = Field(..., min_length=1, max_length=200, description="客户名称")
    client_company: Optional[str] = Field(None, max_length=200, description="客户公司")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")


class ProjectTemplateStatisticsResponse(BaseModel):
    """项目模板统计响应"""
    total_templates: int
    total_categories: int
    total_uses: int
    active_templates: int
    category_distribution: List[dict]
    popular_templates: List[dict]