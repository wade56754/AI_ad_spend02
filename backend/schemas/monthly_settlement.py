"""
月度结算 Schema - TASK-FIN-003 月度锁账

SoT References:
- DATA_SCHEMA.md v5.7 §3.7.1 (monthly_settlements 表)
- API_SOT.md v9.0 §6.5 Monthly Settlements API
- STATE_MACHINE.md v2.9 §13.1 (月度结算状态机)
- MASTER.md v4.8 §2.4 (CEO: 月度锁账确认)

状态机 (4状态):
- pending → confirmed → locked → archived
- confirmed → pending (退回修正)

Version: 1.0
Author: Claude Code (TASK-FIN-003)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MonthlySettlementStatus(str, Enum):
    """月度结算状态枚举 (STATE_MACHINE.md v2.9 §13.1)"""

    PENDING = "pending"  # 待确认 - 系统自动汇总生成
    CONFIRMED = "confirmed"  # 已确认 - 财务确认数据正确
    LOCKED = "locked"  # 已锁定 - 老板最终确认锁定 (终态)
    ARCHIVED = "archived"  # 已归档 - 年度归档 (终态)


# ========== 请求模型 ==========


class MonthlySettlementGenerateRequest(BaseModel):
    """生成月度结算请求"""

    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., description="项目ID")
    settlement_month: date = Field(..., description="结算月份 (YYYY-MM-01)")
    notes: Optional[str] = Field(None, max_length=1000, description="结算备注")


class MonthlySettlementBatchGenerateRequest(BaseModel):
    """批量生成月度结算请求"""

    model_config = ConfigDict(from_attributes=True)

    settlement_month: date = Field(..., description="结算月份 (YYYY-MM-01)")
    project_ids: Optional[List[int]] = Field(None, description="项目ID列表 (为空则生成所有活跃项目)")


class MonthlySettlementConfirmRequest(BaseModel):
    """确认月度结算请求 (finance/admin)"""

    model_config = ConfigDict(from_attributes=True)

    notes: Optional[str] = Field(None, max_length=1000, description="确认备注")


class MonthlySettlementLockRequest(BaseModel):
    """锁定月度结算请求 (ceo/admin)"""

    model_config = ConfigDict(from_attributes=True)

    notes: Optional[str] = Field(None, max_length=1000, description="锁定备注")


class MonthlySettlementRejectRequest(BaseModel):
    """退回月度结算请求 (confirmed → pending)"""

    model_config = ConfigDict(from_attributes=True)

    reason: str = Field(..., min_length=1, max_length=1000, description="退回原因")


class MonthlySettlementUpdateRequest(BaseModel):
    """更新月度结算请求 (仅 pending 状态可更新)"""

    model_config = ConfigDict(from_attributes=True)

    total_spend: Optional[Decimal] = Field(None, ge=0, description="月消耗总额")
    total_conversions: Optional[int] = Field(None, ge=0, description="月进粉总数")
    notes: Optional[str] = Field(None, max_length=1000, description="结算备注")


# ========== 响应模型 ==========


class MonthlySettlementResponse(BaseModel):
    """月度结算响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="月度结算ID")
    project_id: int = Field(..., description="项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    settlement_month: date = Field(..., description="结算月份")
    total_spend: Decimal = Field(..., description="月消耗总额")
    total_conversions: int = Field(..., description="月进粉总数")
    total_revenue: Decimal = Field(..., description="月收入")
    gross_profit: Decimal = Field(..., description="月毛利")
    average_cpl: Optional[Decimal] = Field(None, description="月均 CPL")
    status: MonthlySettlementStatus = Field(..., description="状态")
    confirmed_at: Optional[date] = Field(None, description="财务确认时间")
    confirmed_by: Optional[UUID] = Field(None, description="确认人ID")
    confirmed_by_name: Optional[str] = Field(None, description="确认人姓名")
    locked_at: Optional[date] = Field(None, description="锁定时间")
    locked_by: Optional[UUID] = Field(None, description="锁定人ID")
    locked_by_name: Optional[str] = Field(None, description="锁定人姓名")
    notes: Optional[str] = Field(None, description="结算备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class MonthlySettlementListResponse(BaseModel):
    """月度结算列表响应"""

    model_config = ConfigDict(from_attributes=True)

    items: List[MonthlySettlementResponse] = Field(..., description="结算列表")
    meta: Dict[str, Any] = Field(..., description="分页元数据")


class MonthlySettlementSummary(BaseModel):
    """月度结算摘要"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: Optional[str] = None
    settlement_month: date
    total_spend: Decimal
    total_revenue: Decimal
    gross_profit: Decimal
    status: MonthlySettlementStatus


class MonthlySettlementStatistics(BaseModel):
    """月度结算统计"""

    model_config = ConfigDict(from_attributes=True)

    total_settlements: int = Field(0, description="结算总数")
    pending_count: int = Field(0, description="待确认数量")
    confirmed_count: int = Field(0, description="已确认数量")
    locked_count: int = Field(0, description="已锁定数量")
    total_spend: Decimal = Field(Decimal("0"), description="总消耗")
    total_revenue: Decimal = Field(Decimal("0"), description="总收入")
    total_profit: Decimal = Field(Decimal("0"), description="总毛利")
    by_status: List[Dict[str, Any]] = Field(default_factory=list, description="按状态统计")


class MonthlySettlementProjectSummary(BaseModel):
    """按项目汇总的月度结算"""

    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    settlement_count: int = Field(0, description="结算记录数")
    total_spend: Decimal = Field(Decimal("0"), description="累计消耗")
    total_revenue: Decimal = Field(Decimal("0"), description="累计收入")
    total_profit: Decimal = Field(Decimal("0"), description="累计毛利")
    average_cpl: Optional[Decimal] = Field(None, description="平均 CPL")
