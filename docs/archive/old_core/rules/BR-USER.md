# BR-USER: 用户角色与权限业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-01-21
> **所属模块**: 用户管理 (User & Role Management)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
> - `BUSINESS_RULES.md` - 业务规则索引

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-USER-001 | 角色定义与职责边界 | P0 | ✅ Active |
| BR-USER-002 | 职责分离(SOD)规则 | P0 | ✅ Active |
| BR-USER-003 | 投手与资源绑定规则 | P0 | ✅ Active |
| BR-USER-004 | 管理员特权与审计要求 | P0 | ✅ Active |
| BR-USER-005 | 数据可见范围规则 | P0 | ✅ Active |

---

## BR-USER-001: 角色定义与职责边界

### 业务场景

AI广告代投系统涉及投放执行、数据审核、财务审批、项目管理等多个业务环节，需要明确的角色职责划分，防止越权操作和职责混淆。

### 规则定义

#### 1.1 系统5大角色定义

**引用**: `BUSINESS_RULES.md` 第4章 - 核心角色定义

| 角色代码 | 角色名称 | 业务定位 | 主要职责 |
|---------|---------|---------|---------|
| `admin` | 系统管理员 | 系统运维与紧急处理 | 用户管理、系统配置、数据修复、权限分配 |
| `finance` | 财务人员 | 资金管理与审批 | 充值审批、对账管理、财务报表审核 |
| `data_operator` | 数据操作员 | 数据质量把控 | 日报审核、粉数确认、数据异常复核 |
| `account_manager` | 客户经理 | 项目与客户管理 | 项目创建、账户分配、客户沟通、业绩统计 |
| `media_buyer` | 投手 | 广告投放执行 | 日报提交、充值申请、账户操作、投放优化 |

#### 1.2 角色与模块访问矩阵

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第6章 - RBAC权限设计

| 模块 | admin | finance | data_operator | account_manager | media_buyer |
|-----|-------|---------|---------------|-----------------|-------------|
| **项目管理** | ✅ 全部 | 🔍 只读 | 🔍 只读 | ✅ 创建/编辑自己的项目 | 🔍 查看分配的项目 |
| **广告账户** | ✅ 全部 | 🔍 只读 | 🔍 只读 | ✅ 创建/分配账户 | 🔍 查看分配的账户 |
| **日报提交** | ✅ 代提交 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ✅ 提交自己的日报 |
| **日报审核** | ✅ 全部 | ❌ 禁止 | ✅ 审核所有日报 | ❌ 禁止 | ❌ 禁止 |
| **粉数确认** | ✅ 全部 | ❌ 禁止 | ✅ 确认final | ❌ 禁止 | ✅ 提交raw |
| **充值申请** | ✅ 代申请 | ❌ 禁止申请 | ❌ 禁止 | ✅ 为项目申请 | ✅ 为账户申请 |
| **充值审批** | ✅ 全部 | ✅ 审批所有申请 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| **对账管理** | ✅ 全部 | ✅ 创建/处理批次 | ❌ 禁止 | 🔍 查看项目对账 | ❌ 禁止 |
| **账本查看** | ✅ 全部 | ✅ 全部 | 🔍 只读 | 🔍 查看项目账本 | 🔍 查看账户余额 |
| **审计日志** | ✅ 全部 | ✅ 财务相关 | 🔍 数据相关 | 🔍 项目相关 | ❌ 禁止 |

**图例**:
- ✅ 全部权限 (CRUD)
- 🔍 只读权限 (Read-only)
- ❌ 禁止访问

#### 1.3 各角色可执行的状态流转动作

**引用**: `STATE_MACHINE.md` - 各模块状态机

**日报状态流转**:
```
media_buyer:
  - draft → pending (提交审核)
  - rejected → draft (重新编辑)

data_operator:
  - pending → approved (审核通过)
  - pending → rejected (审核拒绝)
  - raw_submitted → trend_pending (触发风控检查)
  - trend_flagged → trend_resolved (复核通过)
  - final_pending → final_confirmed (确认final粉数)

admin:
  - 所有流转 + 强制回退 (需记录原因)
```

