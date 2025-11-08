import uuid

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.sql import func

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class Topup(Base):
    __tablename__ = "topups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    project_id = Column(GUID(), nullable=False)
    ad_account_id = Column(GUID(), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    status = Column(String(length=32), nullable=False, default="pending")
    created_by = Column(GUID(), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

