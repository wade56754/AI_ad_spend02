"""
资金总览相关 Pydantic 模型

SoT References:
- MASTER.md v4.4 §4.5.5 资金口径定义
- MASTER.md v4.4 §6.5 页面字段集
- A2-fund-overview.md §5 API 接口

依赖代码块:
- pagination: PaginationMeta (响应分页元信息)
- error-codes: 错误码常量

Version: 2.0
Author: Claude Code
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ========== 请求模型 ==========

class FundOverviewParams(BaseModel):
    """资金概览查询参数"""
    model_config = ConfigDict(from_attributes=True)

    date_from: Optional[date] = Field(None, description="开始日期")
    date_to: Optional[date] = Field(None, description="结束日期")


class FundDistributionParams(BaseModel):
    """资金分布查询参数"""
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field(
        "topup",
        pattern="^(topup|spend|balance)$",
        description="排序字段 (topup|spend|balance)"
    )
    order: Optional[str] = Field(
        "desc",
        pattern="^(asc|desc)$",
        description="排序方向 (asc|desc)"
    )
    date_from: Optional[date] = Field(None, description="开始日期")
    date_to: Optional[date] = Field(None, description="结束日期")


class ReceivableListParams(BaseModel):
    """应收明细查询参数"""
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    project_id: Optional[int] = Field(None, gt=0, description="项目ID筛选")
    status: Optional[str] = Field(
        None,
        pattern="^(pending|partial|received)$",
        description="状态筛选"
    )


class PaymentListParams(BaseModel):
    """回款记录查询参数"""
    model_config = ConfigDict(from_attributes=True)

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    project_id: Optional[int] = Field(None, gt=0, description="项目ID筛选")
    date_from: Optional[date] = Field(None, description="开始日期")
    date_to: Optional[date] = Field(None, description="结束日期")


# ========== 响应模型 - 资金概览 ==========

class FundOverviewResponse(BaseModel):
    """
    资金概览响应

    对齐 A2-fund-overview.md §5.2 GET /api/v1/fund/overview
    """
    model_config = ConfigDict(from_attributes=True)

    # 5 个核心资金指标
    total_topup: Decimal = Field(
        Decimal("0.00"),
        description="累计充值 = SUM(topup_record.amount WHERE status='completed')"
    )
    total_spend: Decimal = Field(
        Decimal("0.00"),
        description="累计消耗 = SUM(ad_spend_daily.spend)"
    )
    current_balance: Decimal = Field(
        Decimal("0.00"),
        description="当前余额 = 累计充值 - 累计消耗"
    )
    total_receivable: Decimal = Field(
        Decimal("0.00"),
        description="应收款 = SUM(conversions × unit_price) - 累计回款"
    )
    total_received: Decimal = Field(
        Decimal("0.00"),
        description="累计回款 = SUM(receivable.amount WHERE status='received')"
    )
    fund_occupied: Decimal = Field(
        Decimal("0.00"),
        description="资金占用 = 累计充值 - 累计回款"
    )

    # 变化指标
    topup_change: Optional[float] = Field(
        None,
        description="充值较上月变化百分比"
    )
    spend_change: Optional[float] = Field(
        None,
        description="消耗较上月变化百分比"
    )
    balance_change: Optional[float] = Field(
        None,
        description="余额变化百分比"
    )
    occupy_rate: Optional[float] = Field(
        None,
        description="资金占用率 = 资金占用 / 累计充值 × 100%"
    )

    # 待处理计数
    pending_receivable_count: int = Field(
        0,
        description="待收款笔数"
    )

    # 时间范围
    date_from: Optional[date] = Field(None, description="统计开始日期")
    date_to: Optional[date] = Field(None, description="统计结束日期")


# ========== 响应模型 - 资金分布 ==========

class ProjectFundItem(BaseModel):
    """项目资金分布项"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    owner_id: Optional[UUID] = Field(None, description="负责人ID")
    owner_name: Optional[str] = Field(None, description="负责人姓名")
    total_topup: Decimal = Field(Decimal("0.00"), description="累计充值")
    total_spend: Decimal = Field(Decimal("0.00"), description="累计消耗")
    balance: Decimal = Field(Decimal("0.00"), description="余额")
    receivable: Decimal = Field(Decimal("0.00"), description="应收款")
    received: Decimal = Field(Decimal("0.00"), description="已回款")
    unit_price: Optional[Decimal] = Field(None, description="单价")
    is_pricing_pending: bool = Field(False, description="是否待定价")


