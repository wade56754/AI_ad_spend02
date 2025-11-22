# BR-PROJ: 项目管理业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-11-20
> **所属模块**: 项目管理 (Project Management)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `STATE_MACHINE.md` - 项目状态机
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-PROJ-001 | 项目创建权限控制 | P0 | ✅ Active |
| BR-PROJ-003 | 项目状态流转规则 | P0 | ✅ Active |
| BR-PROJ-004 | 项目删除与级联检查 | P0 | ✅ Active |

---

## BR-PROJ-001: 项目创建权限控制

### 业务场景

客户经理 (Account Manager) 负责为客户创建广告投放项目，项目是系统中所有业务数据的根节点。系统必须确保只有授权人员可以创建项目，并强制填写关键业务信息。

### 规则定义

#### 1.1 角色权限约束

**允许创建项目的角色**:
- `admin` - 系统管理员可创建任意项目
- `account_manager` - 客户经理可创建自己管理的项目

**禁止创建项目的角色**:
- ❌ `media_buyer` - 投手只能使用已分配的项目
- ❌ `data_operator` - 数据操作员无创建权限
- ❌ `finance` - 财务人员无创建权限

#### 1.2 必填字段约束

**引用**: `DATA_SCHEMA.md` 3.2.1 - `projects` 表

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `name` | VARCHAR(200) | **NOT NULL, UNIQUE** | 项目名称，全局唯一 |
| `client_name` | VARCHAR(200) | **NOT NULL** | 客户名称，必填 |
| `account_manager_id` | UUID | **NOT NULL, FK → users.id** | 客户经理ID，创建时自动设为当前用户 |
| `status` | VARCHAR(20) | DEFAULT 'draft' | 初始状态必须为 `draft` |
| `budget_total` | DECIMAL(15,2) | >= 0 | 总预算，可选 |
| `timezone` | VARCHAR(50) | DEFAULT 'Asia/Shanghai' | 项目时区 |

#### 1.3 业务逻辑校验

**前置条件**:
1. 用户角色必须为 `admin` 或 `account_manager`
2. 项目名称 `name` 全局唯一（不区分大小写）
3. 客户经理ID `account_manager_id` 必须引用有效的用户，且该用户角色为 `account_manager`
4. 如果提供预算 `budget_total`，必须 >= 0

