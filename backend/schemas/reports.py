"""
报表管理数据模型
Version: 1.0
Author: Claude协作开发

提供多维度报表查询：
- 效果报表：广告消耗、线索数、CPA
- 利润报表：收入、成本、利润率
- 对账报表：对账状态汇总
- 财务摘要：账户余额、充值、消耗
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ReportPeriod(str, Enum):
    """报表周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportGroupBy(str, Enum):
    """报表分组维度"""
    PROJECT = "project"
    CHANNEL = "channel"
    ACCOUNT = "account"
    DATE = "date"
    SUPPLIER = "supplier"


class ReportExportFormat(str, Enum):
    """报表导出格式"""
    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"
    PDF = "pdf"


# ========== 请求模型 ==========

class ReportQueryRequest(BaseModel):
    """报表查询请求"""
    model_config = ConfigDict(from_attributes=True)

    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    period: Optional[ReportPeriod] = Field(None, description="统计周期")
    group_by: Optional[List[ReportGroupBy]] = Field(None, description="分组维度")
    project_ids: Optional[List[int]] = Field(None, description="项目ID列表")
    channel_ids: Optional[List[int]] = Field(None, description="渠道ID列表")
    account_ids: Optional[List[int]] = Field(None, description="账户ID列表")


class ReportExportRequest(BaseModel):
    """报表导出请求"""
    model_config = ConfigDict(from_attributes=True)

    report_type: str = Field(..., pattern="^(performance|profit|reconciliation|financial|summary)$")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    format: ReportExportFormat = Field(ReportExportFormat.EXCEL, description="导出格式")
    include_details: bool = Field(False, description="是否包含明细")


# ========== 响应模型 ==========

class PerformanceReportItem(BaseModel):
    """效果报表项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: Optional[int] = None
    project_name: Optional[str] = None
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    date: Optional[date] = None

    # 消耗指标
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_leads: int = Field(0, description="总线索数")
    cpa: Optional[Decimal] = Field(None, description="单线索成本")

    # 同比环比
    spend_change_rate: Optional[float] = Field(None, description="消耗变化率(%)")
    leads_change_rate: Optional[float] = Field(None, description="线索变化率(%)")


class PerformanceReportResponse(BaseModel):
    """效果报表响应"""
    items: List[PerformanceReportItem]
    summary: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ProfitReportItem(BaseModel):
    """利润报表项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: Optional[int] = None
    project_name: Optional[str] = None
    date: Optional[date] = None

    # 财务指标
    revenue: Decimal = Field(Decimal("0.00"), description="收入")
    cost: Decimal = Field(Decimal("0.00"), description="成本")
    profit: Decimal = Field(Decimal("0.00"), description="利润")
    profit_rate: Optional[float] = Field(None, description="利润率(%)")

    # 消耗明细
    ad_spend: Decimal = Field(Decimal("0.00"), description="广告消耗")
    topup_amount: Decimal = Field(Decimal("0.00"), description="充值金额")


class ProfitReportResponse(BaseModel):
    """利润报表响应"""
    items: List[ProfitReportItem]
    summary: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReconciliationReportItem(BaseModel):
    """对账报表项"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="统计周期")

    # 批次统计
    total_batches: int = Field(0, description="总批次数")
    draft_batches: int = Field(0, description="草稿批次")
    pending_review_batches: int = Field(0, description="待审核批次")
    approved_batches: int = Field(0, description="已批准批次")
    completed_batches: int = Field(0, description="已完成批次")

    # 金额统计
    total_system_spend: Decimal = Field(Decimal("0.00"), description="系统总消耗")
    total_actual_spend: Decimal = Field(Decimal("0.00"), description="实际总消耗")
    total_discrepancy: Decimal = Field(Decimal("0.00"), description="总差异")

    # 效率统计
    completion_rate: Optional[float] = Field(None, description="完成率(%)")
    discrepancy_rate: Optional[float] = Field(None, description="差异率(%)")


class ReconciliationReportResponse(BaseModel):
    """对账报表响应"""
    items: List[ReconciliationReportItem]
    summary: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class FinancialSummaryItem(BaseModel):
    """财务摘要项"""
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_name: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None

    # 余额信息
    current_balance: Decimal = Field(Decimal("0.00"), description="当前余额")

    # 期间统计
    total_topup: Decimal = Field(Decimal("0.00"), description="期间充值")
    total_spend: Decimal = Field(Decimal("0.00"), description="期间消耗")
    total_transfer_in: Decimal = Field(Decimal("0.00"), description="期间转入")
    total_transfer_out: Decimal = Field(Decimal("0.00"), description="期间转出")
    net_change: Decimal = Field(Decimal("0.00"), description="净变化")


class FinancialSummaryResponse(BaseModel):
    """财务摘要响应"""
    items: List[FinancialSummaryItem]
    summary: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class DashboardSummary(BaseModel):
    """仪表盘摘要"""
    model_config = ConfigDict(from_attributes=True)

    # 今日数据
    today_spend: Decimal = Field(Decimal("0.00"), description="今日消耗")
    today_leads: int = Field(0, description="今日线索")
    today_topup: Decimal = Field(Decimal("0.00"), description="今日充值")

    # 本月数据
    month_spend: Decimal = Field(Decimal("0.00"), description="本月消耗")
    month_leads: int = Field(0, description="本月线索")
    month_topup: Decimal = Field(Decimal("0.00"), description="本月充值")
    month_profit: Decimal = Field(Decimal("0.00"), description="本月利润")

    # 账户统计
    total_accounts: int = Field(0, description="账户总数")
    active_accounts: int = Field(0, description="活跃账户")
    low_balance_accounts: int = Field(0, description="低余额账户")

    # 项目统计
    total_projects: int = Field(0, description="项目总数")
    active_projects: int = Field(0, description="活跃项目")

    # 待办事项
    pending_topups: int = Field(0, description="待审批充值")
    pending_reconciliations: int = Field(0, description="待对账批次")
    pending_reports: int = Field(0, description="待提交日报")

    # 趋势数据
    spend_trend: List[Dict[str, Any]] = Field(default_factory=list, description="消耗趋势")
    leads_trend: List[Dict[str, Any]] = Field(default_factory=list, description="线索趋势")


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: date
    value: Decimal
    label: Optional[str] = None


class TrendReportResponse(BaseModel):
    """趋势报表响应"""
    period: str
    data_points: List[TrendDataPoint]
    summary: Dict[str, Any] = Field(default_factory=dict)


# ========== 导出相关 ==========

class ReportExportTask(BaseModel):
    """报表导出任务"""
    task_id: str
    status: str = Field("pending", description="任务状态")
    progress: int = Field(0, description="进度百分比")
    download_url: Optional[str] = Field(None, description="下载链接")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime
    completed_at: Optional[datetime] = None
