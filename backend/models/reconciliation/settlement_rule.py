"""
Settlement Rule Model

OpenSpec Change: add-reconciliation-control-center
SoT Reference: DATA_SCHEMA.md v5.4 §3.5.7
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import (
    BigInteger, String, Date, DateTime, Text,
    ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class RuleType(str, Enum):
    """结算规则类型"""
    TIERED = "tiered"    # 阶梯计价
    MARKUP = "markup"    # 加成计价


class SettlementRule(Base):
    """
    结算规则配置表

    支持两种结算类型:
    - tiered: 阶梯计价，按粉数阶梯设定不同单价
    - markup: 加成计价，按消耗基数加成

    SoT Reference: DATA_SCHEMA.md v5.4 §3.5.7
    Business Rules: BR-SET-001, BR-SET-002, BR-SET-003
    """
    __tablename__ = "settlement_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="规则名称")
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="规则类型: tiered/markup")
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, comment="规则配置JSON")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, comment="生效开始日")
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="生效结束日")
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default="NOW()")
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default="NOW()", onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    projects = relationship("Project", back_populates="settlement_rule")

    __table_args__ = (
        CheckConstraint("rule_type IN ('tiered', 'markup')", name="chk_settlement_rules_rule_type"),
        CheckConstraint("effective_to IS NULL OR effective_to > effective_from", name="chk_settlement_rules_effective_period"),
    )

    def is_effective(self, check_date: Optional[date] = None) -> bool:
        """检查规则在指定日期是否生效"""
        check_date = check_date or date.today()
        if check_date < self.effective_from:
            return False
        if self.effective_to and check_date > self.effective_to:
            return False
        return True

    def __repr__(self) -> str:
        return f"<SettlementRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"
