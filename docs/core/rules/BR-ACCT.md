# BR-ACCT: 广告账户业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-11-20
> **所属模块**: 广告账户管理 (Ad Account Management)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `STATE_MACHINE.md` - 账户状态机
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-ACCT-001 | 账户创建与绑定约束 | P0 | ✅ Active |
| BR-ACCT-002 | 账户状态机流转规则 | P0 | ✅ Active |

---

## BR-ACCT-001: 账户创建与绑定约束

### 业务场景

广告账户是系统中投放数据的核心载体，每个账户必须关联到具体的广告平台渠道 (如Meta, Google Ads) 和项目。系统必须确保账户编号 (account_code) 的全局唯一性，防止重复绑定导致的数据混乱。

### 规则定义

#### 1.1 字段约束

**引用**: `DATA_SCHEMA.md` 3.2.9 - `ad_accounts` 表

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `account_code` | VARCHAR(100) | **UNIQUE, NOT NULL** | 广告平台账户编号，全局唯一 |
| `channel_id` | UUID | **NOT NULL, FK → channels.id** | 必须绑定有效的渠道 |
| `project_id` | BIGINT | **NOT NULL, FK → projects.id** | 必须关联有效项目 |
| `assigned_to` | UUID | **FK → users.id** | 分配给的投手，可空 |
| `status` | VARCHAR(20) | DEFAULT 'new' | 初始状态为 `new` |
| `daily_budget` | DECIMAL(15,2) | >= 0 | 日预算，可选 |

#### 1.2 唯一性约束

**核心规则**: `account_code` 必须全局唯一，同一个广告平台账号不能被重复绑定到系统中。

**数据库约束**:
```sql
CREATE TABLE ad_accounts (
    id BIGSERIAL PRIMARY KEY,
    account_code VARCHAR(100) UNIQUE NOT NULL,  -- 全局唯一
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    -- 其他字段...
);

-- 唯一索引
CREATE UNIQUE INDEX ad_accounts_account_code_key ON ad_accounts(account_code);
```

#### 1.3 渠道有效性校验

**前置条件**:
1. `channel_id` 必须引用存在的渠道记录
2. 渠道状态必须为 `active` (不允许绑定已禁用的渠道)

