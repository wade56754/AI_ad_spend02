"""
周报相关的 Pydantic 模型 (重构版)

SoT References:
- B3-weekly-brief.md §4.2 API 接口
- API_SOT.md v9.3 标准响应格式
- DATA_SCHEMA.md v5.3 (weekly_briefs 表)

依赖代码块:
- pagination: PaginationMeta
- response-envelope: 标准响应格式

Version: 2.0
Author: Claude Code
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ========== 请求模型 ==========

class WeeklyBriefCreateRequest(BaseModel):
    """
    创建周报请求

    对齐 B3-weekly-brief.md §4.2
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., gt=0, description="项目ID")
    week_start: date = Field(..., description="周开始日期（必须是周一）")
    achievements: Optional[str] = Field(None, max_length=5000, description="本周成果")
    issues: Optional[str] = Field(None, max_length=5000, description="遇到问题")
    solutions: Optional[str] = Field(None, max_length=5000, description="解决方案")
    next_week_plan: Optional[str] = Field(None, max_length=5000, description="下周计划")

    @field_validator('week_start')
    @classmethod
    def validate_week_start(cls, v: date) -> date:
        """验证 week_start 必须是周一"""
        if v.weekday() != 0:  # 0 = Monday
            raise ValueError('week_start 必须是周一')
        return v


class WeeklyBriefUpdateRequest(BaseModel):
    """
    更新周报请求

    只能更新内容字段，不能修改项目和周次
    """
    model_config = ConfigDict(from_attributes=True)

    achievements: Optional[str] = Field(None, max_length=5000, description="本周成果")
    issues: Optional[str] = Field(None, max_length=5000, description="遇到问题")
    solutions: Optional[str] = Field(None, max_length=5000, description="解决方案")
    next_week_plan: Optional[str] = Field(None, max_length=5000, description="下周计划")


class WeeklyBriefListParams(BaseModel):
    """周报列表查询参数"""
    model_config = ConfigDict(from_attributes=True)

    week: Optional[str] = Field(None, description="周次 (如 2025-W51)")
    week_start: Optional[date] = Field(None, description="周开始日期")
    project_id: Optional[int] = Field(None, gt=0, description="项目ID")
    status: Optional[str] = Field(None, pattern="^(draft|submitted)$", description="状态")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


# ========== 响应模型 ==========

class WeeklyBriefResponse(BaseModel):
    """
    周报响应

    对齐 B3-weekly-brief.md §4.2
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: Optional[str] = None
    week_start: date
    week_end: date
    week_label: Optional[str] = None
    submitter_id: Optional[UUID] = None
    submitter_name: Optional[str] = None
    status: str
    weekly_spend: Decimal
    weekly_conversions: int
    weekly_cpl: Decimal
    cpl_trend: Optional[Decimal] = None
    achievements: Optional[str] = None
    issues: Optional[str] = None
    solutions: Optional[str] = None
    next_week_plan: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WeeklyBriefStatsResponse(BaseModel):
    """
    周报统计响应

    对齐 B3-weekly-brief.md §4.2
    """
    model_config = ConfigDict(from_attributes=True)

    total_projects: int = Field(..., description="本周项目总数")
    submitted_count: int = Field(..., description="已提交数")
    draft_count: int = Field(..., description="草稿数")
    submission_rate: Decimal = Field(..., description="提交率 (%)")
    total_weekly_spend: Decimal = Field(..., description="本周总消耗")


class WeeklyBriefListResponse(BaseModel):
    """周报列表响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[WeeklyBriefResponse]
    total: int
    page: int
    page_size: int
    stats: Optional[WeeklyBriefStatsResponse] = None


class WeeklyBriefSubmitResponse(BaseModel):
    """提交周报响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    submitted_at: datetime


# ========== 周数据汇总 ==========

class WeeklyTrendData(BaseModel):
    """周趋势数据"""
    model_config = ConfigDict(from_attributes=True)

    spend_change: Decimal = Field(..., description="消耗环比 (%)")
    conversions_change: Decimal = Field(..., description="进粉环比 (%)")
    cpl_change: Decimal = Field(..., description="CPL环比 (%)")


class LastWeekData(BaseModel):
    """上周数据"""
    model_config = ConfigDict(from_attributes=True)

    spend: Decimal
    conversions: int
    cpl: Decimal


class DailyBreakdown(BaseModel):
    """每日明细"""
    model_config = ConfigDict(from_attributes=True)

    date: date
    spend: Decimal
    conversions: int


class WeeklySummaryResponse(BaseModel):
    """
    项目周数据汇总响应

    对齐 B3-weekly-brief.md §4.2 项目周数据汇总
    """
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    week_start: date
    week_end: date
    weekly_spend: Decimal
    weekly_conversions: int
    weekly_cpl: Decimal
    target_cpl: Optional[Decimal] = None
    cpl_vs_target: Optional[Decimal] = None
    last_week: Optional[LastWeekData] = None
    trends: Optional[WeeklyTrendData] = None
    daily_breakdown: Optional[List[DailyBreakdown]] = None
