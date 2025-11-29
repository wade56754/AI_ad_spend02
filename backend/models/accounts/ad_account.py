"""
广告账户模型 - 核心业务实体

RLS 策略：用户只能访问分配给自己的账户（assigned_to = auth.uid()）
"""
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Column, BigInteger, String, Text, Integer, Numeric, Index, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin, AssignableMixin
from backend.models.enums import AdAccountStatus, UserRole
from backend.models.mixins.serializable import SerializableMixin
from backend.models.mixins.rls_aware import RLSAwareMixin


class AdAccount(Base, TimestampMixin, AssignableMixin, RLSAwareMixin, SerializableMixin):
    """
    广告账户表 - 核心业务实体

    字段：
    - id: 主键
    - project_id/channel_id: 外键
    - assigned_to: 负责人（来自 AssignableMixin）
    - account_code: 账户代码（唯一）
    - account_name: 账户名称
    - status: 账户状态（new/testing/active/suspended/dead/archived）
    - balance: 账户余额
    - opened_at/died_at: 开户/死号时间
    - death_reason/death_loss: 死号原因和损失
    - notes: 备注
    - created_at/updated_at: 时间戳（自动管理）
    """
    __tablename__ = 'ad_accounts'

    # RLS 配置
    __rls_user_field__ = 'assigned_to'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]
    __rls_readonly_roles__ = [UserRole.FINANCE]

    # 序列化配置
    __json_include_relationships__ = ['project', 'channel', 'assignee']

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账户ID")

    # 外键
    project_id = Column(BigInteger, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    # 外键：UUID（对齐 DATA_SCHEMA.md 3.2.9）
    channel_id = Column(PGUUID(as_uuid=True), ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)

    # 基本信息
    account_code = Column(String(50), unique=True, nullable=False, comment="账户代码")
    account_name = Column(String(100), nullable=True, comment="账户名称")
    status = Column(String(20), nullable=False, comment="账户状态")
    balance = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="账户余额")

    # 时间字段
    opened_at = Column(DateTime(timezone=True), nullable=True, comment="开户时间")
    died_at = Column(DateTime(timezone=True), nullable=True, comment="死号时间")

    # 死号相关
    death_reason = Column(Text, nullable=True, comment="死号原因")
    death_loss = Column(Numeric(15, 2), nullable=True, comment="死号损失")

    # 其他
    notes = Column(Text, nullable=True, comment="备注")

    # 并发控制
    version = Column(Integer, nullable=False, server_default='1', comment="乐观锁版本号")

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

    # 多对一：账户 -> 负责人
    assignee = relationship(
        "User",
        foreign_keys="AdAccount.assigned_to",
        lazy="selectin",
        doc="负责人（投手）"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')",
            name='chk_ad_accounts_status'
        ),
        Index('idx_ad_accounts_project_id', 'project_id'),
        Index('idx_ad_accounts_channel_id', 'channel_id'),
        Index('idx_ad_accounts_status', 'status'),
        Index('idx_ad_accounts_assigned_to', 'assigned_to'),
        Index('idx_ad_accounts_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AdAccount(id={self.id}, code='{self.account_code}', status='{self.status}')>"

    # ========== 业务属性 ==========

    @property
    def assigned_user_id(self):
        """
        向后兼容别名：返回 assigned_to 的值

        注意：此属性为向后兼容保留，新代码应使用 assigned_to
        """
        return self.assigned_to

    @assigned_user_id.setter
    def assigned_user_id(self, value):
        """
        向后兼容别名：设置 assigned_to 的值

        注意：此属性为向后兼容保留，新代码应使用 assigned_to
        """
        self.assigned_to = value

    @property
    def status_enum(self) -> AdAccountStatus:
        """返回状态枚举对象"""
        return AdAccountStatus(self.status)

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
            return query.filter(cls.assigned_to == user_id)

        if user_role == UserRole.FINANCE:
            return query

        return query.filter(cls.assigned_to == user_id)

    @classmethod
    def get_active_accounts(cls, session, user_id: UUID, user_role: UserRole):
        """获取用户可访问的活跃账户"""
        return cls.get_user_accessible_query(session, user_id, user_role).filter(
            cls.status == AdAccountStatus.ACTIVE.value
        )

    @classmethod
    def get_low_balance_accounts(cls, session, user_id: UUID, user_role: UserRole, threshold: Decimal):
        """获取余额低于阈值的账户"""
        return cls.get_user_accessible_query(session, user_id, user_role).filter(
            cls.balance < threshold,
            cls.status.in_([AdAccountStatus.ACTIVE.value, AdAccountStatus.TESTING.value])
        )
