"""
广告账户模型 - 核心业务实体

对齐 DATA_SCHEMA.md v5.4 和 init_schema.sql §5.1
字段来源: init_schema.sql 第 315-332 行

OpenSpec Change: add-reconciliation-control-center
- 新增 deposit, deposit_updated_at 字段
- 新增 balance_snapshots, reconciliation_issues 关系
"""
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import AdAccountStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class AdAccount(Base, TimestampMixin, RLSAwareMixin, SerializableMixin):
    """
    广告账户表 - 核心业务实体

    对齐 init_schema.sql §5.1 ad_accounts 表定义

    字段（与数据库完全对齐）：
    - id: BIGSERIAL 主键
    - project_id: BIGINT 项目外键
    - channel_id: UUID 渠道外键
    - supplier_id: UUID 供应商外键
    - owner_id: UUID 负责人外键
    - name: VARCHAR(200) 账户名称
    - account_code: VARCHAR(100) 账户代码（唯一）
    - status: VARCHAR(20) 账户状态
    - status_reason: TEXT 状态原因
    - spend_limit: DECIMAL(15,2) 消耗限额
    - currency: VARCHAR(10) 货币
    - timezone: VARCHAR(50) 时区
    - created_by/updated_by: UUID 创建/更新者
    - created_at/updated_at: TIMESTAMPTZ 时间戳
    """
    __tablename__ = 'ad_accounts'

    # RLS 配置
    __rls_user_field__ = 'owner_id'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]
    __rls_readonly_roles__ = [UserRole.FINANCE]

    # 序列化配置
    __json_include_relationships__ = ['project', 'channel', 'owner']

    # 主键 - BIGSERIAL
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账户ID")

    # 外键 - 对齐 init_schema.sql
    project_id = Column(
        BigInteger,
        ForeignKey('projects.id', ondelete='RESTRICT'),
        nullable=False,
        comment="项目ID"
    )
    channel_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('channels.id', ondelete='SET NULL'),
        nullable=True,
        comment="渠道ID"
    )
    supplier_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('suppliers.id', ondelete='SET NULL'),
        nullable=True,
        comment="供应商ID"
    )
    owner_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="负责人ID"
    )
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('teams.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="所属团队ID"
    )
    buyer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('buyers.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="所属投手ID"
    )

    # 基本信息 - 对齐 init_schema.sql
    name = Column(String(200), nullable=True, comment="账户名称")
    account_code = Column(String(100), unique=True, nullable=True, comment="账户代码")
    status = Column(String(20), nullable=True, comment="账户状态")
    status_reason = Column(Text, nullable=True, comment="状态原因")

    # 消耗配置
    spend_limit = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0.00',
        comment="消耗限额"
    )
    currency = Column(String(10), nullable=False, default='CNY', server_default='CNY', comment="货币")
    timezone = Column(String(50), nullable=False, default='Asia/Shanghai', server_default='Asia/Shanghai', comment="时区")

    # 押款字段 (OpenSpec: add-reconciliation-control-center)
    deposit = Column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0.00',
        comment="当前押款金额 (SoT: DATA_SCHEMA.md v5.4 §5.1)"
    )
    deposit_updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="押款最后更新时间"
    )

    # 审计字段 - 对齐 init_schema.sql
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="创建者ID"
    )
    updated_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="更新者ID"
    )

    # ========== 关系定义 ==========

    # 多对一：账户 -> 项目
    project = relationship(
        "Project",
        back_populates="ad_accounts",
        lazy="joined",
        doc="所属项目"
    )

    # 多对一：账户 -> 渠道
    channel = relationship(
        "Channel",
        back_populates="ad_accounts",
        lazy="joined",
        doc="所属渠道"
    )

    # 多对一：账户 -> 供应商
    supplier = relationship(
        "Supplier",
        foreign_keys=[supplier_id],
        lazy="joined",
        doc="供应商"
    )

    # 多对一：账户 -> 负责人
    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        lazy="selectin",
        doc="负责人（投手）"
    )

    # 多对一：账户 -> 团队
    team = relationship(
        "Team",
        foreign_keys=[team_id],
        lazy="joined",
        doc="所属团队"
    )

    # 多对一：账户 -> 投手
    buyer = relationship(
        "Buyer",
        foreign_keys=[buyer_id],
        lazy="joined",
        doc="所属投手"
    )

    # 一对多：账户 -> 余额快照 (OpenSpec: add-reconciliation-control-center)
    balance_snapshots = relationship(
        "AdAccountBalanceSnapshot",
        back_populates="ad_account",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="余额/押款快照历史"
    )

    # 一对多：账户 -> 对账差异单 (OpenSpec: add-reconciliation-control-center)
    reconciliation_issues = relationship(
        "ReconciliationIssue",
        back_populates="ad_account",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="对账差异单列表"
    )

    # 约束与索引 - 对齐 init_schema.sql
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')",
            name='chk_ad_accounts_status'
        ),
        Index('idx_ad_accounts_project', 'project_id'),
        Index('idx_ad_accounts_channel', 'channel_id'),
        Index('idx_ad_accounts_status', 'status'),
        Index('idx_ad_accounts_supplier', 'supplier_id'),
        Index('idx_ad_accounts_team', 'team_id'),
        Index('idx_ad_accounts_buyer', 'buyer_id'),
    )

    def __repr__(self):
        return f"<AdAccount(id={self.id}, code='{self.account_code}', status='{self.status}')>"

    # ========== 向后兼容属性 ==========

    @property
    def assigned_to(self):
        """向后兼容：返回 owner_id"""
        return self.owner_id

    @assigned_to.setter
    def assigned_to(self, value):
        """向后兼容：设置 owner_id"""
        self.owner_id = value

    @property
    def account_name(self):
        """向后兼容：返回 name"""
        return self.name

    @account_name.setter
    def account_name(self, value):
        """向后兼容：设置 name"""
        self.name = value

    # ========== 业务属性 ==========

    @property
    def status_enum(self) -> AdAccountStatus:
        """返回状态枚举对象"""
        if self.status:
            return AdAccountStatus(self.status)
        return AdAccountStatus.NEW

    @property
    def is_active(self) -> bool:
        """是否是活跃账户"""
        return self.status == AdAccountStatus.ACTIVE.value

    # ========== 状态流转方法 ==========

    def can_transition_to(self, new_status: AdAccountStatus) -> bool:
        """检查是否可以转换到新状态"""
        return self.status_enum.can_transition_to(new_status)

    def transition_to(self, new_status: AdAccountStatus, operator_id: UUID, reason: str = None):
        """
        安全地转换账户状态

        Args:
            new_status: 目标状态
            operator_id: 操作者用户ID
            reason: 状态变更原因

        Returns:
            tuple: (成功标志, 状态变更历史对象)

        Raises:
            ValueError: 不允许的状态转换
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"不允许从 {self.status} 转换到 {new_status.value}"
            )

        old_status = self.status
        self.status = new_status.value
        self.status_reason = reason

        from backend.models.accounts.account_history import AccountStatusHistory
        history = AccountStatusHistory(
            ad_account_id=self.id,
            old_status=old_status,
            new_status=new_status.value,
            changed_by=operator_id,
            reason=reason
        )

        return True, history

    # ========== 查询作用域方法 ==========

    @classmethod
    def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的账户查询（RLS 逻辑）"""
        query = session.query(cls)

        if user_role in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
            return query

        if user_role == UserRole.MEDIA_BUYER:
            return query.filter(cls.owner_id == user_id)

        if user_role == UserRole.FINANCE:
            return query

        return query.filter(cls.owner_id == user_id)

    @classmethod
    def get_active_accounts(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的活跃账户"""
        return cls.get_user_accessible_query(session, user_id, user_role).filter(
            cls.status == AdAccountStatus.ACTIVE.value
        )
