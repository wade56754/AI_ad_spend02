"""
财务管理 V2 Schemas - 资金总览 + 项目盈亏

基于任务规格重构，完全匹配新的 API 响应格式。

SoT References:
- MASTER.md v4.4 §4.5.5 资金口径定义
- LEDGER_SOT.md v1.1 §2-3 双账本
- CORE_MODULES.md v1.0 §4.5 阶梯价格规则

Version: 1.0
Author: Claude Code
Created: 2025-12-25
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 枚举类型
# ============================================================================

ProfitStatus = Literal["healthy", "warning", "danger", "inactive"]
ReceivableStatus = Literal["settled", "outstanding", "refunded"]
TrendGranularity = Literal["day", "week", "month"]
DistributionGroupBy = Literal["project", "supplier", "platform"]
ProjectSortBy = Literal["profit", "profit_rate", "revenue"]


# ============================================================================
# Page 1: 资金总览 (Fund Overview) - Schemas
# ============================================================================

# ---------- API 1: GET /api/v1/finance/fund/overview ----------

class FundSummary(BaseModel):
    """资金概览汇总数据"""
    model_config = ConfigDict(from_attributes=True)

    total_income: Decimal = Field(
        Decimal("0.00"),
        description="本月收款 = SUM(ledger.amount) WHERE type=PROJECT AND entry=TOPUP"
    )
    total_expense: Decimal = Field(
        Decimal("0.00"),
        description="本月支出 = ABS(SUM(ledger.amount)) WHERE type=SUPPLIER"
    )
    total_receivable: Decimal = Field(
        Decimal("0.00"),
        description="应收总额 = SUM(conversions_final × unit_price) 按项目"
    )
    total_received: Decimal = Field(
        Decimal("0.00"),
        description="已收总额 = SUM(ledger.amount) WHERE entry=TOPUP 按项目"
    )
    outstanding: Decimal = Field(
        Decimal("0.00"),
        description="应收未收 = total_receivable - total_received"
    )
    outstanding_count: int = Field(
        0,
        description="未结清项目数"
    )
    available_balance: Decimal = Field(
        Decimal("0.00"),
        description="可用余额 = total_income - total_expense + opening_balance"
    )
    opening_balance: Decimal = Field(
        Decimal("0.00"),
        description="期初余额"
    )


class FundChanges(BaseModel):
    """资金变化率"""
    model_config = ConfigDict(from_attributes=True)

    income_change_pct: Optional[float] = Field(
        None,
        description="收款环比变化百分比"
    )
    expense_change_pct: Optional[float] = Field(
        None,
        description="支出环比变化百分比"
    )
    balance_change_pct: Optional[float] = Field(
        None,
        description="余额环比变化百分比"
    )


class FundOverviewData(BaseModel):
    """资金概览响应数据"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="时间范围，格式: 2025-12")
    currency: str = Field("USD", description="币种")
    summary: FundSummary = Field(..., description="汇总数据")
    changes: FundChanges = Field(default_factory=FundChanges, description="变化率")


# ---------- API 2: GET /api/v1/finance/fund/receivables ----------

class ReceivableItem(BaseModel):
    """应收账款明细项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    client_name: str = Field(..., description="甲方名称")
    total_topup: Decimal = Field(Decimal("0.00"), description="总打款")
    total_receivable: Decimal = Field(Decimal("0.00"), description="应收金额")
    total_received: Decimal = Field(Decimal("0.00"), description="已收金额")
    outstanding: Decimal = Field(Decimal("0.00"), description="未收金额")
    balance: Decimal = Field(Decimal("0.00"), description="余额")
    status: ReceivableStatus = Field("outstanding", description="状态")
    last_payment_date: Optional[date] = Field(None, description="最后回款日期")
    refund_date: Optional[date] = Field(None, description="退款日期（仅 refunded 状态）")


class ReceivablesTotals(BaseModel):
    """应收账款汇总"""
    model_config = ConfigDict(from_attributes=True)

    total_topup: Decimal = Field(Decimal("0.00"), description="打款总额")
    total_receivable: Decimal = Field(Decimal("0.00"), description="应收总额")
    total_outstanding: Decimal = Field(Decimal("0.00"), description="未收总额")


class ReceivablesData(BaseModel):
    """应收账款响应数据"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ReceivableItem] = Field(default_factory=list, description="应收明细列表")
    totals: ReceivablesTotals = Field(default_factory=ReceivablesTotals, description="汇总")


# ---------- API 3: GET /api/v1/finance/fund/distribution ----------

