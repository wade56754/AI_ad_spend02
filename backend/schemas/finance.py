"""
Finance Schemas - Profit Summary & Analysis
Version: 2.0 (SoT Aligned)
Author: Claude协作开发

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects, ad_accounts, channels 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
  - profit_margin = profit / revenue × 100
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ========== 枚举类型 ==========

class ProfitDimensionEnum(str, Enum):
    """利润统计维度枚举"""
    PROJECT = "project"
    ACCOUNT = "account"
    CHANNEL = "channel"
    DATE = "date"


class TrendGranularityEnum(str, Enum):
    """趋势分析粒度枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ========== 请求模型 ==========

class ProfitSummaryRequest(BaseModel):
    """利润汇总查询请求"""
    project_id: Optional[int] = Field(None, description="项目ID (BIGINT)")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class ProfitByDimensionRequest(BaseModel):
    """按维度统计利润请求"""
    dimension: ProfitDimensionEnum = Field(
        ProfitDimensionEnum.PROJECT,
        description="统计维度"
    )
    project_id: Optional[int] = Field(None, description="项目ID过滤")
    channel_id: Optional[int] = Field(None, description="渠道ID过滤")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    limit: int = Field(20, ge=1, le=100, description="返回数量限制")


class ProfitTrendRequest(BaseModel):
    """利润趋势分析请求"""
    project_id: Optional[int] = Field(None, description="项目ID过滤")
    channel_id: Optional[int] = Field(None, description="渠道ID过滤")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    granularity: TrendGranularityEnum = Field(
        TrendGranularityEnum.DAILY,
        description="趋势粒度"
    )


class ProfitCompareRequest(BaseModel):
    """利润对比分析请求"""
    project_ids: List[int] = Field(..., min_length=1, max_length=10, description="对比项目ID列表")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


# ========== 响应模型 - 基础项 ==========

class ProfitSummaryItem(BaseModel):
    """单条利润汇总项（按日期+项目）"""
    model_config = ConfigDict(from_attributes=True)

    report_date: date = Field(..., description="报告日期")
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    conversions_final: int = Field(..., description="最终粉数")
    unit_price: Decimal = Field(..., description="单粉价格")
    revenue: Decimal = Field(..., description="收入 = conversions_final × unit_price")
    real_spend: Decimal = Field(..., description="真实消耗")
    fee: Decimal = Field(default=Decimal("0.00"), description="服务费")
    cost: Decimal = Field(..., description="成本 = real_spend + fee")
    profit: Decimal = Field(..., description="利润 = revenue - cost")
    profit_margin: float = Field(..., description="利润率 = profit / revenue × 100")


class ProfitByProjectItem(BaseModel):
    """按项目汇总利润项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    total_conversions: int = Field(0, description="总粉数")
    avg_unit_price: Decimal = Field(Decimal("0.00"), description="平均单粉价格")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_fee: Decimal = Field(Decimal("0.00"), description="总服务费")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    profit_margin: float = Field(0.0, description="利润率")
    report_count: int = Field(0, description="日报数量")


class ProfitByAccountItem(BaseModel):
    """按账户汇总利润项"""
    model_config = ConfigDict(from_attributes=True)

    ad_account_id: int = Field(..., description="广告账户ID")
    account_name: str = Field(..., description="账户名称")
    project_id: int = Field(..., description="所属项目ID")
    project_name: str = Field(..., description="所属项目名称")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    profit_margin: float = Field(0.0, description="利润率")


class ProfitByChannelItem(BaseModel):
    """按渠道汇总利润项"""
    model_config = ConfigDict(from_attributes=True)

    channel_id: int = Field(..., description="渠道ID")
    channel_name: str = Field(..., description="渠道名称")
    total_accounts: int = Field(0, description="账户数量")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_spend: Decimal = Field(Decimal("0.00"), description="总消耗")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    profit_margin: float = Field(0.0, description="利润率")


class ProfitTrendItem(BaseModel):
    """利润趋势项"""
    model_config = ConfigDict(from_attributes=True)

    period: str = Field(..., description="时间段（日期/周/月）")
    period_start: date = Field(..., description="时间段开始日期")
    period_end: date = Field(..., description="时间段结束日期")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    profit_margin: float = Field(0.0, description="利润率")
    # 同比/环比
    profit_change: Optional[Decimal] = Field(None, description="利润变化额")
    profit_change_rate: Optional[float] = Field(None, description="利润变化率(%)")


class ProfitCompareItem(BaseModel):
    """利润对比项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    profit_margin: float = Field(0.0, description="利润率")
    # 排名
    rank_by_profit: int = Field(0, description="利润排名")
    rank_by_margin: int = Field(0, description="利润率排名")


