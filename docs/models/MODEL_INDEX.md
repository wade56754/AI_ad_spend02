# 模型索引（Model Index）

**版本**: v2.0
**最后更新**: 2025-01-19
**文档状态**: ✅ Source of Truth（真相源）

---

## 📌 真相源引用（Truth Source References）

本文档基于以下代码和文档生成，所有模型定义均来自实际代码实现：

| 文件路径 | 说明 | 用途 |
|---------|------|------|
| `docs/core/DATA_SCHEMA.md` | 数据表结构 SoT | 定义了所有表的字段、约束、索引 |
| `backend/models/` | SQLAlchemy 模型目录 | 包含所有 ORM 模型定义 |
| `backend/models/README.md` | 模型使用指南 | 提供 CRUD 示例和最佳实践 |
| `backend/models/__init__.py` | 模型统一导出 | 定义了公共 API 和导出清单 |
| `backend/models/base.py` | 基类和 Mixin | 提供 Base、Mixin、Enum 定义 |
| `backend/scripts/init_db_schema.py` | 数据库初始化脚本 | v2.3 数据库表创建脚本 |

---

## 1. 模型组织架构

### 1.1 重构说明

**重构版本**: v2.0 (2025-11-19)

**重构目标**：
- ✅ 按业务域拆分模型文件（core, accounts, workflow, finance, audit）
- ✅ 添加完整的 `relationship` 关系定义
- ✅ 引入 Python Enum 类型支持
- ✅ 抽取通用 Mixin（TimestampMixin, UserScopeMixin, RLSAwareMixin）
- ✅ 提供统一的导出接口（`from backend.models import X`）

**废弃说明**：
- ⚠️ `database_models.py` - 向后兼容层，已标记为 DEPRECATED
- ⚠️ 旧版单文件模型（`projects.py`, `users.py`, `channels.py`, `ad_accounts.py`等）- 保留作为兼容层

### 1.2 目录结构

```
backend/models/
├── __init__.py                 # 统一导出接口（推荐使用）
├── base.py                     # Base 类、Mixin、Enum 定义
├── enums.py                    # 业务枚举类型（供模型引用）
│
├── core/                       # 核心业务模型
│   ├── __init__.py
│   ├── user.py                 # User 用户模型
│   ├── channel.py              # Channel, ChannelReview, ChannelPerformance 渠道模型
│   ├── project.py              # Project 项目模型
│   └── project_member.py       # ProjectMember 项目成员模型
│
├── accounts/                   # 账户管理模块
│   ├── __init__.py
│   ├── ad_account.py           # AdAccount 广告账户模型
│   ├── account_history.py      # AccountStatusHistory, AccountAlert 账户历史和预警
│   └── account_request.py      # ChannelAccountRequest 开户申请模型
│
├── workflow/                   # 工作流模块
│   ├── __init__.py
│   ├── daily_report.py         # DailyReport 日报模型
│   ├── ad_spend.py             # AdSpendDaily 外部导入消耗数据
│   └── topup_request.py        # TopupRequest 充值申请模型
│
├── finance/                    # 财务模块
│   ├── __init__.py
│   ├── ledger.py               # LedgerEntry 账本分录模型
│   └── reconciliation.py       # ReconciliationBatch, ReconciliationDetail 对账模型
│
├── audit/                      # 审计模块
│   ├── __init__.py
│   └── audit_log.py            # AuditLog 审计日志模型
│
├── mixins/                     # Mixin 工具类
│   ├── __init__.py
│   ├── rls_aware.py            # RLSAwareMixin RLS 权限过滤
│   └── serializable.py         # SerializableMixin 序列化支持
│
├── [legacy files]              # 向后兼容文件
│   ├── database_models.py      # ⚠️ DEPRECATED 统一模型文件（过渡期）
│   ├── user_profile.py         # ⚠️ 旧版用户模型
│   ├── ledger.py               # ⚠️ 旧版账本模型
│   ├── topup.py                # TopupTransaction, TopupApprovalLog（辅助表）
│   ├── topup_fixed.py          # ⚠️ 修复版（临时）
│   ├── reconciliation.py       # ⚠️ 旧版对账模型
│   ├── reconciliation_extended.py  # ⚠️ 扩展版（临时）
│   ├── projects_fixed.py       # ProjectExpense（临时）
│   ├── notifications.py        # Notification 通知模型（未使用）
│   ├── ai_monitoring.py        # AI 监控模型（扩展模块）
│   └── log.py                  # Log 通用日志模型
│
└── README.md                   # 模型使用指南
```