class DistributionItem(BaseModel):
    """资金分布项"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="项目/渠道 ID")
    name: str = Field(..., description="名称")
    balance: Decimal = Field(Decimal("0.00"), description="余额")
    percentage: float = Field(0.0, description="占比百分比")


class FundDistributionData(BaseModel):
    """资金分布响应数据"""
    model_config = ConfigDict(from_attributes=True)

    group_by: DistributionGroupBy = Field("project", description="分组方式")
    items: List[DistributionItem] = Field(default_factory=list, description="分布列表")
    total: Decimal = Field(Decimal("0.00"), description="总余额")


# ============================================================================
# Page 2: 项目盈亏 (Profit Analysis) - Schemas
# ============================================================================

# ---------- API 4: GET /api/v1/finance/profit/overview ----------

class ProfitSummary(BaseModel):
    """盈亏概览汇总"""
    model_config = ConfigDict(from_attributes=True)

    total_revenue: Decimal = Field(
        Decimal("0.00"),
        description="总收入 = SUM(conversions × unit_price)"
    )
    total_cost: Decimal = Field(
        Decimal("0.00"),
        description="总成本 = SUM(real_spend + fee)"
    )
    total_profit: Decimal = Field(
        Decimal("0.00"),
        description="总利润 = total_revenue - total_cost"
    )
    total_conversions: int = Field(
        0,
        description="总进粉数"
    )
    avg_profit_rate: float = Field(
        0.0,
        description="平均利润率 = total_profit / total_revenue"
    )
    total_fee: Decimal = Field(
        Decimal("0.00"),
        description="总服务费"
    )


class ProfitChanges(BaseModel):
    """盈亏变化率"""
    model_config = ConfigDict(from_attributes=True)

    revenue_change_pct: Optional[float] = Field(
        None,
        description="收入环比变化百分比"
    )
    profit_change_pct: Optional[float] = Field(
        None,
        description="利润环比变化百分比"
    )


class ProfitBenchmarks(BaseModel):
    """盈亏基准"""
    model_config = ConfigDict(from_attributes=True)

    industry_avg_profit_rate: float = Field(
        0.15,
        description="行业平均利润率"
    )
    company_target_profit_rate: float = Field(
        0.20,
        description="公司目标利润率"
    )


class ProfitOverviewData(BaseModel):
    """盈亏概览响应数据"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="时间范围，格式: 2025-12")
    currency: str = Field("USD", description="币种")
    summary: ProfitSummary = Field(..., description="汇总数据")
    changes: ProfitChanges = Field(default_factory=ProfitChanges, description="变化率")
    benchmarks: ProfitBenchmarks = Field(default_factory=ProfitBenchmarks, description="基准值")


# ---------- API 5: GET /api/v1/finance/profit/projects ----------

class PriceTier(BaseModel):
    """阶梯价格定义"""
    model_config = ConfigDict(from_attributes=True)

    min: int = Field(..., description="最小粉数")
    max: Optional[int] = Field(None, description="最大粉数，null 表示无上限")
    price: Decimal = Field(..., description="单价")


class PriceRules(BaseModel):
    """价格规则"""
    model_config = ConfigDict(from_attributes=True)

    type: Literal["fixed", "tiered", "spend_ratio"] = Field(
        "fixed",
        description="定价类型: fixed=固定单价, tiered=阶梯, spend_ratio=按消耗比例"
    )
    tiers: Optional[List[PriceTier]] = Field(
        None,
        description="阶梯价格（仅 tiered 类型）"
    )
    ratio: Optional[float] = Field(
        None,
        description="消耗比例（仅 spend_ratio 类型）"
    )


class ProjectProfitItem(BaseModel):
    """项目利润明细项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    status: str = Field("active", description="项目状态")
    profit_status: ProfitStatus = Field(
        "healthy",
        description="利润状态: healthy(≥15%), warning(5-15%), danger(<5%), inactive"
    )
    conversions: Optional[int] = Field(None, description="进粉数，按消耗结算时为 null")
    revenue: Decimal = Field(Decimal("0.00"), description="收入")
    avg_unit_price: Decimal = Field(Decimal("0.00"), description="平均单价")
    cost: Decimal = Field(Decimal("0.00"), description="成本")
    fee_rate: float = Field(0.0, description="费率")
    profit: Decimal = Field(Decimal("0.00"), description="利润")
    profit_rate: float = Field(0.0, description="利润率")
    price_rules: Optional[PriceRules] = Field(None, description="价格规则")


class ProjectProfitTotals(BaseModel):
    """项目利润汇总"""
    model_config = ConfigDict(from_attributes=True)

    total_conversions: int = Field(0, description="总进粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    avg_profit_rate: float = Field(0.0, description="平均利润率")


class ProjectProfitsData(BaseModel):
    """项目利润响应数据"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProjectProfitItem] = Field(default_factory=list, description="项目列表")
    totals: ProjectProfitTotals = Field(
        default_factory=ProjectProfitTotals,
        description="汇总"
    )


