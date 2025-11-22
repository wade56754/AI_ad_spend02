# 行级安全策略（Row Level Security Policies）

**版本**：v1.1
**最后更新**：2025-11-20
**文档状态**：✅ **当前实现行为的 Implementation SoT**

---

## 文档定位说明

### 与 `docs/core/RLS_POLICIES.md` 的关系

- **本文档（security/RLS_POLICIES.md）**：描述当前生效的**应用层权限实现**
  - 定位：**Implementation SoT**（实现行为的真相源）
  - 描述：实际如何实现权限控制

- **`docs/core/RLS_POLICIES.md`**：描述未来**数据库层 RLS 的规划**
  - 定位：**规划级 SoT**（系统整体真相源的规划部分）
  - 描述：应该如何实现权限控制

### SoT 层级

**重要**：系统整体 SoT 仍以 `docs/core/*` 为根。

- 当规划与实现冲突时，以 `docs/core/*` 为权威来源
- 但当前运行的系统行为以本文档描述为准

**如需修改权限逻辑，以本文档为实现参考**。

---

## 1. RLS 架构概述

### 1.1 当前实现状态

**⚠️ 重要声明**：当前系统 **RLS 未在数据库层启用**，权限控制完全在**应用层实现**。

```yaml
# 当前配置
ENABLE_RLS: false  # 数据库 RLS 功能关闭

# 权限实现层级
应用层权限（已启用）:
  - Router 层: @require_role / @require_permissions 装饰器
  - Service 层: 基于 user_id 和 user_role 的查询过滤
  - ORM 层: RLSAwareMixin 和 UserScopeMixin 提供权限过滤方法

数据库层 RLS（未启用）:
  - PostgreSQL Row Level Security: 关闭
  - Supabase RLS Policies: 未配置
```

### 1.2 设计原则

尽管 RLS 当前未在数据库层启用，系统仍然按照 RLS 设计理念进行架构：

1. **用户作用域隔离**：每个表通过 `created_by` 或 `assigned_to` 字段关联用户
2. **角色分级权限**：5 个用户角色拥有不同的数据访问范围
3. **查询级别过滤**：Service 层所有查询都应用权限过滤逻辑
4. **防御纵深**：即使 RLS 未启用，应用层仍确保数据隔离

### 1.3 为什么当前不启用数据库 RLS？

**技术考量**：
- PostgreSQL RLS 与 SQLAlchemy ORM 集成复杂度较高
- Supabase RLS 策略管理需要额外的维护成本
- 当前应用规模下，应用层权限控制性能和安全性已足够

**未来迁移路径**：
- 系统规模扩大时（如多租户 SaaS 化）
- 需要更强的安全隔离时（如监管合规要求）
- 引入第三方工具直接访问数据库时

将在第 8 节详细说明迁移步骤。

---

## 2. 角色与权限体系

### 2.1 用户角色定义

系统定义 5 个标准用户角色（`backend/core/permissions.py:UserRole`）：

| 角色代码 | 角色名称 | 说明 | 数据访问范围 |
|---------|---------|------|-------------|
| `admin` | 系统管理员 | 全权限 | **所有数据** |
| `finance` | 财务 | 充值审批、财务对账 | 所有项目（只读） + 充值/对账（全权限） |
| `data_operator` | 户管/数据员 | 账户管理、数据审核 | 所有项目（只读） + 账户/日报/充值（全权限） |
| `account_manager` | 项目经理 | 项目管理、团队管理 | **自己管理的项目**及其下属数据 |
| `media_buyer` | 投手 | 账户投放、日报提交 | **自己创建的记录**或**分配给自己的账户** |

**历史兼容说明**：
- 旧角色名 `manager` → 新名称 `account_manager`
- 旧角色名 `data_clerk` → 新名称 `data_operator`
- 历史数据可读，新增逻辑禁止使用旧名

### 2.2 权限维度矩阵

完整权限矩阵定义在 `backend/core/permissions.py:ROLE_PERMISSIONS`，以下为简化版：

