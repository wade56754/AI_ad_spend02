"""
回款记录模块（对齐 DATA_SCHEMA.md v5.8 §3.4.5 + MASTER.md v4.8 §4.5.5）

包含：
- ReceivableStatus: 回款状态枚举
- Receivable: 回款记录表

设计来源：
- DATA_SCHEMA.md v5.8 §3.4.5
- MASTER.md v4.8 §4.5.5 - 已回款 SoT 定义

重要说明：
- `receivable.amount WHERE status='received'` 为「已回款」的唯一事实源
- 已回款公式：SELECT SUM(amount) FROM receivable WHERE status = 'received' AND project_id = ?

FK 类型对齐说明（DATA_SCHEMA.md v5.8）：
- project_id: BigInteger FK → projects.id (BIGSERIAL)
- recorded_by, confirmed_by: UUID FK → users.id (UUID)
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Numeric,
    DateTime,
    Index,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin


# =====================================================================
# Enum 枚举定义 (对齐 DATA_SCHEMA.md v5.8 §3.4.5)
# =====================================================================


class ReceivableStatus(str, PyEnum):
    """
    回款状态枚举

    必须与 DATA_SCHEMA.md v5.8 §3.4.5 保持一致。

    状态说明：
    - pending: 待确认 - 记录已创建，等待财务确认到账
    - received: 已到账 - 款项已到账（终态，received_at 必填）
    - cancelled: 已取消 - 回款记录作废（终态）
    """

    PENDING = "pending"  # 待确认
    RECEIVED = "received"  # 已到账（终态）
    CANCELLED = "cancelled"  # 已取消（终态）


# =====================================================================
# Model 定义 (对齐 DATA_SCHEMA.md v5.8 §3.4.5)
# =====================================================================


class Receivable(Base, TimestampMixin):
    """
    回款记录表

    记录项目的客户回款信息。是"已回款"数据的唯一事实源。

    业务规则引用（MASTER.md v4.8 §4.5.5）：
    - 已回款 SoT: SELECT SUM(amount) FROM receivable WHERE status = 'received' AND project_id = ?
    - status='received' 时 received_at 不能为空

    FK 类型对齐：
    - id: BIGSERIAL (BigInteger autoincrement)
    - project_id: BIGINT FK → projects.id (ON DELETE RESTRICT)
    - recorded_by, confirmed_by: UUID FK → users.id
    """

    __tablename__ = "receivable"

    # 主键：BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="回款记录唯一标识")

    # 项目外键 - FK 类型必须与 parent PK 一致
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="所属项目",
    )

    # 核心金额字段 - 使用 DECIMAL(15,2)
    amount = Column(Numeric(15, 2), nullable=False, comment="回款金额（必须为正数）")

    # 状态字段
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="回款状态：pending（待确认）/ received（已到账）/ cancelled（已取消）",
    )

    # 到账时间
    received_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="实际到账时间（status='received'时必填）",
    )

    # 回款来源信息
    source = Column(String(50), nullable=True, comment="回款来源（客户名/渠道等）")

    invoice_no = Column(String(100), nullable=True, comment="发票编号")

    notes = Column(Text, nullable=True, comment="备注说明")

    # 操作人员 - UUID FK → users.id
    recorded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="记录人",
    )

    confirmed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="确认人（status='received'时填充）",
    )

    # 约束和索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'received', 'cancelled')",
            name="chk_receivable_status",
        ),
        CheckConstraint("amount > 0", name="chk_receivable_amount_positive"),
        Index("idx_receivable_project", "project_id"),
        Index("idx_receivable_status", "status"),
        Index("idx_receivable_received_at", "received_at"),
        Index("idx_receivable_created_at", "created_at"),
        {"comment": "回款记录表（已回款 SoT）- DATA_SCHEMA.md v5.8 §3.4.5"},
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    recorder = relationship("User", foreign_keys=[recorded_by])
    confirmer = relationship("User", foreign_keys=[confirmed_by])

    def __repr__(self):
        return (
            f"<Receivable(id={self.id}, project_id={self.project_id}, "
            f"amount={self.amount}, status={self.status})>"
        )
