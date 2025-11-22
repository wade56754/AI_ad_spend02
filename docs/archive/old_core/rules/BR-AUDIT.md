# BR-AUDIT: 审计日志业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-01-21
> **所属模块**: 审计管理 (Audit & Compliance)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
> - `BUSINESS_RULES.md` - 业务规则索引

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-AUDIT-001 | 审计核心原则 | P0 | ✅ Active |
| BR-AUDIT-002 | 必审计模块与动作 | P0 | ✅ Active |
| BR-AUDIT-003 | 审计日志字段规范 | P0 | ✅ Active |
| BR-AUDIT-004 | 系统自动动作审计 | P0 | ✅ Active |
| BR-AUDIT-005 | 审计日志查询与过滤 | P1 | ✅ Active |

---

## BR-AUDIT-001: 审计核心原则

### 业务场景

AI广告代投系统涉及资金流转、数据审核、权限操作等敏感业务，必须完整记录所有关键操作，确保数据可追溯、不可篡改，满足审计合规要求。

### 规则定义

#### 1.1 三大核心原则

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第7章 - 审计系统设计

| 原则 | 说明 | 技术实现 |
|-----|------|---------|
| **不可逆性** | 审计日志一旦写入，禁止删除或修改 | 数据库无 DELETE/UPDATE 权限，仅 INSERT + SELECT |
| **完整追溯性** | 所有敏感操作必须记录 `before/after` 快照 | JSON 格式存储 `payload_before` / `payload_after` |
| **时间戳UTC标准** | 统一使用 UTC 时间戳 | `occurred_at TIMESTAMPTZ NOT NULL` |

#### 1.2 审计日志表结构

**引用**: `DATA_SCHEMA.md` 3.5.1 - `audit_logs` 表

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,                -- 操作类型 (CREATE_PROJECT, APPROVE_REPORT, ADMIN_FORCE_APPROVE, etc.)
    resource_type VARCHAR(50) NOT NULL,          -- 资源类型 (project, daily_report, topup_request, ledger_entry, etc.)
    resource_id VARCHAR(100),                    -- 资源ID (可为NULL，如批量操作)
    actor_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,  -- 操作人ID
    actor_role VARCHAR(50) NOT NULL,             -- 操作人角色 (admin, finance, media_buyer, system)
    payload_before JSONB,                        -- 修改前快照
    payload_after JSONB,                         -- 修改后快照
    reason TEXT,                                 -- 操作原因 (管理员操作必填)
    tags TEXT[],                                 -- 标签 (ADMIN_OVERRIDE, SOD_BYPASS, SYSTEM_AUTO, etc.)
    ip_address VARCHAR(45),                      -- 操作IP地址
    user_agent TEXT,                             -- 浏览器UA
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- 操作时间 (UTC)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_resource_type_id ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_occurred_at ON audit_logs(occurred_at DESC);
CREATE INDEX idx_audit_logs_tags ON audit_logs USING GIN(tags);
```

#### 1.3 不可逆性保障

**数据库层保障**:
```sql
-- 禁止应用层删除/修改审计日志
REVOKE DELETE, UPDATE ON audit_logs FROM app_user;
GRANT INSERT, SELECT ON audit_logs TO app_user;
```

**应用层保障**:
```python
# backend/services/audit_service.py
class AuditService:
    def create_log(self, log_data: AuditLogCreate) -> AuditLog:
        """创建审计日志 (仅允许创建,禁止修改/删除)"""
        log = AuditLog(
            action=log_data.action,
            resource_type=log_data.resource_type,
            resource_id=log_data.resource_id,
            actor_id=log_data.actor_id,
            actor_role=log_data.actor_role,
            payload_before=log_data.payload_before,
            payload_after=log_data.payload_after,
            reason=log_data.reason,
            tags=log_data.tags,
            ip_address=log_data.ip_address,
            user_agent=log_data.user_agent,
            occurred_at=datetime.now(timezone.utc)
        )

        self.db.add(log)
        self.db.commit()
        return log

    def delete_log(self, log_id: int):
        """禁止删除审计日志"""
        raise ForbiddenException(
            code="AUDIT_001",
            message="审计日志禁止删除（不可逆原则）"
        )

    def update_log(self, log_id: int, updates: Dict):
        """禁止修改审计日志"""
        raise ForbiddenException(
            code="AUDIT_002",
            message="审计日志禁止修改（不可逆原则）"
        )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 尝试删除审计日志 | `AUDIT_001` | 403 | "审计日志禁止删除（不可逆原则）" |