**Service层实现示例**:
```python
# backend/services/project_service.py
class ProjectService:
    def create_project(self, payload: ProjectCreate, user: Dict) -> Project:
        # 1. 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "account_manager"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
                message="仅管理员和客户经理可以创建项目"
            )

        # 2. 项目名称唯一性检查
        existing = self.db.query(Project).filter(
            func.lower(Project.name) == payload.name.lower()
        ).first()

        if existing:
            raise ConflictException(
                code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code,  # BIZ_003
                message=f"项目名称 '{payload.name}' 已存在"
            )

        # 3. 验证客户经理ID有效性（如果指定）
        if payload.account_manager_id:
            manager = self.db.query(User).filter(
                User.id == payload.account_manager_id,
                User.role == "account_manager",
                User.is_active == True
            ).first()

            if not manager:
                raise ValidationException(
                    code=BusinessErrorCodes.INVALID_INPUT.code,  # BIZ_002
                    message="指定的客户经理不存在或已被禁用"
                )
        else:
            # 默认设为当前用户（仅当当前用户是客户经理）
            if user_role == "account_manager":
                payload.account_manager_id = user.get("user", {}).id
            else:
                raise ValidationException(
                    code=BusinessErrorCodes.INVALID_INPUT.code,
                    message="管理员创建项目时必须指定客户经理"
                )

        # 4. 预算合规性检查
        if payload.budget_total and payload.budget_total < 0:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="项目预算不能为负数"
            )

        # 5. 创建项目
        project = Project(
            name=payload.name,
            client_name=payload.client_name,
            account_manager_id=payload.account_manager_id,
            status="draft",
            budget_total=payload.budget_total or Decimal("0.00"),
            timezone=payload.timezone or "Asia/Shanghai",
            created_by=user.get("user", {}).id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.db.add(project)
        self.db.commit()

        # 6. 自动添加创建者为项目成员
        self._add_project_member(
            project_id=project.id,
            user_id=payload.account_manager_id,
            role="project_owner"
        )

        return project
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 角色权限不足 | `AUTH_500` | 403 | "仅管理员和客户经理可以创建项目" |
| 项目名称重复 | `BIZ_003` | 409 | "项目名称 '测试项目' 已存在" |
| 客户经理无效 | `BIZ_002` | 400 | "指定的客户经理不存在或已被禁用" |
| 预算为负数 | `BIZ_002` | 400 | "项目预算不能为负数" |

**引用**: `ERROR_CODES.md` - 认证错误码 (AUTH_*), 业务错误码 (BIZ_*)

### 测试用例 (Test Intent)

**TC-PROJ-001-01: 客户经理创建项目**
- **Given**: 用户 Alice 角色为 `account_manager`
- **When**: Alice 创建项目 `{name: "测试项目A", client_name: "客户A"}`
- **Then**:
  - 创建成功，返回 HTTP 201
  - `account_manager_id` 自动设为 Alice 的ID
  - `status` 为 `draft`
  - Alice 自动成为项目成员

**TC-PROJ-001-02: 管理员指定客户经理创建项目**
- **Given**: 用户 Admin 角色为 `admin`，用户 Bob 角色为 `account_manager`
- **When**: Admin 创建项目 `{name: "测试项目B", client_name: "客户B", account_manager_id: Bob.id}`
- **Then**: 创建成功，`account_manager_id` 为 Bob 的ID

**TC-PROJ-001-03: 投手尝试创建项目**
- **Given**: 用户 Carol 角色为 `media_buyer`
- **When**: Carol 尝试创建项目
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-PROJ-001-04: 项目名称重复**
- **Given**: 已存在项目名称为 "测试项目A"
- **When**: 尝试创建同名项目
- **Then**: 返回 HTTP 409，错误码 `BIZ_003`

**TC-PROJ-001-05: 缺少必填字段 client_name**
- **Given**: 用户 Alice 角色为 `account_manager`
- **When**: Alice 创建项目 `{name: "测试项目C"}` (缺少 client_name)
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

---

## BR-PROJ-003: 项目状态流转规则

### 业务场景

项目的生命周期从创建 (draft) 到激活 (active)，可能会暂停 (suspended)，最终归档 (archived)。系统必须强制执行状态流转规则，防止非法状态变更。

### 规则定义

#### 3.1 状态机定义

**引用**: `STATE_MACHINE.md` - 项目状态机 (Project Lifecycle)

```
┌─────────┐  激活   ┌────────┐  暂停   ┌───────────┐
│  draft  │ ─────→ │ active │ ─────→ │ suspended │
└─────────┘        └────┬───┘        └─────┬─────┘
                        │ 归档             │ 归档
                        ▼                  ▼
                   ┌──────────┐       ┌──────────┐
                   │ archived │ ◄─────│ archived │
                   └──────────┘       └──────────┘
                        ▲
                        │ 仅admin可回退
                        │
                   ┌────┴────┐
                   │  active │
                   └─────────┘
```

**合法状态值** (引用 `backend/models/enums.py`):
```python
class ProjectStatus(str, Enum):
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 激活
    SUSPENDED = "suspended"  # 暂停
    ARCHIVED = "archived"    # 归档
