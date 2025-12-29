"""
Ad Account Balance Snapshot Model

OpenSpec Change: add-reconciliation-control-center
SoT Reference: DATA_SCHEMA.md v5.4 §3.5.5

Note: Renamed to AdAccountBalanceSnapshot to avoid conflict with
existing finance.balance_snapshot.BalanceSnapshot model.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    BigInteger, String, Date, DateTime, Text, Numeric,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class SnapshotSource(str, Enum):
    """快照数据来源"""
    MANUAL = "manual"   # 手工录入
    API = "api"         # API 拉取
    IMPORT = "import"   # 批量导入


class AdAccountBalanceSnapshot(Base):
    """
    广告账户余额/押款快照表

    用于对账守恒公式校验，记录广告账户每日的余额和押款状态。

    SoT Reference: DATA_SCHEMA.md v5.4 §3.5.5
    Business Rules: BR-REC-001 对账守恒公式, BR-REC-003 快照缺失处理
    """
    __tablename__ = "ad_account_balance_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ad_account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ad_accounts.id"), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, comment="快照日期")
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, comment="当日余额")
    deposit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"), comment="当日押款")
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, comment="当日剩余可用 = balance - deposit")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual", comment="数据来源")
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default="NOW()")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    # Relationships
    ad_account = relationship("AdAccount", back_populates="balance_snapshots")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint("ad_account_id", "snapshot_date", name="uq_ad_account_balance_snapshots_account_date"),
        CheckConstraint("source IN ('manual', 'api', 'import')", name="chk_ad_account_balance_snapshots_source"),
    )

    def __repr__(self) -> str:
        return f"<AdAccountBalanceSnapshot(id={self.id}, account={self.ad_account_id}, date={self.snapshot_date}, balance={self.balance})>"