| 尝试修改审计日志 | `AUDIT_002` | 403 | "审计日志禁止修改（不可逆原则）" |

### 测试用例 (Test Intent)

**TC-AUDIT-001-01: 创建审计日志**
- **Given**: 用户 Alice 创建项目 P1
- **When**: 系统自动记录审计日志
- **Then**:
  - `action` = `CREATE_PROJECT`
  - `actor_id` = Alice 的ID
  - `payload_after` 包含项目完整信息

**TC-AUDIT-001-02: 尝试删除审计日志（禁止）**
- **Given**: 审计日志 L1 存在
- **When**: 尝试调用 `DELETE /audit-logs/L1`
- **Then**: 返回 HTTP 403，错误码 `AUDIT_001`

**TC-AUDIT-001-03: 尝试修改审计日志（禁止）**
- **Given**: 审计日志 L2 存在
- **When**: 尝试调用 `PUT /audit-logs/L2`
- **Then**: 返回 HTTP 403，错误码 `AUDIT_002`

---

## BR-AUDIT-002: 必审计模块与动作

### 业务场景

系统核心业务模块的关键操作必须强制记录审计日志，确保所有敏感变更可追溯。

### 规则定义

#### 2.1 必审计模块列表

**引用**: `BUSINESS_RULES.md` 第5章 - 审计要求

| 模块 | 必审计动作 | 审计级别 |
|-----|-----------|---------|
| **daily_reports** | CREATE, SUBMIT, APPROVE, REJECT, REOPEN, UPDATE, ADMIN_OVERRIDE | P0 |
| **ledger_entries** | CREATE, REVERSAL | P0 |
| **topup_requests** | CREATE, SUBMIT, APPROVE, REJECT, COMPLETE, CANCEL | P0 |
| **projects** | CREATE, UPDATE, ACTIVATE, SUSPEND, ARCHIVE, RESTORE | P0 |
| **ad_accounts** | CREATE, UPDATE, ASSIGN, STATUS_CHANGE | P1 |
| **users** | CREATE, UPDATE_ROLE, DEACTIVATE, PASSWORD_RESET | P0 |
| **transfers** | CREATE_TRANSFER (死号迁移) | P0 |
| **reconciliation_batches** | CREATE, PROCESS, CLOSE, ADJUST | P0 |

#### 2.2 日报审核流程审计

**完整审计链路**:
```
1. CREATE_REPORT (投手创建日报)
   - actor: media_buyer
   - payload_after: {report_date, ad_account_id, spend, ...}

2. SUBMIT_REPORT (投手提交审核)
   - actor: media_buyer
   - payload_before: {status: "draft"}
   - payload_after: {status: "pending"}

3. APPROVE_REPORT (数据操作员审核通过)
   - actor: data_operator
   - payload_before: {status: "pending"}
   - payload_after: {status: "approved", approved_by, approved_at}

4. CONFIRM_FINAL (运营确认final粉数)
   - actor: data_operator
   - payload_before: {status: "final_pending", conversions_final: null}
   - payload_after: {status: "final_confirmed", conversions_final: 95}

5. LOCK_FINAL (系统计费锁定)
   - actor: system
   - payload_before: {status: "final_confirmed"}
   - payload_after: {status: "final_locked"}
   - tags: ["SYSTEM_AUTO"]
```