---

## 2. 模型清单

### 2.1 核心模型（8个）

#### 👤 用户与权限

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `User` | `core/user.py` | `users` | UUID | 业务用户表（与 Supabase Auth 同步） |

**关系**：
- 一对多：User → Project（创建的项目）
- 一对多：User → AdAccount（负责的账户）
- 一对多：User → DailyReport（提交的日报）
- 一对多：User → TopupRequest（申请的充值）

#### 🏢 项目管理

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `Project` | `core/project.py` | `projects` | BIGSERIAL | 项目主表 |
| `ProjectMember` | `core/project_member.py` | `project_members` | BIGSERIAL | 项目成员关系表 |
| `ProjectExpense` | `projects_fixed.py` | `project_expenses` | BIGSERIAL | 项目费用记录 |

**关系**：
- Project ↔ User（多对一：创建者）
- Project ↔ AdAccount（一对多：项目下的账户）
- Project ↔ ProjectMember（一对多：项目成员）
- ProjectMember ↔ User（多对一：成员用户）

#### 📡 渠道管理

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `Channel` | `core/channel.py` | `channels` | UUID | 渠道主数据 |
| `ChannelReview` | `core/channel.py` | `channel_reviews` | UUID | 渠道评审记录 |
| `ChannelPerformance` | `core/channel.py` | `channel_performance` | UUID | 渠道表现统计 |
| `ChannelAccountRequest` | `accounts/account_request.py` | `channel_account_requests` | UUID | 渠道开户申请 |

**关系**：
- Channel ↔ AdAccount（一对多：渠道下的账户）
- Channel ↔ ChannelReview（一对多：评审记录）
- ChannelAccountRequest ↔ Channel（多对一：申请的渠道）

### 2.2 业务流程模型（5个）

#### 💳 账户管理

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `AdAccount` | `accounts/ad_account.py` | `ad_accounts` | BIGSERIAL | 广告账户（核心） |
| `AccountStatusHistory` | `accounts/account_history.py` | `account_status_history` | BIGSERIAL | 账户状态流水 |
| `AccountAlert` | `accounts/account_history.py` | `account_alerts` | BIGSERIAL | 账户预警 |

**关系**：
- AdAccount ↔ Project（多对一：所属项目）
- AdAccount ↔ Channel（多对一：所属渠道）
- AdAccount ↔ User（多对一：负责人 owner_id）
- AdAccount ↔ DailyReport（一对多：账户日报）
- AdAccount ↔ AccountStatusHistory（一对多：状态历史）
- AdAccount ↔ AccountAlert（一对多：账户预警）

#### 📊 日报与消耗

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `DailyReport` | `workflow/daily_report.py` | `daily_reports` | BIGSERIAL | 投手每日报告 |
| `AdSpendDaily` | `workflow/ad_spend.py` | `ad_spend_daily` | UUID | 外部导入日消耗数据 |

**关系**：
- DailyReport ↔ AdAccount（多对一：所属账户）
- DailyReport ↔ User（多对一：创建者、审核者）
- AdSpendDaily ↔ AdAccount（通过 `ad_account_code` 关联）

#### 💰 充值与流程

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `TopupRequest` | `workflow/topup_request.py` | `topup_requests` | BIGSERIAL | 充值申请 |
| `TopupTransaction` | `topup.py` | `topup_transactions` | BIGSERIAL | 充值到账流水 |
| `TopupApprovalLog` | `topup.py` | `topup_approval_logs` | BIGSERIAL | 充值审批记录 |

**关系**：
- TopupRequest ↔ Project（多对一：所属项目）
- TopupRequest ↔ AdAccount（多对一：目标账户，可空）
- TopupRequest ↔ User（多对一：申请人）
- TopupRequest ↔ TopupTransaction（一对多：到账流水）
- TopupRequest ↔ TopupApprovalLog（一对多：审批记录）

