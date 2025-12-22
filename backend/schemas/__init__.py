"""
Pydantic Schemas
Version: 2.0 (SoT Aligned - STATE_MACHINE.md v2.6)
Author: Claude协作开发

注意：status 字段使用字符串类型，默认值应与 models.base 枚举保持一致。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# 导入规范枚举用于默认值
from backend.models.base import TopupStatus, ProjectStatus, AdAccountStatus


class ORMBase(BaseModel):
    # Pydantic v2: 启用属性读取以替代 v1 的 orm_mode
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# Users
class UserBase(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class UserRead(UserBase, TimestampMixin, ORMBase):
    id: UUID


# Projects
class ProjectBase(BaseModel):
    name: str
    client_name: Optional[str] = None
    currency: str = "USD"
    status: str = ProjectStatus.ACTIVE.value  # 使用枚举默认值
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ProjectRead(ProjectBase, TimestampMixin, ORMBase):
    id: UUID


# Channels - 匹配 init_schema.sql 中的 channels 表
class ChannelBase(BaseModel):
    name: str
    platform: Optional[str] = None
    status: Optional[str] = "active"  # active/inactive
    risk_level: Optional[str] = None  # low/medium/high
    created_by: Optional[UUID] = None
    channel_metadata: Optional[Dict[str, Any]] = None  # JSONB 存储扩展数据


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    channel_metadata: Optional[Dict[str, Any]] = None


class ChannelRead(ChannelBase, TimestampMixin, ORMBase):
    id: UUID


# Ad Accounts - 对齐 init_schema.sql §5.1 ad_accounts 表
class AdAccountBase(BaseModel):
    """
    广告账户基础字段 - 对齐 init_schema.sql 第 315-332 行

    字段说明：
    - project_id: 项目ID (BIGINT)
    - channel_id: 渠道ID (UUID)
    - supplier_id: 供应商ID (UUID)
    - owner_id: 负责人ID (UUID)
    - name: 账户名称 (VARCHAR 200)
    - account_code: 账户代码 (VARCHAR 100, UNIQUE)
    - status: 账户状态
    - status_reason: 状态原因
    - spend_limit: 消耗限额
    - currency: 货币
    - timezone: 时区
    """
    project_id: int  # BigInteger
    channel_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None  # 负责人
    name: Optional[str] = None  # 账户名称
    account_code: Optional[str] = None  # 账户代码
    status: Optional[str] = AdAccountStatus.NEW.value
    status_reason: Optional[str] = None
    spend_limit: Decimal = Decimal("0.00")
    currency: str = "CNY"
    timezone: str = "Asia/Shanghai"


class AdAccountCreate(AdAccountBase):
    pass


class AdAccountUpdate(BaseModel):
    name: Optional[str] = None
    project_id: Optional[int] = None
    channel_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    status: Optional[str] = None
    status_reason: Optional[str] = None
    spend_limit: Optional[Decimal] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class AdAccountStatusUpdate(BaseModel):
    status: str
    status_reason: Optional[str] = None


class AdAccountRead(AdAccountBase, TimestampMixin, ORMBase):
    """广告账户读取响应 - 对齐 init_schema.sql"""
    id: int  # BigInteger
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


# Ad Spend Daily
class AdSpendDailyBase(BaseModel):
    ad_account_id: UUID
    user_id: UUID
    date: date
    spend: Decimal = Decimal("0")
    leads_count: int = 0
    cost_per_lead: Decimal = Decimal("0")
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class AdSpendDailyCreate(AdSpendDailyBase):
    pass


class AdSpendDailyUpdate(BaseModel):
    ad_account_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    date: Optional[date] = None
    spend: Optional[Decimal] = None
    leads_count: Optional[int] = None
    cost_per_lead: Optional[Decimal] = None
    is_anomaly: Optional[bool] = None
    anomaly_reason: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class AdSpendDailyRead(AdSpendDailyBase, TimestampMixin, ORMBase):
    id: UUID


# Ledgers
class LedgerBase(BaseModel):
    type: str
    project_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    ad_account_id: Optional[UUID] = None
    amount: Decimal
    currency: str = "USD"
    occurred_at: datetime
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class LedgerCreate(LedgerBase):
    pass


class LedgerUpdate(BaseModel):
    type: Optional[str] = None
    project_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    ad_account_id: Optional[UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    occurred_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class LedgerRead(LedgerBase, TimestampMixin, ORMBase):
    id: UUID


# Topups
class TopupBase(BaseModel):
    ad_account_id: UUID
    project_id: UUID
    channel_id: UUID
    requested_by: UUID
    amount: Decimal
    service_fee_amount: Optional[Decimal] = None
    status: str = TopupStatus.PENDING_REVIEW.value  # 使用枚举默认值 (pending_review 而非 pending)
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class TopupCreate(TopupBase):
    pass


class TopupUpdate(BaseModel):
    ad_account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    requested_by: Optional[UUID] = None
    amount: Optional[Decimal] = None
    service_fee_amount: Optional[Decimal] = None
    status: Optional[str] = None
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class TopupRead(TopupBase, TimestampMixin, ORMBase):
    id: UUID


class TopupActionBase(BaseModel):
    actor_id: UUID
    remark: Optional[str] = None


class TopupApprove(TopupActionBase):
    pass


class TopupPay(TopupActionBase):
    pass


class TopupConfirm(TopupActionBase):
    pass


class TopupReject(TopupActionBase):
    pass


# Reconciliations
class ReconciliationBase(BaseModel):
    ledger_id: UUID
    ad_spend_id: UUID
    match_score: Decimal = Decimal("1")
    matched_by: str
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ReconciliationCreate(ReconciliationBase):
    pass


class ReconciliationUpdate(BaseModel):
    ledger_id: Optional[UUID] = None
    ad_spend_id: Optional[UUID] = None
    match_score: Optional[Decimal] = None
    matched_by: Optional[str] = None
    remark: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ReconciliationRead(ReconciliationBase, TimestampMixin, ORMBase):
    id: UUID


class ReconciliationAutoRequest(BaseModel):
    ledger_id: UUID
    actor_id: Optional[UUID] = None
    remark: Optional[str] = None


class ReconciliationManualRequest(BaseModel):
    ledger_id: UUID
    ad_spend_id: UUID
    actor_id: Optional[UUID] = None
    match_score: Optional[Decimal] = None
    remark: Optional[str] = None


# Import Jobs
class ImportJobBase(BaseModel):
    type: str
    status: str = "pending"  # ImportJob 有自己的状态机，保持原样
    file_path: Optional[str] = None
    file_hash: str
    error_log: Optional[Any] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobUpdate(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    error_log: Optional[Any] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ImportJobRead(ImportJobBase, TimestampMixin, ORMBase):
    id: UUID


# Logs
class LogBase(BaseModel):
    actor_id: Optional[UUID] = None
    action: str
    target_table: Optional[str] = None
    target_id: Optional[UUID] = None
    before_data: Optional[Any] = None
    after_data: Optional[Any] = None
    ip: Optional[str] = None


class LogCreate(LogBase):
    pass


class LogUpdate(BaseModel):
    actor_id: Optional[UUID] = None
    action: Optional[str] = None
    target_table: Optional[str] = None
    target_id: Optional[UUID] = None
    before_data: Optional[Any] = None
    after_data: Optional[Any] = None
    ip: Optional[str] = None


class LogRead(LogBase, TimestampMixin, ORMBase):
    id: UUID


