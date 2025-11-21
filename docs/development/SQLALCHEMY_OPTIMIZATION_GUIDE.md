# SQLAlchemy 模型层架构优化建议报告

> **文档版本**: v1.0
> **创建日期**: 2025-11-19
> **目标读者**: Python/FastAPI/SQLAlchemy 架构师、后端开发者
> **项目**: AI广告代投系统
> **技术栈**: FastAPI + SQLAlchemy 2.0 + Supabase + PostgreSQL + RLS

---

## 📋 执行摘要

基于对 `SQLALCHEMY_MODELS_SUMMARY.md` 的深度分析，当前模型层虽然与数据库完全对齐，但在**工程化、可维护性、抽象设计**方面存在显著提升空间。本报告将从 7 个维度提出 **可立即执行** 的优化方案。

---

## 🔍 当前模型层不足分析

### 1. 文件结构问题

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 16 个模型挤在单个 24KB 文件中 | ⚠️ 中 | 代码导航困难，Git 合并冲突频繁 |
| 缺少模块化分层（base/business/finance/audit） | ⚠️ 中 | 业务边界不清晰，新人理解成本高 |
| 旧版模型文件散落在 models/ 目录下 | ⚠️ 低 | 导入混乱，增加维护负担 |

### 2. 抽象层级问题

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 缺少统一的 TimestampMixin（created_at/updated_at 重复 16 次） | 🔴 高 | 违反 DRY 原则，修改成本高 |
| 没有 SoftDeleteMixin（未来需求必然出现） | ⚠️ 中 | 后续添加需要修改所有模型 |
| 缺少 AuditMixin（RLS 权限字段 created_by 未统一） | 🔴 高 | 权限逻辑分散，容易遗漏 |
| 没有 StatusMixin（状态字段模式重复） | ⚠️ 中 | 状态流转逻辑无法复用 |

### 3. 类型安全问题

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 状态字段使用裸字符串，无 Python Enum | 🔴 高 | IDE 无提示，容易拼写错误 |
| 缺少 TypedDict/Pydantic 映射（JSONB 字段） | ⚠️ 中 | metadata/old_values 字段类型不明确 |
| 没有角色枚举（role 字段使用字符串） | 🔴 高 | 与权限系统脱节 |

### 4. 关系定义缺失

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 所有模型都只定义外键，无 relationship | 🔴 高 | 无法使用 ORM 关联查询 |
| 缺少 backref/back_populates | 🔴 高 | 双向导航不可用（如 `project.ad_accounts`） |
| 没有 lazy 策略配置 | ⚠️ 中 | 容易触发 N+1 查询问题 |

### 5. 业务逻辑问题

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 状态流转逻辑（STATE_MACHINE.md）未体现在模型中 | 🔴 高 | 状态变更无约束，业务规则分散 |
| 缺少模型级别的验证方法（如 `can_transition_to(new_status)`） | 🔴 高 | 状态机规则需在 Service 层重复实现 |
| 没有查询作用域（如 `query_for_user(user_id)`） | 🔴 高 | 每个 API 都要手动写 RLS 过滤条件 |

### 6. 工程化缺陷

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 缺少模型工厂（用于测试数据生成） | ⚠️ 中 | 单元测试难写，数据准备繁琐 |
| 没有序列化器（to_dict/from_dict） | ⚠️ 中 | API 响应需手动映射字段 |
| 缺少模型事件钩子（before_insert/after_update） | ⚠️ 中 | 审计日志、缓存失效等逻辑分散 |

### 7. RLS 一致性问题

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| created_by/assigned_to 字段未与 RLS 策略明确关联 | 🔴 高 | 权限校验逻辑不透明 |
| 模型中无法表达"当前用户可访问哪些记录" | 🔴 高 | ORM 查询与 RLS 策略脱节 |

---

## 🎯 优化方案（7 大模块）

---

## 📦 模块 1：文件结构重构

### 问题
所有 16 个模型挤在一个 `database_models.py` 中，导航困难，合并冲突频繁。

### 优化理由
- **可维护性**：按业务领域拆分，每个文件 200-300 行，符合认知负荷
- **团队协作**：不同开发者可并行修改不同模块，减少冲突
- **清晰边界**：代码组织反映业务架构（用户权限 / 项目账户 / 财务 / 审计）

### 改进方式

#### 新目录结构
```
backend/models/
├── __init__.py                    # 统一导出
├── base.py                        # Base + 所有 Mixin
├── enums.py                       # 所有枚举类型
├── mixins/                        # 通用 Mixin 模块
│   ├── __init__.py
│   ├── serializable.py            # 序列化 Mixin
│   └── rls_aware.py               # RLS 感知 Mixin
├── core/                          # 核心业务模型
│   ├── __init__.py
│   ├── user.py                    # User
│   ├── channel.py                 # Channel, ChannelReview, ChannelPerformance
│   └── project.py                 # Project
├── accounts/                      # 账户管理模型
│   ├── __init__.py
│   ├── ad_account.py              # AdAccount
│   ├── account_request.py         # ChannelAccountRequest
│   └── account_history.py         # AccountStatusHistory, AccountAlert
├── workflow/                      # 业务流程模型
│   ├── __init__.py
│   ├── daily_report.py            # DailyReport
│   ├── topup_request.py           # TopupRequest
│   └── ad_spend.py                # AdSpendDaily
├── finance/                       # 财务模型
│   ├── __init__.py
│   ├── ledger.py                  # LedgerEntry
│   └── reconciliation.py          # ReconciliationBatch, ReconciliationDetail
└── audit/                         # 审计模型
    ├── __init__.py
    └── audit_log.py               # AuditLog
```