### 2.3 财务模块（3个）

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `LedgerEntry` | `finance/ledger.py` | `ledger_entries` | BIGSERIAL | 资金总账分录 |
| `ReconciliationBatch` | `finance/reconciliation.py` | `reconciliation_batches` | BIGSERIAL | 对账批次 |
| `ReconciliationDetail` | `finance/reconciliation.py` | `reconciliation_details` | BIGSERIAL | 对账明细 |

**关系**：
- LedgerEntry ↔ Project（多对一：所属项目）
- LedgerEntry ↔ AdAccount（多对一：所属账户）
- ReconciliationBatch ↔ Project（多对一：对账项目）
- ReconciliationDetail ↔ ReconciliationBatch（多对一：所属批次）
- ReconciliationDetail ↔ AdAccount（多对一：对账账户）

### 2.4 审计与日志（2个）

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `AuditLog` | `audit/audit_log.py` | `audit_logs` | BIGSERIAL | 系统审计日志 |
| `Log` | `log.py` | `logs` | BIGSERIAL | 通用业务日志 |

**关系**：
- AuditLog ↔ User（多对一：操作者）
- Log ↔ User（多对一：创建者）

### 2.5 扩展模块（2个）

| 模型类 | 文件路径 | 表名 | 主键类型 | 说明 |
|--------|---------|------|---------|------|
| `AIMonitoring` | `ai_monitoring.py` | `ai_monitoring` | BIGSERIAL | AI 监控记录（扩展） |
| `Notification` | `notifications.py` | `notifications` | BIGSERIAL | 通知记录（未使用） |

---

## 3. 基础设施组件

### 3.1 Base 类和 Mixin

**文件**: `backend/models/base.py`

#### Base 类

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

所有模型必须继承 `Base`。

#### Mixin 列表

| Mixin 类 | 提供字段/方法 | 说明 |
|----------|--------------|------|
| `TimestampMixin` | `created_at`, `updated_at` | 自动时间戳管理 |
| `CreatedAtMixin` | `created_at` | 仅创建时间（不可变记录） |
| `SoftDeleteMixin` | `is_deleted`, `deleted_at` | 软删除支持（未来） |
| `UserScopeMixin` | `created_by`, `query_for_user()` | 用户作用域（RLS 支持） |
| `AssignableMixin` | `assigned_to`, `query_assigned_to_user()` | 可分配作用域（RLS 支持） |

**使用示例**：

```python
from backend.models.base import Base, TimestampMixin, UserScopeMixin

class MyModel(Base, TimestampMixin, UserScopeMixin):
    __tablename__ = 'my_table'
    # ... 字段定义
```

#### RLS 相关 Mixin

**文件**: `backend/models/mixins/rls_aware.py`

| Mixin 类 | 提供方法 | 说明 |
|----------|---------|------|
| `RLSAwareMixin` | `apply_rls_filter()`, `get_for_user()`, `is_accessible_by()`, `is_modifiable_by()` | RLS 权限过滤接口 |

**使用示例**：

```python
from backend.models.base import Base
from backend.models.mixins.rls_aware import RLSAwareMixin

class Project(Base, RLSAwareMixin):
    __tablename__ = 'projects'
    __rls_user_field__ = 'created_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_OPERATOR]
```

详细用法参见 `docs/security/RLS_POLICIES.md`。

### 3.2 Enum 枚举类型

**文件**: `backend/models/enums.py` 和 `backend/models/base.py`

