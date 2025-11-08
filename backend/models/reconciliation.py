import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.sql import func

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    ad_account_id = Column(GUID(), nullable=False)
    daily_spend_id = Column(GUID(), ForeignKey("ad_spend_daily.id"), nullable=False)
    finance_txn_id = Column(GUID(), nullable=False)
    match_type = Column(String(length=16), nullable=False)
    status = Column(String(length=32), nullable=False)
    amount_diff = Column(Numeric(18, 2), nullable=False)
    date_diff = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ReconciliationLog(Base):
    __tablename__ = "reconciliation_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    reconciliation_id = Column(GUID(), ForeignKey("reconciliations.id"), nullable=True)
    action = Column(String(length=64), nullable=False)
    operator_id = Column(GUID(), nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