**充值申请状态流转**:
```
media_buyer / account_manager:
  - draft → pending_review (提交审核)

finance:
  - pending_review → approved (审批通过)
  - pending_review → rejected (审批拒绝)
  - approved → completed (确认到账)

admin:
  - 所有流转 + 强制取消 (需记录原因)
```

**项目状态流转**:
```
account_manager:
  - draft → active (激活项目)
  - active → suspended (暂停项目)
  - suspended → active (恢复项目)
  - active/suspended → archived (归档项目)

admin:
  - archived → active (紧急恢复,需审批)
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 角色权限不足 | `AUTH_500` | 403 | "仅数据操作员可以审核日报" |
| 越权访问资源 | `AUTH_500` | 403 | "您无权访问该项目的数据" |
| 禁止的状态流转 | `STATE_400` | 400 | "投手不能执行该状态流转" |
| 未分配角色 | `AUTH_501` | 403 | "用户未分配有效角色" |

**引用**: `ERROR_CODES.md` - 认证错误码 (AUTH_*)

### 测试用例 (Test Intent)

**TC-USER-001-01: 投手提交日报**
- **Given**: 投手 Alice 负责账户 #1001
- **When**: Alice 提交日报 `{ad_account_id: 1001, spend: 500}`
- **Then**: 创建成功，状态为 `draft`

**TC-USER-001-02: 投手尝试审核日报（禁止）**
- **Given**: 投手 Alice 提交日报 R1，状态为 `pending`
- **When**: Alice 尝试审核自己的日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-USER-001-03: 数据操作员审核日报**
- **Given**: 数据操作员 Bob，日报 R2 状态为 `pending`
- **When**: Bob 审核通过日报
- **Then**: 状态更新为 `approved`

**TC-USER-001-04: 财务人员审批充值**
- **Given**: 财务人员 Carol，充值申请 T1 状态为 `pending_review`
- **When**: Carol 审批通过
- **Then**: 状态更新为 `approved`

**TC-USER-001-05: 客户经理创建项目**
- **Given**: 客户经理 Dave
- **When**: Dave 创建项目 `{name: "测试项目", client_name: "客户A"}`
- **Then**: 项目创建成功，`account_manager_id` 为 Dave 的ID

---

## BR-USER-002: 职责分离(SOD)规则

### 业务场景

为防止内部欺诈和数据篡改，系统必须强制执行职责分离原则：**提交人 ≠ 审核人 ≠ 审批人**。

### 规则定义

#### 2.1 核心SOD规则

**引用**: `BUSINESS_RULES.md` 第4.2节 - 职责分离规则

**必须分离的职责组合**:

| 业务流程 | 提交角色 | 审核/审批角色 | 禁止规则 |
|---------|---------|--------------|---------|
| 日报审核 | `media_buyer` | `data_operator` | 投手不能审核自己的日报 |
| 充值审批 | `media_buyer`/`account_manager` | `finance` | 申请人不能审批自己的充值 |
| 粉数确认 | `media_buyer` (raw) | `data_operator` (final) | 提交raw者不能确认final |
| 对账调账 | `finance` (创建批次) | `finance` (不同人) | 创建人不能是唯一审核人 |

#### 2.2 Service层实现示例

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def approve_report(self, report_id: int, user: Dict) -> DailyReport:
        """审核日报 (data_operator 操作)"""
        report = self._get_report_or_404(report_id)

        # 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "data_operator"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅数据操作员可以审核日报"
            )

        # 职责分离检查: 审核人 ≠ 提交人
        if report.created_by == user.get("user", {}).id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="不能审核自己提交的日报（职责分离）"
            )

        # 状态流转
        ensure_transition_allowed(report.status, "approved")

        with self.db.begin():
            report.status = "approved"
            report.approved_by = user.get("user", {}).id
            report.approved_at = datetime.now(timezone.utc)

            self._create_audit_log(
                action="APPROVE_REPORT",
                entity_id=str(report.id),
                user=user,
                payload_before={"status": "pending"},
                payload_after={"status": "approved"}
            )

        return report
```

#### 2.3 管理员例外情况