| Enum 类 | 说明 | 合法值 |
|---------|------|--------|
| `UserRole` | 用户角色 | `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer` |
| `ProjectStatus` | 项目状态 | `draft`, `active`, `suspended`, `archived` |
| `AdAccountStatus` | 账户状态 | `new`, `testing`, `active`, `suspended`, `dead`, `archived` |
| `DailyReportStatus` | 日报状态 | `draft`, `pending`, `approved`, `rejected` |
| `TopupStatus` | 充值状态 | `draft`, `pending_review`, `finance_approve`, `paid`, `completed`, `rejected`, `cancelled` |
| `ChannelStatus` | 渠道状态 | `active`, `inactive` |
| `ReviewStatus` | 评审状态 | `draft`, `pending`, `approved`, `rejected` |
| `LedgerEntryType` | 账本分录类型 | `topup_received`, `spend`, `adjustment` |
| `ReconciliationBatchStatus` | 对账批次状态 | `draft`, `pending`, `reviewing`, `closed` |
| `ReconciliationDetailStatus` | 对账明细状态 | `pending`, `confirmed`, `adjusted` |
| `AccountAlertStatus` | 预警状态 | `open`, `ack`, `resolved` |
| `AccountAlertSeverity` | 预警严重性 | `low`, `medium`, `high`, `critical` |

**使用示例**：

```python
from backend.models import Project, ProjectStatus

project = Project(
    project_name="测试项目",
    status=ProjectStatus.DRAFT.value  # 使用枚举的 .value
)

# 类型安全检查
if project.status == ProjectStatus.ACTIVE.value:
    print("项目已激活")
```

**注意**：
- 所有状态枚举值必须与 `docs/core/STATE_MACHINE.md` 定义一致
- 数据库表中有相应的 CHECK 约束强制枚举值有效性

---

## 4. 模型导入指南

### 4.1 推荐导入方式

```python
# ✅ 推荐：从 backend.models 导入
from backend.models import (
    Base,
    User,
    Project,
    AdAccount,
    DailyReport,
    TopupRequest,
    LedgerEntry,
    ProjectStatus,
    UserRole,
)

# ✅ 推荐：按需导入 Mixin
from backend.models import TimestampMixin, UserScopeMixin
```

### 4.2 不推荐的导入方式

```python
# ❌ 不推荐：从 database_models 导入（已废弃）
from backend.models.database_models import User, Project

# ⚠️ 过渡期可用：从具体文件导入
from backend.models.core.user import User
from backend.models.core.project import Project
```

### 4.3 导入 Base 类

```python
# ✅ 推荐
from backend.models import Base

# ✅ 也可以
from backend.models.base import Base
```

### 4.4 导入所有模型（用于类型提示）

```python
from backend.models import *  # 包含 __all__ 定义的所有模型

# 或者明确导入
from backend.models import (
    # 核心模型
    User, Channel, Project, ProjectMember,
    # 账户模型
    AdAccount, AccountStatusHistory, AccountAlert,
    # 业务流程
    DailyReport, TopupRequest, AdSpendDaily,
    # 财务模型
    LedgerEntry, ReconciliationBatch, ReconciliationDetail,
    # 审计日志
    AuditLog, Log,
    # Enum
    UserRole, ProjectStatus, AdAccountStatus,
)
```

---

## 5. 模型关系图

### 5.1 核心关系链路

```
User ──┬─→ Project ──→ AdAccount ──┬─→ DailyReport
       │                           │
       │                           ├─→ TopupRequest
       │                           │
       │                           └─→ LedgerEntry
       │
       ├─→ AdAccount (owner_id)
       │
       ├─→ DailyReport (created_by)
       │
       └─→ TopupRequest (applicant_id)

Channel ──→ AdAccount

Project ──┬─→ ProjectMember
          │
          ├─→ ProjectExpense
          │
          └─→ TopupRequest
```

### 5.2 财务关系链路

```
TopupRequest ──┬─→ TopupTransaction
               │
               └─→ TopupApprovalLog

Project ──→ LedgerEntry ←── AdAccount

Project ──→ ReconciliationBatch ──→ ReconciliationDetail ←── AdAccount
```

### 5.3 审计关系链路

```
User ──┬─→ AuditLog
       │
       └─→ Log

AdAccount ──┬─→ AccountStatusHistory
            │
            └─→ AccountAlert
```

---

## 6. 模型使用最佳实践

### 6.1 创建模型实例

```python
from backend.models import Project, ProjectStatus, AdAccount
from uuid import UUID

# ✅ 推荐：使用 Enum
project = Project(
    project_name="示例项目",
    project_code="PROJ001",
    client_name="示例客户",
    status=ProjectStatus.DRAFT.value,
    created_by=UUID("user-uuid-here")
)

# ✅ 推荐：利用 Mixin 自动填充字段
# TimestampMixin 会自动设置 created_at 和 updated_at
# UserScopeMixin 的 created_by 在创建时手动指定

db.add(project)
db.commit()
```