#### 2.3 账本操作审计

**引用**: `STATE_MACHINE.md` - 粉数确认状态机 (v2.6)

**所有账本记录必审计**:
```python
# backend/services/ledger_service.py
class LedgerService:
    def create_entry(self, entry_data: LedgerEntryCreate, user: Dict) -> LedgerEntry:
        """创建账本记录 (自动审计)"""
        entry = LedgerEntry(
            project_id=entry_data.project_id,
            entry_type=entry_data.entry_type,
            amount=entry_data.amount,
            balance_after=self._calculate_balance(entry_data),
            related_id=entry_data.related_id,
            occurred_at=datetime.now(timezone.utc),
            notes=entry_data.notes
        )

        self.db.add(entry)
        self.db.flush()

        # 强制审计
        self._create_audit_log(
            action="CREATE_LEDGER_ENTRY",
            resource_type="ledger_entry",
            resource_id=str(entry.id),
            actor_id=user.get("user", {}).id,
            actor_role=user.get("profile", {}).get("role"),
            payload_after={
                "entry_type": entry.entry_type,
                "amount": str(entry.amount),
                "balance_after": str(entry.balance_after),
                "project_id": entry.project_id,
                "related_id": entry.related_id
            },
            tags=["LEDGER_OPERATION"]
        )

        return entry
```

#### 2.4 死号迁移审计

**引用**: `BRD_chapter1_v3.1.md` 第9章 - 死号迁移流程

**迁移操作必须记录双向审计**:
```
1. TRANSFER_OUT (A账户转出)
   - resource_type: "transfer"
   - resource_id: "TRANSFER-20250121-001"
   - payload_before: {from_account: "A", balance: 1000}
   - payload_after: {from_account: "A", balance: 0, amount: -1000}

2. TRANSFER_IN (B账户转入)
   - resource_type: "transfer"
   - resource_id: "TRANSFER-20250121-001"
   - payload_before: {to_account: "B", balance: 0}
   - payload_after: {to_account: "B", balance: 1000, amount: +1000}

3. CREATE_REVERSAL_PAIR (创建红冲对)
   - actor: finance / admin
   - reason: "死号迁移: A→B，原因: 账户封禁"
   - tags: ["TRANSFER", "REVERSAL"]
```

#### 2.5 项目配置变更审计

**高敏感配置变更必审计**:
- 项目时区 (`timezone`)
- 项目预算 (`budget_total`)
- 客户经理变更 (`account_manager_id`)
- 项目状态变更 (`status`)