**规则**: `admin` 角色可以绕过SOD限制，但必须记录审计日志并填写原因。

```python
# backend/services/daily_report_service.py
def admin_force_approve(self, report_id: int, user: Dict, reason: str) -> DailyReport:
    """管理员强制审核（绕过SOD）"""
    # 严格权限校验
    if user.get("profile", {}).get("role") != "admin":
        raise AuthorizationException(
            code=AuthErrorCodes.PERMISSION_DENIED.code,
            message="仅管理员可以强制审核"
        )

    # 必须提供原因
    if not reason:
        raise ValidationException(
            code=BusinessErrorCodes.INVALID_INPUT.code,
            message="管理员强制审核必须提供原因"
        )

    report = self._get_report_or_404(report_id)

    with self.db.begin():
        report.status = "approved"
        report.approved_by = user.get("user", {}).id
        report.approved_at = datetime.now(timezone.utc)

        # 审计日志标记为 ADMIN_OVERRIDE
        self._create_audit_log(
            action="ADMIN_FORCE_APPROVE",
            entity_id=str(report.id),
            user=user,
            payload_before={"status": report.status},
            payload_after={"status": "approved"},
            notes=f"管理员强制审核原因: {reason}",
            tags=["ADMIN_OVERRIDE", "SOD_BYPASS"]
        )

    return report
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 自我审核 | `BIZ_001` | 400 | "不能审核自己提交的日报（职责分离）" |
| 自我审批 | `BIZ_001` | 400 | "不能审批自己的充值申请" |
| 缺少原因 | `BIZ_002` | 400 | "管理员强制审核必须提供原因" |

### 测试用例 (Test Intent)

**TC-USER-002-01: 正常职责分离流程**
- **Given**: 投手 Alice 提交日报 R1，数据操作员 Bob
- **When**: Bob 审核通过
- **Then**: 状态更新为 `approved`，`approved_by` 为 Bob

**TC-USER-002-02: 投手自我审核（禁止）**
- **Given**: 投手 Alice 提交日报 R2
- **When**: Alice 尝试审核自己的日报
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-USER-002-03: 管理员强制审核（允许但需记录）**
- **Given**: 投手 Alice 提交日报 R3，管理员 Admin
- **When**: Admin 调用 `admin_force_approve(R3, reason="紧急上线")`
- **Then**:
  - 状态更新为 `approved`
  - 审计日志包含 `ADMIN_OVERRIDE` 标签
  - 原因记录为 "紧急上线"

---

## BR-USER-003: 投手与资源绑定规则

### 业务场景

投手 (Media Buyer) 需要被分配到具体的项目和广告账户，系统必须确保投手只能操作自己负责的资源，防止跨项目数据泄露。

### 规则定义

#### 3.1 投手-项目绑定

**引用**: `DATA_SCHEMA.md` 3.2.11 - `project_members` 表

**规则**: 投手必须被添加到项目成员列表 (`project_members`) 才能访问该项目的数据。

```sql
CREATE TABLE project_members (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'project_owner', 'media_buyer', 'viewer'
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);
```

**业务规则**:
- `media_buyer` 只能查看被分配的项目列表
- `account_manager` 自动成为自己创建项目的 `project_owner`
- `admin` 可以访问所有项目（不需要显式添加）

#### 3.2 投手-广告账户绑定

**引用**: `DATA_SCHEMA.md` 3.2.9 - `ad_accounts.assigned_to`

**规则**: 广告账户通过 `assigned_to` 字段绑定到具体投手。

```sql
CREATE TABLE ad_accounts (
    id BIGSERIAL PRIMARY KEY,
    account_code VARCHAR(100) UNIQUE NOT NULL,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,  -- 投手ID
    -- 其他字段...
);
```

**业务规则**:
- 投手只能为 `assigned_to = 自己` 的账户提交日报
- 客户经理可以重新分配账户给其他投手
- 账户可以暂时不分配投手 (`assigned_to = NULL`)

#### 3.3 跨项目权限隔离

**规则**: 投手 A 不能访问投手 B 负责的项目/账户数据。

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: Dict) -> DailyReport:
        """创建日报"""
        # 验证账户存在性
        account = self.db.query(AdAccount).filter(
            AdAccount.id == payload.ad_account_id
        ).first()

        if not account:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message="广告账户不存在"
            )

        # 投手权限检查: 只能为自己负责的账户提交日报
        user_role = user.get("profile", {}).get("role")
        if user_role == "media_buyer":
            if account.assigned_to != user.get("user", {}).id:
                raise AuthorizationException(
                    code=AuthErrorCodes.PERMISSION_DENIED.code,
                    message="您没有权限为该账户提交日报"
                )

        # 项目成员检查: 投手是否属于该项目
        if user_role == "media_buyer":
            is_member = self.db.query(ProjectMember).filter(
                ProjectMember.project_id == account.project_id,
                ProjectMember.user_id == user.get("user", {}).id
            ).first()

            if not is_member:
                raise AuthorizationException(
                    code=AuthErrorCodes.PERMISSION_DENIED.code,
                    message="您不是该项目成员，无法提交日报"
                )

        # 创建日报...
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 跨账户操作 | `AUTH_500` | 403 | "您没有权限为该账户提交日报" |
| 跨项目访问 | `AUTH_500` | 403 | "您不是该项目成员" |
| 账户未分配 | `BIZ_002` | 400 | "该账户尚未分配投手" |

### 测试用例 (Test Intent)

**TC-USER-003-01: 投手提交自己账户的日报**
- **Given**: 投手 Alice 负责账户 #1001
- **When**: Alice 提交账户 #1001 的日报
- **Then**: 创建成功

**TC-USER-003-02: 投手尝试提交他人账户日报（禁止）**
- **Given**: 投手 Alice 负责账户 #1001，投手 Bob 负责账户 #1002
- **When**: Alice 尝试提交账户 #1002 的日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-USER-003-03: 客户经理重新分配账户**
- **Given**: 客户经理 Dave，账户 #1003 当前分配给 Alice
- **When**: Dave 将账户 #1003 重新分配给 Bob
- **Then**: `ad_accounts.assigned_to` 更新为 Bob 的ID

**TC-USER-003-04: 投手查看项目列表（仅自己的项目）**
- **Given**: 投手 Alice 是项目 #101, #102 的成员
- **When**: Alice 调用 `GET /projects`
- **Then**: 仅返回项目 #101 和 #102

---

## BR-USER-004: 管理员特权与审计要求

### 业务场景

系统管理员 (Admin) 拥有最高权限，可以执行紧急修复、数据回退等操作，但所有特权操作必须强制记录审计日志，防止滥用。

### 规则定义

#### 4.1 管理员特权操作列表

**引用**: `BUSINESS_RULES.md` 第4.3节 - 管理员特权

| 特权操作 | 业务场景 | 审计要求 |
|---------|---------|---------|
| 强制审核日报 | 数据操作员离职，日报积压 | 必须填写 `reason`，标记 `ADMIN_OVERRIDE` |
| 强制审批充值 | 财务人员不在，紧急充值 | 必须填写 `reason`，通知财务团队 |
| 修改已锁定数据 | final_locked 后发现粉数错误 | 必须通过红冲机制，记录完整链路 |
| 恢复归档项目 | 客户临时恢复项目 | 必须填写 `reason`，审计日志标记 `RESTORE` |
| 删除用户 | 员工离职 | 仅逻辑删除 (`is_active=false`)，保留数据 |
| 修改用户角色 | 组织架构调整 | 记录 `before/after` 角色 |

#### 4.2 强制原因填写规则

**规则**: 管理员执行以下操作时，`reason` 字段为必填：

- 强制审核/审批（绕过SOD）
- 修改终态数据（`approved`, `final_locked`）
- 恢复归档资源（`archived → active`）
- 强制取消流程（`pending → cancelled`）

```python
# backend/services/base_service.py
def require_admin_reason(func):
    """管理员操作强制填写原因的装饰器"""
    def wrapper(self, *args, reason: str = None, **kwargs):
        # 检查是否为管理员
        user = kwargs.get("user")
        if user.get("profile", {}).get("role") != "admin":
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="该操作仅限管理员"
            )

        # 检查原因是否填写
        if not reason or len(reason.strip()) < 5:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="管理员操作必须提供原因（至少5个字符）"
            )

        # 执行操作
        result = func(self, *args, **kwargs)

        # 记录审计日志
        self._create_audit_log(
            action=func.__name__.upper(),
            entity_id=str(args[0]) if args else None,
            user=user,
            notes=f"管理员操作原因: {reason}",
            tags=["ADMIN_OVERRIDE"]
        )

        return result

    return wrapper
