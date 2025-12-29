"""
周报 Schema (TASK-WEEKLY-002, TASK-WEEKLY-003)

SoT References:
- DATA_SCHEMA.md v5.6 §weekly_briefs
- B3-weekly-brief.md §4.2

Version: 1.1
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class WeeklyReportCreate(BaseModel):
    """
    创建周报请求 (TASK-WEEKLY-002)

    SoT: DATA_SCHEMA.md v5.6 §weekly_briefs
    约束:
    - 必须指定 project_id, week_start_date
    - week_start_date 必须是周一
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., gt=0, description="项目ID")
    week_start_date: date = Field(..., description="周开始日期（必须是周一）")

    # 周报内容 (Phase 1: 均为可选)
    issues: Optional[str] = Field(None, max_length=5000, description="遇到问题")
    next_week_plan: Optional[str] = Field(None, max_length=5000, description="下周计划")
    achievements: Optional[str] = Field(None, max_length=5000, description="本周成果")
    solutions: Optional[str] = Field(None, max_length=5000, description="解决方案")

    @field_validator('week_start_date')
    @classmethod
    def validate_week_start_date(cls, v: date) -> date:
        """验证 week_start_date 必须是周一"""
        if v.weekday() != 0:  # 0 = Monday
            raise ValueError('week_start_date 必须是周一')
        return v


class WeeklyReportUpdate(BaseModel):
    """
    更新周报请求 (TASK-WEEKLY-003)

    SoT: DATA_SCHEMA.md v5.6 §weekly_briefs
    约束:
    - 只能更新内容字段，不能修改 project_id 和 week_start_date
    - 只能更新 draft 状态的周报
    """
    model_config = ConfigDict(from_attributes=True)

    # 周报内容 (均为可选，只更新提供的字段)
    issues: Optional[str] = Field(None, max_length=5000, description="遇到问题")
    next_week_plan: Optional[str] = Field(None, max_length=5000, description="下周计划")
    achievements: Optional[str] = Field(None, max_length=5000, description="本周成果")
    solutions: Optional[str] = Field(None, max_length=5000, description="解决方案")


class WeeklyReportResponse(BaseModel):
    """
    周报响应 (TASK-WEEKLY-002)

    SoT: DATA_SCHEMA.md v5.6 §weekly_briefs
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="周报ID")
    project_id: int = Field(..., description="项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    week_start_date: date = Field(..., description="周开始日期")
    week_end_date: date = Field(..., description="周结束日期")
    status: str = Field(..., description="状态 (draft/submitted)")
    created_by: Optional[UUID] = Field(None, description="创建人ID")
    created_by_name: Optional[str] = Field(None, description="创建人姓名")

    # 汇总数据
    weekly_spend: Decimal = Field(Decimal("0.00"), description="周消耗")
    weekly_conversions: int = Field(0, description="周进粉")
    weekly_cpl: Decimal = Field(Decimal("0.00"), description="周CPL")

    # 周报内容
    issues: Optional[str] = Field(None, description="遇到问题")
    next_week_plan: Optional[str] = Field(None, description="下周计划")
    achievements: Optional[str] = Field(None, description="本周成果")
    solutions: Optional[str] = Field(None, description="解决方案")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    submitted_at: Optional[datetime] = Field(None, description="提交时间")
