"""
CEO Dashboard Pydantic Schemas

SoT Reference:
- CLAUDE_CLI_TASK_CEO_DASHBOARD_REFACTOR_V3.md §4

Version: 3.0
Author: Claude Code
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# 通用组件
# ============================================

class MetricItem(BaseModel):
    """指标项"""
    model_config = ConfigDict(from_attributes=True)

    total: float
    label: str
    note: Optional[str] = None


class BreakdownItem(BaseModel):
    """明细项"""
    model_config = ConfigDict(from_attributes=True)

    type: str
    label: str
    amount: float


# ============================================
# 现金状况
# ============================================

class BalanceInfo(BaseModel):
    """余额信息"""
    opening: float
    closing: float
    change: float
    change_pct: float


class IncomeInfo(BaseModel):
    """收入信息"""
    total: float
    breakdown: List[BreakdownItem]


class ExpenseInfo(BaseModel):
    """支出信息"""
    total: float
    breakdown: List[BreakdownItem]


class RunwayInfo(BaseModel):
    """周转信息"""
    days: int
    avg_daily_ad_spend: float
    note: str


class CashStatusResponse(BaseModel):
    """公司现金状况响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    balance: BalanceInfo
    income: IncomeInfo
    expense: ExpenseInfo
    runway: RunwayInfo


# ============================================
# 利润概览
# ============================================

class RevenueInfo(BaseModel):
    """收入信息"""
    total: float
    label: str
    conversions: int
    avg_unit_price: Optional[float] = None
    note: str


class CostInfo(BaseModel):
    """成本信息（不含手续费）"""
    total: float
    label: str
    note: str


class ProfitInfo(BaseModel):
    """利润信息"""
    total: float
    label: str
    rate: float
    rate_pct: float
    target_rate: float
    gap: float
    status: str
    status_label: str


class CPLInfo(BaseModel):
    """CPL 信息"""
    overall: float
    formula: str


class FeeReferenceInfo(BaseModel):
    """手续费参考（不计入成本）"""
    estimated_rate: float
    estimated_amount: float
    note: str


class ProfitSummaryResponse(BaseModel):
    """利润概览响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    formula: str
    revenue: RevenueInfo
    cost: CostInfo
    profit: ProfitInfo
    cpl: CPLInfo
    fee_reference: FeeReferenceInfo


# ============================================
# 项目余额
# ============================================

class ProjectBalanceItem(BaseModel):
    """项目余额项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    client_name: Optional[str]
    cumulative_revenue: float
    cumulative_cost: float
    balance: float
    status: str
    status_label: str
    refund_amount: Optional[float] = None
    refund_date: Optional[str] = None
    note: Optional[str] = None


class ProjectBalanceTotals(BaseModel):
    """项目余额汇总"""
    cumulative_revenue: float
    cumulative_cost: float
    total_balance: float


class ProjectBalanceSummary(BaseModel):
    """项目余额统计"""
    total_count: int
    prepaid_count: int
    pending_refund_count: int
    refunded_count: int
    settled_count: int
    need_topup_count: int


class ProjectBalanceResponse(BaseModel):
    """项目余额响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    formula: str
    items: List[ProjectBalanceItem]
    totals: ProjectBalanceTotals
    summary: ProjectBalanceSummary


# ============================================
# 待办事项
# ============================================

class AbnormalProjectMetrics(BaseModel):
    """异常项目指标"""
    revenue: float
    cost: float
    profit: float
    profit_rate: float


class ActionButton(BaseModel):
    """操作按钮"""
    key: str
    label: str
    variant: str


class AbnormalProjectItem(BaseModel):
    """异常项目项"""
    project_id: int
    project_name: str
    issue_type: str
    severity: str
    metrics: AbnormalProjectMetrics
    message: str
    suggested_action: str
    actions: List[ActionButton]


class PendingReportItem(BaseModel):
    """待处理日报项"""
    date: str
    count: int
    statuses: Optional[List[Dict[str, Any]]] = None


class PendingRefundItem(BaseModel):
    """待退款项目"""
    project_name: str
    amount: float


class ActionItemsResponse(BaseModel):
    """待办事项响应"""
    model_config = ConfigDict(from_attributes=True)

    abnormal_projects: Dict[str, Any]
    pending_reports: Dict[str, Any]
    pending_refunds: Dict[str, Any]


# ============================================
# 项目排行
# ============================================

class PricingInfo(BaseModel):
    """定价信息"""
    type: str
    unit_price: Optional[float] = None
    markup_rate: Optional[float] = None
    tiers: Optional[List[Dict[str, Any]]] = None
    note: str


class ProjectMetrics(BaseModel):
    """项目指标"""
    conversions: Optional[int]
    revenue: float
    cost: float
    profit: float
    profit_rate: float
    profit_rate_pct: float
    cpl: Optional[float]


class ProjectRankingItem(BaseModel):
    """项目排行项"""
    model_config = ConfigDict(from_attributes=True)

    rank: int
    project_id: int
    project_name: str
    client_name: Optional[str] = None
    profit_status: str
    pricing: PricingInfo
    metrics: ProjectMetrics


class ProjectRankingSummary(BaseModel):
    """项目排行统计"""
    total_projects: int
    healthy_count: int
    warning_count: int
    danger_count: int
    total_profit: float
    avg_profit_rate: float


class ProjectRankingResponse(BaseModel):
    """项目排行响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    formula: str
    items: List[ProjectRankingItem]
    summary: ProjectRankingSummary


# ============================================
# 趋势数据
# ============================================

class TrendItem(BaseModel):
    """趋势数据项"""
    date: str
    revenue: float
    spend: float
    profit: float
    conversions: int


class TrendDataResponse(BaseModel):
    """趋势数据响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    granularity: str
    items: List[TrendItem]


# ============================================
# CEO 仪表盘概览
# ============================================

class CashStatusSummary(BaseModel):
    """现金状况摘要"""
    opening_balance: float
    closing_balance: float
    total_income: float
    total_expense: float
    balance_change_pct: float
    runway_days: int


class ProfitStatusSummary(BaseModel):
    """利润状况摘要"""
    total_revenue: float
    total_cost: float
    total_profit: float
    profit_rate: float
    profit_rate_pct: float
    total_conversions: int
    avg_cpl: float
    target_profit_rate: float
    profit_status: str


class ProjectBalanceOverview(BaseModel):
    """项目余额概览"""
    total_projects: int
    prepaid_count: int
    pending_refund_count: int
    refunded_count: int
    total_prepaid_balance: float


class ActionItemsSummary(BaseModel):
    """待办事项摘要"""
    abnormal_projects_count: int
    pending_reports_count: int
    pending_refunds_count: int


class TopProject(BaseModel):
    """Top 项目"""
    project_name: str
    profit: float
    profit_rate: float
    profit_rate_pct: float
    status: str


class CEOOverviewResponse(BaseModel):
    """CEO 仪表盘概览响应"""
    model_config = ConfigDict(from_attributes=True)

    period: str
    currency: str
    generated_at: str
    formula_version: str
    formula_note: str

    cash_status: CashStatusSummary
    profit_summary: ProfitStatusSummary
    project_balance_summary: ProjectBalanceOverview
    action_items: Dict[str, Any]
    top_projects: List[TopProject]