```

#### 3.2 状态流转矩阵

| 当前状态 | 目标状态 | 允许角色 | 前置条件 |
|---------|---------|---------|---------|
| `draft` | `active` | `account_manager`, `admin` | 项目信息完整 |
| `active` | `suspended` | `account_manager`, `admin` | 无限制 |
| `suspended` | `active` | `account_manager`, `admin` | 无限制 |
| `active` | `archived` | `account_manager`, `admin` | 无未完成充值/日报 |
| `suspended` | `archived` | `account_manager`, `admin` | 无未完成充值/日报 |
| `archived` | `active` | **仅 `admin`** | 紧急恢复场景 |

**禁止的流转**:
- ❌ `draft` → `suspended` (必须先激活)
- ❌ `draft` → `archived` (必须先激活)
- ❌ `archived` → `suspended` (终态限制)

#### 3.3 Service层实现示例

```python
# backend/services/state_machine.py
PROJECT_STATE_TRANSITIONS = {
    "draft": {"active"},
    "active": {"suspended", "archived"},
    "suspended": {"active", "archived"},
    "archived": {"active"}  # 仅admin可用
}

def ensure_transition_allowed(current: str, target: str):
    allowed = PROJECT_STATE_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise BusinessRuleException(
            code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,  # STATE_400
            message=f"非法状态流转: {current} → {target}"
        )

# backend/services/project_service.py
class ProjectService:
    def activate_project(self, project_id: int, user: Dict) -> Project:
        """激活项目 (draft → active)"""
        project = self._get_project_or_404(project_id)

        # 权限校验
        if not self._check_project_permission(project, user, "manage"):
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您没有权限管理该项目"
            )

        # 状态流转校验
        ensure_transition_allowed(project.status, "active")

        # 业务规则检查：项目信息是否完整
        if not project.client_name or not project.account_manager_id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="项目信息不完整，无法激活"
            )

        with self.db.begin():
            project.status = "active"
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user.get("user", {}).id

            self._create_audit_log(
                action="ACTIVATE_PROJECT",
                entity_id=str(project.id),
                user=user,
                payload_before={"status": "draft"},
                payload_after={"status": "active"}
            )

        return project

    def archive_project(self, project_id: int, user: Dict) -> Project:
        """归档项目 (active/suspended → archived)"""
        project = self._get_project_or_404(project_id)

        # 权限校验
        if not self._check_project_permission(project, user, "manage"):
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您没有权限管理该项目"
            )

        # 状态流转校验
        ensure_transition_allowed(project.status, "archived")

        # 业务规则检查：确认无未完成的充值申请
        pending_topups = self.db.query(TopupRequest).filter(
            TopupRequest.project_id == project_id,
            TopupRequest.status.notin_(["completed", "cancelled", "rejected"])
        ).count()

        if pending_topups > 0:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_001
                message=f"项目还有 {pending_topups} 个未完成的充值申请，无法归档"
            )

        # 业务规则检查：确认无未审核的日报
        pending_reports = self.db.query(DailyReport).filter(
            DailyReport.ad_account_id.in_(
                self.db.query(AdAccount.id).filter(AdAccount.project_id == project_id)
            ),
            DailyReport.status == "pending"
        ).count()

        if pending_reports > 0:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"项目下有 {pending_reports} 条待审核日报，无法归档"
            )

        with self.db.begin():
            project.status = "archived"
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user.get("user", {}).id

            # 级联归档所有活跃的广告账户
            self._cascade_archive_accounts(project_id, user)

            self._create_audit_log(
                action="ARCHIVE_PROJECT",
                entity_id=str(project.id),
                user=user,
                payload_before={"status": project.status},
                payload_after={"status": "archived"}
            )

        return project

    def restore_archived_project(self, project_id: int, user: Dict) -> Project:
        """恢复归档项目 (archived → active, 仅admin)"""
        project = self._get_project_or_404(project_id)

        # 严格权限校验：仅admin可恢复
        if user.get("profile", {}).get("role") != "admin":
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅管理员可以恢复归档项目"
            )

        # 状态流转校验
        ensure_transition_allowed(project.status, "active")

        with self.db.begin():
            project.status = "active"
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user.get("user", {}).id

            self._create_audit_log(
                action="RESTORE_ARCHIVED_PROJECT",
                entity_id=str(project.id),
                user=user,
                payload_before={"status": "archived"},
                payload_after={"status": "active"},
                notes="管理员紧急恢复归档项目"
            )

        return project
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 非法状态流转 | `STATE_400` | 400 | "非法状态流转: draft → archived" |
| 未完成充值阻止归档 | `BIZ_001` | 400 | "项目还有 3 个未完成的充值申请，无法归档" |
| 未审核日报阻止归档 | `BIZ_001` | 400 | "项目下有 5 条待审核日报，无法归档" |
| 非admin恢复归档项目 | `AUTH_500` | 403 | "仅管理员可以恢复归档项目" |

