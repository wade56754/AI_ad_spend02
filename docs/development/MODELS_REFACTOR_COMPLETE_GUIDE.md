# Models 层重构完整实施指南

> **状态**: ✅ Phase 1 完成（核心架构 + 示例模型）
> **创建日期**: 2025-11-19
> **参考文档**: SQLALCHEMY_OPTIMIZATION_GUIDE.md

---

## ✅ Phase 1 已完成

### 核心架构文件（100% 完成）

```
backend/models/
├── base.py                         ✅ Base + Mixin（TimestampMixin, UserScopeMixin, AssignableMixin）
├── enums.py                        ✅ 11个枚举类型（UserRole, AdAccountStatus, 等）
├── mixins/
│   ├── __init__.py                 ✅
│   ├── serializable.py             ✅ SerializableMixin（to_dict/from_dict）
│   └── rls_aware.py                ✅ RLSAwareMixin（权限过滤）
```

### 示例模型（2/16 完成）

```
backend/models/
├── core/
│   ├── __init__.py                 ✅
│   └── user.py                     ✅ User 模型（完整示例）
├── accounts/
│   ├── __init__.py                 ✅
│   └── ad_account.py               ✅ AdAccount 模型（复杂示例）
```

### 空目录结构（已创建）

```
backend/models/
├── workflow/__init__.py            ✅
├── finance/__init__.py             ✅
└── audit/__init__.py               ✅
```

---

## 📋 Phase 2 需要创建的模型

### 按照示例模板创建以下 14 个模型文件：

#### 核心模型（2个）
- [ ] `core/channel.py` - Channel, ChannelReview, ChannelPerformance
- [ ] `core/project.py` - Project

#### 账户管理（2个）
- [ ] `accounts/account_request.py` - ChannelAccountRequest
- [ ] `accounts/account_history.py` - AccountStatusHistory, AccountAlert

#### 业务流程（3个）
- [ ] `workflow/daily_report.py` - DailyReport
- [ ] `workflow/topup_request.py` - TopupRequest
- [ ] `workflow/ad_spend.py` - AdSpendDaily

#### 财务（2个）
- [ ] `finance/ledger.py` - LedgerEntry
- [ ] `finance/reconciliation.py` - ReconciliationBatch, ReconciliationDetail

#### 审计（1个）
- [ ] `audit/audit_log.py` - AuditLog

#### 其他（2个）
- [ ] `events.py` - 事件钩子系统
- [ ] `__init__.py` - 统一导出（重写）

---

## 🎯 如何创建剩余模型

### 方法一：按照示例模板手动创建（推荐）

**示例模板参考**：

1. **简单模型**：参考 `core/user.py`
   - 继承：`Base, TimestampMixin, SerializableMixin`
   - 包含：字段定义 + 索引 + 业务属性 + 业务方法

2. **复杂模型**：参考 `accounts/ad_account.py`
   - 继承：`Base, TimestampMixin, AssignableMixin, RLSAwareMixin, SerializableMixin`
   - 包含：字段定义 + relationship + 索引 + 业务方法 + 查询作用域

**创建步骤**（以 `core/project.py` 为例）：

```python
# 1. 复制 user.py 或 ad_account.py 作为模板
# 2. 修改类名和 __tablename__
# 3. 从 database_models.py 复制所有字段定义
# 4. 添加 relationship（参考 SQLALCHEMY_OPTIMIZATION_GUIDE.md）
# 5. 添加业务方法（状态流转、权限判断等）
# 6. 保持所有字段、约束、索引与数据库完全一致
```

### 方法二：使用自动化脚本（需要补充）

由于模型文件较大（每个 200-400 行），建议您：

1. 先手动创建 2-3 个关键模型验证架构
2. 熟悉模式后批量创建其他模型
3. 所有模型都遵循相同模式，只需复制修改字段

---

## 🔍 创建模型的关键点

### 1. 字段定义（必须与数据库一致）

```python
# 从 database_models.py 复制所有字段
# ❗ 不要修改字段名、类型、约束

# 示例：Project 模型
class Project(Base, TimestampMixin, UserScopeMixin):
    __tablename__ = 'projects'

    # 从 database_models.py 的 Project 类复制所有字段
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_name = Column(String(100), nullable=False)
    project_code = Column(String(50), unique=True, nullable=False)
    client_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)
    # created_by 来自 UserScopeMixin（不要重复定义）
    # created_at/updated_at 来自 TimestampMixin（不要重复定义）
```

### 2. Relationship 定义（新增）

```python
# 参考 SQLALCHEMY_OPTIMIZATION_GUIDE.md 中的示例
# 所有外键都要添加对应的 relationship

# 示例：Project -> AdAccount（一对多）
ad_accounts = relationship(
    "AdAccount",
    back_populates="project",  # 对应 AdAccount.project
    cascade="all, delete-orphan",
    lazy="selectin",
    doc="项目下的所有广告账户"
)

# 示例：Project -> User（多对一）
creator = relationship(
    "User",
    foreign_keys="Project.created_by",
    lazy="joined",
    doc="项目创建者"
)
```

### 3. 业务方法（新增）