```python
def update_project(self, project_id: int, updates: ProjectUpdate, user: Dict) -> Project:
    """更新项目配置 (自动审计)"""
    project = self._get_project_or_404(project_id)

    # 记录修改前快照
    before_snapshot = {
        "name": project.name,
        "timezone": project.timezone,
        "budget_total": str(project.budget_total),
        "account_manager_id": str(project.account_manager_id),
        "status": project.status
    }

    # 应用更新
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(project, key, value)

    # 记录修改后快照
    after_snapshot = {
        "name": project.name,
        "timezone": project.timezone,
        "budget_total": str(project.budget_total),
        "account_manager_id": str(project.account_manager_id),
        "status": project.status
    }

    # 审计日志
    self._create_audit_log(
        action="UPDATE_PROJECT",
        resource_type="project",
        resource_id=str(project_id),
        actor_id=user.get("user", {}).id,
        actor_role=user.get("profile", {}).get("role"),
        payload_before=before_snapshot,
        payload_after=after_snapshot,
        tags=["PROJECT_CONFIG"]
    )

    self.db.commit()
    return project
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 审计日志写入失败 | `SYS_003` | 500 | "审计日志写入失败，操作已回滚" |

### 测试用例 (Test Intent)

**TC-AUDIT-002-01: 日报完整审计链路**
- **Given**: 投手 Alice 创建并提交日报 R1，数据操作员 Bob 审核通过
- **When**: 查询 R1 的审计日志
- **Then**: 返回 3 条日志: CREATE_REPORT, SUBMIT_REPORT, APPROVE_REPORT

**TC-AUDIT-002-02: 账本操作自动审计**
- **Given**: 财务人员 Carol 确认充值到账
- **When**: 系统创建 ledger_entry
- **Then**: 自动记录 CREATE_LEDGER_ENTRY 审计日志

**TC-AUDIT-002-03: 死号迁移双向审计**
- **Given**: 管理员 Admin 执行死号迁移 A→B
- **When**: 查询迁移审计日志
- **Then**: 返回 TRANSFER_OUT + TRANSFER_IN 两条日志，`resource_id` 相同

---

## BR-AUDIT-003: 审计日志字段规范

### 业务场景

为确保审计日志的完整性和可查询性，必须规范化字段命名、数据类型和必填要求。

### 规则定义

#### 3.1 核心字段规范

**引用**: `DATA_SCHEMA.md` 3.5.1 - `audit_logs` 表

| 字段 | 类型 | 必填 | 说明 | 示例 |
|-----|------|------|------|------|
| `action` | VARCHAR(100) | ✅ | 操作类型（大写+下划线） | `APPROVE_REPORT`, `ADMIN_FORCE_APPROVE` |
| `resource_type` | VARCHAR(50) | ✅ | 资源类型（小写+下划线） | `daily_report`, `topup_request`, `ledger_entry` |
| `resource_id` | VARCHAR(100) | ⚠️ | 资源ID（批量操作可为空） | `"12345"`, `"TRANSFER-20250121-001"` |
| `actor_id` | UUID | ✅ | 操作人ID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `actor_role` | VARCHAR(50) | ✅ | 操作人角色 | `"admin"`, `"finance"`, `"system"` |
| `payload_before` | JSONB | ⚠️ | 修改前快照（UPDATE/DELETE必填） | `{"status": "draft", "spend": 100.00}` |
| `payload_after` | JSONB | ⚠️ | 修改后快照（CREATE/UPDATE必填） | `{"status": "pending", "spend": 100.00}` |
| `reason` | TEXT | ⚠️ | 操作原因（管理员操作必填） | `"数据操作员离职，紧急审核"` |
| `tags` | TEXT[] | ⬜ | 标签数组 | `["ADMIN_OVERRIDE", "SOD_BYPASS"]` |
| `ip_address` | VARCHAR(45) | ⬜ | 操作IP（支持IPv6） | `"192.168.1.100"`, `"2001:db8::1"` |
| `user_agent` | TEXT | ⬜ | 浏览器UA | `"Mozilla/5.0 ..."` |
| `occurred_at` | TIMESTAMPTZ | ✅ | 操作时间（UTC） | `"2025-01-21T10:30:00Z"` |

**图例**:
- ✅ 必填
- ⚠️ 条件必填
- ⬜ 可选

#### 3.2 action 命名规范

**格式**: `动词_名词` (大写+下划线)

**常见动词**:
- `CREATE` - 创建资源
- `UPDATE` - 修改资源
- `DELETE` - 删除资源（逻辑删除）
- `SUBMIT` - 提交审核
- `APPROVE` - 审核通过
- `REJECT` - 审核拒绝
- `CANCEL` - 取消操作
- `RESTORE` - 恢复资源
- `ADMIN_FORCE_` - 管理员强制操作

**示例**:
```
CREATE_PROJECT
UPDATE_PROJECT
ARCHIVE_PROJECT
RESTORE_PROJECT
SUBMIT_REPORT
APPROVE_REPORT
REJECT_REPORT
ADMIN_FORCE_APPROVE
CONFIRM_TOPUP_COMPLETED
CREATE_LEDGER_ENTRY
TRANSFER_OUT
TRANSFER_IN
```

#### 3.3 payload 快照规范

**规则**: `payload_before` / `payload_after` 必须包含关键业务字段的完整快照。

**示例 - 日报审核**:
```json
{
  "action": "APPROVE_REPORT",
  "resource_type": "daily_report",
  "resource_id": "12345",
  "actor_id": "uuid-bob",
  "actor_role": "data_operator",
  "payload_before": {
    "status": "pending",
    "approved_by": null,
    "approved_at": null
  },
  "payload_after": {
    "status": "approved",
    "approved_by": "uuid-bob",
    "approved_at": "2025-01-21T10:30:00Z"
  },
  "occurred_at": "2025-01-21T10:30:00Z"
}
```

**示例 - 管理员强制修改**:
```json
{
  "action": "ADMIN_UPDATE_FINAL",
  "resource_type": "daily_report",
  "resource_id": "67890",
  "actor_id": "uuid-admin",
  "actor_role": "admin",
  "payload_before": {
    "conversions_final": 100,
    "status": "final_locked"
  },
  "payload_after": {
    "conversions_final": 95,
    "status": "final_locked"
  },
  "reason": "客户确认粉数错误，需紧急修正",
  "tags": ["ADMIN_OVERRIDE", "FINAL_LOCKED_MODIFY"],
  "occurred_at": "2025-01-21T11:00:00Z"
}
```

#### 3.4 reason 强制填写场景

**规则**: 以下操作 `reason` 为必填：

- 管理员强制操作 (`ADMIN_*`)
- 修改终态数据 (`final_locked`, `approved`, `completed`)
- 恢复归档资源 (`RESTORE_*`)
- 红冲操作 (`CREATE_REVERSAL`)
- 死号迁移 (`TRANSFER_*`)

```python
def validate_reason_required(action: str, actor_role: str):
    """验证是否需要填写原因"""
    # 管理员操作必须填写原因
    if action.startswith("ADMIN_"):
        return True

    # 特殊操作必须填写原因
    REASON_REQUIRED_ACTIONS = [
        "RESTORE_PROJECT",
        "RESTORE_ARCHIVED_ACCOUNT",
        "CREATE_REVERSAL",
        "TRANSFER_OUT",
        "TRANSFER_IN",
        "MODIFY_FINAL_LOCKED"
    ]

    return action in REASON_REQUIRED_ACTIONS
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 缺少必填字段 | `BIZ_002` | 400 | "审计日志缺少 action 字段" |
| reason未填写 | `BIZ_002` | 400 | "管理员操作必须提供 reason" |
| payload格式错误 | `BIZ_002` | 400 | "payload_before 必须为 JSON 对象" |