#### 示例代码：`backend/models/base.py`

```python
"""
SQLAlchemy 基类和通用 Mixin
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr

# 声明式基类
Base = declarative_base()


class TimestampMixin:
    """时间戳 Mixin - 自动管理 created_at 和 updated_at"""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class SoftDeleteMixin:
    """软删除 Mixin - 未来扩展使用"""

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        comment="是否已删除"
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )


class UserScopeMixin:
    """用户作用域 Mixin - 支持 RLS 权限控制"""

    @declared_attr
    def created_by(cls):
        """创建者 ID - 用于 RLS 权限过滤"""
        return Column(
            UUID(as_uuid=True),
            nullable=True,
            comment="创建者用户ID"
        )

    @classmethod
    def query_for_user(cls, session, user_id: UUID):
        """
        获取当前用户可访问的记录查询

        Args:
            session: SQLAlchemy Session
            user_id: 当前用户 UUID

        Returns:
            Query: 已过滤的查询对象
        """
        return session.query(cls).filter(cls.created_by == user_id)


class AssignableMixin:
    """可分配 Mixin - 用于账户/任务分配场景"""

    @declared_attr
    def assigned_to(cls):
        """负责人 ID - 用于 RLS 权限过滤"""
        return Column(
            UUID(as_uuid=True),
            nullable=True,
            comment="负责人用户ID"
        )

    @classmethod
    def query_assigned_to_user(cls, session, user_id: UUID):
        """获取分配给当前用户的记录"""
        return session.query(cls).filter(cls.assigned_to == user_id)
```

#### 示例代码：`backend/models/enums.py`

```python
"""
所有枚举类型定义 - 与 STATE_MACHINE.md 和 DATA_SCHEMA.md 对齐
"""
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    FINANCE = "finance"
    DATA_MANAGER = "data_manager"
    MEDIA_BUYER = "media_buyer"
    CLIENT = "client"


class ChannelStatus(str, Enum):
    """渠道状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AdAccountStatus(str, Enum):
    """广告账户状态"""
    NEW = "new"
    TESTING = "testing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEAD = "dead"
    ARCHIVED = "archived"

    def can_transition_to(self, target: 'AdAccountStatus') -> bool:
        """
        检查是否可以转换到目标状态

        基于 STATE_MACHINE.md 的状态转换规则
        """
        transitions = {
            self.NEW: [self.TESTING, self.ACTIVE, self.SUSPENDED],
            self.TESTING: [self.ACTIVE, self.SUSPENDED, self.DEAD],
            self.ACTIVE: [self.SUSPENDED, self.DEAD, self.ARCHIVED],
            self.SUSPENDED: [self.ACTIVE, self.DEAD],
            self.DEAD: [self.ARCHIVED],
            self.ARCHIVED: [],  # 终态，不可转换
        }
        return target in transitions.get(self, [])


class DailyReportStatus(str, Enum):
    """日报状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TopupRequestStatus(str, Enum):
    """充值申请状态"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINANCE_APPROVE = "finance_approve"
    PAID = "paid"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReconciliationBatchStatus(str, Enum):
    """对账批次状态"""
    DRAFT = "draft"
    PENDING = "pending"
    REVIEWING = "reviewing"
    CLOSED = "closed"


class ReconciliationDetailStatus(str, Enum):
    """对账明细状态"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"


class AccountAlertStatus(str, Enum):
    """账户预警状态"""
    OPEN = "open"
    ACK = "ack"
    RESOLVED = "resolved"


class LedgerEntryType(str, Enum):
    """总账分录类型"""
    TOPUP_RECEIVED = "topup_received"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"


class ChannelAccountRequestStatus(str, Enum):
    """渠道开户申请状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChannelReviewStatus(str, Enum):
    """渠道评审状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

#### 示例代码：`backend/models/core/user.py`

```python
"""
用户核心模型
"""
from sqlalchemy import Column, String, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.models.base import Base, TimestampMixin
from backend.models.enums import UserRole


class User(Base, TimestampMixin):
    """
    系统用户表

    RLS 策略：用户只能访问自己的记录（id = auth.uid()）
    """
    __tablename__ = 'users'

    # 主键
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="用户UUID（Supabase auth.uid）"
    )

    # 基本信息
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")

    # 角色与状态
    role = Column(String(20), nullable=False, comment="角色")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")

    # 索引
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_is_active', 'is_active'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    @property
    def role_enum(self) -> UserRole:
        """返回角色枚举对象"""
        return UserRole(self.role)

    def has_role(self, *roles: UserRole) -> bool:
        """检查用户是否拥有指定角色之一"""
        return self.role_enum in roles

    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.role_enum == UserRole.ADMIN

    def is_finance(self) -> bool:
        """是否是财务"""
        return self.role_enum == UserRole.FINANCE