```

#### 4.3 审计日志强制要求

**规则**: 管理员操作的审计日志必须包含以下字段：

- `action`: 操作类型 (如 `ADMIN_FORCE_APPROVE`)
- `actor_id`: 管理员用户ID
- `actor_role`: `admin`
- `reason`: 操作原因（不少于5字符）
- `payload_before`: 修改前快照
- `payload_after`: 修改后快照
- `tags`: 包含 `ADMIN_OVERRIDE` 标签
- `occurred_at`: UTC时间戳

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 非管理员尝试特权操作 | `AUTH_500` | 403 | "该操作仅限管理员" |
| 缺少原因 | `BIZ_002` | 400 | "管理员操作必须提供原因" |
| 原因过短 | `BIZ_002` | 400 | "原因长度不少于5个字符" |

### 测试用例 (Test Intent)

**TC-USER-004-01: 管理员强制审核日报**
- **Given**: 日报 R1 状态为 `pending`，管理员 Admin
- **When**: Admin 调用 `admin_force_approve(R1, reason="数据操作员离职")`
- **Then**:
  - 状态更新为 `approved`
  - 审计日志包含 `ADMIN_OVERRIDE` 标签
  - 原因为 "数据操作员离职"

**TC-USER-004-02: 管理员操作缺少原因（禁止）**
- **Given**: 日报 R2 状态为 `pending`，管理员 Admin
- **When**: Admin 调用 `admin_force_approve(R2)` without `reason`
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

**TC-USER-004-03: 非管理员尝试特权操作**
- **Given**: 客户经理 Dave
- **When**: Dave 尝试调用 `admin_force_approve`
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

---

## BR-USER-005: 数据可见范围规则

### 业务场景

不同角色对数据的可见范围不同，系统必须在业务层强制执行数据隔离，防止敏感信息泄露。

### 规则定义

#### 5.1 按角色划分的数据边界

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第6.2节 - 数据可见性规则

| 数据类型 | admin | finance | data_operator | account_manager | media_buyer |
|---------|-------|---------|---------------|-----------------|-------------|
| **所有项目** | ✅ 全部 | ✅ 全部 | ✅ 全部 | 🔒 仅自己管理的项目 | 🔒 仅分配的项目 |
| **所有广告账户** | ✅ 全部 | ✅ 全部 | ✅ 全部 | 🔒 仅自己项目下的账户 | 🔒 仅分配给自己的账户 |
| **所有日报** | ✅ 全部 | 🔍 只读 | ✅ 全部 | 🔍 仅自己项目的日报 | 🔒 仅自己提交的日报 |
| **所有充值申请** | ✅ 全部 | ✅ 全部 | ❌ 禁止 | 🔒 仅自己项目的充值 | 🔒 仅自己提交的充值 |
| **PROJECT账本** | ✅ 全部 | ✅ 全部 | 🔍 只读 | 🔍 仅自己项目的账本 | 🔍 仅账户余额 |
| **SUPPLIER账本** | ✅ 全部 | ✅ 全部 | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 |
| **审计日志** | ✅ 全部 | ✅ 财务相关 | 🔍 数据相关 | 🔍 项目相关 | ❌ 禁止 |
| **用户列表** | ✅ 全部 | 🔍 只读 | 🔍 只读 | 🔍 仅项目成员 | 🔍 仅同项目投手 |

**图例**:
- ✅ 完整访问
- 🔍 只读访问
- 🔒 限定范围访问
- ❌ 禁止访问

#### 5.2 Service层数据过滤实现

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def list_reports(self, filters: Dict, user: Dict, pagination: PaginationParams):
        """获取日报列表（按角色过滤）"""
        user_role = user.get("profile", {}).get("role")
        user_id = user.get("user", {}).id

        # 基础查询
        query = self.db.query(DailyReport)

        # 按角色过滤数据范围
        if user_role == "admin":
            # 管理员可见所有数据
            pass

        elif user_role == "finance":
            # 财务可见所有数据（只读）
            pass

        elif user_role == "data_operator":
            # 数据操作员可见所有数据
            pass

        elif user_role == "account_manager":
            # 客户经理仅可见自己管理的项目的日报
            managed_project_ids = self.db.query(Project.id).filter(
                Project.account_manager_id == user_id
            ).subquery()

            query = query.join(AdAccount).filter(
                AdAccount.project_id.in_(managed_project_ids)
            )

        elif user_role == "media_buyer":
            # 投手仅可见自己提交的日报
            query = query.filter(DailyReport.created_by == user_id)

        else:
            # 未知角色，禁止访问
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="未分配有效角色"
            )

        # 应用其他过滤条件
        if filters.get("project_id"):
            query = query.join(AdAccount).filter(
                AdAccount.project_id == filters["project_id"]
            )

        # 分页
        total = query.count()
        reports = query.offset(pagination.offset).limit(pagination.limit).all()

        return {"total": total, "items": reports}
```