### 测试用例 (Test Intent)

**TC-AUDIT-003-01: 正常审计日志创建**
- **Given**: 投手 Alice 提交日报
- **When**: 系统创建审计日志
- **Then**:
  - `action` = `SUBMIT_REPORT`
  - `payload_before.status` = `"draft"`
  - `payload_after.status` = `"pending"`

**TC-AUDIT-003-02: 管理员操作缺少原因（禁止）**
- **Given**: 管理员 Admin 强制审核日报
- **When**: 调用 `admin_force_approve` without `reason`
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

**TC-AUDIT-003-03: payload 快照完整性验证**
- **Given**: 更新项目预算从 10000 → 20000
- **When**: 查询审计日志
- **Then**:
  - `payload_before.budget_total` = `"10000.00"`
  - `payload_after.budget_total` = `"20000.00"`

---

## BR-AUDIT-004: 系统自动动作审计

### 业务场景

系统自动化流程（如趋势风控检查、计费锁定）也需要记录审计日志，`actor_role` 设为 `system`，确保所有状态变更可追溯。

### 规则定义

#### 4.1 system 用户标识

**规则**: 系统自动操作使用特殊用户标识：

- `actor_id`: `00000000-0000-0000-0000-000000000000` (全零UUID)
- `actor_role`: `"system"`
- `tags`: 必须包含 `"SYSTEM_AUTO"`