```

#### 示例代码：`backend/models/__init__.py`（重构后）

```python
"""
AI广告代投系统 - 数据模型统一导出
"""

# 基础组件
from .base import Base, TimestampMixin, SoftDeleteMixin, UserScopeMixin, AssignableMixin
from .enums import (
    UserRole,
    ChannelStatus,
    ProjectStatus,
    AdAccountStatus,
    DailyReportStatus,
    TopupRequestStatus,
    ReconciliationBatchStatus,
    ReconciliationDetailStatus,
    AccountAlertStatus,
    LedgerEntryType,
)

# 核心模型
from .core.user import User
from .core.channel import Channel, ChannelReview, ChannelPerformance
from .core.project import Project

# 账户管理
from .accounts.ad_account import AdAccount
from .accounts.account_request import ChannelAccountRequest
from .accounts.account_history import AccountStatusHistory, AccountAlert

# 业务流程
from .workflow.daily_report import DailyReport
from .workflow.topup_request import TopupRequest
from .workflow.ad_spend import AdSpendDaily

# 财务
from .finance.ledger import LedgerEntry
from .finance.reconciliation import ReconciliationBatch, ReconciliationDetail

# 审计
from .audit.audit_log import AuditLog

__all__ = [
    # 基础
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UserScopeMixin",
    "AssignableMixin",

    # 枚举
    "UserRole",
    "ChannelStatus",
    "ProjectStatus",
    "AdAccountStatus",
    "DailyReportStatus",
    "TopupRequestStatus",
    "ReconciliationBatchStatus",
    "ReconciliationDetailStatus",
    "AccountAlertStatus",
    "LedgerEntryType",

    # 模型
    "User",
    "Channel",
    "ChannelReview",
    "ChannelPerformance",
    "Project",
    "AdAccount",
    "ChannelAccountRequest",
    "AccountStatusHistory",
    "AccountAlert",
    "DailyReport",
    "TopupRequest",
    "AdSpendDaily",
    "LedgerEntry",
    "ReconciliationBatch",
    "ReconciliationDetail",
    "AuditLog",
]
```

---

## 🔗 模块 2：Relationship 关系定义

### 问题
当前所有模型只定义了外键（ForeignKey），没有 SQLAlchemy 的 `relationship`，导致无法使用 ORM 的关联查询能力。

### 优化理由
- **开发效率**：可以直接 `project.ad_accounts` 而非手动 JOIN
- **N+1 优化**：通过 `lazy='selectin'` 等策略避免性能问题
- **代码可读性**：关系导航比 JOIN 更直观

### 改进方式

#### 示例代码：`backend/models/core/project.py`

```python
"""
项目模型
"""
from sqlalchemy import Column, BigInteger, String, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import Base, TimestampMixin, UserScopeMixin
from backend.models.enums import ProjectStatus


class Project(Base, TimestampMixin, UserScopeMixin):
    """
    项目表

    RLS 策略：用户只能访问自己创建的项目（created_by = auth.uid()）
    """
    __tablename__ = 'projects'

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="项目ID")

    # 基本信息
    project_name = Column(String(100), nullable=False, comment="项目名称")
    project_code = Column(String(50), unique=True, nullable=False, comment="项目代码")
    client_name = Column(String(100), nullable=False, comment="客户名称")
    description = Column(Text, nullable=True, comment="项目描述")
    status = Column(String(20), nullable=False, comment="项目状态")

    # ========== 关系定义 ==========

    # 一对多：项目 -> 广告账户
    ad_accounts = relationship(
        "AdAccount",
        back_populates="project",
        cascade="all, delete-orphan",  # 删除项目时级联删除账户
        lazy="selectin",  # 避免 N+1 查询
        order_by="AdAccount.created_at.desc()",
        doc="项目下的所有广告账户"
    )

    # 一对多：项目 -> 渠道开户申请
    account_requests = relationship(
        "ChannelAccountRequest",
        back_populates="project",
        lazy="dynamic",  # 返回 Query 对象，适合大量数据
        doc="项目的渠道开户申请记录"
    )

    # 多对一：项目 -> 创建者（用户）
    creator = relationship(
        "User",
        foreign_keys="Project.created_by",
        lazy="joined",  # 总是加载创建者信息
        doc="项目创建者"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'suspended', 'archived')",
            name='projects_status_check'
        ),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, code='{self.project_code}', status='{self.status}')>"

    @property
    def status_enum(self) -> ProjectStatus:
        """返回状态枚举对象"""
        return ProjectStatus(self.status)

    def active_accounts_count(self) -> int:
        """获取活跃账户数量"""
        from backend.models.enums import AdAccountStatus
        return sum(1 for acc in self.ad_accounts if acc.status == AdAccountStatus.ACTIVE.value)
```

#### 示例代码：`backend/models/accounts/ad_account.py`

```python
"""
广告账户模型
"""
from decimal import Decimal
from sqlalchemy import Column, BigInteger, String, Text, Numeric, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import Base, TimestampMixin, AssignableMixin
from backend.models.enums import AdAccountStatus