**示例**:
```python
# backend/services/ad_account_service.py
class AdAccountService:
    def create_account(self, payload: AdAccountCreate, user: Dict) -> AdAccount:
        # 1. 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "account_manager"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅管理员和客户经理可以创建广告账户"
            )

        # 2. 验证项目存在性
        project = self.db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message=f"项目 {payload.project_id} 不存在"
            )

        # 3. 验证项目状态（不能为归档状态）
        if project.status == "archived":
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="无法为已归档的项目创建广告账户"
            )

        # 4. 验证渠道存在性和状态
        channel = self.db.query(Channel).filter(Channel.id == payload.channel_id).first()
        if not channel:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message=f"渠道 {payload.channel_id} 不存在"
            )

        if not channel.is_active:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"渠道 '{channel.name}' 已被禁用，无法绑定"
            )

        # 5. 验证 account_code 唯一性
        existing = self.db.query(AdAccount).filter(
            AdAccount.account_code == payload.account_code
        ).first()

        if existing:
            raise ConflictException(
                code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code,  # BIZ_003
                message=f"广告账户 '{payload.account_code}' 已存在（项目: {existing.project.name}）"
            )

        # 6. 验证投手有效性（如果指定）
        if payload.assigned_to:
            buyer = self.db.query(User).filter(
                User.id == payload.assigned_to,
                User.role == "media_buyer",
                User.is_active == True
            ).first()

            if not buyer:
                raise ValidationException(
                    code=BusinessErrorCodes.INVALID_INPUT.code,
                    message="指定的投手不存在或已被禁用"
                )

        # 7. 创建广告账户
        account = AdAccount(
            account_code=payload.account_code,
            account_name=payload.account_name,
            channel_id=payload.channel_id,
            project_id=payload.project_id,
            assigned_to=payload.assigned_to,
            status="new",
            daily_budget=payload.daily_budget or Decimal("0.00"),
            created_by=user.get("user", {}).id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.db.add(account)
        self.db.commit()

        return account
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 账户编号重复 | `BIZ_003` | 409 | "广告账户 'ACT_123456' 已存在" |
| 项目不存在 | `BIZ_100` | 404 | "项目 12345 不存在" |
| 项目已归档 | `BIZ_001` | 400 | "无法为已归档的项目创建广告账户" |
| 渠道不存在 | `BIZ_100` | 404 | "渠道 UUID 不存在" |
| 渠道已禁用 | `BIZ_001` | 400 | "渠道 'Meta' 已被禁用，无法绑定" |
| 投手无效 | `BIZ_002` | 400 | "指定的投手不存在或已被禁用" |

**引用**: `ERROR_CODES.md` - 业务错误码 (BIZ_*)

### 测试用例 (Test Intent)

**TC-ACCT-001-01: 正常创建广告账户**
- **Given**: 项目 #101 存在且状态为 `active`，渠道 Meta 存在且启用
- **When**: 客户经理创建账户 `{account_code: "ACT_123", channel_id: "Meta", project_id: 101}`
- **Then**:
  - 创建成功，返回 HTTP 201
  - `status` 为 `new`
  - `created_at` 记录UTC时间

**TC-ACCT-001-02: 账户编号重复**
- **Given**: 已存在账户 `ACT_123` 绑定到项目 #101
- **When**: 尝试创建相同 `account_code` 的账户
- **Then**: 返回 HTTP 409，错误码 `BIZ_003`

**TC-ACCT-001-03: 绑定已禁用的渠道**
- **Given**: 渠道 TikTok 已被禁用 (`is_active=false`)
- **When**: 尝试创建账户绑定到 TikTok
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-ACCT-001-04: 为归档项目创建账户**
- **Given**: 项目 #102 状态为 `archived`
- **When**: 尝试创建账户绑定到项目 #102
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-ACCT-001-05: 分配给无效投手**
- **Given**: 用户 Alice 角色为 `data_operator` (非投手)
- **When**: 尝试创建账户并指定 `assigned_to=Alice.id`
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

---

## BR-ACCT-002: 账户状态机流转规则

### 业务场景

广告账户的生命周期从新建 (new)、测试 (testing)、激活 (active) 到可能的暂停 (suspended)、死亡 (dead)、归档 (archived)。系统必须强制执行状态流转规则，特别是 `dead` 状态的不可逆性。

### 规则定义

#### 2.1 状态机定义

**引用**: `STATE_MACHINE.md` - 广告账户状态机 (Ad Account Lifecycle)

```
┌──────┐  测试  ┌────────┐  激活  ┌────────┐
│ new  │ ────→ │testing │ ────→ │ active │
└──────┘       └────────┘       └───┬────┘
                    │                │
                    │ 暂停           │ 暂停
                    ▼                ▼
               ┌───────────┐    ┌───────────┐
               │ suspended │ ←──│ suspended │
               └─────┬─────┘    └─────┬─────┘
                     │                │
                     │ 死亡           │ 死亡
                     ▼                ▼
                ┌──────┐        ┌──────┐
                │ dead │ ◄──────│ dead │
                └───┬──┘        └──────┘
                    │
                    │ 归档
                    ▼
               ┌──────────┐
               │ archived │
               └──────────┘
```

**合法状态值** (引用 `backend/models/enums.py`):
```python
class AccountStatus(str, Enum):
    NEW = "new"              # 新建
    TESTING = "testing"      # 测试中
    ACTIVE = "active"        # 激活
    SUSPENDED = "suspended"  # 暂停
    DEAD = "dead"            # 死亡（不可恢复）
    ARCHIVED = "archived"    # 归档
