"""
供应商（户商）管理数据模型
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- DATA_SCHEMA.md v5.2 (supplier entity)
- BUSINESS_RULES.md v3.1 (supplier constraints)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class SupplierStatus(str, Enum):
    """供应商状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class PaymentMethod(str, Enum):
    """支付方式枚举"""
    BANK_TRANSFER = "bank_transfer"
    WIRE = "wire"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    OTHER = "other"


# ========== 请求模型 ==========

class SupplierCreateRequest(BaseModel):
    """创建供应商请求"""
    # NOTE: populate_by_name=True 允许通过字段名或 alias 填充
    # validation_alias="metadata" 用于接收 API 请求中的 metadata 字段
    # serialization_alias="metadata" 用于序列化输出时使用 metadata 字段名
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=200, description="供应商名称")
    contact_name: Optional[str] = Field(None, max_length=100, description="联系人姓名")
    contact_email: Optional[str] = Field(None, max_length=255, description="联系人邮箱")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系人电话")
    base_currency: str = Field("USD", max_length=3, description="基础货币")
    payment_method: PaymentMethod = Field(PaymentMethod.BANK_TRANSFER, description="支付方式")
    payment_terms: Optional[str] = Field(None, max_length=500, description="支付条款")
    bank_info: Optional[Dict[str, Any]] = Field(None, description="银行账户信息")
    tax_id: Optional[str] = Field(None, max_length=50, description="税务ID")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    country: Optional[str] = Field(None, max_length=2, description="国家代码 (ISO 3166-1 alpha-2)")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    # ORM 属性名为 extra_metadata，API 字段名仍为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
        description="元数据"
    )


class SupplierUpdateRequest(BaseModel):
    """更新供应商请求"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="供应商名称")
    contact_name: Optional[str] = Field(None, max_length=100, description="联系人姓名")
    contact_email: Optional[str] = Field(None, max_length=255, description="联系人邮箱")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系人电话")
    base_currency: Optional[str] = Field(None, max_length=3, description="基础货币")
    payment_method: Optional[PaymentMethod] = Field(None, description="支付方式")
    payment_terms: Optional[str] = Field(None, max_length=500, description="支付条款")
    bank_info: Optional[Dict[str, Any]] = Field(None, description="银行账户信息")
    tax_id: Optional[str] = Field(None, max_length=50, description="税务ID")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    country: Optional[str] = Field(None, max_length=2, description="国家代码")
    status: Optional[SupplierStatus] = Field(None, description="供应商状态")
    notes: Optional[str] = Field(None, max_length=2000, description="备注")
    # ORM 属性名为 extra_metadata，API 字段名仍为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="metadata",
        serialization_alias="metadata",
        description="元数据"
    )


# ========== 响应模型 ==========

class SupplierResponse(BaseModel):
    """供应商响应"""
    # NOTE: populate_by_name=True 允许从 ORM 属性 extra_metadata 读取
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    base_currency: str
    payment_method: PaymentMethod
    payment_terms: Optional[str]
    bank_info: Optional[Dict[str, Any]]
    tax_id: Optional[str]
    address: Optional[str]
    country: Optional[str]
    status: SupplierStatus
    notes: Optional[str]
    # ORM 属性名为 extra_metadata，API 序列化输出为 metadata
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias="extra_metadata",
        serialization_alias="metadata",
        description="元数据"
    )

    # 统计字段（由 service 层填充）
    total_accounts: int = Field(0, description="关联广告账户数")
    total_spend: Decimal = Field(Decimal("0"), description="总消耗金额")

    # 审计字段
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    """供应商列表响应"""
    items: List[SupplierResponse]
    meta: Dict[str, Any]


class SupplierSummary(BaseModel):
    """供应商摘要"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: SupplierStatus
    base_currency: str
    total_accounts: int = 0
    created_at: datetime


class SupplierStatisticsResponse(BaseModel):
    """供应商统计响应"""
    model_config = ConfigDict(from_attributes=True)

    total_suppliers: int = Field(0, description="供应商总数")
    active_suppliers: int = Field(0, description="活跃供应商数")
    inactive_suppliers: int = Field(0, description="非活跃供应商数")
    total_accounts_managed: int = Field(0, description="管理的账户总数")
    total_spend: Decimal = Field(Decimal("0"), description="总消耗")
    currency_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="货币分布")
    payment_method_distribution: List[Dict[str, Any]] = Field(default_factory=list, description="支付方式分布")