class AdAccount(Base, TimestampMixin, AssignableMixin):
    """
    广告账户表 - 核心业务实体

    RLS 策略：用户只能访问分配给自己的账户（assigned_to = auth.uid()）
    """
    __tablename__ = 'ad_accounts'

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账户ID")

    # 外键
    project_id = Column(BigInteger, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    channel_id = Column(BigInteger, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)

    # 基本信息
    account_code = Column(String(50), unique=True, nullable=False, comment="账户代码")
    account_name = Column(String(100), nullable=True, comment="账户名称")
    status = Column(String(20), nullable=False, comment="账户状态")

    # 财务信息
    balance = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="账户余额")
    total_spent = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="总消耗")
    total_recharged = Column(Numeric(15, 2), nullable=False, default=Decimal('0.00'), comment="总充值")

    # 其他
    notes = Column(Text, nullable=True, comment="备注")

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

    # 一对多：账户 -> 日报
    daily_reports = relationship(
        "DailyReport",
        back_populates="ad_account",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="DailyReport.report_date.desc()",
        doc="账户的所有日报"
    )

    # 一对多：账户 -> 充值申请
    topup_requests = relationship(
        "TopupRequest",
        back_populates="ad_account",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="账户的充值申请记录"
    )

    # 一对多：账户 -> 账户预警
    alerts = relationship(
        "AccountAlert",
        back_populates="ad_account",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="AccountAlert.created_at.desc()",
        doc="账户预警记录"
    )

    # 约束与索引
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')",
            name='ad_accounts_status_check'
        ),
        Index('idx_ad_accounts_project_id', 'project_id'),
        Index('idx_ad_accounts_channel_id', 'channel_id'),
        Index('idx_ad_accounts_status', 'status'),
        Index('idx_ad_accounts_assigned_to', 'assigned_to'),
        Index('idx_ad_accounts_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<AdAccount(id={self.id}, code='{self.account_code}', status='{self.status}')>"

    @property
    def status_enum(self) -> AdAccountStatus:
        """返回状态枚举对象"""
        return AdAccountStatus(self.status)

    def can_transition_to(self, new_status: AdAccountStatus) -> bool:
        """检查是否可以转换到新状态"""
        return self.status_enum.can_transition_to(new_status)

    def get_open_alerts_count(self) -> int:
        """获取未处理的预警数量"""
        from backend.models.enums import AccountAlertStatus
        return sum(1 for alert in self.alerts if alert.status == AccountAlertStatus.OPEN.value)
```

---

## 🎨 模块 3：模型业务方法

### 问题
当前模型只是数据容器，缺少业务逻辑方法，导致状态流转、权限判断等逻辑分散在 Service 层。

### 优化理由
- **内聚性**：业务规则应该靠近数据定义
- **复用性**：避免在多个 Service 中重复相同逻辑
- **测试性**：模型方法更容易单元测试

### 改进方式

#### 示例代码：状态流转方法

```python
# 在 AdAccount 模型中添加

def transition_to(self, new_status: AdAccountStatus, operator_id: UUID, reason: str = None) -> tuple:
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
            f"不允许从 {self.status} 转换到 {new_status.value}，"
            f"请检查 STATE_MACHINE.md 中的状态机定义"
        )

    old_status = self.status
    self.status = new_status.value

    # 记录状态变更历史（需要在事务中提交）
    from backend.models.accounts.account_history import AccountStatusHistory
    history = AccountStatusHistory(
        ad_account_id=self.id,
        old_status=old_status,
        new_status=new_status.value,
        changed_by=operator_id,
        reason=reason
    )

    return True, history
```

#### 示例代码：权限判断方法

```python
# 在 DailyReport 模型中添加

def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """
    检查用户是否可以编辑此日报

    规则：
    - 投手只能编辑自己提交的草稿
    - 数据员和管理员可以编辑任何草稿
    - 已批准/拒绝的日报不可编辑
    """
    from backend.models.enums import DailyReportStatus

    # 已批准或已拒绝的不可编辑
    if self.status in [DailyReportStatus.APPROVED.value, DailyReportStatus.REJECTED.value]:
        return False

    # 管理员和数据员可以编辑任何草稿
    if user_role in [UserRole.ADMIN, UserRole.DATA_MANAGER]:
        return True

    # 投手只能编辑自己提交的草稿
    if user_role == UserRole.MEDIA_BUYER:
        return self.submitted_by == user_id and self.status == DailyReportStatus.DRAFT.value

    return False

def can_be_approved_by(self, user_role: UserRole) -> bool:
    """检查用户是否有权限批准此日报"""
    from backend.models.enums import DailyReportStatus

    return (
        self.status == DailyReportStatus.PENDING.value
        and user_role in [UserRole.DATA_MANAGER, UserRole.ADMIN]
    )
```

#### 示例代码：查询作用域方法

```python
# 在 AdAccount 模型中添加（类方法）

