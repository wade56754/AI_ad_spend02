"""
结算管理数据模型
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- DATA_SCHEMA.md v5.2 (settlement entity)
- BUSINESS_RULES.md v3.1 (settlement constraints)
- LEDGER_SOT.md v1.1 (settlement ledger entries)
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class SettlementStatus(str, Enum):
    """结算状态枚举"""
    DRAFT = "draft"              # 草稿
    PENDING = "pending"          # 待审核
    APPROVED = "approved"        # 已审核
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 已拒绝


class SettlementType(str, Enum):
    """结算类型枚举"""
    SUPPLIER_PAYMENT = "supplier_payment"    # 供应商结算
    CLIENT_BILLING = "client_billing"        # 客户账单
    INTERNAL_TRANSFER = "internal_transfer"  # 内部转账
    REFUND = "refund"                        # 退款


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


# ========== 请求模型 ==========

class SettlementCreateRequest(BaseModel):
    """创建结算请求"""
    # NOTE: populate_by_name=True 允许通过字段名或 alias 填充
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    settlement_type: SettlementType = Field(..., description="结算类型")
    supplier_id: Optional[int] = Field(None, description="供应商ID（供应商结算时必填）")
    client_id: Optional[int] = Field(None, description="客户ID（客户账单时必填）")
    period_start: date = Field(..., description="结算周期开始日期")
    period_end: date = Field(..., description="结算周期结束日期")
    currency: str = Field("USD", max_length=3, description="结算货币")
    amount: Decimal = Field(..., ge=0, description="结算金额")
    exchange_rate: Decimal = Field(Decimal("1.0"), ge=0, description="汇率")
    due_date: Optional[date] = Field(None, description="到期日期")
    description: Optional[str] = Field(None, max_length=1000, description="结算说明")
    reference_ids: Optional[List[int]] = Field(None, description="关联的日报ID列表")
    # ORM 属性名为 extra_metadata，API 字段名仍为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
        description="元数据"
    )

    @field_validator('period_end')
    @classmethod
    def validate_period_end(cls, v, info):
        """验证结算周期结束日期"""
        if 'period_start' in info.data and v < info.data['period_start']:
            raise ValueError("结算周期结束日期不能早于开始日期")
        return v


class SettlementUpdateRequest(BaseModel):
    """更新结算请求"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    status: Optional[SettlementStatus] = Field(None, description="结算状态")
    amount: Optional[Decimal] = Field(None, ge=0, description="结算金额")
    exchange_rate: Optional[Decimal] = Field(None, ge=0, description="汇率")
    due_date: Optional[date] = Field(None, description="到期日期")
    description: Optional[str] = Field(None, max_length=1000, description="结算说明")
    payment_status: Optional[PaymentStatus] = Field(None, description="支付状态")
    paid_amount: Optional[Decimal] = Field(None, ge=0, description="已支付金额")
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    reference_ids: Optional[List[int]] = Field(None, description="关联的日报ID列表")
    # ORM 属性名为 extra_metadata，API 字段名仍为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
        description="元数据"
    )


class SettlementApproveRequest(BaseModel):
    """审批结算请求"""
    model_config = ConfigDict(from_attributes=True)

    action: str = Field(..., pattern="^(approve|reject)$", description="审批动作")
    comment: Optional[str] = Field(None, max_length=500, description="审批备注")


class SettlementPaymentRequest(BaseModel):
    """记录结算支付请求"""
    model_config = ConfigDict(from_attributes=True)

    paid_amount: Decimal = Field(..., gt=0, description="支付金额")
    payment_method: str = Field(..., max_length=50, description="支付方式")
    payment_reference: Optional[str] = Field(None, max_length=200, description="支付凭证号")
    paid_at: datetime = Field(default_factory=datetime.utcnow, description="支付时间")
    notes: Optional[str] = Field(None, max_length=500, description="支付备注")


# ========== 响应模型 ==========

class SettlementResponse(BaseModel):
    """结算响应"""
    # NOTE: populate_by_name=True 允许从 ORM 属性 extra_metadata 读取
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    settlement_no: str = Field(..., description="结算单号")
    settlement_type: SettlementType
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    client_id: Optional[int]
    client_name: Optional[str] = None
    period_start: date
    period_end: date
    currency: str
    amount: Decimal
    exchange_rate: Decimal
    amount_in_base_currency: Decimal = Field(Decimal("0"), description="基础货币金额")
    due_date: Optional[date]
    status: SettlementStatus
    payment_status: PaymentStatus
    paid_amount: Decimal = Field(Decimal("0"))
    paid_at: Optional[datetime]
    description: Optional[str]
    reference_ids: Optional[List[int]]
    # ORM 属性名为 extra_metadata，API 序列化输出为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="extra_metadata",
        serialization_alias="metadata",
        description="元数据"
    )

    # 审计字段
    created_by: int
    created_by_name: Optional[str] = None
    approved_by: Optional[int]
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SettlementListResponse(BaseModel):
    """结算列表响应"""
    items: List[SettlementResponse]
    meta: Dict[str, Any]


class SettlementSummary(BaseModel):
    """结算摘要"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    settlement_no: str
    settlement_type: SettlementType
    amount: Decimal
    currency: str
    status: SettlementStatus
    payment_status: PaymentStatus
    due_date: Optional[date]
    created_at: datetime


class SettlementStatisticsResponse(BaseModel):
    """结算统计响应"""
    model_config = ConfigDict(from_attributes=True)

    total_settlements: int = Field(0, description="结算总数")
    pending_settlements: int = Field(0, description="待处理结算数")
    completed_settlements: int = Field(0, description="已完成结算数")
    total_amount: Decimal = Field(Decimal("0"), description="总结算金额")
    total_paid: Decimal = Field(Decimal("0"), description="总已支付金额")
    total_unpaid: Decimal = Field(Decimal("0"), description="总未支付金额")
    overdue_count: int = Field(0, description="逾期结算数")
    overdue_amount: Decimal = Field(Decimal("0"), description="逾期金额")
    by_type: List[Dict[str, Any]] = Field(default_factory=list, description="按类型统计")
    by_status: List[Dict[str, Any]] = Field(default_factory=list, description="按状态统计")
