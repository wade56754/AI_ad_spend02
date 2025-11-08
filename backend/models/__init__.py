from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(Text, unique=True)
    name = Column(Text)
    role = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False, unique=True)
    client_name = Column(Text)
    currency = Column(Text, nullable=False, server_default="USD")
    status = Column(Text, nullable=False, server_default="active")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False, unique=True)
    service_fee_type = Column(Text, nullable=False, server_default="percent")
    service_fee_value = Column(Numeric(18, 2), nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AdAccount(Base):
    __tablename__ = "ad_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Text, nullable=False, server_default="new")
    dead_reason = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AdSpendDaily(Base):
    __tablename__ = "ad_spend_daily"
    __table_args__ = (
        UniqueConstraint("ad_account_id", "date", name="ad_spend_daily_unique_account_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    ad_account_id = Column(UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    spend = Column(Numeric(18, 2), nullable=False, server_default="0")
    leads_count = Column(Integer, nullable=False, server_default="0")
    cost_per_lead = Column(Numeric(18, 2), nullable=False, server_default="0")
    anomaly_flag = Column(Boolean, nullable=False, server_default="false")
    anomaly_reason = Column(Text)
    note = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    type = Column(Text, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"))
    ad_account_id = Column(UUID(as_uuid=True), ForeignKey("ad_accounts.id"))
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(Text, nullable=False, server_default="USD")
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    remark = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Topup(Base):
    __tablename__ = "topups"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    ad_account_id = Column(UUID(as_uuid=True), ForeignKey("ad_accounts.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    service_fee_amount = Column(Numeric(18, 2))
    status = Column(Text, nullable=False, server_default="pending")
    remark = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledgers.id"), nullable=False)
    ad_spend_id = Column(UUID(as_uuid=True), ForeignKey("ad_spend_daily.id"), nullable=False)
    match_score = Column(Numeric(5, 2), nullable=False, server_default="1")
    matched_by = Column(Text, nullable=False)
    remark = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        UniqueConstraint("file_hash", name="import_jobs_file_hash_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default="pending")
    file_path = Column(Text)
    file_hash = Column(Text, nullable=False)
    error_log = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Log(Base):
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(Text, nullable=False)
    target_table = Column(Text)
    target_id = Column(UUID(as_uuid=True))
    before_data = Column(JSONB)
    after_data = Column(JSONB)
    ip = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


