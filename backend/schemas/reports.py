"""
Reports 模块 Pydantic Schema 定义

对齐 SoT：
- LEDGER_SOT.md v1.1：双账本模型（PROJECT vs SUPPLIER）
- STATE_MACHINE.md v2.6：日报状态约束
- DATA_SCHEMA.md v5.2：表结构定义
- AUTH_SPEC.md v2.0：角色权限

Version: 1.0
Created: 2025-12-07
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ===== 枚举定义 =====

class GroupByPeriod(str, Enum):
    """时间分组粒度"""
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'


class ReportSortBy(str, Enum):
    """报表排序字段"""
    REVENUE = 'revenue'
    COST = 'cost'
    PROFIT = 'profit'
    CONVERSIONS = 'conversions'


class SortOrder(str, Enum):
    """排序方向"""
    ASC = 'asc'
    DESC = 'desc'


# ===== 查询参数 Schema =====

class ReportQueryParams(BaseModel):
    """报表查询参数基类"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    group_by: GroupByPeriod = Field(GroupByPeriod.DAY, description="时间分组粒度")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: ReportSortBy = Field(ReportSortBy.REVENUE, description="排序字段")
    sort_order: SortOrder = Field(SortOrder.DESC, description="排序方向")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """验证日期范围"""
        if v and 'start_date' in info.data and info.data['start_date']:
            if v < info.data['start_date']:
                raise ValueError("结束日期不能早于开始日期")
        return v


class ProjectReportQueryParams(ReportQueryParams):
    """项目报表查询参数"""
    project_id: Optional[int] = Field(None, description="项目 ID（可选筛选）")


class ChannelReportQueryParams(ReportQueryParams):
    """渠道报表查询参数"""
    channel_id: Optional[str] = Field(None, description="渠道 ID（UUID）")
    sort_by: str = Field('cost', description="排序字段（cost/topup/balance）")


class BuyerReportQueryParams(ReportQueryParams):
    """投手报表查询参数"""
    buyer_id: Optional[str] = Field(None, description="投手 ID（UUID）")


# ===== 报表行 Schema =====

class ProjectReportRow(BaseModel):
    """项目维度报表行"""
    project_id: int
    project_name: str
    account_manager_name: Optional[str] = None
    report_period: str = Field(..., description="报表周期（'2025-01-15' 或 '2025-W03' 或 '2025-01'）")

    # 粉数指标（来自 daily_reports）
    total_conversions_raw: int = Field(0, description="总粉数（raw）")
    total_conversions_final: int = Field(0, description="总粉数（final）")
    avg_unit_price: Decimal = Field(Decimal(0), description="平均单价")

    # 财务指标（来自 ledger_entries）
    total_revenue: Decimal = Field(Decimal(0), description="总收入（PROJECT 账本 REVENUE）")
    total_cost: Decimal = Field(Decimal(0), description="总成本（SUPPLIER 账本 COST，绝对值）")
    total_topup: Decimal = Field(Decimal(0), description="总充值（TOPUP 分录）")
    gross_profit: Decimal = Field(Decimal(0), description="毛利（revenue - cost）")
    profit_margin: Decimal = Field(Decimal(0), description="毛利率（%）")

    # 统计指标
    report_count: int = Field(0, description="日报数量")
    ad_account_count: int = Field(0, description="广告账户数")
    active_days: int = Field(0, description="有数据的天数")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)  # Decimal 转 float 用于 JSON 序列化
        }


class ProjectAccountReportRow(BaseModel):
    """项目账户维度报表行（项目详细报表）"""
    ad_account_id: int
    ad_account_name: str
    channel_name: str
    media_buyer_name: str

    # 指标同 ProjectReportRow
    total_conversions_final: int = 0
    total_revenue: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    gross_profit: Decimal = Decimal(0)
    profit_margin: Decimal = Decimal(0)

    report_count: int = 0
    active_days: int = 0

    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: float(v)}


class ChannelReportRow(BaseModel):
    """渠道维度报表行"""
    channel_id: str = Field(..., description="渠道 ID（UUID）")
    channel_name: str
    channel_code: str
    report_period: str

    # 成本指标（来自 SUPPLIER 账本）
    total_cost: Decimal = Field(Decimal(0), description="总成本（COST 分录，绝对值）")
    total_topup: Decimal = Field(Decimal(0), description="总充值（TOPUP 分录）")
    total_transfer_in: Decimal = Field(Decimal(0), description="转入金额（TRANSFER_IN）")
    total_transfer_out: Decimal = Field(Decimal(0), description="转出金额（TRANSFER_OUT，绝对值）")
    current_balance: Decimal = Field(Decimal(0), description="当期余额")

    # 统计指标
    ad_account_count: int = 0
    active_days: int = 0

    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: float(v)}


class BuyerReportRow(BaseModel):
    """投手维度报表行"""
    buyer_id: str = Field(..., description="投手 ID（UUID）")
    buyer_username: str
    buyer_full_name: Optional[str] = None
    account_manager_name: Optional[str] = None
    report_period: str

    # 绩效指标
    total_conversions_final: int = 0
    total_revenue: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    gross_profit: Decimal = Decimal(0)
    profit_margin: Decimal = Decimal(0)

    # 统计指标
    managed_accounts_count: int = 0
    active_projects_count: int = 0
    active_days: int = 0

    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: float(v)}


# ===== 汇总统计 Schema =====

class ReportSummary(BaseModel):
    """报表汇总统计"""
    total_revenue: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    total_profit: Decimal = Decimal(0)
    avg_profit_margin: Decimal = Decimal(0)
    total_conversions: int = 0

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


# ===== 仪表板汇总 Schema =====

class DashboardOverview(BaseModel):
    """仪表板总览"""
    total_revenue: Decimal
    total_cost: Decimal
    total_profit: Decimal
    avg_profit_margin: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class DashboardByProject(BaseModel):
    """按项目统计"""
    active_projects: int
    top_projects: List[ProjectReportRow]


class DashboardByChannel(BaseModel):
    """按渠道统计"""
    active_channels: int
    total_balance: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class DashboardByBuyer(BaseModel):
    """按投手统计"""
    active_buyers: int
    avg_conversions_per_buyer: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class TrendData(BaseModel):
    """趋势数据点"""
    period: str  # '2025-01-15' 或 '2025-01'
    revenue: Decimal
    cost: Decimal
    profit: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class DashboardTrend(BaseModel):
    """趋势数据"""
    daily: List[TrendData]
    monthly: List[TrendData]


class DashboardSummary(BaseModel):
    """仪表板完整汇总"""
    overview: DashboardOverview
    by_project: DashboardByProject
    by_channel: DashboardByChannel
    by_buyer: DashboardByBuyer
    trend: DashboardTrend

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


# ===== 响应 Schema =====

class ProjectReportListResponse(BaseModel):
    """项目报表列表响应"""
    items: List[ProjectReportRow]
    summary: ReportSummary
    meta: Dict[str, Any] = Field(..., description="分页元数据")


class ProjectAccountReportResponse(BaseModel):
    """项目详细报表响应"""
    project: Dict[str, Any]  # {id, name, account_manager: {id, username}}
    accounts: List[ProjectAccountReportRow]
    summary: ReportSummary


class ChannelReportListResponse(BaseModel):
    """渠道报表列表响应"""
    items: List[ChannelReportRow]
    summary: ReportSummary
    meta: Dict[str, Any]


class BuyerReportListResponse(BaseModel):
    """投手报表列表响应"""
    items: List[BuyerReportRow]
    summary: ReportSummary
    meta: Dict[str, Any]