| 功能模块 | admin | account_manager | data_operator | finance | media_buyer |
|---------|-------|-----------------|---------------|---------|-------------|
| **用户管理** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **项目管理** | ✅ CRUD | ✅ CRU | 👁️ R | 👁️ R | ❌ |
| **渠道管理** | ✅ CRUD | 👁️ R | ✅ CRUD | ❌ | ❌ |
| **账户管理** | ✅ CRUD | ✅ CRU | ✅ CRUD | 👁️ R | 👁️ R |
| **日报管理** | ✅ CRUD + Audit | 👁️ R | ✅ CRUD + Audit | 👁️ R | ✅ CRU |
| **充值管理** | ✅ CRUD + Approve | 👁️ R | ✅ CRUD | ✅ CRUD + Approve | ✅ CRUD |
| **财务对账** | ✅ CRUD | 👁️ R | ❌ | ✅ CRUD | ❌ |
| **报表查看** | ✅ + Export | ✅ + Export | 👁️ R | ✅ + Export | 👁️ R |
| **AI 监控** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **系统配置** | ✅ | ❌ | ❌ | ❌ | ❌ |

**图例**：
- ✅ = 全权限（CRUD）
- 👁️ = 只读权限（R）
- ❌ = 无权限

---

## 3. 表级 RLS 策略设计

### 3.1 策略分类

系统表按数据访问模式分为 4 类：

#### 类型 A：全局共享表（无 RLS）

**特征**：所有用户可读，管理员/特定角色可写
**表清单**：
- `channels` - 渠道主数据
- `channel_contacts` - 渠道联系人
- `channel_reviews` - 渠道评审记录
- `channel_account_requests` - 渠道开户申请
- `channel_performance` - 渠道表现统计

**RLS 策略设计**（未启用）：
```sql
-- 示例：channels 表
CREATE POLICY "channels_read_all" ON channels FOR SELECT
  USING (true);  -- 所有认证用户可读

CREATE POLICY "channels_write_admin_data_operator" ON channels FOR ALL
  USING (
    (SELECT role FROM users WHERE id = auth.uid())
    IN ('admin', 'data_operator')
  );
```

#### 类型 B：用户作用域表（基于 created_by）

**特征**：用户只能访问自己创建的记录，管理员/特定角色可访问全部
**RLS 字段**：`created_by UUID` （FK → users.id）
**表清单**：
- `projects` - 项目主表
- `project_members` - 项目成员
- `project_expenses` - 项目费用记录
- `daily_reports` - 日报
- `topup_requests` - 充值申请

**RLS 策略设计**（未启用）：
```sql
-- 示例：projects 表
CREATE POLICY "projects_read" ON projects FOR SELECT
  USING (
    created_by = auth.uid()  -- 创建者可读
    OR (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'finance', 'data_operator')  -- 管理员角色可读全部
    OR id IN (
      SELECT project_id FROM project_members WHERE user_id = auth.uid()  -- 项目成员可读
    )
  );

CREATE POLICY "projects_write" ON projects FOR ALL
  USING (
    created_by = auth.uid()  -- 创建者可写
    OR (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'account_manager')
  );
```

**应用层实现**（`backend/models/core/project.py:181-194`）：
```python
@classmethod
def get_user_accessible_query(cls, session, user_id, user_role: UserRole):
    """获取用户可访问的项目查询（RLS 逻辑）"""
    query = session.query(cls)

    # 管理员和数据员可以访问所有项目
    if user_role in [UserRole.ADMIN, UserRole.DATA_MANAGER]:
        return query

    # 投手只能访问自己创建的项目
    if user_role == UserRole.MEDIA_BUYER:
        return query.filter(cls.created_by == user_id)

    # 其他角色默认可以访问自己创建的项目
    return query.filter(cls.created_by == user_id)
```

#### 类型 C：账户分配表（基于 owner_id / assigned_to）

**特征**：用户可以访问分配给自己的账户及其相关数据
**RLS 字段**：`owner_id UUID` 或 `assigned_to UUID`
**表清单**：
- `ad_accounts` - 广告账户（`owner_id`）
- `account_status_history` - 账户状态流水（通过 `ad_account_id` 关联）
- `account_alerts` - 账户预警
- `account_documents` - 账户附件
- `account_notes` - 账户备注

**RLS 策略设计**（未启用）：
```sql
-- 示例：ad_accounts 表
CREATE POLICY "ad_accounts_read" ON ad_accounts FOR SELECT
  USING (
    owner_id = auth.uid()  -- 账户负责人可读
    OR (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'data_operator', 'finance')
    OR project_id IN (
      SELECT id FROM projects WHERE created_by = auth.uid()  -- 项目创建者可读其下所有账户
    )
  );

CREATE POLICY "ad_accounts_write" ON ad_accounts FOR ALL
  USING (
    owner_id = auth.uid()
    OR (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'account_manager', 'data_operator')
  );
```