```python
# backend/services/audit_service.py
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")

def create_system_audit_log(
    action: str,
    resource_type: str,
    resource_id: str,
    payload_before: Dict = None,
    payload_after: Dict = None,
    notes: str = None
):
    """创建系统自动操作审计日志"""
    return AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=SYSTEM_USER_ID,
        actor_role="system",
        payload_before=payload_before,
        payload_after=payload_after,
        reason=notes,
        tags=["SYSTEM_AUTO"],
        occurred_at=datetime.now(timezone.utc)
    )
```

#### 4.2 自动化流程审计示例

**趋势风控检查**:
```python
# backend/services/daily_report_service.py
def trigger_trend_check(self, report_id: int):
    """触发趋势风控检查 (系统自动)"""
    report = self._get_report_or_404(report_id)

    # 状态流转: raw_submitted → trend_pending
    report.status = "trend_pending"

    # 执行风控检查
    is_flagged, reason = self._check_trend_anomaly(report)

    if is_flagged:
        report.status = "trend_flagged"
        report.trend_flag_reason = reason
    else:
        report.status = "trend_ok"

    # 系统审计日志
    self._create_system_audit_log(
        action="TREND_CHECK_AUTO",
        resource_type="daily_report",
        resource_id=str(report_id),
        payload_before={"status": "raw_submitted"},
        payload_after={
            "status": report.status,
            "trend_flag_reason": report.trend_flag_reason
        },
        notes=f"系统自动风控检查: {reason if is_flagged else '正常'}"
    )

    self.db.commit()
```

**计费锁定**:
```python
def lock_final_for_billing(self, report_id: int):
    """计费锁定 (系统自动)"""
    report = self._get_report_or_404(report_id)

    # 状态流转: final_confirmed → final_locked
    report.status = "final_locked"
    report.locked_at = datetime.now(timezone.utc)

    # 创建 ledger_entry (REVENUE)
    revenue = report.conversions_final * report.unit_price
    ledger_entry = self._create_ledger_entry(
        project_id=report.project_id,
        entry_type="REVENUE",
        amount=revenue,
        related_id=report.id,
        notes=f"粉数计费: {report.conversions_final} × {report.unit_price}"
    )

    # 系统审计日志
    self._create_system_audit_log(
        action="BILLING_LOCK_AUTO",
        resource_type="daily_report",
        resource_id=str(report_id),
        payload_before={"status": "final_confirmed"},
        payload_after={
            "status": "final_locked",
            "locked_at": report.locked_at.isoformat(),
            "ledger_entry_id": ledger_entry.id
        },
        notes=f"系统自动计费锁定，revenue = {revenue}"
    )

    self.db.commit()
```

### 测试用例 (Test Intent)

**TC-AUDIT-004-01: 系统自动风控检查**
- **Given**: 日报 R1 状态为 `raw_submitted`
- **When**: 系统执行趋势风控检查，发现粉数骤降
- **Then**:
  - 状态变为 `trend_flagged`
  - 审计日志 `actor_role` = `"system"`
  - `tags` 包含 `"SYSTEM_AUTO"`

**TC-AUDIT-004-02: 系统自动计费锁定**
- **Given**: 日报 R2 状态为 `final_confirmed`
- **When**: 系统到达 T+1日 14:00，执行计费锁定
- **Then**:
  - 状态变为 `final_locked`
  - 创建 ledger_entry
  - 审计日志记录 `BILLING_LOCK_AUTO`

---

## BR-AUDIT-005: 审计日志查询与过滤

### 业务场景

管理员、财务人员需要根据时间、角色、模块等维度查询审计日志，快速定位异常操作。

### 规则定义

#### 5.1 查询权限矩阵

