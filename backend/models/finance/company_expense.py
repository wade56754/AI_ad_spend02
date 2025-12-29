"""
公司运营支出模型
Version: 1.0
Author: Claude Code

记录非广告业务的公司级运营支出，不进入 ledger_entries 双账本体系。

SoT References:
- LEDGER_SOT.md v1.1 (不进入账本)
- BUSINESS_RULES.md v3.2 (金额规范)

expense_type 枚举值:
- salary: 工资
- setup_fee: 开户费
- service_fee: 服务费（IP、VPN、BM等）
- exchange: 换汇
- reimbursement: 报销
- other: 其他

category 枚举值:
- operation: 运营
- hr: 人力资源
- infrastructure: 基础设施
- tools: 工具
- other: 其他
"""

from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Date, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin
from backend.models.mixins.serializable import SerializableMixin


class ExpenseType:
    """支出类型常量"""
    SALARY = "salary"
    SETUP_FEE = "setup_fee"
    SERVICE_FEE = "service_fee"
    EXCHANGE = "exchange"
    REIMBURSEMENT = "reimbursement"
    OTHER = "other"


class ExpenseCategory:
    """支出分类常量"""
    OPERATION = "operation"
    HR = "hr"
    INFRASTRUCTURE = "infrastructure"
    TOOLS = "tools"
    OTHER = "other"


class ExpenseStatus:
    """支出状态常量"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class CompanyExpense(Base, TimestampMixin, SerializableMixin):
    """
    公司运营支出表

    记录非广告业务的公司级运营支出：
    - 工资支出
    - 开户费
    - 服务费（IP、VPN、BM等）
    - 换汇
    - 报销
    - 其他运营支出

    注意：此表记录的支出不进入 ledger_entries 双账本体系
    """
    __tablename__ = 'company_expenses'

    # 序列化配置
    __json_include_relationships__ = ['creator', 'approver']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="支出ID")

    # 基本信息
    expense_type = Column(String(50), nullable=False, comment="支出类型")
    category = Column(String(50), nullable=False, comment="分类")
    amount = Column(Numeric(15, 2), nullable=False, comment="金额")
    currency = Column(String(10), nullable=True, default="USD", comment="币种")
    occurred_at = Column(Date, nullable=False, comment="发生日期")
    description = Column(Text, nullable=True, comment="描述")
    receipt_url = Column(Text, nullable=True, comment="收据URL")

    # 审批信息
    status = Column(String(20), nullable=True, default=ExpenseStatus.PENDING, comment="状态")
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="创建人")
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="审批人")

    # ========== 关系定义 ==========

    creator = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
        doc="创建者"
    )

    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        lazy="selectin",
        doc="审批人"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "category IN ('operation', 'hr', 'infrastructure', 'tools', 'other')",
            name='chk_company_expenses_category'
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'paid')",
            name='chk_company_expenses_status'
        ),
        Index('idx_company_expenses_category', 'category'),
        Index('idx_company_expenses_occurred_at', 'occurred_at'),
        Index('idx_company_expenses_status', 'status'),
        Index('idx_company_expenses_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<CompanyExpense(id={self.id}, type='{self.expense_type}', amount={self.amount})>"

    # ========== 业务属性 ==========

    @property
    def is_pending(self) -> bool:
        """是否待审批"""
        return self.status == ExpenseStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """是否已审批"""
        return self.status == ExpenseStatus.APPROVED

    @property
    def is_paid(self) -> bool:
        """是否已支付"""
        return self.status == ExpenseStatus.PAID

    # ========== 业务方法 ==========

    def approve(self, approver_id):
        """审批通过"""
        self.status = ExpenseStatus.APPROVED
        self.approved_by = approver_id

    def reject(self, approver_id, reason: str = None):
        """审批拒绝"""
        self.status = ExpenseStatus.REJECTED
        self.approved_by = approver_id
        if reason:
            self.description = f"{self.description or ''}\n[拒绝原因] {reason}"

    def mark_paid(self):
        """标记为已支付"""
        if self.status == ExpenseStatus.APPROVED:
            self.status = ExpenseStatus.PAID
        else:
            raise ValueError("只有已审批的支出才能标记为已支付")