### 测试用例 (Test Intent)

**TC-PROJ-003-01: 激活草稿项目**
- **Given**: 项目 #101 状态为 `draft`
- **When**: 客户经理调用 `POST /projects/101/activate`
- **Then**: 状态更新为 `active`

**TC-PROJ-003-02: 暂停活跃项目**
- **Given**: 项目 #102 状态为 `active`
- **When**: 客户经理调用 `POST /projects/102/suspend`
- **Then**: 状态更新为 `suspended`

**TC-PROJ-003-03: 归档项目（正常流程）**
- **Given**: 项目 #103 状态为 `active`，无未完成充值，无待审核日报
- **When**: 客户经理调用 `POST /projects/103/archive`
- **Then**:
  - 项目状态更新为 `archived`
  - 关联的活跃广告账户自动归档

**TC-PROJ-003-04: 归档前检查失败（有未完成充值）**
- **Given**: 项目 #104 有 2 个状态为 `pending_review` 的充值申请
- **When**: 尝试归档项目
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-PROJ-003-05: 管理员恢复归档项目**
- **Given**: 项目 #105 状态为 `archived`，管理员 Admin
- **When**: Admin 调用 `POST /projects/105/restore`
- **Then**: 状态更新为 `active`，审计日志记录恢复操作

**TC-PROJ-003-06: 非admin尝试恢复归档项目**
- **Given**: 项目 #106 状态为 `archived`，客户经理 Alice
- **When**: Alice 尝试恢复项目
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-PROJ-003-07: 非法状态流转（draft → suspended）**
- **Given**: 项目 #107 状态为 `draft`
- **When**: 尝试调用 `POST /projects/107/suspend`
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

---

## BR-PROJ-004: 项目删除与级联检查

### 业务场景

项目是系统核心业务数据的根节点，物理删除项目会导致关联的广告账户、日报、充值记录等数据丢失。系统必须禁止物理删除，强制使用归档流程。

### 规则定义

#### 4.1 禁止物理删除

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第 5.2.1 节 - 禁止物理删除原则

**核心规则**: 项目表 `projects` 禁止 `DELETE` 操作，必须通过状态流转至 `archived` 实现逻辑删除。

**数据库约束**:
```sql
-- ✅ 正确：使用 RESTRICT 防止误删除
CREATE TABLE topup_requests (
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT
);

CREATE TABLE ad_accounts (
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT
);

-- ❌ 错误：使用 CASCADE 会级联删除业务数据
CREATE TABLE topup_requests (
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE  -- 禁止！
);
```

#### 4.2 归档前置检查

**必须满足的条件**:
1. **无未完成的充值申请**: `topup_requests.status NOT IN ('completed', 'cancelled', 'rejected')`
2. **无待审核的日报**: `daily_reports.status != 'pending'`
3. **无活跃的广告账户**: `ad_accounts.status NOT IN ('dead', 'archived')` (可选，自动级联归档)

**检查逻辑**:
```python
class ProjectService:
    def _validate_archive_prerequisites(self, project_id: int):
        """归档前置条件检查"""
        errors = []

        # 1. 检查未完成充值
        pending_topups = self.db.query(TopupRequest).filter(
            TopupRequest.project_id == project_id,
            TopupRequest.status.notin_(["completed", "cancelled", "rejected"])
        ).all()

        if pending_topups:
            topup_ids = [str(t.id) for t in pending_topups]
            errors.append(f"存在 {len(pending_topups)} 个未完成的充值申请: {', '.join(topup_ids)}")

        # 2. 检查待审核日报
        pending_reports = self.db.query(DailyReport).filter(
            DailyReport.ad_account_id.in_(
                self.db.query(AdAccount.id).filter(AdAccount.project_id == project_id)
            ),
            DailyReport.status == "pending"
        ).all()

        if pending_reports:
            report_ids = [str(r.id) for r in pending_reports]
            errors.append(f"存在 {len(pending_reports)} 条待审核日报: {', '.join(report_ids)}")

        # 3. 如果有错误，抛出异常
        if errors:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_001
                message="无法归档项目，请先处理以下问题：\n" + "\n".join(errors)
            )
```