**应用层实现**（`backend/services/ad_account_service.py`）：
```python
def _apply_rls_filter(self, query, current_user: User):
    """应用 RLS 过滤"""
    if current_user.role in ["admin", "data_operator"]:
        return query  # 管理员和数据员可访问所有账户
    elif current_user.role == "account_manager":
        # 项目经理可访问其管理的项目下的所有账户
        return query.join(Project).filter(Project.account_manager_id == current_user.id)
    elif current_user.role == "media_buyer":
        # 投手只能访问自己负责的账户
        return query.filter(AdAccount.owner_id == current_user.id)
    else:
        return query.filter(AdAccount.owner_id == current_user.id)
```

#### 类型 D：审计日志表（只读，无删改）

**特征**：只允许插入，任何人不得修改或删除
**表清单**：
- `audit_logs` - 系统审计日志
- `user_sessions` - 用户会话记录
- `daily_report_audit_logs` - 日报审计日志
- `topup_approval_logs` - 充值审批日志
- `account_status_history` - 账户状态历史

**RLS 策略设计**（未启用）：
```sql
-- 示例：audit_logs 表
CREATE POLICY "audit_logs_read_admin" ON audit_logs FOR SELECT
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "audit_logs_insert_only" ON audit_logs FOR INSERT
  WITH CHECK (true);  -- 所有认证用户可插入

-- 禁止 UPDATE 和 DELETE
-- （无对应策略，默认拒绝）
```

---

## 4. 核心表 RLS 策略详解

### 4.1 users 表

**字段**：`id UUID (PK, FK → auth.users)`, `role`, `created_by`

**策略设计**：
- **Read**：
  - admin 可读所有用户
  - account_manager 可读所有用户（用于分配项目成员）
  - 其他角色只能读自己
- **Write**：
  - admin 可创建/更新/删除用户
  - 用户可更新自己的 profile 字段（preferences, notification_settings）

**应用层实现位置**：`backend/services/user_service.py`（未提供，需实现）

### 4.2 projects 表

**字段**：`id BIGSERIAL (PK)`, `created_by UUID`, `account_manager_id UUID`

**策略设计**：
- **Read**：
  - admin, finance, data_operator 可读所有项目
  - account_manager 可读 `account_manager_id = self` 的项目
  - media_buyer 可读 `created_by = self` 的项目或作为成员的项目
- **Write**：
  - admin 可 CRUD 所有项目
  - account_manager 可创建项目，可更新 `account_manager_id = self` 的项目

**应用层实现**：见 3.1 节代码示例

### 4.3 ad_accounts 表

**字段**：`id BIGSERIAL (PK)`, `project_id BIGINT`, `owner_id UUID`, `created_by UUID`

**策略设计**：
- **Read**：
  - admin, data_operator 可读所有账户
  - finance 可读所有账户（只读）
  - account_manager 可读其管理项目下的所有账户
  - media_buyer 可读 `owner_id = self` 的账户
- **Write**：
  - admin, data_operator 可 CRUD 所有账户
  - account_manager 可在其管理的项目下创建账户
  - media_buyer 可更新 `owner_id = self` 的账户（部分字段）

**应用层实现**：见 3.1 节代码示例

### 4.4 daily_reports 表

**字段**：`id BIGSERIAL (PK)`, `ad_account_id BIGINT`, `created_by UUID`, `status VARCHAR`

**策略设计**：
- **Read**：
  - admin, data_operator, finance 可读所有日报
  - media_buyer 可读 `created_by = self` 的日报或其负责账户的日报
- **Write**：
  - media_buyer 可创建和更新 `status = draft` 的日报
  - data_operator 可审核（更新 `status` 字段）
  - admin 可 CRUD 所有日报

**特殊权限**：
- **审核权限**：只有 admin 和 data_operator 可以执行审核操作（`DAILY_REPORT_AUDIT` 权限）

**应用层实现**：`backend/services/daily_report_service.py`

### 4.5 topup_requests 表

**字段**：`id BIGSERIAL (PK)`, `project_id BIGINT`, `applicant_id UUID`, `status VARCHAR`

**策略设计**：
- **Read**：
  - admin, finance, data_operator 可读所有充值申请
  - media_buyer 可读 `applicant_id = self` 的申请