```

#### 2.2 状态流转矩阵

| 当前状态 | 目标状态 | 允许角色 | 前置条件 | 说明 |
|---------|---------|---------|---------|------|
| `new` | `testing` | `account_manager`, `admin` | 无 | 开始测试 |
| `testing` | `active` | `account_manager`, `admin` | 测试成功 | 正式激活 |
| `testing` | `suspended` | `account_manager`, `admin` | 无 | 测试暂停 |
| `active` | `suspended` | `account_manager`, `admin` | 无 | 投放暂停 |
| `suspended` | `active` | `account_manager`, `admin` | 无 | 恢复投放 |
| `suspended` | `testing` | `account_manager`, `admin` | 无 | 重新测试 |
| `active` | `dead` | `account_manager`, `admin` | 无 | 账户封禁 |
| `suspended` | `dead` | `account_manager`, `admin` | 无 | 账户封禁 |
| `dead` | `archived` | `admin` | 无 | 归档死亡账户 |

**禁止的流转**:
- ❌ `dead` → 任何非 `archived` 状态 (**不可恢复**)
- ❌ `archived` → 任何状态 (终态)
- ❌ `new` → `dead` (必须先测试或激活)

#### 2.3 Service层实现示例

```python
# backend/services/state_machine.py
ACCOUNT_STATE_TRANSITIONS = {
    "new": {"testing"},
    "testing": {"active", "suspended"},
    "active": {"suspended", "dead"},
    "suspended": {"active", "testing", "dead"},
    "dead": {"archived"},
    "archived": set()  # 终态
}

def ensure_transition_allowed(current: str, target: str):
    allowed = ACCOUNT_STATE_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise BusinessRuleException(
            code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,  # STATE_400
            message=f"非法状态流转: {current} → {target}"
        )

# backend/services/ad_account_service.py
class AdAccountService:
    def activate_account(self, account_id: int, user: Dict) -> AdAccount:
        """激活账户 (testing → active)"""
        account = self._get_account_or_404(account_id)

        # 权限校验
        if not self._check_account_permission(account, user):
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您没有权限管理该账户"
            )

        # 状态流转校验
        ensure_transition_allowed(account.status, "active")

        with self.db.begin():
            account.status = "active"
            account.updated_at = datetime.now(timezone.utc)
            account.updated_by = user.get("user", {}).id

            self._create_audit_log(
                action="ACTIVATE_ACCOUNT",
                entity_id=str(account.id),
                user=user,
                payload_before={"status": "testing"},
                payload_after={"status": "active"}
            )

        return account

    def mark_as_dead(self, account_id: int, reason: str, user: Dict) -> AdAccount:
        """标记账户为死亡状态 (active/suspended → dead)"""
        account = self._get_account_or_404(account_id)

        # 权限校验
        if not self._check_account_permission(account, user):
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="您没有权限管理该账户"
            )

        # 状态流转校验
        ensure_transition_allowed(account.status, "dead")

        # 业务规则：必须提供死亡原因
        if not reason:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="标记账户为死亡状态时必须提供原因"
            )

        with self.db.begin():
            account.status = "dead"
            account.status_reason = reason
            account.updated_at = datetime.now(timezone.utc)
            account.updated_by = user.get("user", {}).id

            self._create_audit_log(
                action="MARK_ACCOUNT_DEAD",
                entity_id=str(account.id),
                user=user,
                payload_before={"status": account.status},
                payload_after={"status": "dead", "reason": reason},
                notes=f"账户死亡原因: {reason}"
            )

        return account

    def archive_dead_account(self, account_id: int, user: Dict) -> AdAccount:
        """归档死亡账户 (dead → archived, 仅admin)"""
        account = self._get_account_or_404(account_id)

        # 严格权限校验：仅admin可归档
        if user.get("profile", {}).get("role") != "admin":
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅管理员可以归档账户"
            )

        # 状态流转校验
        ensure_transition_allowed(account.status, "archived")

        with self.db.begin():
            account.status = "archived"
            account.updated_at = datetime.now(timezone.utc)
            account.updated_by = user.get("user", {}).id

            self._create_audit_log(
                action="ARCHIVE_ACCOUNT",
                entity_id=str(account.id),
                user=user,
                payload_before={"status": "dead"},
                payload_after={"status": "archived"}
            )

        return account