### 6.2 查询模型（应用 RLS）

```python
from backend.models import Project, User
from uuid import UUID

current_user_id = UUID("user-uuid-here")
current_user_role = "media_buyer"

# ✅ 推荐：使用 RLS 查询方法
projects = Project.get_user_accessible_query(
    db, current_user_id, current_user_role
).all()

# ✅ 推荐：使用 Mixin 提供的方法
projects = Project.query_for_user(db, current_user_id).all()

# ❌ 不推荐：直接查询（绕过 RLS）
projects = db.query(Project).all()  # 危险：未应用权限过滤
```

### 6.3 更新模型（检查权限）

```python
from backend.models import Project

project = db.query(Project).filter(Project.id == project_id).first()

# ✅ 推荐：检查权限
if not project.can_be_edited_by(current_user.id, current_user.role):
    raise PermissionDeniedError("无权限编辑该项目")

project.project_name = "新名称"
project.updated_by = current_user.id  # 手动设置更新者
db.commit()

# TimestampMixin 会自动更新 updated_at
```

### 6.4 关联查询（使用 relationship）

```python
from backend.models import Project
from sqlalchemy.orm import joinedload

# ✅ 推荐：使用 joinedload 避免 N+1 查询
project = db.query(Project).options(
    joinedload(Project.ad_accounts),  # 预加载账户
    joinedload(Project.creator)        # 预加载创建者
).filter(Project.id == project_id).first()

# 访问关联对象
for account in project.ad_accounts:
    print(account.name)

print(f"项目创建者：{project.creator.username}")
```

### 6.5 状态流转（使用状态机）

```python
from backend.models import Project, ProjectStatus

project = db.query(Project).filter(Project.id == project_id).first()

# ✅ 推荐：使用模型提供的状态流转方法
if project.can_transition_to(ProjectStatus.ACTIVE):
    project.transition_to(
        new_status=ProjectStatus.ACTIVE,
        operator_id=current_user.id,
        reason="项目准备就绪"
    )
    db.commit()
else:
    raise BusinessLogicError("不允许的状态转换")

# ❌ 不推荐：直接修改状态
project.status = ProjectStatus.ACTIVE.value  # 绕过状态机验证
```

### 6.6 批量操作

```python
from backend.models import AdAccount
from sqlalchemy import and_

# ✅ 推荐：批量更新（应用 RLS）
accounts = AdAccount.get_for_user(
    db, current_user.id, current_user.role
).filter(
    and_(
        AdAccount.project_id == project_id,
        AdAccount.status == 'testing'
    )
).all()

for account in accounts:
    account.status = 'active'
    account.updated_by = current_user.id

db.commit()

# ⚠️ 慎用：bulk_update（绕过 ORM 逻辑）
# 使用 bulk 操作会绕过 Mixin 的自动时间戳更新
```

---

## 7. 常见问题与陷阱

### 7.1 主键类型不一致

**问题**：外键字段类型与被引用主键类型不一致

```python
# ❌ 错误示例
class Project(Base):
    id = Column(BigInteger, primary_key=True)  # BIGSERIAL

class AdAccount(Base):
    project_id = Column(Integer, ForeignKey('projects.id'))  # ❌ 类型不匹配

# ✅ 正确示例
class AdAccount(Base):
    project_id = Column(BigInteger, ForeignKey('projects.id'))  # ✅ 类型一致
```

**规则**：
- User 表主键：UUID
- 业务表主键：BigInteger (BIGSERIAL)
- 外键必须与被引用主键类型完全一致

### 7.2 忘记应用 RLS 过滤

**问题**：直接查询未应用权限过滤

```python
# ❌ 危险：绕过 RLS
def get_all_projects():
    return db.query(Project).all()  # 返回所有项目，包括用户无权访问的

# ✅ 安全：应用 RLS
def get_user_projects(current_user: User):
    return Project.get_user_accessible_query(
        db, current_user.id, current_user.role
    ).all()
```