- **Write**：
  - media_buyer 可创建申请
  - finance 可审批（更新 `status` 到 `finance_approve`）
  - admin 可 CRUD 所有申请

**状态流转权限**：
- `draft → pending_review`：applicant 本人或 admin
- `pending_review → finance_approve`：finance 或 admin
- `finance_approve → paid → completed`：finance 或 admin
- `* → rejected / cancelled`：finance 或 admin

**应用层实现**：`backend/services/topup_service.py`

### 4.6 ledger_entries 表

**字段**：`id BIGSERIAL (PK)`, `project_id BIGINT`, `created_by UUID`

**策略设计**：
- **Read**：
  - admin, finance 可读所有账本记录
  - data_operator 可读所有记录（只读）
  - account_manager 可读其管理项目的记录
- **Write**：
  - 只有系统自动生成（充值到账、日报审核通过触发）
  - admin 和 finance 可手动创建调整记录

**应用层实现**：`backend/services/ledger_service.py`

### 4.7 reconciliation_* 表

**字段**：各表包含 `project_id BIGINT`, `created_by UUID`

**策略设计**：
- **Read**：
  - admin, finance 可读所有对账记录
  - account_manager 可读其管理项目的对账记录
- **Write**：
  - finance 可创建对账批次
  - admin 和 finance 可更新对账状态

**应用层实现**：`backend/services/reconciliation_service.py`

---

## 5. 应用层权限实现机制

### 5.1 Router 层：装饰器权限检查

**位置**：`backend/routers/*.py`

**实现方式**：

```python
from backend.core.permissions import require_role, require_permissions, admin_required

# 方式 1：角色限制
@router.post("/projects")
@require_role("admin", "account_manager")
async def create_project(...):
    ...

# 方式 2：权限限制（推荐）
from backend.core.permissions import Permission

@router.delete("/projects/{project_id}")
@require_permissions(Permission.PROJECT_DELETE)
async def delete_project(...):
    ...

# 方式 3：便捷装饰器
@router.get("/audit-logs")
@admin_required
async def get_audit_logs(...):
    ...
```

**注意事项**：
- ⚠️ 当前部分路由的 `@require_role` 装饰器被注释掉，权限检查在 Service 层执行
- 推荐在 Router 层进行粗粒度权限检查（如是否登录、角色是否允许）
- 细粒度权限检查（如是否可访问特定资源）应在 Service 层执行

### 5.2 Service 层：查询级别权限过滤

**位置**：`backend/services/*.py`

**核心模式**：

```python
class ProjectService:
    def get_projects(self, current_user: User, filters: dict):
        # 1. 基础查询
        query = self.db.query(Project)

        # 2. 应用 RLS 过滤
        query = self._apply_rls_filter(query, current_user)

        # 3. 应用业务过滤
        if filters.get("status"):
            query = query.filter(Project.status == filters["status"])

        return query.all()

    def _apply_rls_filter(self, query, user: User):
        """应用 RLS 权限过滤"""
        if user.role == "admin":
            return query  # 管理员可访问所有
        elif user.role == "account_manager":
            return query.filter(Project.account_manager_id == user.id)
        elif user.role == "media_buyer":
            return query.filter(Project.created_by == user.id)
        else:
            return query  # finance/data_operator 可访问所有
```

**关键原则**：
1. **所有查询必须应用权限过滤**：禁止直接 `session.query(Model).all()`
2. **优先使用模型方法**：调用 `Model.get_user_accessible_query(session, user_id, user_role)`
3. **不要信任前端参数**：即使前端传递了 `project_id`，仍需验证用户是否有权访问

### 5.3 ORM 层：Mixin 提供的权限方法

**位置**：`backend/models/base.py`, `backend/models/mixins/rls_aware.py`

**UserScopeMixin**：

```python
class Project(Base, TimestampMixin, UserScopeMixin):
    __tablename__ = 'projects'
    # ... 字段定义

    # 继承的方法：
    # - query_for_user(session, user_id)  # 返回当前用户可访问的查询
```

**RLSAwareMixin**：

```python
class Project(Base, RLSAwareMixin):
    __rls_user_field__ = 'created_by'
    __rls_admin_roles__ = [UserRole.ADMIN, UserRole.DATA_MANAGER]

    # 继承的方法：
    # - apply_rls_filter(query, current_user_id, current_user_role)
    # - get_for_user(session, current_user_id, current_user_role, filters)
    # - is_accessible_by(user_id, user_role)
    # - is_modifiable_by(user_id, user_role)
```

