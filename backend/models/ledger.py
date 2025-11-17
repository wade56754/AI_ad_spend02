"""
财务流水和账本模块（对齐 DATA_SCHEMA.md 3.4.4）
包含账本条目等相关模型
"""

from sqlalchemy import Column, BigInteger, String, Text, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.db import Base


class LedgerEntry(Base):
    """资金总账表（对齐 DATA_SCHEMA.md 3.4.4）"""
    __tablename__ = "ledger_entries"

    # 主键：BIGSERIAL（对齐 DATA_SCHEMA）
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账本条目ID")
    
    # 关联信息（外键类型对齐 DATA_SCHEMA）
    project_id = Column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="项目ID"
    )
    ad_account_id = Column(
        BigInteger,
        ForeignKey("ad_accounts.id"),
        nullable=True,
        index=True,
        comment="广告账户ID"
    )
    
    # 条目信息（对齐 DATA_SCHEMA）
    entry_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="条目类型：topup_received/spend/adjustment/..."
    )
    amount = Column(Numeric(15, 2), nullable=False, comment="金额（借方为正，贷方为负）")
    currency = Column(String(10), nullable=False, comment="货币类型")
    reference_id = Column(BigInteger, nullable=True, comment="关联ID（topup_transactions 或 daily_reports）")
    
    # 时间信息（对齐 DATA_SCHEMA：TIMESTAMPTZ）
    occurred_at = Column(
        func.now(),
        server_default=func.now(),
        nullable=False,
        comment="发生时间"
    )
    
    # 审计字段（外键指向 user_profiles.id，UUID）
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=True,
        comment="创建人ID"
    )
    notes = Column(Text, nullable=True, comment="备注说明")

    # 索引（对齐 DATA_SCHEMA 3.4.4）
    __table_args__ = (
        Index('idx_ledger_project', 'project_id'),
        Index('idx_ledger_account', 'ad_account_id'),
        Index('idx_ledger_entry_type', 'entry_type'),
        {'comment': '资金总账表'}
    )

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    ad_account = relationship("AdAccount", foreign_keys=[ad_account_id])
    creator = relationship("UserProfile", foreign_keys=[created_by])