详见 `docs/security/RLS_POLICIES.md` 第9节"安全最佳实践"。

### 7.3 关联查询 N+1 问题

**问题**：未使用预加载导致 N+1 查询

```python
# ❌ N+1 查询问题
projects = db.query(Project).all()
for project in projects:
    print(project.creator.username)  # 每次访问触发一次查询

# ✅ 使用 joinedload 预加载
from sqlalchemy.orm import joinedload

projects = db.query(Project).options(
    joinedload(Project.creator)
).all()
for project in projects:
    print(project.creator.username)  # 不触发额外查询
```

### 7.4 时区处理不当

**问题**：未使用 TIMESTAMPTZ 或时区混乱

```python
# ❌ 不推荐：使用 DateTime(timezone=False)
created_at = Column(DateTime)  # 不带时区

# ✅ 推荐：使用 DateTime(timezone=True)
created_at = Column(DateTime(timezone=True), server_default=func.now())

# 应用层使用 UTC 时间
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 7.5 状态枚举值硬编码

**问题**：使用字符串字面量代替 Enum

```python
# ❌ 不推荐：硬编码字符串
project.status = "active"  # 容易拼写错误

# ✅ 推荐：使用 Enum
from backend.models import ProjectStatus
project.status = ProjectStatus.ACTIVE.value  # 类型安全
```

### 7.6 未处理级联删除

**问题**：删除父记录时未考虑子记录

```python
# ⚠️ 注意：删除 Project 会级联删除所有 AdAccount
project = db.query(Project).filter(Project.id == project_id).first()
db.delete(project)  # CASCADE: 删除所有关联的 ad_accounts
db.commit()

# ✅ 推荐：先检查是否有关联数据
if len(project.ad_accounts) > 0:
    raise BusinessLogicError("项目下还有广告账户，无法删除")
db.delete(project)
db.commit()
```

**级联删除规则**（详见 DATA_SCHEMA.md 第4节）：
- `CASCADE`：自动删除子记录
- `RESTRICT`：禁止删除有关联的父记录
- `SET NULL`：将外键设置为 NULL

---

## 8. 数据迁移与版本管理

### 8.1 Alembic 迁移

**位置**：`backend/alembic/versions/`

**当前策略**：
- 使用 Alembic 管理数据库 Schema 变更
- 迁移脚本按日期和主题命名（如 `20251119_add_user_scope_foreign_keys.py`）
- 每次模型变更后必须生成迁移脚本

**生成迁移**：

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "Add user_id foreign key to projects"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 8.2 模型版本对应关系

| 模型版本 | DATA_SCHEMA 版本 | 数据库脚本版本 | 说明 |
|---------|----------------|---------------|------|
| v2.0 | v5.0 | init_db_schema.py v2.3 | 当前版本（2025-11-19） |
| v1.x | v4.x | legacy scripts | 旧版本（已废弃） |

### 8.3 Schema 变更流程

1. **修改模型定义**（`backend/models/`)
2. **更新 DATA_SCHEMA.md**（`docs/core/DATA_SCHEMA.md`）
3. **生成 Alembic 迁移脚本**
4. **执行迁移并测试**
5. **更新本 MODEL_INDEX.md**

---

## 9. 性能优化建议

### 9.1 索引使用

**已定义的索引**（参考 DATA_SCHEMA.md）：

- `users`：`username`, `role`, `account_manager_id`, `created_at`, `last_login_at`
- `projects`：`project_code` (UNIQUE), `status`, `created_by`
- `ad_accounts`：`account_code` (UNIQUE), `project_id`, `channel_id`, `status`, `owner_id`
- `daily_reports`：`(report_date, ad_account_id)` (UNIQUE), `ad_account_id`, `status`, `created_by`
- `topup_requests`：`request_no` (UNIQUE), `project_id`, `status`, `applicant_id`

### 9.2 查询优化

```python
# ✅ 使用 selectinload 加载一对多关系
from sqlalchemy.orm import selectinload

project = db.query(Project).options(
    selectinload(Project.ad_accounts)  # 一次性加载所有账户
).filter(Project.id == project_id).first()