**使用示例**：

```python
# Service 层
from backend.models.core.project import Project

def get_user_projects(self, user_id: UUID, user_role: str):
    query = self.db.query(Project)
    query = Project.apply_rls_filter(query, user_id, user_role)
    return query.all()

# 或直接使用便捷方法
def get_user_projects_v2(self, user_id: UUID, user_role: str):
    return Project.get_for_user(self.db, user_id, user_role).all()
```

### 5.4 实例级权限检查

**场景**：更新/删除单个资源时，需要检查用户是否有权操作该资源

```python
def update_project(self, project_id: int, data: dict, current_user: User):
    # 1. 查询资源
    project = self.db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ResourceNotFoundError(f"项目 {project_id} 不存在")

    # 2. 权限检查（方式 1：使用模型方法）
    if not project.can_be_edited_by(current_user.id, current_user.role):
        raise PermissionDeniedError("无权限编辑该项目")

    # 3. 权限检查（方式 2：使用 RLSAwareMixin）
    if not project.is_modifiable_by(current_user.id, current_user.role):
        raise PermissionDeniedError("无权限编辑该项目")

    # 4. 执行更新
    for key, value in data.items():
        setattr(project, key, value)
    self.db.commit()
    return project
```

---

## 6. 权限检查工具类

### 6.1 PermissionChecker 类

**位置**：`backend/core/permissions.py:257-299`

**用途**：提供便捷的权限检查方法

```python
from backend.core.permissions import PermissionChecker, get_permission_checker

# 方式 1：手动创建
checker = PermissionChecker(current_user)
if checker.has_permission(Permission.PROJECT_CREATE):
    # 创建项目
    ...

# 方式 2：依赖注入
@router.post("/projects")
async def create_project(
    data: ProjectCreateRequest,
    checker: PermissionChecker = Depends(get_permission_checker)
):
    if not checker.has_permission(Permission.PROJECT_CREATE):
        raise PermissionDeniedError("无权限创建项目")
    ...
```

**主要方法**：
- `has_role(role)` - 检查是否具有指定角色
- `has_any_role(*roles)` - 检查是否具有任意指定角色
- `has_permission(permission)` - 检查是否具有指定权限
- `has_any_permission(*permissions)` - 检查是否具有任意指定权限
- `has_all_permissions(*permissions)` - 检查是否具有所有指定权限

### 6.2 便捷装饰器

**位置**：`backend/core/permissions.py:302-349`

```python
from backend.core.permissions import (
    admin_required,
    manager_required,
    finance_required,
    data_clerk_required,
    media_buyer_required
)

# 使用示例
@router.get("/system-config")
@admin_required
async def get_system_config(current_user: User = Depends(admin_required)):
    ...

@router.post("/topup-approve/{request_id}")
@finance_required
async def approve_topup(request_id: int, user: User = Depends(finance_required)):
    ...
```

---

## 7. 常见权限场景实现

### 7.1 场景 1：列表查询（带分页和过滤）

```python
@router.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    projects, total = service.get_projects(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status=status
    )
    return success_response(data={"items": projects, "total": total})

# Service 实现
class ProjectService:
    def get_projects(self, current_user: User, page: int, page_size: int, status: Optional[str]):
        # 1. 应用 RLS 过滤
        query = Project.get_user_accessible_query(self.db, current_user.id, current_user.role)

        # 2. 应用业务过滤
        if status:
            query = query.filter(Project.status == status)

        # 3. 分页
        total = query.count()
        projects = query.offset((page - 1) * page_size).limit(page_size).all()

        return projects, total
```

### 7.2 场景 2：单资源查询（需权限验证）

```python
@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service)
):
    project = service.get_project(project_id, current_user)
    return success_response(data=project)

# Service 实现
class ProjectService:
    def get_project(self, project_id: int, current_user: User) -> Project:
        # 方式 1：查询 + 权限检查
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ResourceNotFoundError(f"项目 {project_id} 不存在")

        if not self._can_user_access_project(current_user, project):
            raise PermissionDeniedError("无权限查看该项目")

        return project

    # 方式 2：直接使用 RLS 查询（推荐）
    def get_project_v2(self, project_id: int, current_user: User) -> Project:
        query = Project.get_user_accessible_query(self.db, current_user.id, current_user.role)
        project = query.filter(Project.id == project_id).first()

        if not project:
            raise ResourceNotFoundError(f"项目 {project_id} 不存在或无权访问")

        return project
```