#### 4.3 级联归档规则

**规则**: 归档项目时，自动归档所有关联的活跃广告账户。

**实现**:
```python
def _cascade_archive_accounts(self, project_id: int, user: Dict):
    """级联归档广告账户"""
    active_accounts = self.db.query(AdAccount).filter(
        AdAccount.project_id == project_id,
        AdAccount.status.notin_(["dead", "archived"])
    ).all()

    for account in active_accounts:
        account.status = "archived"
        account.updated_at = datetime.now(timezone.utc)
        account.updated_by = user.get("user", {}).id

        self._create_audit_log(
            action="CASCADE_ARCHIVE_ACCOUNT",
            entity_id=str(account.id),
            user=user,
            notes=f"项目 {project_id} 归档时自动归档广告账户"
        )
```

#### 4.4 API层防护

**禁用 DELETE 端点**:
```python
# ❌ 禁止提供物理删除接口
# @router.delete("/projects/{project_id}")
# async def delete_project(project_id: int):
#     ...

# ✅ 正确：提供归档接口
@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: int,
    service: ProjectService = Depends(),
    current_user: Dict = Depends(require_role(["admin", "account_manager"]))
):
    """归档项目（逻辑删除）"""
    project = service.archive_project(project_id, current_user)
    return success_response(
        data=ProjectResponse.model_validate(project),
        message="项目已归档"
    )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 存在未完成充值 | `BIZ_001` | 400 | "项目还有 3 个未完成的充值申请，无法归档" |
| 存在待审核日报 | `BIZ_001` | 400 | "项目下有 5 条待审核日报，无法归档" |
| 尝试物理删除 | `DB_005` | 400 | "禁止物理删除项目，请使用归档功能" |
| 外键约束违反 | `DB_001` | 500 | "无法删除项目，存在关联数据" |

### 测试用例 (Test Intent)

**TC-PROJ-004-01: 正常归档流程**
- **Given**: 项目 #101，无未完成充值，无待审核日报，有 2 个活跃广告账户
- **When**: 客户经理调用 `POST /projects/101/archive`
- **Then**:
  - 项目状态更新为 `archived`
  - 2 个广告账户自动归档
  - 审计日志记录 3 条操作

**TC-PROJ-004-02: 归档前检查失败（多个问题）**
- **Given**: 项目 #102，有 2 个未完成充值，3 条待审核日报
- **When**: 尝试归档项目
- **Then**: 返回 HTTP 400，错误消息包含：
  ```
  无法归档项目，请先处理以下问题：
  存在 2 个未完成的充值申请: 1001, 1002
  存在 3 条待审核日报: 2001, 2002, 2003
  ```

**TC-PROJ-004-03: 数据库层阻止物理删除**
- **Given**: 项目 #103 存在
- **When**: 数据库层执行 `DELETE FROM projects WHERE id = 103`
- **Then**: 数据库返回外键约束错误，删除失败

**TC-PROJ-004-04: API层禁用 DELETE 方法**
- **Given**: 项目 #104 存在
- **When**: 调用 `DELETE /api/v1/projects/104`
- **Then**: 返回 HTTP 405 Method Not Allowed 或 HTTP 404 Not Found

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `STATE_MACHINE.md` - 项目状态机
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

### B. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-20 | 初始版本，包含 BR-PROJ-001, 003, 004 | 系统架构团队 |

---

**END OF DOCUMENT**