@classmethod
def get_user_accessible_query(cls, session, user_id: UUID, user_role: UserRole):
    """
    获取用户可访问的账户查询（RLS 逻辑）

    Args:
        session: SQLAlchemy Session
        user_id: 当前用户 ID
        user_role: 当前用户角色

    Returns:
        Query: 已应用权限过滤的查询对象
    """
    query = session.query(cls)

    # 管理员可以访问所有账户
    if user_role == UserRole.ADMIN:
        return query

    # 投手只能访问分配给自己的账户
    if user_role == UserRole.MEDIA_BUYER:
        return query.filter(cls.assigned_to == user_id)

    # 数据员可以访问所有账户
    if user_role == UserRole.DATA_MANAGER:
        return query

    # 财务可以访问所有账户（只读）
    if user_role == UserRole.FINANCE:
        return query

    # 默认：只能访问自己创建的（如果有 created_by 字段）
    return query.filter(cls.created_by == user_id)

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
```

---

## 📊 模块 4：序列化器 (Serializer)

### 问题
模型对象无法直接返回给 API，需要手动映射字段到字典，代码重复且容易遗漏。

### 优化理由
- **DRY 原则**：统一的序列化逻辑，避免每个 API 重复编写
- **类型安全**：配合 Pydantic Schema 使用，确保类型正确
- **性能优化**：可以控制关联对象的加载深度

### 改进方式

#### 示例代码：`backend/models/mixins/serializable.py`

```python
"""
序列化 Mixin
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class SerializableMixin:
    """
    序列化 Mixin - 将模型对象转换为字典
    """

    # 子类可以覆盖这些属性来控制序列化行为
    __json_hidden__ = []  # 隐藏字段（如 hashed_password）
    __json_include_relationships__ = []  # 需要包含的关联对象

    def to_dict(
        self,
        include_relationships: bool = False,
        exclude: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            include_relationships: 是否包含关联对象
            exclude: 排除的字段列表

        Returns:
            Dict: 序列化后的字典
        """
        exclude = exclude or []
        exclude.extend(self.__json_hidden__)

        result = {}

        # 序列化列字段
        for column in self.__table__.columns:
            if column.name in exclude:
                continue

            value = getattr(self, column.name)
            result[column.name] = self._serialize_value(value)

        # 序列化关联对象
        if include_relationships:
            for rel_name in self.__json_include_relationships__:
                if rel_name in exclude:
                    continue

                rel_value = getattr(self, rel_name, None)
                if rel_value is None:
                    result[rel_name] = None
                elif isinstance(rel_value, list):
                    result[rel_name] = [
                        item.to_dict(include_relationships=False)
                        if hasattr(item, 'to_dict') else str(item)
                        for item in rel_value
                    ]
                else:
                    result[rel_name] = (
                        rel_value.to_dict(include_relationships=False)
                        if hasattr(rel_value, 'to_dict') else str(rel_value)
                    )

        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """序列化单个值"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, UUID):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return value

    @classmethod
    def from_dict(cls, data: Dict[str, Any], session=None):
        """
        从字典创建模型实例（用于反序列化）

        Args:
            data: 数据字典
            session: SQLAlchemy Session（如果需要处理关联对象）

        Returns:
            Model: 模型实例
        """
        # 过滤掉不属于模型列的字段
        valid_columns = {col.name for col in cls.__table__.columns}
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}

        return cls(**filtered_data)
```

#### 使用示例

```python
# 在模型中继承 SerializableMixin

from backend.models.mixins.serializable import SerializableMixin

class User(Base, TimestampMixin, SerializableMixin):
    __tablename__ = 'users'

    # 隐藏敏感字段
    __json_hidden__ = ['hashed_password']

    # ... 其他字段定义

# API 层使用
@router.get("/users/{user_id}")
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 直接序列化为字典
    return {"success": True, "data": user.to_dict()}
```

---

## 🧪 模块 5：模型工厂 (Factory)

### 问题
测试中需要大量创建模型实例，手动创建繁琐且数据不真实。

### 优化理由
- **测试效率**：快速生成测试数据
- **数据真实性**：使用 Faker 生成符合业务逻辑的数据
- **可维护性**：集中管理测试数据创建逻辑

### 改进方式

#### 示例代码：`backend/tests/factories.py`

```python
"""
模型工厂 - 用于测试数据生成
"""
import factory
from factory import Faker, SubFactory, LazyAttribute
from factory.alchemy import SQLAlchemyModelFactory
from decimal import Decimal
from datetime import datetime, timedelta

from backend.models import (
    User, Project, AdAccount, DailyReport,
    UserRole, ProjectStatus, AdAccountStatus, DailyReportStatus
)
from backend.core.database import SessionLocal


class BaseFactory(SQLAlchemyModelFactory):
    """基础工厂类"""
    class Meta:
        abstract = True
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    """用户工厂"""
    class Meta:
        model = User

    username = Faker('user_name')
    email = Faker('email')
    hashed_password = "hashed_password_here"
    role = UserRole.MEDIA_BUYER.value
    is_active = True


class AdminUserFactory(UserFactory):
    """管理员工厂"""
    role = UserRole.ADMIN.value


class ProjectFactory(BaseFactory):
    """项目工厂"""
    class Meta:
        model = Project

    project_name = Faker('company')
    project_code = Faker('bothify', text='PRJ-####')
    client_name = Faker('company')
    description = Faker('text', max_nb_chars=200)
    status = ProjectStatus.ACTIVE.value
    created_by = SubFactory(UserFactory)


class AdAccountFactory(BaseFactory):
    """广告账户工厂"""
    class Meta:
        model = AdAccount

    project = SubFactory(ProjectFactory)
    channel_id = 1  # 假设已有渠道
    account_code = Faker('bothify', text='ACC-########')
    account_name = Faker('company')
    status = AdAccountStatus.ACTIVE.value
    balance = Decimal('1000.00')
    total_spent = Decimal('500.00')
    total_recharged = Decimal('1500.00')
    assigned_to = SubFactory(UserFactory)


class DailyReportFactory(BaseFactory):
    """日报工厂"""
    class Meta:
        model = DailyReport

    ad_account = SubFactory(AdAccountFactory)
    report_date = LazyAttribute(lambda _: datetime.now().date() - timedelta(days=1))
    impressions = Faker('random_int', min=1000, max=100000)
    clicks = Faker('random_int', min=10, max=1000)
    spend = LazyAttribute(lambda obj: Decimal(str(obj.clicks * 0.5)))
    conversions = Faker('random_int', min=1, max=50)
    status = DailyReportStatus.PENDING.value
    submitted_by = SubFactory(UserFactory)


# 使用示例（在测试中）
def test_create_daily_report():
    """测试创建日报"""
    # 快速创建测试数据
    report = DailyReportFactory.create()

    assert report.id is not None
    assert report.status == DailyReportStatus.PENDING.value
    assert report.spend > 0

    # 批量创建
    reports = DailyReportFactory.create_batch(10)
    assert len(reports) == 10
```

---

## 🔐 模块 6：RLS 一致性增强

### 问题
模型中的权限字段（created_by, assigned_to）与 Supabase RLS 策略的关系不明确。

### 优化理由
- **安全性**：确保 ORM 查询与 RLS 策略一致，避免权限泄漏
- **可维护性**：明确标注哪些字段用于 RLS 过滤
- **可测试性**：可以在单元测试中验证权限逻辑

### 改进方式

#### 示例代码：`backend/models/mixins/rls_aware.py`

```python
"""
RLS 感知 Mixin - 确保 ORM 查询与 Supabase RLS 策略一致
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, Query