### 7.3 场景 3：资源创建（需验证外键引用）

```python
@router.post("/ad-accounts")
async def create_ad_account(
    data: AdAccountCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AdAccountService = Depends(get_ad_account_service)
):
    account = service.create_ad_account(data, current_user)
    return success_response(data=account, status_code=201)

# Service 实现
class AdAccountService:
    def create_ad_account(self, data: AdAccountCreateRequest, current_user: User):
        # 1. 权限检查：是否可创建账户
        if current_user.role not in ["admin", "account_manager", "data_operator"]:
            raise PermissionDeniedError("无权限创建广告账户")

        # 2. 验证项目访问权限
        project = self.db.query(Project).filter(Project.id == data.project_id).first()
        if not project:
            raise ResourceNotFoundError(f"项目 {data.project_id} 不存在")

        if current_user.role == "account_manager":
            if project.account_manager_id != current_user.id:
                raise PermissionDeniedError("只能在自己管理的项目下创建账户")

        # 3. 创建账户
        account = AdAccount(
            project_id=data.project_id,
            channel_id=data.channel_id,
            owner_id=data.owner_id or current_user.id,
            created_by=current_user.id,
            **data.model_dump(exclude={"project_id", "channel_id", "owner_id"})
        )
        self.db.add(account)
        self.db.commit()
        return account
```

### 7.4 场景 4：资源更新（需验证所有权）

```python
# Service 实现
class AdAccountService:
    def update_ad_account(self, account_id: int, data: dict, current_user: User):
        # 1. 查询账户
        account = self.db.query(AdAccount).filter(AdAccount.id == account_id).first()
        if not account:
            raise ResourceNotFoundError(f"广告账户 {account_id} 不存在")

        # 2. 权限检查
        if current_user.role == "media_buyer":
            # 投手只能更新自己负责的账户
            if account.owner_id != current_user.id:
                raise PermissionDeniedError("只能更新自己负责的账户")

            # 投手只能更新部分字段
            allowed_fields = {"name", "status_reason", "notes"}
            if not set(data.keys()).issubset(allowed_fields):
                raise PermissionDeniedError(f"只能更新以下字段：{allowed_fields}")

        elif current_user.role == "account_manager":
            # 项目经理只能更新其管理项目下的账户
            project = self.db.query(Project).filter(Project.id == account.project_id).first()
            if project.account_manager_id != current_user.id:
                raise PermissionDeniedError("只能更新自己管理项目下的账户")

        # 3. admin 和 data_operator 可更新所有字段

        # 4. 执行更新
        for key, value in data.items():
            setattr(account, key, value)
        account.updated_by = current_user.id
        self.db.commit()
        return account
```

### 7.5 场景 5：级联查询（确保所有关联表都应用 RLS）

```python
# 错误示例：未对关联表应用 RLS
def get_project_with_accounts_WRONG(project_id: int, current_user: User):
    project = Project.get_for_user(db, current_user.id, current_user.role).filter(
        Project.id == project_id
    ).first()

    # ❌ 直接查询 ad_accounts，未应用 RLS
    accounts = db.query(AdAccount).filter(AdAccount.project_id == project_id).all()

    return {"project": project, "accounts": accounts}

# 正确示例：所有关联表都应用 RLS
def get_project_with_accounts_CORRECT(project_id: int, current_user: User):
    project = Project.get_for_user(db, current_user.id, current_user.role).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise ResourceNotFoundError("项目不存在或无权访问")

    # ✅ 对 ad_accounts 也应用 RLS 过滤
    accounts_query = db.query(AdAccount).filter(AdAccount.project_id == project_id)
    accounts_query = AdAccount.apply_rls_filter(accounts_query, current_user.id, current_user.role)
    accounts = accounts_query.all()

    return {"project": project, "accounts": accounts}
```

---

## 8. 未来迁移到数据库 RLS 的路径

### 8.1 迁移必要性评估

**何时考虑启用数据库 RLS**：
1. 系统进入多租户 SaaS 模式
2. 需要满足监管合规要求（如 GDPR 数据隔离）
3. 引入第三方工具直接访问数据库（如 BI 工具）
4. 应用层权限泄漏风险增加

**当前不迁移的理由**：
- 应用层权限控制已足够安全
- 避免增加 ORM 集成复杂度
- 维护成本可控

### 8.2 迁移步骤

