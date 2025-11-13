"""
项目管理相关的Pydantic模型
Version: 1.0
Author: Claude协作开发
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProjectCreateRequest(BaseModel):
    """项目创建请求"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    client_name: str = Field(..., min_length=1, max_length=200, description="客户联系人姓名")
    client_company: str = Field(..., min_length=1, max_length=200, description="客户公司名称")
    description: Optional[str] = Field(None, max_length=1000, description="项目描述")
    budget: Decimal = Field(0, ge=0, decimal_places=2, description="项目预算")
    currency: str = Field("USD", max_length=10, description="货币类型")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    end_date: Optional[date] = Field(None, description="项目结束日期")
    account_manager_id: Optional[int] = Field(None, gt=0, description="项目经理ID")

    @field_validator('end_date')
    def validate_dates(cls, v, info):
        if v and 'start_date' in info.data and info.data['start_date']:
            if v < info.data['start_date']:
                raise ValueError('结束日期不能小于开始日期')
        return v


class ProjectUpdateRequest(BaseModel):
    """项目更新请求"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_company: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(planning|active|paused|completed|cancelled)$")
    budget: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_manager_id: Optional[int] = Field(None, gt=0)

    @field_validator('end_date')
    def validate_dates(cls, v, info):
        if v and 'start_date' in info.data and info.data['start_date']:
            if v < info.data['start_date']:
                raise ValueError('结束日期不能小于开始日期')
        return v


class ProjectMemberAssignRequest(BaseModel):
    """项目成员分配请求"""
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., gt=0, description="用户ID")
    role: str = Field(..., pattern="^(account_manager|media_buyer|analyst)$", description="角色")


class ProjectExpenseRequest(BaseModel):
    """项目费用记录请求"""
    model_config = ConfigDict(from_attributes=True)

    expense_type: str = Field(..., pattern="^(media_spend|service_fee|other)$", description="费用类型")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="金额")
    description: Optional[str] = Field(None, max_length=500, description="费用说明")
    expense_date: date = Field(..., description="费用日期")


# 响应模型
class ProjectResponse(BaseModel):
    """项目响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    client_name: str
    client_company: str
    description: Optional[str]
    status: str
    budget: Decimal
    currency: str
    start_date: Optional[date]
    end_date: Optional[date]
    account_manager_id: Optional[int]
    account_manager_name: Optional[str]
    total_spent: Decimal
    total_accounts: int
    active_accounts: int
    created_by: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def remaining_budget(self) -> Decimal:
        """剩余预算"""
        return max(Decimal('0'), self.budget - self.total_spent)

    @computed_field
    @property
    def budget_usage_percent(self) -> Decimal:
        """预算使用百分比"""
        if self.budget == 0:
            return Decimal('0')
        return (self.total_spent / self.budget) * 100


class ProjectMemberResponse(BaseModel):
    """项目成员响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    project_role: str
    joined_at: datetime


class ProjectExpenseResponse(BaseModel):
    """项目费用响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_type: str
    amount: Decimal
    description: Optional[str]
    expense_date: date
    created_by_name: str
    created_at: datetime


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: List[ProjectResponse]
    meta: Dict[str, Any]


class ProjectStatisticsResponse(BaseModel):
    """项目统计响应"""
    model_config = ConfigDict(from_attributes=True)

    total_projects: int
    active_projects: int
    paused_projects: int
    completed_projects: int
    cancelled_projects: int
    total_budget: Decimal
    total_spent: Decimal
    total_clients: int
    avg_project_value: Decimal
    top_performers: List[Dict[str, Any]]

    @computed_field
    @property
    def overall_roi(self) -> Optional[Decimal]:
        """整体ROI"""
        if self.total_spent == 0:
            return None
        # 这里需要根据实际业务逻辑计算
        return Decimal('0')  # 占位符