| 角色 | 可查询范围 | 说明 |
|-----|-----------|------|
| `admin` | 全部审计日志 | 无限制 |
| `finance` | 财务相关模块 | `topup_request`, `ledger_entry`, `reconciliation_batch` |
| `data_operator` | 数据相关模块 | `daily_report`, `ad_account` |
| `account_manager` | 自己管理的项目 | 仅可查看自己项目的审计日志 |
| `media_buyer` | ❌ 禁止访问 | 投手无权查看审计日志 |

#### 5.2 查询接口设计

```python
# backend/routers/audit_logs.py
@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tags: Optional[List[str]] = Query(None),
    pagination: PaginationParams = Depends(),
    user: Dict = Depends(get_current_user),
    service: AuditService = Depends()
):
    """查询审计日志"""
    filters = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "actor_id": actor_id,
        "action": action,
        "start_date": start_date,
        "end_date": end_date,
        "tags": tags
    }

    result = service.list_logs(filters, user, pagination)

    return PaginatedResponse(
        total=result["total"],
        items=[AuditLogResponse.model_validate(log) for log in result["items"]],
        page=pagination.page,
        page_size=pagination.page_size
    )
```

#### 5.3 敏感操作高亮规则

**高危标签** (需前端高亮显示):
- `ADMIN_OVERRIDE` - 管理员强制操作
- `SOD_BYPASS` - 职责分离绕过
- `FINAL_LOCKED_MODIFY` - 修改已锁定数据
- `TRANSFER` - 死号迁移
- `REVERSAL` - 红冲操作

```typescript
// frontend/components/AuditLogTable.tsx
function getActionBadgeColor(tags: string[]): string {
  if (tags.includes("ADMIN_OVERRIDE")) return "red";
  if (tags.includes("FINAL_LOCKED_MODIFY")) return "orange";
  if (tags.includes("TRANSFER")) return "purple";
  if (tags.includes("SYSTEM_AUTO")) return "blue";
  return "gray";
}
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 无权访问审计日志 | `AUTH_500` | 403 | "投手无权查看审计日志" |
| 跨项目查询 | `AUTH_500` | 403 | "您无权查看该项目的审计日志" |

### 测试用例 (Test Intent)

**TC-AUDIT-005-01: 管理员查询所有审计日志**
- **Given**: 管理员 Admin
- **When**: Admin 调用 `GET /audit-logs`
- **Then**: 返回所有审计日志

**TC-AUDIT-005-02: 财务人员查询充值审计日志**
- **Given**: 财务人员 Carol
- **When**: Carol 调用 `GET /audit-logs?resource_type=topup_request`
- **Then**: 返回所有充值申请的审计日志

**TC-AUDIT-005-03: 按时间范围查询**
- **Given**: 管理员 Admin
- **When**: Admin 调用 `GET /audit-logs?start_date=2025-01-01&end_date=2025-01-31`
- **Then**: 返回 2025年1月的审计日志

**TC-AUDIT-005-04: 按标签筛选高危操作**
- **Given**: 管理员 Admin
- **When**: Admin 调用 `GET /audit-logs?tags=ADMIN_OVERRIDE`
- **Then**: 返回所有管理员强制操作的日志

**TC-AUDIT-005-05: 投手尝试查询审计日志（禁止）**
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

### B. 审计日志 action 速查表

| action | 中文名称 | resource_type | actor_role |
|--------|---------|---------------|-----------|
| CREATE_PROJECT | 创建项目 | project | account_manager, admin |
| APPROVE_REPORT | 审核日报 | daily_report | data_operator, admin |
| ADMIN_FORCE_APPROVE | 管理员强制审核 | daily_report | admin |
| CREATE_LEDGER_ENTRY | 创建账本记录 | ledger_entry | system, finance, admin |
| TRANSFER_OUT | 死号迁移转出 | transfer | admin, finance |
| BILLING_LOCK_AUTO | 系统计费锁定 | daily_report | system |
| TREND_CHECK_AUTO | 系统趋势检查 | daily_report | system |

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-01-21 | 初始版本，包含 BR-AUDIT-001~005 | 系统架构团队 |

---

**END OF DOCUMENT**