#### 阶段 1：准备工作

1. **审计当前权限实现**
   ```bash
   # 扫描所有未应用 RLS 的查询
   grep -r "session.query(" backend/services/
   grep -r "db.query(" backend/services/
   ```

2. **补全 Mixin 使用**
   - 确保所有核心表都继承了 `UserScopeMixin` 或 `RLSAwareMixin`
   - 定义 `__rls_user_field__` 和 `__rls_admin_roles__`

3. **创建数据库 RLS 策略脚本**
   ```sql
   -- backend/migrations/enable_rls.sql

   -- 启用 RLS
   ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
   ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
   -- ...

   -- 创建策略
   CREATE POLICY "projects_select" ON projects FOR SELECT
     USING (
       created_by = auth.uid()
       OR (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'finance', 'data_operator')
     );

   -- ...
   ```

#### 阶段 2：灰度发布

1. **启用 RLS 但不强制**
   ```sql
   -- 创建一个宽松的策略，允许所有操作
   CREATE POLICY "temp_allow_all" ON projects FOR ALL
     USING (true);
   ```

2. **监控 RLS 策略日志**
   - 使用 PostgreSQL 日志分析 RLS 策略命中情况
   - 对比应用层和数据库层权限差异

3. **逐表收紧策略**
   ```sql
   -- 先删除宽松策略
   DROP POLICY "temp_allow_all" ON projects;

   -- 应用正式策略
   CREATE POLICY "projects_select" ON projects FOR SELECT USING (...);
   CREATE POLICY "projects_insert" ON projects FOR INSERT WITH CHECK (...);
   -- ...
   ```

#### 阶段 3：清理应用层代码

1. **移除 Service 层 RLS 过滤**（可选）
   - 数据库 RLS 启用后，应用层可简化权限逻辑
   - 但仍建议保留应用层检查作为防御纵深

2. **更新 ORM 配置**
   ```python
   # backend/core/db.py

   # 设置 Supabase RLS 上下文
   def set_rls_context(session, user_id: UUID):
       session.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))
   ```

3. **测试覆盖**
   - 针对每个角色编写权限测试
   - 确保 RLS 策略与应用层行为一致

#### 阶段 4：生产部署

1. **配置环境变量**
   ```bash
   ENABLE_RLS=true
   ```

2. **执行迁移脚本**
   ```bash
   alembic upgrade head
   # 或手动执行 enable_rls.sql
   ```

3. **监控和回滚计划**
   - 监控权限拒绝错误率
   - 准备快速回滚脚本

### 8.3 Supabase RLS 特殊配置

如果使用 Supabase 托管数据库，需额外配置：

```sql
-- 1. 创建用于 RLS 的函数
CREATE OR REPLACE FUNCTION auth.current_user_id() RETURNS uuid AS $$
  SELECT COALESCE(
    nullif(current_setting('request.jwt.claims', true), '')::json->>'sub',
    (current_setting('request.headers', true)::json->>'x-user-id')
  )::uuid;
$$ LANGUAGE SQL STABLE;

-- 2. 在策略中使用
CREATE POLICY "projects_select" ON projects FOR SELECT
  USING (created_by = auth.current_user_id());
```

---

## 9. 安全最佳实践

### 9.1 防御纵深原则

即使数据库 RLS 未启用，也应遵循多层防御：

1. **Router 层**：粗粒度角色检查
2. **Service 层**：细粒度资源访问权限
3. **ORM 层**：使用 Mixin 提供的权限过滤方法
4. **数据库层**：（未来）RLS 策略作为最后一道防线

### 9.2 常见安全陷阱

#### 陷阱 1：直接查询未应用 RLS

```python
# ❌ 危险：未应用 RLS
def get_all_projects(self):
    return self.db.query(Project).all()

# ✅ 安全：应用 RLS
def get_all_projects(self, current_user: User):
    return Project.get_user_accessible_query(
        self.db, current_user.id, current_user.role
    ).all()
```

#### 陷阱 2：信任前端传递的 user_id

```python
# ❌ 危险：信任前端参数
@router.get("/user/{user_id}/projects")
async def get_user_projects(user_id: UUID):
    return db.query(Project).filter(Project.created_by == user_id).all()

# ✅ 安全：使用认证的 current_user
@router.get("/my-projects")
async def get_my_projects(current_user: User = Depends(get_current_user)):
    return Project.query_for_user(db, current_user.id).all()
```