#### 5.3 API层权限校验

```python
# backend/routers/daily_reports.py
@router.get("", response_model=PaginatedResponse[DailyReportResponse])
async def list_reports(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    user: Dict = Depends(get_current_user),
    service: DailyReportService = Depends()
):
    """获取日报列表"""
    filters = {"project_id": project_id, "status": status}
    result = service.list_reports(filters, user, pagination)

    return PaginatedResponse(
        total=result["total"],
        items=[DailyReportResponse.model_validate(r) for r in result["items"]],
        page=pagination.page,
        page_size=pagination.page_size
    )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 跨项目访问 | `AUTH_500` | 403 | "您无权访问该项目的数据" |
| 角色未分配 | `AUTH_501` | 403 | "未分配有效角色" |
| 访问禁止模块 | `AUTH_500` | 403 | "投手无权查看审计日志" |

### 测试用例 (Test Intent)

**TC-USER-005-01: 投手查看日报列表（仅自己的）**
- **Given**: 投手 Alice 提交过日报 R1, R2，投手 Bob 提交过 R3
- **When**: Alice 调用 `GET /daily-reports`
- **Then**: 仅返回 R1, R2

**TC-USER-005-02: 客户经理查看项目日报**
- **Given**: 客户经理 Dave 管理项目 #101，该项目下有日报 R1-R10
- **When**: Dave 调用 `GET /daily-reports?project_id=101`
- **Then**: 返回 R1-R10

**TC-USER-005-03: 投手尝试查看他人日报（禁止）**
- **Given**: 投手 Alice，日报 R3 由投手 Bob 提交
- **When**: Alice 调用 `GET /daily-reports/R3`
- **Then**: 返回 HTTP 404 (假装不存在，防止信息泄露)

**TC-USER-005-04: 财务人员查看所有充值申请**
- **Given**: 财务人员 Carol，系统中有 50 个充值申请
- **When**: Carol 调用 `GET /topup-requests`
- **Then**: 返回所有 50 个充值申请

**TC-USER-005-05: 投手尝试查看审计日志（禁止）**
- **Given**: 投手 Alice
- **When**: Alice 调用 `GET /audit-logs`
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
- `BUSINESS_RULES.md` - 业务规则索引
- `STATE_MACHINE.md` - 状态机定义

### B. 角色权限速查表

**快速判断规则**:
- 提交操作 → `media_buyer` / `account_manager`
- 审核操作 → `data_operator`
- 审批操作 → `finance`
- 紧急操作 → `admin` (需填写原因)
- 查看所有数据 → `admin` / `finance`

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-01-21 | 初始版本，包含 BR-USER-001~005 | 系统架构团队 |

---

**END OF DOCUMENT**
