"""
利润聚合与报表 Schema 定义
Version: 1.0
Author: Claude协作开发

对齐文档：
- PROFIT_SOT.md v1.1
- DATA_SCHEMA.md v5.2 §3.6

Pydantic v2 模式
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ========== Enum 枚举 ==========

class ProfitPeriodType(str, Enum):
    """利润聚合周期类型枚举（对齐 PROFIT_SOT.md v1.1 §2.1）"""
    DAILY = "daily"
    MONTHLY = "monthly"


class ProfitReportType(str, Enum):
    """利润报表类型枚举（对齐 PROFIT_SOT.md v1.1 §2.2）"""
    MONTHLY_SUMMARY = "monthly_summary"
    PROJECT_DETAIL = "project_detail"
    ACCOUNT_DETAIL = "account_detail"


class ProfitReportStatus(str, Enum):
    """利润报表状态枚举（对齐 PROFIT_SOT.md v1.1 §2.2）"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    LOCKED = "locked"


class ProfitGranularity(str, Enum):
    """利润查询粒度"""
    DAILY = "daily"
    MONTHLY = "monthly"


# ========== 请求模型 ==========

class GenerateProfitRequest(BaseModel):
    """
    生成/刷新利润聚合请求

    对齐 PROFIT_SOT.md v1.1 §3.2
    """
    model_config = ConfigDict(from_attributes=True)

    period_type: ProfitPeriodType = Field(
        ...,
        description="周期类型: daily | monthly"
    )
    period_start: date = Field(
        ...,
        description="周期开始日期 (ISO 8601)"
    )
    period_end: date = Field(
        ...,
        description="周期结束日期 (ISO 8601)"
    )
    project_id: Optional[int] = Field(
        None,
        description="指定项目ID，不传则全量聚合"
    )
    force_refresh: bool = Field(
        False,
        description="强制刷新已锁定数据（仅 admin 可用）"
    )

    @field_validator('period_start')
    @classmethod
    def validate_period_start(cls, v: date) -> date:
        """BR-PROFIT-005: 开始日期不能是未来日期"""
        if v > date.today():
            raise ValueError('开始日期不能是未来')
        return v

    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v: date, info) -> date:
        """BR-PROFIT-005: 结束日期必须 >= 开始日期"""
        period_start = info.data.get('period_start')
        if period_start and v < period_start:
            raise ValueError('结束日期不能早于开始日期')
        return v


class GetMonthlyProfitParams(BaseModel):
    """
    获取月度利润表参数

    对齐 PROFIT_SOT.md v1.1 §3.3
    """
    model_config = ConfigDict(from_attributes=True)

    year: int = Field(
        ...,
        ge=2020,
        le=2099,
        description="年份 (2020-2099)"
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="月份 (1-12)"
    )
    project_id: Optional[int] = Field(
        None,
        description="指定项目ID，不传返回所有项目"
    )
    include_accounts: bool = Field(
        False,
        description="是否包含账户明细"
    )