# ========== 响应模型 - 汇总 ==========

class ProfitSummaryResponse(BaseModel):
    """利润汇总响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitSummaryItem] = Field(default_factory=list, description="利润明细列表")
    total_conversions: int = Field(default=0, description="总粉数")
    total_revenue: Decimal = Field(default=Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(default=Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(default=Decimal("0.00"), description="总利润")
    overall_profit_margin: float = Field(default=0.0, description="总体利润率")


class ProfitByProjectResponse(BaseModel):
    """按项目汇总利润响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitByProjectItem] = Field(default_factory=list, description="项目利润列表")
    total_projects: int = Field(0, description="项目总数")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    overall_profit_margin: float = Field(0.0, description="总体利润率")


class ProfitByAccountResponse(BaseModel):
    """按账户汇总利润响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitByAccountItem] = Field(default_factory=list, description="账户利润列表")
    total_accounts: int = Field(0, description="账户总数")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    overall_profit_margin: float = Field(0.0, description="总体利润率")


class ProfitByChannelResponse(BaseModel):
    """按渠道汇总利润响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitByChannelItem] = Field(default_factory=list, description="渠道利润列表")
    total_channels: int = Field(0, description="渠道总数")
    total_conversions: int = Field(0, description="总粉数")
    total_revenue: Decimal = Field(Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    overall_profit_margin: float = Field(0.0, description="总体利润率")


class ProfitTrendResponse(BaseModel):
    """利润趋势分析响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitTrendItem] = Field(default_factory=list, description="趋势数据列表")
    granularity: str = Field(..., description="趋势粒度")
    period_count: int = Field(0, description="时间段数量")
    # 统计指标
    avg_profit: Decimal = Field(Decimal("0.00"), description="平均利润")
    max_profit: Decimal = Field(Decimal("0.00"), description="最高利润")
    min_profit: Decimal = Field(Decimal("0.00"), description="最低利润")
    profit_volatility: float = Field(0.0, description="利润波动率(%)")


class ProfitCompareResponse(BaseModel):
    """利润对比分析响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitCompareItem] = Field(default_factory=list, description="对比数据列表")
    compare_count: int = Field(0, description="对比项目数")
    best_profit_project: Optional[str] = Field(None, description="利润最高项目")
    best_margin_project: Optional[str] = Field(None, description="利润率最高项目")
    total_profit: Decimal = Field(Decimal("0.00"), description="总利润")
    avg_profit_margin: float = Field(0.0, description="平均利润率")


# ========== 统计概览 ==========

class ProfitOverviewResponse(BaseModel):
    """利润概览响应"""
    model_config = ConfigDict(from_attributes=True)

    # 今日数据
    today_revenue: Decimal = Field(Decimal("0.00"), description="今日收入")
    today_cost: Decimal = Field(Decimal("0.00"), description="今日成本")
    today_profit: Decimal = Field(Decimal("0.00"), description="今日利润")
    today_profit_margin: float = Field(0.0, description="今日利润率")

    # 本周数据
    week_revenue: Decimal = Field(Decimal("0.00"), description="本周收入")
    week_cost: Decimal = Field(Decimal("0.00"), description="本周成本")
    week_profit: Decimal = Field(Decimal("0.00"), description="本周利润")
    week_profit_margin: float = Field(0.0, description="本周利润率")

    # 本月数据
    month_revenue: Decimal = Field(Decimal("0.00"), description="本月收入")
    month_cost: Decimal = Field(Decimal("0.00"), description="本月成本")
    month_profit: Decimal = Field(Decimal("0.00"), description="本月利润")
    month_profit_margin: float = Field(0.0, description="本月利润率")

    # 环比变化
    profit_change_from_yesterday: Optional[float] = Field(None, description="较昨日利润变化率")
    profit_change_from_last_week: Optional[float] = Field(None, description="较上周利润变化率")
    profit_change_from_last_month: Optional[float] = Field(None, description="较上月利润变化率")

    # Top 项目
    top_profit_projects: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="利润TOP项目"
    )
