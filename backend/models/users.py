import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.core.db import Base
from backend.models.ad_spend_daily import GUID


class Role(Base):
    __tablename__ = "roles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(length=32), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="users_email_key"),)

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)
    email = Column(String(length=255), nullable=False)
    name = Column(String(length=255), nullable=True)
    role = Column(String(length=64), nullable=False, default="trader")
    role_id = Column(GUID(), ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role_rel = relationship(Role, lazy="joined")