from backend.models.enums import UserRole


class RLSAwareMixin:
    """
    RLS 感知 Mixin

    标注哪些字段用于 RLS 权限控制，并提供统一的查询接口
    """

    # 子类需要定义这些属性
    __rls_user_field__ = None  # 用于 RLS 过滤的用户字段（如 'created_by', 'assigned_to'）
    __rls_admin_roles__ = [UserRole.ADMIN]  # 可以访问所有记录的角色
    __rls_readonly_roles__ = []  # 只读角色（可以看但不能改）

    @classmethod
    def apply_rls_filter(
        cls,
        query: Query,
        current_user_id: UUID,
        current_user_role: UserRole
    ) -> Query:
        """
        应用 RLS 过滤条件到查询

        Args:
            query: SQLAlchemy Query 对象
            current_user_id: 当前用户 UUID
            current_user_role: 当前用户角色

        Returns:
            Query: 已应用 RLS 过滤的查询对象
        """
        # 管理员可以访问所有记录
        if current_user_role in cls.__rls_admin_roles__:
            return query

        # 检查是否定义了 RLS 字段
        if not cls.__rls_user_field__:
            raise ValueError(f"{cls.__name__} 未定义 __rls_user_field__，无法应用 RLS 过滤")

        # 应用用户字段过滤
        user_field = getattr(cls, cls.__rls_user_field__)
        return query.filter(user_field == current_user_id)

    @classmethod
    def get_for_user(
        cls,
        session: Session,
        current_user_id: UUID,
        current_user_role: UserRole,
        filters: Optional[List] = None
    ) -> Query:
        """
        获取当前用户可访问的记录查询

        Args:
            session: SQLAlchemy Session
            current_user_id: 当前用户 UUID
            current_user_role: 当前用户角色
            filters: 额外的过滤条件列表

        Returns:
            Query: 已应用 RLS 和额外过滤的查询对象
        """
        query = session.query(cls)

        # 应用 RLS 过滤
        query = cls.apply_rls_filter(query, current_user_id, current_user_role)

        # 应用额外过滤条件
        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)

        return query

    def is_accessible_by(
        self,
        user_id: UUID,
        user_role: UserRole
    ) -> bool:
        """
        检查当前用户是否可以访问此记录

        Args:
            user_id: 用户 UUID
            user_role: 用户角色

        Returns:
            bool: 是否可访问
        """
        # 管理员可以访问所有记录
        if user_role in self.__rls_admin_roles__:
            return True

        # 检查 RLS 字段
        if not self.__rls_user_field__:
            return False

        user_field_value = getattr(self, self.__rls_user_field__)
        return user_field_value == user_id

    def is_modifiable_by(
        self,
        user_id: UUID,
        user_role: UserRole
    ) -> bool:
        """
        检查当前用户是否可以修改此记录

        Args:
            user_id: 用户 UUID
            user_role: 用户角色

        Returns:
            bool: 是否可修改
        """
        # 只读角色不能修改
        if user_role in self.__rls_readonly_roles__:
            return False

        # 其他同 is_accessible_by
        return self.is_accessible_by(user_id, user_role)
```

#### 使用示例

```python
# 在 AdAccount 模型中使用

from backend.models.mixins.rls_aware import RLSAwareMixin

