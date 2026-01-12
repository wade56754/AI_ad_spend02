"""
Dashboard Schema 定义 (Legacy V1/V2)

SoT Reference: MASTER.md v4.4 - CEO Dashboard / 运营驾驶舱

⚠️ 注意：此文件名为 `_legacy.py`，但包含的是当前正在使用的 Schema 定义。
这些 Schema 正在被以下模块使用：
- backend/schemas/dashboard/__init__.py

未来重构建议：将此文件重命名为 `dashboard_schemas.py` 或 `dashboard_models.py`。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============ 筛选条件 ============

class DashboardFilters(BaseModel):
    """Dashboard 筛选条件"""
    model_config = ConfigDict(frozen=True)

    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    project_id: Optional[int] = Field(None, description="项目ID筛选")
    channel_id: Optional[str] = Field(None, description="渠道ID筛选")


# ============ KPI 数据 ============

class KpiData(BaseModel):
    """KPI 指标数据"""
    model_config = ConfigDict(from_attributes=True)

    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_conversions: int = Field(0, description="总转化数")
    total_follows: int = Field(0, description="总进粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    avg_cpl: Optional[Decimal] = Field(None, description="平均单粉成本 (CPL)")
    roi: Optional[float] = Field(None, description="投资回报率 (ROI)")
    profit_margin: Optional[float] = Field(None, description="利润率")

    # 环比变化
    spend_change: Optional[float] = Field(None, description="消耗环比变化 (%)")
    conversion_change: Optional[float] = Field(None, description="转化环比变化 (%)")
    cpl_change: Optional[float] = Field(None, description="CPL环比变化 (%)")


class KpiResponse(BaseModel):
    """KPI 响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="统计周期")
    start_date: date
    end_date: date
    kpi: KpiData
    comparison_period: Optional[str] = Field(None, description="对比周期")


# ============ 趋势数据 ============

class TrendItem(BaseModel):
    """趋势数据项"""
    model_config = ConfigDict(from_attributes=True)

    report_date: date = Field(..., description="日期")
    spend: Decimal = Field(Decimal("0.00"), description="消耗")
    conversions: int = Field(0, description="转化数")
    follows: int = Field(0, description="进粉数")
    cpl: Optional[Decimal] = Field(None, description="单粉成本")


class TrendResponse(BaseModel):
    """趋势响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    start_date: date
    end_date: date
    granularity: str = Field("day", description="粒度: day/week/month")
    items: List[TrendItem] = Field(default_factory=list)


# ============ 项目排行 ============

class ProjectRankingItem(BaseModel):
    """项目排名项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_follows: int = Field(0, description="总进粉数")
    cost_per_follow: Optional[Decimal] = Field(None, description="单粉成本")
    roas: Optional[float] = Field(None, description="广告回报率")
    rank: int = Field(0, description="排名")


class RankingResponse(BaseModel):
    """排行响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    start_date: date
    end_date: date
    ranking_type: str = Field("spend", description="排名类型: spend/cpl/roas")
    items: List[ProjectRankingItem] = Field(default_factory=list)


# ============ 待办事项 ============

class TodoItem(BaseModel):
    """待办事项"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="类型: pending_report/pending_topup/trend_flagged")
    label: str = Field(..., description="显示标签")
    count: int = Field(0, description="数量")
    priority: str = Field("normal", description="优先级: low/normal/high/urgent")
    items: List[dict] = Field(default_factory=list, description="具体项目列表")


class TodoResponse(BaseModel):
    """待办响应"""
    model_config = ConfigDict(from_attributes=True)

    total_count: int = Field(0, description="待办总数")
    items: List[TodoItem] = Field(default_factory=list)


# ============ 告警 ============

class AlertItem(BaseModel):
    """告警项"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="告警类型")
    severity: str = Field("medium", description="严重程度: low/medium/high/critical")
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    message: str = Field(..., description="告警消息")
    created_at: Optional[datetime] = None


# ============ 综合汇总 ============

class DashboardSummary(BaseModel):
    """Dashboard 综合汇总"""
    model_config = ConfigDict(from_attributes=True)

    # 时间范围
    period: str = Field(..., description="统计周期")
    start_date: date
    end_date: date

    # 项目统计
    total_projects: int = Field(0, description="项目总数")
    active_projects: int = Field(0, description="活跃项目数")
    suspended_projects: int = Field(0, description="暂停项目数")

    # KPI
    kpi: KpiData

    # 待办事项计数
    pending_reports: int = Field(0, description="待审核日报数")
    pending_topups: int = Field(0, description="待审批充值数")
    trend_flagged_count: int = Field(0, description="趋势异常日报数")

    # 告警列表
    alerts: List[AlertItem] = Field(default_factory=list)

    # Phase 信息
    current_phase: int = Field(1, description="当前 Phase (1 或 2)")


class DashboardDetail(BaseModel):
    """Dashboard 详细数据"""
    model_config = ConfigDict(from_attributes=True)

    summary: DashboardSummary
    trend: TrendResponse
    top_spend_projects: List[ProjectRankingItem] = Field(default_factory=list)
    worst_cpl_projects: List[ProjectRankingItem] = Field(default_factory=list)
    todos: TodoResponse