```

#### 2.4 死亡状态不可恢复规则

**核心约束**: 一旦账户进入 `dead` 状态，禁止恢复到任何非 `archived` 状态。

**业务原因**:
- 广告平台封禁的账户无法技术手段恢复
- 保持数据真实性，防止人为篡改历史状态
- 审计合规要求

**错误处理**:
```python
def restore_dead_account(self, account_id: int, user: Dict) -> AdAccount:
    """尝试恢复死亡账户（禁止操作）"""
    account = self._get_account_or_404(account_id)

    if account.status == "dead":
        raise BusinessRuleException(
            code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,  # STATE_400
            message="死亡状态的账户不可恢复，请创建新账户"
        )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 非法状态流转 | `STATE_400` | 400 | "非法状态流转: dead → active" |
| 死亡账户恢复 | `STATE_400` | 400 | "死亡状态的账户不可恢复" |
| 缺少死亡原因 | `BIZ_002` | 400 | "标记账户为死亡状态时必须提供原因" |
| 非admin归档 | `AUTH_500` | 403 | "仅管理员可以归档账户" |

### 测试用例 (Test Intent)

**TC-ACCT-002-01: 正常状态流转（new → testing → active）**
- **Given**: 广告账户 #1001 状态为 `new`
- **When**:
  1. 客户经理调用 `POST /ad-accounts/1001/start-testing`
  2. 测试成功后调用 `POST /ad-accounts/1001/activate`
- **Then**:
  - 状态依次变为 `testing` → `active`
  - 审计日志记录2次状态变更

**TC-ACCT-002-02: 暂停后恢复**
- **Given**: 账户 #1002 状态为 `active`
- **When**:
  1. 调用 `POST /ad-accounts/1002/suspend`
  2. 调用 `POST /ad-accounts/1002/resume`
- **Then**: 状态变为 `suspended` → `active`

**TC-ACCT-002-03: 标记账户死亡**
- **Given**: 账户 #1003 状态为 `active`
- **When**: 调用 `POST /ad-accounts/1003/mark-dead` with `{reason: "平台封禁"}`
- **Then**:
  - 状态更新为 `dead`
  - `status_reason` 记录为 "平台封禁"

**TC-ACCT-002-04: 尝试恢复死亡账户（禁止）**
- **Given**: 账户 #1004 状态为 `dead`
- **When**: 尝试调用 `POST /ad-accounts/1004/activate`
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

**TC-ACCT-002-05: 管理员归档死亡账户**
- **Given**: 账户 #1005 状态为 `dead`，管理员 Admin
- **When**: Admin 调用 `POST /ad-accounts/1005/archive`
- **Then**: 状态更新为 `archived`

**TC-ACCT-002-06: 非admin尝试归档**
- **Given**: 账户 #1006 状态为 `dead`，客户经理 Alice
- **When**: Alice 尝试归档账户
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-ACCT-002-07: 非法状态流转（new → dead）**
- **Given**: 账户 #1007 状态为 `new`
- **When**: 尝试调用 `POST /ad-accounts/1007/mark-dead`
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

**TC-ACCT-002-08: 标记死亡但缺少原因**
- **Given**: 账户 #1008 状态为 `active`
- **When**: 调用 `POST /ad-accounts/1008/mark-dead` without `reason`
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `STATE_MACHINE.md` - 账户状态机
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

### B. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-20 | 初始版本，包含 BR-ACCT-001, 002 | 系统架构团队 |

---

**END OF DOCUMENT**