class AdAccount(Base, TimestampMixin, AssignableMixin, RLSAwareMixin, SerializableMixin):
    __tablename__ = 'ad_accounts'

    # RLS 配置
    __rls_user_field__ = 'assigned_to'  # 使用 assigned_to 字段进行 RLS 过滤
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_MANAGER]  # 管理员和数据员可以访问所有账户
    __rls_readonly_roles__ = [UserRole.FINANCE]  # 财务只读

    # ... 其他字段定义


# API 层使用
@router.get("/ad-accounts")
def list_ad_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户可访问的广告账户列表"""

    # 自动应用 RLS 过滤
    accounts_query = AdAccount.get_for_user(
        session=db,
        current_user_id=current_user.id,
        current_user_role=current_user.role_enum,
        filters=[AdAccount.status == AdAccountStatus.ACTIVE.value]  # 额外过滤条件
    )

    accounts = accounts_query.all()

    return {
        "success": True,
        "data": [acc.to_dict() for acc in accounts]
    }
```

---

## 📅 模块 7：事件钩子系统

### 问题
缺少模型级别的事件钩子（before_insert, after_update），导致审计日志、缓存失效等横切关注点分散在业务代码中。

### 优化理由
- **关注点分离**：业务逻辑与审计、通知等解耦
- **可扩展性**：新增功能无需修改现有模型
- **可测试性**：事件处理器可以独立测试

### 改进方式

#### 示例代码：`backend/models/events.py`

```python
"""
模型事件钩子系统
"""
from sqlalchemy import event
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Any

from backend.models import AdAccount, DailyReport, TopupRequest
from backend.models.audit.audit_log import AuditLog


def record_audit_log(
    session: Session,
    user_id: UUID,
    resource_type: str,
    resource_id: Any,
    action: str,
    old_values: dict = None,
    new_values: dict = None
):
    """记录审计日志"""
    audit_log = AuditLog(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=str(resource_id),
        action=action,
        old_values=old_values,
        new_values=new_values
    )
    session.add(audit_log)


# ========== AdAccount 事件钩子 ==========

@event.listens_for(AdAccount, 'after_update')
def ad_account_after_update(mapper, connection, target: AdAccount):
    """
    广告账户更新后触发

    功能：
    1. 记录状态变更历史
    2. 触发余额预警
    """
    session = Session.object_session(target)
    if not session:
        return

    # 检查状态是否变更
    history = target.__history__
    if 'status' in history.attrs and history.attrs.status.history.has_changes():
        old_status = history.attrs.status.history.deleted[0]
        new_status = target.status

        # 记录状态变更（已在 transition_to 方法中处理，这里仅示例）
        print(f"AdAccount {target.id} 状态从 {old_status} 变更为 {new_status}")

    # 检查余额预警
    if target.balance < 100:  # 阈值可配置
        from backend.models.accounts.account_history import AccountAlert
        from backend.models.enums import AccountAlertStatus

        # 创建预警（如果不存在）
        existing_alert = session.query(AccountAlert).filter(
            AccountAlert.ad_account_id == target.id,
            AccountAlert.status == AccountAlertStatus.OPEN.value,
            AccountAlert.alert_type == 'low_balance'
        ).first()

        if not existing_alert:
            alert = AccountAlert(
                ad_account_id=target.id,
                alert_type='low_balance',
                severity='high',
                message=f'账户余额不足：当前余额 {target.balance}',
                status=AccountAlertStatus.OPEN.value
            )
            session.add(alert)


@event.listens_for(AdAccount, 'before_delete')
def ad_account_before_delete(mapper, connection, target: AdAccount):
    """
    广告账户删除前检查

    防止误删：活跃账户不允许删除
    """
    from backend.models.enums import AdAccountStatus

    if target.status in [AdAccountStatus.ACTIVE.value, AdAccountStatus.TESTING.value]:
        raise ValueError(f"不允许删除活跃状态的账户（ID: {target.id}）")


# ========== DailyReport 事件钩子 ==========

@event.listens_for(DailyReport, 'after_insert')
def daily_report_after_insert(mapper, connection, target: DailyReport):
    """
    日报创建后触发

    功能：通知数据员审核
    """
    from backend.models.enums import DailyReportStatus

    if target.status == DailyReportStatus.PENDING.value:
        # 发送通知（集成通知系统）
        print(f"新日报待审核：Report ID {target.id}, Date {target.report_date}")


# ========== TopupRequest 事件钩子 ==========

@event.listens_for(TopupRequest, 'after_update')
def topup_request_after_update(mapper, connection, target: TopupRequest):
    """
    充值申请更新后触发

    功能：
    1. 状态变更为已完成时，更新账户余额
    2. 发送通知
    """
    session = Session.object_session(target)
    if not session:
        return

    from backend.models.enums import TopupRequestStatus

    history = target.__history__
    if 'status' in history.attrs and history.attrs.status.history.has_changes():
        new_status = target.status

        # 充值完成，更新账户余额
        if new_status == TopupRequestStatus.COMPLETED.value:
            ad_account = session.query(AdAccount).filter(
                AdAccount.id == target.ad_account_id
            ).first()

            if ad_account:
                ad_account.total_recharged += target.amount
                ad_account.balance += target.amount
                session.add(ad_account)

                print(f"账户 {ad_account.account_code} 充值 {target.amount}，当前余额 {ad_account.balance}")


def setup_model_events():
    """
    注册所有模型事件钩子

    在应用启动时调用
    """
    # 事件钩子通过 @event.listens_for 装饰器已自动注册
    # 这里可以添加额外的初始化逻辑
    print("模型事件钩子已注册")
```

#### 在应用启动时注册

```python
# backend/main.py

from fastapi import FastAPI
from backend.models.events import setup_model_events

app = FastAPI()

@app.on_event("startup")
def startup_event():
    """应用启动时初始化"""
    setup_model_events()
    print("应用启动完成")
```

---

## 📝 总结：优化实施路线图

### 🎯 优先级排序

| 优先级 | 模块 | 工作量 | 价值 | 建议时间 |
|-------|------|-------|------|---------|
| 🔴 P0 | 模块2：Relationship 关系定义 | 2-3天 | 极高 | 立即开始 |
| 🔴 P0 | 模块1：Enum 枚举类型 | 1天 | 极高 | 立即开始 |
| 🟡 P1 | 模块3：模型业务方法 | 3-4天 | 高 | 第1周 |
| 🟡 P1 | 模块6：RLS 一致性增强 | 2天 | 高 | 第1周 |
| 🟢 P2 | 模块4：序列化器 | 1-2天 | 中 | 第2周 |
| 🟢 P2 | 模块1：文件结构重构 | 2-3天 | 中 | 第2周 |
| ⚪ P3 | 模块5：模型工厂 | 1天 | 中 | 第3周 |
| ⚪ P3 | 模块7：事件钩子系统 | 2天 | 中 | 第3周 |

### 📋 实施步骤

#### Phase 1（第1周）：核心基础优化
1. **创建 `enums.py`**：定义所有状态枚举和角色枚举
2. **更新 `base.py`**：添加 TimestampMixin, UserScopeMixin, AssignableMixin
3. **添加 Relationship**：在现有 `database_models.py` 中添加所有关系定义
4. **创建 RLSAwareMixin**：实现统一的 RLS 查询接口

#### Phase 2（第2周）：工程化增强
1. **创建 SerializableMixin**：实现 to_dict/from_dict
2. **拆分模型文件**：按业务域重构目录结构
3. **添加业务方法**：在各模型中添加状态流转、权限判断方法

#### Phase 3（第3周）：测试与辅助工具
1. **创建模型工厂**：使用 factory_boy 生成测试数据
2. **实现事件钩子**：添加审计日志、通知等横切关注点
3. **编写单元测试**：验证所有新增功能

### ✅ 验收标准

- [ ] 所有状态字段使用 Enum 而非裸字符串
- [ ] 所有模型都继承必要的 Mixin（Timestamp, RLSAware 等）
- [ ] 所有外键都定义了对应的 relationship
- [ ] 所有模型都有 `to_dict()` 方法
- [ ] 所有权限控制逻辑都通过 `get_for_user()` 实现
- [ ] 状态流转都通过 `transition_to()` 方法验证
- [ ] 测试覆盖率 > 80%

---

## 📚 附录

### A. 依赖安装

```bash
# 安装测试工厂依赖
pip install factory-boy faker

# 安装类型检查工具
pip install mypy sqlalchemy[mypy]
```

### B. 配置示例

#### `mypy.ini` - 类型检查配置

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-factory.*]
ignore_missing_imports = True
```

### C. 测试示例

```python
# backend/tests/test_models.py

import pytest
from backend.models import AdAccount, AdAccountStatus, UserRole
from backend.tests.factories import AdAccountFactory, UserFactory


def test_ad_account_status_transition():
    """测试账户状态转换"""
    account = AdAccountFactory.create(status=AdAccountStatus.NEW.value)
    operator = UserFactory.create()

    # 允许的转换
    success, history = account.transition_to(
        AdAccountStatus.TESTING,
        operator_id=operator.id,
        reason="进入测试阶段"
    )
    assert success is True
    assert account.status == AdAccountStatus.TESTING.value

    # 不允许的转换
    with pytest.raises(ValueError):
        account.transition_to(AdAccountStatus.ARCHIVED, operator.id)


def test_rls_filter():
    """测试 RLS 权限过滤"""
    user1 = UserFactory.create(role=UserRole.MEDIA_BUYER.value)
    user2 = UserFactory.create(role=UserRole.MEDIA_BUYER.value)

    # 创建分配给不同用户的账户
    account1 = AdAccountFactory.create(assigned_to=user1.id)
    account2 = AdAccountFactory.create(assigned_to=user2.id)

    # User1 只能看到自己的账户
    accessible = AdAccount.get_for_user(
        session=db,
        current_user_id=user1.id,
        current_user_role=user1.role_enum
    ).all()

    assert len(accessible) == 1
    assert accessible[0].id == account1.id
```

---

**本优化方案与当前架构（FastAPI + SQLAlchemy 2.0 + Supabase + RLS）完全兼容，所有代码均可直接使用 Claude Code 生成并集成到项目中。**

**文档版本**: v1.0
**创建日期**: 2025-11-19
**最后更新**: 2025-11-19
**维护者**: 数据库架构团队