# ---------- API 6: GET /api/v1/finance/profit/suppliers ----------

class SupplierCostItem(BaseModel):
    """渠道成本明细项"""
    model_config = ConfigDict(from_attributes=True)

    supplier_id: str = Field(..., description="供应商 ID (UUID)")
    supplier_name: str = Field(..., description="供应商名称")
    platform: Optional[str] = Field(None, description="平台: FB/TikTok/Google 等")
    fee_rate: float = Field(0.0, description="费率")
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_fee: Decimal = Field(Decimal("0.00"), description="总服务费")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本 = spend + fee")
    account_count: int = Field(0, description="账户数量")


class SupplierCostSummary(BaseModel):
    """渠道成本汇总"""
    model_config = ConfigDict(from_attributes=True)

    avg_fee_rate: float = Field(0.0, description="平均费率")
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_fee: Decimal = Field(Decimal("0.00"), description="总服务费")


class SupplierCostsData(BaseModel):
    """渠道成本响应数据"""
    model_config = ConfigDict(from_attributes=True)

    items: List[SupplierCostItem] = Field(default_factory=list, description="渠道列表")
    summary: SupplierCostSummary = Field(
        default_factory=SupplierCostSummary,
        description="汇总"
    )


# ---------- API 7: GET /api/v1/finance/profit/trend ----------

class TrendSeriesItem(BaseModel):
    """趋势数据点"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="时间段标识: 2025-W48 或 2025-12-01")
    revenue: Decimal = Field(Decimal("0.00"), description="收入")
    cost: Decimal = Field(Decimal("0.00"), description="成本")
    profit: Decimal = Field(Decimal("0.00"), description="利润")


class ProfitTrendData(BaseModel):
    """利润趋势响应数据"""
    model_config = ConfigDict(from_attributes=True)

    granularity: TrendGranularity = Field("week", description="颗粒度")
    series: List[TrendSeriesItem] = Field(default_factory=list, description="趋势数据")


# ============================================================================
# 请求参数 Schemas
# ============================================================================

class FundOverviewParams(BaseModel):
    """资金概览查询参数"""
    model_config = ConfigDict(from_attributes=True)

    period: Optional[str] = Field(
        None,
        pattern=r"^(month|quarter|year)$",
        description="时间范围: month/quarter/year"
    )
    date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="指定月份: 2025-12"
    )


class ReceivablesParams(BaseModel):
    """应收账款查询参数"""
    model_config = ConfigDict(from_attributes=True)

    period: Optional[str] = Field(None, description="时间范围")
    status: Optional[str] = Field(
        "all",
        pattern=r"^(all|outstanding|settled)$",
        description="状态: all/outstanding/settled"
    )
    sort_by: Optional[str] = Field(
        "outstanding",
        pattern=r"^(outstanding|receivable|client)$",
        description="排序: outstanding/receivable/client"
    )


class FundDistributionParams(BaseModel):
    """资金分布查询参数"""
    model_config = ConfigDict(from_attributes=True)

    group_by: Optional[DistributionGroupBy] = Field(
        "project",
        description="分组: project/supplier/platform"
    )
    period: Optional[str] = Field(None, description="时间范围")


class ProfitOverviewParams(BaseModel):
    """盈亏概览查询参数"""
    model_config = ConfigDict(from_attributes=True)

    period: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}$",
        description="指定月份: 2025-12"
    )


class ProjectProfitsParams(BaseModel):
    """项目利润查询参数"""
    model_config = ConfigDict(from_attributes=True)

    period: Optional[str] = Field(None, description="时间范围")
    sort_by: Optional[ProjectSortBy] = Field(
        "profit",
        description="排序: profit/profit_rate/revenue"
    )
    status: Optional[str] = Field(
        "all",
        pattern=r"^(all|active|inactive)$",
        description="状态: all/active/inactive"
    )


class SupplierCostsParams(BaseModel):
    """渠道成本查询参数"""
    model_config = ConfigDict(from_attributes=True)

    period: Optional[str] = Field(None, description="时间范围")


class ProfitTrendParams(BaseModel):
    """利润趋势查询参数"""
    model_config = ConfigDict(from_attributes=True)

    granularity: Optional[TrendGranularity] = Field(
        "week",
        description="颗粒度: day/week/month"
    )
    period: Optional[str] = Field(None, description="时间范围")
