"""
Commission Rule Model

投手提成配置规则
TASK-PRJ-003: 提成配置

业务规则:
- 提成基于 conversions_final（已确认有效线索）
- 阶梯提成按月累计，每月从 0 开始
- 跨项目分别计算，不合并
- 仅 status=final_confirmed 的日报计入

示例: 1-50: $1, 51-100: $1.5, 101+: $2
投手本月确认 120 个: 50×1 + 50×1.5 + 20×2 = $165

SoT Reference: BUSINESS_RULES.md v5.0
"""
from datetime import date, datetime
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    String,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class CommissionRule(Base):
    """
    投手提成配置表

    支持阶梯提成:
    - tiers: 阶梯配置数组
    - 每个 tier: {min: 最小进粉数, max: 最大进粉数, rate: 单粉提成}
    - max=null 表示无上限

    示例 config:
    {
        "tiers": [
            {"min": 1, "max": 50, "rate": 1.0},
            {"min": 51, "max": 100, "rate": 1.5},
            {"min": 101, "max": null, "rate": 2.0}
        ],
        "currency": "CNY",
        "description": "标准阶梯提成"
    }
    """

    __tablename__ = "commission_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="规则名称")
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, comment="阶梯提成配置JSON"
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为默认规则")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, comment="生效开始日")
    effective_to: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="生效结束日"
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default="NOW()"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default="NOW()", onupdate=datetime.utcnow
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    projects = relationship("Project", back_populates="commission_rule")

    __table_args__ = (
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="chk_commission_rules_effective_period",
        ),
    )

    def is_effective(self, check_date: Optional[date] = None) -> bool:
        """检查规则在指定日期是否生效"""
        check_date = check_date or date.today()
        if check_date < self.effective_from:
            return False
        if self.effective_to and check_date > self.effective_to:
            return False
        return True

    def calculate_commission(self, conversions: int) -> float:
        """
        根据阶梯规则计算提成

        Args:
            conversions: 已确认进粉数 (conversions_final)

        Returns:
            提成金额
        """
        tiers = self.config.get("tiers", [])
        if not tiers:
            return 0.0

        total_commission = 0.0
        remaining = conversions

        for tier in sorted(tiers, key=lambda t: t.get("min", 0)):
            tier_min = tier.get("min", 0)
            tier_max = tier.get("max")  # None 表示无上限
            tier_rate = float(tier.get("rate", 0))

            if remaining <= 0:
                break

            # 计算当前档位的进粉数
            if tier_max is None:
                # 无上限档位
                tier_count = remaining
            else:
                tier_count = min(remaining, tier_max - tier_min + 1)

            # 确保不超过档位上限
            if tier_count > 0:
                total_commission += tier_count * tier_rate
                remaining -= tier_count

        return total_commission

    def __repr__(self) -> str:
        return f"<CommissionRule(id={self.id}, name='{self.name}')>"