# ✅ 使用 joinedload 加载多对一关系
account = db.query(AdAccount).options(
    joinedload(AdAccount.project),
    joinedload(AdAccount.channel)
).filter(AdAccount.id == account_id).first()

# ✅ 使用 defer 延迟加载大字段
from sqlalchemy.orm import defer

accounts = db.query(AdAccount).options(
    defer(AdAccount.notes),  # 延迟加载 notes 字段
    defer(AdAccount.metadata)
).all()
```

### 9.3 批量操作优化

```python
# ✅ 推荐：使用 bulk_insert_mappings
data = [
    {"project_name": "项目1", "project_code": "P001", "status": "draft"},
    {"project_name": "项目2", "project_code": "P002", "status": "draft"},
]
db.bulk_insert_mappings(Project, data)
db.commit()

# ⚠️ 注意：bulk 操作绕过 ORM 事件和 Mixin 逻辑
# 需要手动处理 created_at, updated_at 等字段
```

### 9.4 连接池配置

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 连接池大小
    max_overflow=10,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接前测试可用性
    pool_recycle=3600,     # 连接回收时间（秒）
)
```

---

## 10. 附录

### 10.1 相关文档

- [数据模型 SoT](../core/DATA_SCHEMA.md) - 表结构和字段定义
- [状态机 SoT](../core/STATE_MACHINE.md) - 业务状态流转规则
- [RLS 策略 SoT](../security/RLS_POLICIES.md) - 权限控制实现
- [模型使用指南](../../backend/models/README.md) - CRUD 示例和最佳实践
- [SQLAlchemy 优化指南](../development/SQLALCHEMY_OPTIMIZATION_GUIDE.md) - 性能优化技巧

### 10.2 模型统计

| 分类 | 模型数量 | 文件数量 |
|------|---------|---------|
| 核心模型（user, project, channel） | 8 | 4 |
| 账户管理（ad_account, history, alert） | 4 | 3 |
| 业务流程（report, spend, topup） | 6 | 4 |
| 财务模块（ledger, reconciliation） | 3 | 2 |
| 审计日志（audit, log） | 2 | 2 |
| 扩展模块（ai, notification） | 2 | 2 |
| **总计** | **25** | **17** |

### 10.3 模型覆盖率

| 表名（DATA_SCHEMA.md） | 模型类 | 实现状态 |
|-----------------------|--------|---------|
| `users` | `User` | ✅ implemented |
| `projects` | `Project` | ✅ implemented |
| `project_members` | `ProjectMember` | ✅ implemented |
| `project_expenses` | `ProjectExpense` | ✅ implemented |
| `channels` | `Channel` | ✅ implemented |
| `channel_reviews` | `ChannelReview` | ✅ implemented |
| `channel_performance` | `ChannelPerformance` | ✅ implemented |
| `channel_account_requests` | `ChannelAccountRequest` | ✅ implemented |
| `ad_accounts` | `AdAccount` | ✅ implemented |
| `account_status_history` | `AccountStatusHistory` | ✅ implemented |
| `account_alerts` | `AccountAlert` | ✅ implemented |
| `daily_reports` | `DailyReport` | ✅ implemented |
| `ad_spend_daily` | `AdSpendDaily` | ✅ implemented |
| `topup_requests` | `TopupRequest` | ✅ implemented |
| `topup_transactions` | `TopupTransaction` | ✅ implemented |
| `topup_approval_logs` | `TopupApprovalLog` | ✅ implemented |
| `ledger_entries` | `LedgerEntry` | ✅ implemented |
| `reconciliation_batches` | `ReconciliationBatch` | ✅ implemented |
| `reconciliation_details` | `ReconciliationDetail` | ✅ implemented |
| `audit_logs` | `AuditLog` | ✅ implemented |
| **覆盖率** | **20/20** | **100%** |

### 10.4 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v2.0 | 2025-01-19 | 按业务域重构模型目录；添加完整文档 | Claude |
| v1.0 | 2025-11-17 | 初始版本（database_models.py 单文件） | 系统架构团队 |

---

**文档维护者**: 后端开发团队
**最后审核**: 2025-01-19
**下次审核**: 季度性审核或模型结构重大变更时
