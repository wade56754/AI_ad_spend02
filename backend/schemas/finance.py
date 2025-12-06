"""
Finance Schemas - Profit Summary
Version: 1.0 (SoT Aligned)
Author: Claude协作开发

SoT 对齐:
- DATA_SCHEMA.md v5.2: daily_reports, projects 表结构
- BUSINESS_RULES.md v3.1: 利润计算公式
  - revenue = conversions_final × unit_price
  - cost = real_spend + fee
  - profit = revenue - cost
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ProfitSummaryRequest(BaseModel):
    """利润汇总查询请求"""
    project_id: Optional[int] = Field(None, description="项目ID (BIGINT)")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class ProfitSummaryItem(BaseModel):
    """单条利润汇总项"""
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


class ProfitSummaryResponse(BaseModel):
    """利润汇总响应"""
    model_config = ConfigDict(from_attributes=True)

    items: List[ProfitSummaryItem] = Field(default_factory=list, description="利润明细列表")
    total_conversions: int = Field(default=0, description="总粉数")
    total_revenue: Decimal = Field(default=Decimal("0.00"), description="总收入")
    total_cost: Decimal = Field(default=Decimal("0.00"), description="总成本")
    total_profit: Decimal = Field(default=Decimal("0.00"), description="总利润")
    overall_profit_margin: float = Field(default=0.0, description="总体利润率")