class ChannelFundItem(BaseModel):
    """渠道资金分布项"""
    model_config = ConfigDict(from_attributes=True)

    channel_id: Optional[str] = Field(None, description="渠道/供应商ID (UUID字符串)")
    channel_name: str = Field(..., description="渠道名称")
    total_topup: Decimal = Field(Decimal("0.00"), description="累计充值")
    total_spend: Decimal = Field(Decimal("0.00"), description="累计消耗")
    balance: Decimal = Field(Decimal("0.00"), description="余额")
    account_count: int = Field(0, description="账户数量")


class FundDistributionProjectsResponse(BaseModel):
    """按项目资金分布响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProjectFundItem] = Field(
        default_factory=list,
        description="项目资金分布列表"
    )
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")

    # 汇总
    summary: Optional[Dict[str, Decimal]] = Field(
        None,
        description="汇总数据 {total_topup, total_spend, total_balance}"
    )


class FundDistributionChannelsResponse(BaseModel):
    """按渠道资金分布响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ChannelFundItem] = Field(
        default_factory=list,
        description="渠道资金分布列表"
    )
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")

    # 汇总
    summary: Optional[Dict[str, Decimal]] = Field(
        None,
        description="汇总数据 {total_topup, total_spend, total_balance}"
    )


# ========== 响应模型 - 应收明细 ==========

class ReceivableItem(BaseModel):
    """应收明细项"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="应收ID")
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    amount: Decimal = Field(..., description="应收金额")
    received_amount: Decimal = Field(Decimal("0.00"), description="已收金额")
    pending_amount: Decimal = Field(Decimal("0.00"), description="待收金额")
    status: str = Field(..., description="状态: pending/partial/received")
    due_date: Optional[date] = Field(None, description="预计回款日期")
    days_pending: int = Field(0, description="待收天数")
    created_at: datetime = Field(..., description="创建时间")
    notes: Optional[str] = Field(None, description="备注")


class ReceivableListResponse(BaseModel):
    """应收明细列表响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ReceivableItem] = Field(default_factory=list, description="应收列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")

    # 汇总
    total_amount: Decimal = Field(Decimal("0.00"), description="应收总额")
    total_pending: Decimal = Field(Decimal("0.00"), description="待收总额")


# ========== 响应模型 - 回款记录 ==========

class PaymentItem(BaseModel):
    """回款记录项"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="回款ID")
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    amount: Decimal = Field(..., description="回款金额")
    payment_date: date = Field(..., description="回款日期")
    payment_method: Optional[str] = Field(None, description="回款方式")
    reference_no: Optional[str] = Field(None, description="凭证号")
    created_at: datetime = Field(..., description="记录时间")
    created_by_name: Optional[str] = Field(None, description="操作人")
    notes: Optional[str] = Field(None, description="备注")


class PaymentListResponse(BaseModel):
    """回款记录列表响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[PaymentItem] = Field(default_factory=list, description="回款列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(20, description="每页数量")

    # 汇总
    total_amount: Decimal = Field(Decimal("0.00"), description="回款总额")


# ========== 响应模型 - 预警 ==========

class FundAlertItem(BaseModel):
    """资金预警项"""
    model_config = ConfigDict(from_attributes=True)

    alert_type: str = Field(
        ...,
        description="预警类型: high_occupy_rate/negative_balance/overdue_receivable"
    )
    severity: str = Field(
        "medium",
        description="严重程度: low/medium/high/critical"
    )
    project_id: Optional[int] = Field(None, description="相关项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    message: str = Field(..., description="预警消息")
    value: Optional[Decimal] = Field(None, description="相关数值")
    threshold: Optional[Decimal] = Field(None, description="阈值")
    created_at: datetime = Field(..., description="产生时间")


class FundAlertsResponse(BaseModel):
    """资金预警列表响应"""
    model_config = ConfigDict(from_attributes=True)

    alerts: List[FundAlertItem] = Field(default_factory=list, description="预警列表")
    total: int = Field(0, description="预警总数")
    critical_count: int = Field(0, description="严重预警数")
    high_count: int = Field(0, description="高优先级数")
