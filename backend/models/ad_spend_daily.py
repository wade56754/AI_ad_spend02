import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.types import CHAR, TypeDecorator

from backend.core.db import Base


class GUID(TypeDecorator):
    """Platform-independent UUID type."""

    impl = PGUUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value if dialect.name == "postgresql" else str(value)
        value = uuid.UUID(str(value))
        return value if dialect.name == "postgresql" else str(value)

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class AdSpendDaily(Base):
    __tablename__ = "ad_spend_daily"
    __table_args__ = (
        UniqueConstraint("ad_account_id", "date", name="ad_spend_daily_unique_account_date"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    ad_account_id = Column(GUID(), ForeignKey("ad_accounts.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    spend = Column(Numeric(18, 2), nullable=False, server_default="0")
    leads_count = Column(Integer, nullable=False, server_default="0")
    cost_per_lead = Column(Numeric(18, 2), nullable=False, server_default="0")
    is_anomaly = Column(Boolean, nullable=False, server_default="false")
    anomaly_reason = Column(Text)
    note = Column(Text)
    created_by = Column(GUID(), ForeignKey("users.id"))
    updated_by = Column(GUID(), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

