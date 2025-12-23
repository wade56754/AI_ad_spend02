"""
供应商模型 - 户商管理实体
Version: 1.0
Author: Claude Code (full_pipeline)

Aligned with SoT:
- DATA_SCHEMA.md v5.2 (supplier entity)
- BUSINESS_RULES.md v3.1 (supplier constraints)
- LEDGER_SOT.md v1.1 (cost-side ledger entries)

RLS 策略：admin/finance 可访问所有供应商记录
"""

from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Index, CheckConstraint, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin, UserScopeMixin
from backend.models.mixins.serializable import SerializableMixin


class SupplierStatus:
    """供应商状态常量"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class PaymentMethod:
    """支付方式常量"""
    BANK_TRANSFER = "bank_transfer"
    WIRE = "wire"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    OTHER = "other"


class Supplier(Base, TimestampMixin, UserScopeMixin, SerializableMixin):
    """
    供应商表 - 户商管理

    字段：
    - id: 主键
    - name: 供应商名称（唯一）
    - contact_name/email/phone: 联系人信息
    - base_currency: 基础货币
    - payment_method: 支付方式
    - payment_terms: 支付条款
    - bank_info: 银行账户信息（JSON）
    - tax_id: 税务ID
    - address: 地址
    - country: 国家代码
    - status: 供应商状态
    - notes: 备注
    - extra_metadata: 元数据（JSON），DB 列名为 "metadata"
    - created_by: 创建者（来自 UserScopeMixin）
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'suppliers'

    # 序列化配置
    __json_include_relationships__ = ['creator']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="供应商ID")

    # 基本信息
    name = Column(String(200), unique=True, nullable=False, comment="供应商名称")
    contact_name = Column(String(100), nullable=True, comment="联系人姓名")
    contact_email = Column(String(255), nullable=True, comment="联系人邮箱")
    contact_phone = Column(String(50), nullable=True, comment="联系人电话")

    # 财务信息
    base_currency = Column(String(3), nullable=False, default="USD", comment="基础货币")
    payment_method = Column(String(50), nullable=False, default=PaymentMethod.BANK_TRANSFER, comment="支付方式")
    payment_terms = Column(String(500), nullable=True, comment="支付条款")
    bank_info = Column(JSONB, nullable=True, comment="银行账户信息")
    tax_id = Column(String(50), nullable=True, comment="税务ID")

    # 地址信息
    address = Column(String(500), nullable=True, comment="地址")
    country = Column(String(2), nullable=True, comment="国家代码 (ISO 3166-1 alpha-2)")

    # 状态
    status = Column(String(20), nullable=False, default=SupplierStatus.ACTIVE, comment="供应商状态")

    # 其他
    notes = Column(Text, nullable=True, comment="备注")
    # NOTE: 属性名从 metadata 改为 extra_metadata，避免与 SQLAlchemy Declarative Base.metadata 冲突
    # 数据库列名仍为 "metadata"，与 SoT DATA_SCHEMA.md v5.2 保持一致
    extra_metadata = Column("metadata", JSONB, nullable=True, comment="元数据")

    # 统计字段（可由触发器或定时任务更新）
    total_accounts = Column(BigInteger, nullable=False, default=0, comment="关联广告账户数")
    total_spend = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="总消耗金额")

    # Phase 1 Financial SoT 新增字段
    fee_rate = Column(Numeric(5, 4), nullable=True, default=Decimal('0.1000'), comment="手续费率 (0.01-0.15)")
    fee_type = Column(String(20), nullable=True, default='PERCENTAGE', comment="费率类型 (PERCENTAGE/FIXED)")
    platform = Column(String(20), nullable=True, comment="平台 (FB/TK/Google)")

    # ========== 关系定义 ==========

    # 多对一：供应商 -> 创建者
    creator = relationship(
        "User",
        foreign_keys="Supplier.created_by",
        lazy="selectin",
        doc="创建者"
    )

    # 一对多：供应商 -> 广告账户（暂用 TODO 注释，等 AdAccount 添加 supplier_id 外键后启用）
    # TODO: 建立 Supplier ↔ AdAccount（1:N）关系
    # ad_accounts = relationship(
    #     "AdAccount",
    #     back_populates="supplier",
    #     lazy="dynamic",
    #     doc="关联的广告账户"
    # )

    # 一对多：供应商 -> 结算（暂用 TODO 注释，等 Settlement 模型创建后启用）
    # TODO: 建立 Supplier ↔ Settlement（1:N）关系
    # settlements = relationship(
    #     "Settlement",
    #     back_populates="supplier",
    #     lazy="dynamic",
    #     doc="关联的结算记录"
    # )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'pending_review')",
            name='chk_suppliers_status'
        ),
        CheckConstraint(
            "payment_method IN ('bank_transfer', 'wire', 'paypal', 'crypto', 'other')",
            name='chk_suppliers_payment_method'
        ),
        # Phase 1 Financial SoT 新增约束
        CheckConstraint(
            "fee_type IN ('PERCENTAGE', 'FIXED') OR fee_type IS NULL",
            name='chk_suppliers_fee_type'
        ),
        CheckConstraint(
            "(fee_rate >= 0 AND fee_rate <= 1) OR fee_rate IS NULL",
            name='chk_suppliers_fee_rate_range'
        ),
        Index('idx_suppliers_name', 'name'),
        Index('idx_suppliers_status', 'status'),
        Index('idx_suppliers_country', 'country'),
        Index('idx_suppliers_created_by', 'created_by'),
        # Phase 1 Financial SoT 新增索引
        Index('idx_suppliers_platform', 'platform'),
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def is_active(self) -> bool:
        """是否是活跃供应商"""
        return self.status == SupplierStatus.ACTIVE

    # ========== 业务方法 ==========

    def can_delete(self) -> bool:
        """检查是否可以删除（没有关联账户才能删除）"""
        return self.total_accounts == 0

    def suspend(self, reason: str = None):
        """暂停供应商"""
        self.status = SupplierStatus.SUSPENDED
        if reason and self.notes:
            self.notes = f"{self.notes}\n[暂停原因] {reason}"
        elif reason:
            self.notes = f"[暂停原因] {reason}"

    def activate(self):
        """激活供应商"""
        self.status = SupplierStatus.ACTIVE
