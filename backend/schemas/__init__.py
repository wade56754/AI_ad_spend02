from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ORMBase(BaseModel):
    class Config:
        orm_mode = True


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
    status: str = "active"
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


# Channels
class ChannelBase(BaseModel):
    name: str
    service_fee_type: str = "percent"
    service_fee_value: Decimal = Decimal("0")
    is_active: bool = True
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    service_fee_type: Optional[str] = None
    service_fee_value: Optional[Decimal] = None
    is_active: Optional[bool] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class ChannelRead(ChannelBase, TimestampMixin, ORMBase):
    id: UUID


# Ad Accounts
class AdAccountBase(BaseModel):
    name: str
    project_id: UUID
    channel_id: UUID
    assigned_user_id: Optional[UUID] = None
    status: str = "new"
    dead_reason: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class AdAccountCreate(AdAccountBase):
    pass


class AdAccountUpdate(BaseModel):
    name: Optional[str] = None
    project_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    status: Optional[str] = None
    dead_reason: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class AdAccountStatusUpdate(BaseModel):
    status: str
    updated_by: Optional[UUID] = None
    dead_reason: Optional[str] = None


class AdAccountRead(AdAccountBase, TimestampMixin, ORMBase):
    id: UUID


# Ad Spend Daily
class AdSpendDailyBase(BaseModel):
    ad_account_id: UUID
    user_id: UUID
    date: date
    spend: Decimal = Decimal("0")
    leads_count: int = 0
    cost_per_lead: Decimal = Decimal("0")
    anomaly_flag: bool = False
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
    anomaly_flag: Optional[bool] = None
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
    status: str = "pending"
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
    status: str = "pending"
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