#### 陷阱 3：级联查询遗漏 RLS

```python
# ❌ 危险：关联表未应用 RLS
def get_project_detail(project_id: int, current_user: User):
    project = Project.get_for_user(db, current_user.id, current_user.role).filter(
        Project.id == project_id
    ).first()

    # 未对 ad_accounts 应用 RLS
    accounts = db.query(AdAccount).filter(AdAccount.project_id == project_id).all()
    return {"project": project, "accounts": accounts}

# ✅ 安全：所有关联表都应用 RLS
def get_project_detail(project_id: int, current_user: User):
    project = Project.get_for_user(db, current_user.id, current_user.role).filter(
        Project.id == project_id
    ).first()

    if not project:
        raise ResourceNotFoundError()

    accounts_query = db.query(AdAccount).filter(AdAccount.project_id == project_id)
    accounts_query = AdAccount.apply_rls_filter(accounts_query, current_user.id, current_user.role)
    accounts = accounts_query.all()

    return {"project": project, "accounts": accounts}
```

#### 陷阱 4：批量操作跳过权限检查

```python
# ❌ 危险：批量删除未验证权限
@router.delete("/projects/batch")
async def batch_delete_projects(project_ids: List[int], current_user: User):
    db.query(Project).filter(Project.id.in_(project_ids)).delete()
    db.commit()

# ✅ 安全：逐个验证权限
@router.delete("/projects/batch")
async def batch_delete_projects(project_ids: List[int], current_user: User):
    for project_id in project_ids:
        project = Project.get_for_user(db, current_user.id, current_user.role).filter(
            Project.id == project_id
        ).first()

        if not project:
            raise ResourceNotFoundError(f"项目 {project_id} 不存在或无权访问")

        if not project.can_be_deleted_by(current_user.id, current_user.role):
            raise PermissionDeniedError(f"无权删除项目 {project_id}")

        db.delete(project)

    db.commit()
```

### 9.3 代码审查检查清单

在代码审查时，确保以下项：

- [ ] 所有 `session.query()` 或 `db.query()` 都应用了 RLS 过滤
- [ ] 没有直接使用前端传递的 `user_id` 进行查询
- [ ] 资源创建时验证了外键引用的访问权限
- [ ] 资源更新/删除时验证了所有权或修改权限
- [ ] 级联查询中所有关联表都应用了 RLS
- [ ] 批量操作逐个验证了权限
- [ ] 敏感操作（如状态流转）有额外的权限检查

---

## 10. 附录

### 10.1 相关文档

- [数据模型 SoT](../core/DATA_SCHEMA.md) - 表结构和字段定义
- [错误码 SoT](../ERROR_CODES.md) - 权限错误码定义
- [项目模块 API 文档](../modules/projects/API_GUIDE.md) - 项目模块权限说明
- [状态机 SoT](../core/STATE_MACHINE.md) - 状态流转权限规则

### 10.2 权限矩阵速查表

| 操作 | admin | account_manager | data_operator | finance | media_buyer |
|------|-------|-----------------|---------------|---------|-------------|
| 查看所有项目 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 创建项目 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 更新项目 | ✅ | ✅ (自己管理的) | ❌ | ❌ | ❌ |
| 删除项目 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 查看所有账户 | ✅ | ✅ (项目下的) | ✅ | ✅ | ❌ |
| 创建账户 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 更新账户 | ✅ | ✅ | ✅ | ❌ | ✅ (自己的) |
| 删除账户 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 提交日报 | ✅ | ❌ | ✅ | ❌ | ✅ |
| 审核日报 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 申请充值 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 审批充值 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 创建对账 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 查看审计日志 | ✅ | ❌ | ❌ | ❌ | ❌ |

### 10.3 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.1 | 2025-11-20 | **文档定位调整**：<br>• 标记为"当前实现行为的 Implementation SoT"<br>• 增加"文档定位说明"章节<br>• 明确与 `docs/core/RLS_POLICIES.md` 的关系<br>• 强调 SoT 层级：系统整体以 core 为根<br>• 配合方案 A 执行计划（见 `docs/RLS_STRATEGY_EXEC_PLAN_A.md`） | Backend Team |
| v1.0 | 2025-01-19 | 初始版本，基于当前应用层权限实现 | Backend Team |

---

**文档维护者**：后端开发团队
**最后审核**：2025-11-20
**下次审核**：季度性审核或权限体系重大变更时