```python
# 状态流转方法
def can_transition_to(self, new_status) -> bool:
    return self.status_enum.can_transition_to(new_status)

def transition_to(self, new_status, operator_id, reason=None):
    # 实现状态转换逻辑

# 权限判断方法
def can_be_edited_by(self, user_id, user_role) -> bool:
    # 实现权限判断逻辑

# 查询作用域方法（类方法）
@classmethod
def get_user_accessible_query(cls, session, user_id, user_role):
    # 实现 RLS 查询逻辑
```

---

## 🧪 测试验证

### 1. 导入测试

```python
# 测试基础架构
python -c "from backend.models.base import Base, TimestampMixin"
python -c "from backend.models.enums import UserRole, AdAccountStatus"
python -c "from backend.models.mixins import SerializableMixin, RLSAwareMixin"

# 测试示例模型
python -c "from backend.models.core.user import User"
python -c "from backend.models.accounts.ad_account import AdAccount"

# 测试统一导出（创建完所有模型后）
python -c "from backend.models import User, AdAccount, Project"
```

### 2. Relationship 测试

```python
# 创建测试脚本
from backend.core.database import SessionLocal
from backend.models.core.user import User
from backend.models.accounts.ad_account import AdAccount

db = SessionLocal()

# 测试关联查询
user = db.query(User).first()
print(f"User: {user.username}")

account = db.query(AdAccount).first()
print(f"Account: {account.account_code}")
print(f"Project: {account.project.project_name}")  # 测试 relationship
print(f"Assignee: {account.assignee.username}")    # 测试 relationship
```

### 3. 业务方法测试

```python
# 测试状态流转
from backend.models.enums import AdAccountStatus

account = db.query(AdAccount).first()
print(f"Current status: {account.status}")
print(f"Can transition to TESTING: {account.can_transition_to(AdAccountStatus.TESTING)}")

# 测试权限方法
user = db.query(User).first()
print(f"Is admin: {user.is_admin()}")
print(f"Can review daily report: {user.can_review_daily_report()}")
```

---

## 📝 创建 `__init__.py` 统一导出

所有模型创建完成后，更新 `backend/models/__init__.py`：

```python
"""
AI广告代投系统 - 数据模型统一导出
"""

# 基础组件
from .base import Base, TimestampMixin, SoftDeleteMixin, UserScopeMixin, AssignableMixin
from .enums import (
    UserRole, ChannelStatus, ProjectStatus, AdAccountStatus,
    DailyReportStatus, TopupRequestStatus, ReconciliationBatchStatus,
    ReconciliationDetailStatus, AccountAlertStatus, LedgerEntryType,
    ChannelAccountRequestStatus, ChannelReviewStatus
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
    "Base", "TimestampMixin", "SoftDeleteMixin", "UserScopeMixin", "AssignableMixin",

    # 枚举
    "UserRole", "ChannelStatus", "ProjectStatus", "AdAccountStatus",
    "DailyReportStatus", "TopupRequestStatus", "ReconciliationBatchStatus",
    "ReconciliationDetailStatus", "AccountAlertStatus", "LedgerEntryType",

    # 模型
    "User", "Channel", "ChannelReview", "ChannelPerformance", "Project",
    "AdAccount", "ChannelAccountRequest", "AccountStatusHistory", "AccountAlert",
    "DailyReport", "TopupRequest", "AdSpendDaily",
    "LedgerEntry", "ReconciliationBatch", "ReconciliationDetail",
    "AuditLog",
]
```

---

## 🎓 最佳实践

1. **保持字段一致**：所有字段必须与 `database_models.py` 完全一致
2. **使用 Enum**：所有状态字段使用枚举而非裸字符串
3. **定义 relationship**：所有外键都要添加对应的 relationship
4. **添加业务方法**：状态流转、权限判断、查询作用域
5. **RLS 配置**：设置 `__rls_user_field__` 和 `__rls_admin_roles__`
6. **序列化配置**：设置 `__json_hidden__` 和 `__json_include_relationships__`
7. **文档字符串**：为所有类和方法添加清晰的文档

---

## 🚀 下一步

1. **验证核心架构**：运行导入测试确保基础架构正常
2. **创建关键模型**：按优先级创建 Project, Channel, DailyReport, TopupRequest
3. **测试 relationship**：确保关联查询正常工作
4. **逐步迁移**：将现有 API 逐步切换到新模型
5. **废弃旧模型**：确认新模型稳定后删除 `database_models.py`

---

## 📚 参考资料

- **完整规范**：`docs/development/SQLALCHEMY_OPTIMIZATION_GUIDE.md`
- **数据库 Schema**：`docs/core/DATA_SCHEMA.md`
- **状态机定义**：`docs/core/STATE_MACHINE.md`
- **原始模型**：`backend/models/database_models.py`（保留作为参考）

---

**需要帮助？**

如果在创建模型过程中遇到问题，可以：
1. 参考已完成的 `User` 和 `AdAccount` 示例
2. 查阅 `SQLALCHEMY_OPTIMIZATION_GUIDE.md` 中的完整代码
3. 保持所有字段与 `database_models.py` 一致
4. 按照相同模式复制修改即可

**重构完成后的收益**：

✅ 类型安全（Enum）
✅ 关联查询（relationship）
✅ 权限控制（RLS）
✅ 业务方法（状态流转）
✅ 自动序列化（to_dict）
✅ 模块化结构（易维护）