class GetDailyProfitParams(BaseModel):
    """
    获取日度利润数据参数

    对齐 PROFIT_SOT.md v1.1 §3.4
    """
    model_config = ConfigDict(from_attributes=True)

    start_date: date = Field(
        ...,
        description="开始日期"
    )
    end_date: date = Field(
        ...,
        description="结束日期"
    )
    project_id: Optional[int] = Field(
        None,
        description="指定项目ID"
    )
    page: int = Field(
        1,
        ge=1,
        description="页码"
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="每页数量"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """BR-PROFIT-005: 结束日期 >= 开始日期, 且范围不超过 366 天"""
        start_date = info.data.get('start_date')
        if start_date:
            if v < start_date:
                raise ValueError('结束日期不能早于开始日期')
            if (v - start_date).days > 366:
                raise ValueError('日期范围不能超过366天')
        return v


class GetProjectProfitParams(BaseModel):
    """
    获取项目利润明细参数

    对齐 PROFIT_SOT.md v1.1 §3.5
    """
    model_config = ConfigDict(from_attributes=True)

    start_date: date = Field(
        ...,
        description="开始日期"
    )
    end_date: date = Field(
        ...,
        description="结束日期"
    )
    granularity: ProfitGranularity = Field(
        ProfitGranularity.MONTHLY,
        description="粒度: daily | monthly"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """结束日期 >= 开始日期"""
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('结束日期不能早于开始日期')
        return v


class GetAccountProfitParams(BaseModel):
    """
    获取账户消耗明细参数

    对齐 PROFIT_SOT.md v1.1 §3.6
    """
    model_config = ConfigDict(from_attributes=True)

    start_date: date = Field(
        ...,
        description="开始日期"
    )
    end_date: date = Field(
        ...,
        description="结束日期"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """结束日期 >= 开始日期"""
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('结束日期不能早于开始日期')
        return v


class GetProfitSummaryParams(BaseModel):
    """
    获取整体利润汇总参数

    对齐 PROFIT_SOT.md v1.1 §3.7
    """
    model_config = ConfigDict(from_attributes=True)

    year: int = Field(
        ...,
        ge=2020,
        le=2099,
        description="年份"
    )
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="月份"
    )


# ========== 响应子模型 ==========

class PeriodInfo(BaseModel):
    """周期信息"""
    model_config = ConfigDict(from_attributes=True)

    type: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    year: Optional[int] = None
    month: Optional[int] = None


class GenerateSummary(BaseModel):
    """生成聚合汇总信息"""
    model_config = ConfigDict(from_attributes=True)

    total_projects: int = Field(0, description="项目数")
    total_accounts: int = Field(0, description="账户数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    gross_profit: Decimal = Field(Decimal("0.00"), description="毛利")


class ProfitSummaryData(BaseModel):
    """利润汇总数据"""
    model_config = ConfigDict(from_attributes=True)

    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    gross_profit: Decimal = Field(Decimal("0.00"), description="毛利")
    gross_margin_pct: Optional[Decimal] = Field(None, description="毛利率(%)")
    total_conversions: int = Field(0, description="总转化数")
    total_real_spend: Decimal = Field(Decimal("0.00"), description="总真实消耗")
    total_topup: Decimal = Field(Decimal("0.00"), description="总充值")
    report_count: int = Field(0, description="已锁定日报数量")
    is_locked: bool = Field(False, description="是否已锁定")


class ProjectProfitItem(BaseModel):
    """项目利润条目"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    gross_margin_pct: Optional[Decimal] = None
    conversions: int = 0
    real_spend: Decimal = Field(Decimal("0.00"))
    report_count: int = 0
    accounts: Optional[List["AccountProfitItem"]] = None


class AccountProfitItem(BaseModel):
    """账户利润条目"""
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_name: str
    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    conversions: int = 0
    real_spend: Decimal = Field(Decimal("0.00"))


class DailyProfitItem(BaseModel):
    """日度利润条目"""
    model_config = ConfigDict(from_attributes=True)

    period_start: date
    period_end: date
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    conversions: int = 0


class TrendPoint(BaseModel):
    """趋势数据点"""
    model_config = ConfigDict(from_attributes=True)

    date: date
    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    conversions: Optional[int] = None
    real_spend: Optional[Decimal] = None


class ProjectInfo(BaseModel):
    """项目信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit_price: Optional[Decimal] = None


class AccountInfo(BaseModel):
    """账户信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_code: Optional[str] = None
    project_id: int
    project_name: str


class ProjectDetailSummary(BaseModel):
    """项目详情汇总"""
    model_config = ConfigDict(from_attributes=True)

    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    gross_margin_pct: Optional[Decimal] = None
    conversions: int = 0
    avg_unit_cost: Optional[Decimal] = None


class AccountDetailSummary(BaseModel):
    """账户详情汇总"""
    model_config = ConfigDict(from_attributes=True)

    revenue: Decimal = Field(Decimal("0.00"))
    cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    gross_margin_pct: Optional[Decimal] = None
    conversions: int = 0
    real_spend: Decimal = Field(Decimal("0.00"))
    avg_unit_cost: Optional[Decimal] = None
    report_count: int = 0


class OverallSummary(BaseModel):
    """整体汇总数据"""
    model_config = ConfigDict(from_attributes=True)

    total_revenue: Decimal = Field(Decimal("0.00"))
    total_cost: Decimal = Field(Decimal("0.00"))
    gross_profit: Decimal = Field(Decimal("0.00"))
    gross_margin_pct: Optional[Decimal] = None
    total_conversions: int = 0
    total_topup: Decimal = Field(Decimal("0.00"))
    net_transfer: Decimal = Field(Decimal("0.00"))
    project_count: int = 0
    account_count: int = 0
    report_count: int = 0


class TopProjectItem(BaseModel):
    """TOP 项目条目"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    gross_profit: Decimal = Field(Decimal("0.00"))


# ========== 响应模型 ==========

class GenerateProfitResponseData(BaseModel):
    """
    生成利润聚合响应数据

    对齐 PROFIT_SOT.md v1.1 §3.2 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    generated_count: int = Field(0, description="生成记录数")
    period: PeriodInfo
    summary: GenerateSummary


class MonthlyProfitResponseData(BaseModel):
    """
    月度利润表响应数据

    对齐 PROFIT_SOT.md v1.1 §3.3 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    period: PeriodInfo
    summary: ProfitSummaryData
    by_project: List[ProjectProfitItem] = Field(default_factory=list)


class DailyProfitResponseData(BaseModel):
    """
    日度利润数据响应

    对齐 PROFIT_SOT.md v1.1 §3.4 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    items: List[DailyProfitItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    pages: int = 0


class ProjectProfitResponseData(BaseModel):
    """
    项目利润明细响应数据

    对齐 PROFIT_SOT.md v1.1 §3.5 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    project: ProjectInfo
    period: PeriodInfo
    summary: ProjectDetailSummary
    trend: List[TrendPoint] = Field(default_factory=list)
    by_account: List[AccountProfitItem] = Field(default_factory=list)


class AccountProfitResponseData(BaseModel):
    """
    账户消耗明细响应数据

    对齐 PROFIT_SOT.md v1.1 §3.6 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    account: AccountInfo
    period: PeriodInfo
    summary: AccountDetailSummary
    daily_trend: List[TrendPoint] = Field(default_factory=list)


class ProfitSummaryResponseData(BaseModel):
    """
    整体利润汇总响应数据

    对齐 PROFIT_SOT.md v1.1 §3.7 响应结构
    """
    model_config = ConfigDict(from_attributes=True)

    period: PeriodInfo
    overall: OverallSummary
    top_projects: List[TopProjectItem] = Field(default_factory=list)
    is_locked: bool = False


# ========== ORM 映射响应 ==========

class ProfitAggregateResponse(BaseModel):
    """
    利润聚合记录响应

    用于直接从 ORM 模型映射
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    period_type: str
    period_start: datetime
    period_end: datetime
    project_id: Optional[int] = None
    ad_account_id: Optional[int] = None
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    gross_margin_pct: Optional[Decimal] = None
    total_conversions: int
    total_real_spend: Decimal
    total_topup: Decimal
    transfer_in: Decimal
    transfer_out: Decimal
    is_locked: bool
    locked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ProfitReportSnapshotResponse(BaseModel):
    """
    利润报表快照响应

    用于直接从 ORM 模型映射
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    period_month: str
    project_id: Optional[int] = None
    report_data: Dict[str, Any]
    status: str
    generated_at: datetime
    confirmed_at: Optional[datetime] = None
    created_at: datetime


# 解决循环引用
ProjectProfitItem.model_rebuild()
