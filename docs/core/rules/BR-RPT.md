# BR-RPT: 日报管理业务规则

> **文档版本**: v2.0
> **最后更新**: 2025-01-21
> **所属模块**: 日报管理 (Daily Report Management)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义 (v5.1)
> - `ERROR_CODES.md` - 错误码定义
> - `STATE_MACHINE.md` - 粉数确认状态机 (v2.6)
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
> - `BRD_chapter1_v3.1.md` - 业务需求基线

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-RPT-001 | 日报提交权限与约束 | P0 | ✅ Active |
| BR-RPT-002 | 日报审核权限控制 | P0 | ✅ Active |
| BR-RPT-004 | 终态保护与数据锁定 | P0 | ✅ Active |
| BR-RPT-005 | 粉数确认流程规则 | P0 | ✅ Active |

---

## BR-RPT-001: 日报提交权限与约束

### 业务场景

投手 (Media Buyer) 每日需要提交广告账户的消费数据日报。系统必须确保日报数据的真实性和时效性，防止提交未来日期或重复日期的日报。

### 规则定义

#### 1.1 角色权限约束

**允许提交日报的角色**:
- `media_buyer` - 投手可为自己负责的广告账户提交日报
- `admin` - 管理员可代替任何投手提交日报（紧急情况）

**禁止提交日报的角色**:
- ❌ `account_manager` - 客户经理仅可查看日报
- ❌ `data_operator` - 数据操作员仅负责审核，不能提交
- ❌ `finance` - 财务人员仅可查看日报

#### 1.2 字段约束

**引用**: `DATA_SCHEMA.md` 3.3.1 - `daily_reports` 表

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `report_date` | DATE | **NOT NULL** | 日报日期，必须 <= 当前服务器时间(UTC) |
| `ad_account_id` | BIGINT | **NOT NULL, FK → ad_accounts.id** | 必须绑定有效的广告账户 |
| `spend` | DECIMAL(15,2) | **NOT NULL, >= 0** | 广告消费金额，不能为负数 |
| `impressions` | BIGINT | >= 0 | 展示次数 |
| `clicks` | BIGINT | >= 0 | 点击次数 |
| `conversions` | INTEGER | >= 0 | 转化次数 |
| `status` | VARCHAR(20) | DEFAULT 'draft' | 初始状态为 `draft` |
| `created_by` | UUID | **NOT NULL, FK → users.id** | 创建人ID |

**唯一性约束**:
```sql
-- report_date + ad_account_id 组合唯一
CREATE UNIQUE INDEX daily_reports_date_account_key
    ON daily_reports(report_date, ad_account_id);
```

#### 1.3 日期合规性校验

**核心规则**: `report_date` 必须 <= 当前服务器时间(UTC)，禁止提交未来日期的日报。

**时区处理** (引用 `MASTER_DESIGN_DOCUMENT.md` 4.3):
- 后端接收日期时使用UTC时间
- 截止时间以项目配置的时区为准

**示例**:
```python
# backend/services/daily_report_service.py
class DailyReportService:
    def create_report(self, payload: DailyReportCreate, user: Dict) -> DailyReport:
        # 1. 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "media_buyer"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅投手可以提交日报"
            )

        # 2. 验证广告账户存在性
        account = self.db.query(AdAccount).filter(
            AdAccount.id == payload.ad_account_id
        ).first()

        if not account:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
                message=f"广告账户 {payload.ad_account_id} 不存在"
            )

        # 3. 验证用户是否有权限访问该账户
        if user_role == "media_buyer":
            if account.assigned_to != user.get("user", {}).id:
                raise AuthorizationException(
                    code=AuthErrorCodes.PERMISSION_DENIED.code,
                    message="您没有权限为该账户提交日报"
                )

        # 4. 验证账户状态（不能为死亡或归档状态）
        if account.status in ["dead", "archived"]:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"账户状态为 {account.status}，无法提交日报"
            )

        # 5. 日期合规性检查
        today_utc = datetime.now(timezone.utc).date()
        if payload.report_date > today_utc:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_DATE.code,  # BIZ_201
                message=f"日报日期 {payload.report_date} 不能晚于当前日期 {today_utc}"
            )

        # 6. 检查唯一性（同一账户同一天只能有一条日报）
        existing = self.db.query(DailyReport).filter(
            DailyReport.report_date == payload.report_date,
            DailyReport.ad_account_id == payload.ad_account_id
        ).first()

        if existing:
            raise ConflictException(
                code=BusinessErrorCodes.RESOURCE_ALREADY_EXISTS.code,
                message=f"日期 {payload.report_date} 的日报已存在"
            )

        # 7. 数据合规性检查
        if payload.spend < 0:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="广告消费金额不能为负数"
            )

        # 8. 创建日报
        report = DailyReport(
            report_date=payload.report_date,
            ad_account_id=payload.ad_account_id,
            spend=payload.spend,
            impressions=payload.impressions or 0,
            clicks=payload.clicks or 0,
            conversions=payload.conversions or 0,
            status="draft",
            created_by=user.get("user", {}).id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.db.add(report)
        self.db.commit()

        return report
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 角色权限不足 | `AUTH_500` | 403 | "仅投手可以提交日报" |
| 广告账户不存在 | `BIZ_100` | 404 | "广告账户 12345 不存在" |
| 无账户访问权限 | `AUTH_500` | 403 | "您没有权限为该账户提交日报" |
| 账户状态无效 | `BIZ_001` | 400 | "账户状态为 dead，无法提交日报" |
| 日期为未来 | `BIZ_201` | 400 | "日报日期不能晚于当前日期" |
| 日期重复 | `BIZ_003` | 409 | "日期 2025-11-20 的日报已存在" |
| 消费为负数 | `BIZ_002` | 400 | "广告消费金额不能为负数" |

**引用**: `ERROR_CODES.md` - 认证错误码 (AUTH_*), 业务错误码 (BIZ_*)

### 测试用例 (Test Intent)

**TC-RPT-001-01: 投手正常提交日报**
- **Given**: 投手 Alice 负责账户 #1001，今天是 2025-11-20 (UTC)
- **When**: Alice 提交日报 `{report_date: "2025-11-20", ad_account_id: 1001, spend: 500.00}`
- **Then**:
  - 创建成功，返回 HTTP 201
  - `status` 为 `draft`
  - `created_by` 为 Alice 的ID

**TC-RPT-001-02: 提交未来日期日报（禁止）**
- **Given**: 投手 Alice，今天是 2025-11-20 (UTC)
- **When**: Alice 尝试提交 `{report_date: "2025-11-21", ...}`
- **Then**: 返回 HTTP 400，错误码 `BIZ_201`

**TC-RPT-001-03: 重复提交同一天日报**
- **Given**: 账户 #1001 已有 2025-11-20 的日报
- **When**: Alice 再次提交同日期日报
- **Then**: 返回 HTTP 409，错误码 `BIZ_003`

**TC-RPT-001-04: 投手尝试提交他人账户日报**
- **Given**: 投手 Alice 负责账户 #1001，投手 Bob 负责账户 #1002
- **When**: Alice 尝试提交账户 #1002 的日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-RPT-001-05: 为死亡账户提交日报（禁止）**
- **Given**: 账户 #1003 状态为 `dead`
- **When**: 尝试提交日报
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-RPT-001-06: 消费金额为负数**
- **Given**: 投手 Alice
- **When**: 提交日报 `{spend: -100.00}`
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

**TC-RPT-001-07: 数据操作员尝试提交日报**
- **Given**: 用户 Carol 角色为 `data_operator`
- **When**: Carol 尝试提交日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

---

## BR-RPT-002: 日报审核权限控制

### 业务场景

数据操作员 (Data Operator) 负责审核投手提交的日报数据，确保数据的准确性和完整性。系统必须确保审核权限的严格控制，防止投手自我审核。

### 规则定义

#### 2.1 角色权限约束

**允许审核日报的角色**:
- `data_operator` - 数据操作员负责日报审核
- `admin` - 管理员可执行审核操作（紧急情况）

**禁止审核日报的角色**:
- ❌ `media_buyer` - 投手不能审核自己提交的日报
- ❌ `account_manager` - 客户经理无审核权限
- ❌ `finance` - 财务人员无审核权限

#### 2.2 状态机流转规则

**引用**: `STATE_MACHINE.md` - 日报状态机 (Daily Report Lifecycle)

```
┌─────────┐   提交      ┌─────────┐   审核通过   ┌──────────┐
│  draft  │ ────────→  │ pending │ ─────────→  │ approved │
└─────────┘            └─────────┘             └──────────┘
     ▲                      │                        (终态)
     │ 驳回                 │ 驳回
     └──────────────────────┴────────────────→ ┌──────────┐
                                               │ rejected │
                                               └──────────┘
                                                  (终态)
```

**状态流转矩阵**:

| 当前状态 | 目标状态 | 允许角色 | 操作 |
|---------|---------|---------|------|
| `draft` | `pending` | `media_buyer` (提交人) | 提交审核 |
| `pending` | `approved` | `data_operator`, `admin` | 审核通过 |
| `pending` | `rejected` | `data_operator`, `admin` | 审核拒绝 |
| `rejected` | `draft` | `media_buyer` (原提交人) | 重新编辑 |
| `approved` | - | 禁止流转 | 终态 |
| `rejected` | - | 禁止流转 | 终态 |

#### 2.3 Service层实现示例

```python
# backend/services/daily_report_service.py
class DailyReportService:
    def submit_for_review(self, report_id: int, user: Dict) -> DailyReport:
        """提交日报审核 (draft → pending)"""
        report = self._get_report_or_404(report_id)

        # 仅创建人可提交
        if report.created_by != user.get("user", {}).id:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅日报创建人可以提交审核"
            )

        # 状态流转校验
        ensure_transition_allowed(report.status, "pending")

        with self.db.begin():
            report.status = "pending"
            report.submitted_at = datetime.now(timezone.utc)
            report.updated_at = datetime.now(timezone.utc)

            self._create_audit_log(
                action="SUBMIT_REPORT",
                entity_id=str(report.id),
                user=user,
                payload_before={"status": "draft"},
                payload_after={"status": "pending"}
            )

        return report

    def approve_report(self, report_id: int, user: Dict, comments: str = None) -> DailyReport:
        """审核通过日报 (pending → approved)"""
        report = self._get_report_or_404(report_id)

        # 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "data_operator"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅数据操作员可以审核日报"
            )

        # 状态流转校验
        ensure_transition_allowed(report.status, "approved")

        # 职责分离检查：审核人 ≠ 提交人
        if report.created_by == user.get("user", {}).id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="不能审核自己提交的日报（职责分离）"
            )

        with self.db.begin():
            report.status = "approved"
            report.approved_by = user.get("user", {}).id
            report.approved_at = datetime.now(timezone.utc)
            report.reviewer_comments = comments
            report.updated_at = datetime.now(timezone.utc)

            self._create_audit_log(
                action="APPROVE_REPORT",
                entity_id=str(report.id),
                user=user,
                payload_before={"status": "pending"},
                payload_after={"status": "approved", "comments": comments}
            )

        return report

    def reject_report(self, report_id: int, user: Dict, reason: str) -> DailyReport:
        """审核拒绝日报 (pending → rejected)"""
        report = self._get_report_or_404(report_id)

        # 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "data_operator"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅数据操作员可以审核日报"
            )

        # 状态流转校验
        ensure_transition_allowed(report.status, "rejected")

        # 必须提供拒绝原因
        if not reason:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="拒绝日报时必须提供原因"
            )

        with self.db.begin():
            report.status = "rejected"
            report.approved_by = user.get("user", {}).id
            report.approved_at = datetime.now(timezone.utc)
            report.reviewer_comments = reason
            report.updated_at = datetime.now(timezone.utc)

            self._create_audit_log(
                action="REJECT_REPORT",
                entity_id=str(report.id),
                user=user,
                payload_before={"status": "pending"},
                payload_after={"status": "rejected", "reason": reason}
            )

        return report
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 角色权限不足 | `AUTH_500` | 403 | "仅数据操作员可以审核日报" |
| 投手自我审核 | `BIZ_001` | 400 | "不能审核自己提交的日报" |
| 非法状态流转 | `STATE_400` | 400 | "非法状态流转: approved → pending" |
| 缺少拒绝原因 | `BIZ_002` | 400 | "拒绝日报时必须提供原因" |

### 测试用例 (Test Intent)

**TC-RPT-002-01: 正常审核通过流程**
- **Given**: 投手 Alice 提交日报 R1，数据操作员 Bob
- **When**:
  1. Alice 提交审核 (draft → pending)
  2. Bob 审核通过 (pending → approved)
- **Then**:
  - 状态变为 `approved`
  - `approved_by` 为 Bob 的ID
  - 审计日志记录2次操作

**TC-RPT-002-02: 审核拒绝并重新提交**
- **Given**: 日报 R2 状态为 `pending`
- **When**:
  1. Bob 拒绝日报，原因 "数据异常"
  2. Alice 修改后重新提交
- **Then**: 状态变为 `rejected` → `draft` → `pending`

**TC-RPT-002-03: 投手尝试审核自己的日报**
- **Given**: 投手 Alice 提交日报 R3，状态为 `pending`
- **When**: Alice 尝试审核通过自己的日报
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-RPT-002-04: 客户经理尝试审核日报**
- **Given**: 客户经理 Carol，日报 R4 状态为 `pending`
- **When**: Carol 尝试审核日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

**TC-RPT-002-05: 拒绝日报但未提供原因**
- **Given**: 数据操作员 Bob，日报 R5 状态为 `pending`
- **When**: Bob 调用拒绝接口但 `reason` 为空
- **Then**: 返回 HTTP 400，错误码 `BIZ_002`

---

## BR-RPT-004: 终态保护与数据锁定

### 业务场景

日报一旦审核通过 (`approved`) 或拒绝 (`rejected`)，数据必须锁定，防止事后篡改。这是审计合规的关键要求。

### 规则定义

#### 4.1 终态定义

**引用**: `MASTER_DESIGN_DOCUMENT.md` 第 5.2.2 节 - 终态保护规则

**终态列表**:
- `approved` - 审核通过（不可修改）
- `rejected` - 审核拒绝（不可修改）

**非终态**:
- `draft` - 可编辑
- `pending` - 审核中（仅可审核操作，不可编辑数据）

#### 4.2 数据锁定规则

**核心规则**: 日报进入终态后，禁止修改任何业务字段（spend, impressions, clicks 等）。

**允许的操作**:
- ✅ 查询（GET）
- ✅ 添加审核备注（仅admin）

**禁止的操作**:
- ❌ 修改消费金额、展示次数等业务数据
- ❌ 修改日报日期
- ❌ 修改状态（终态不可流转）

**实现**:
```python
class DailyReportService:
    def update_report(self, report_id: int, updates: DailyReportUpdate, user: Dict) -> DailyReport:
        """更新日报数据"""
        report = self._get_report_or_404(report_id)

        # 终态保护检查
        FINAL_STATUSES = ["approved", "rejected"]
        if report.status in FINAL_STATUSES:
            # 仅admin可添加备注
            if user.get("profile", {}).get("role") == "admin" and updates.is_only_note():
                # 允许admin添加备注
                report.admin_notes = updates.admin_notes
                report.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                return report
            else:
                raise BusinessRuleException(
                    code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,  # STATE_400
                    message=f"日报状态为 {report.status}，数据已锁定，无法编辑"
                )

        # 仅创建人可编辑
        if report.created_by != user.get("user", {}).id:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅日报创建人可以编辑"
            )

        # 状态检查：只有 draft 状态可编辑
        if report.status != "draft":
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="仅草稿状态的日报可编辑"
            )

        # 允许编辑
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(report, key, value)

        report.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return report
```

#### 4.3 重新提交机制

**规则**: `rejected` 状态的日报可恢复为 `draft`，修改后重新提交，但会生成新的审核记录。

**实现**:
```python
def reopen_rejected_report(self, report_id: int, user: Dict) -> DailyReport:
    """重新打开被拒绝的日报 (rejected → draft)"""
    report = self._get_report_or_404(report_id)

    # 仅创建人可重新打开
    if report.created_by != user.get("user", {}).id:
        raise AuthorizationException(
            code=AuthErrorCodes.PERMISSION_DENIED.code,
            message="仅日报创建人可以重新打开"
        )

    # 状态检查
    if report.status != "rejected":
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message="仅被拒绝的日报可以重新打开"
        )

    with self.db.begin():
        report.status = "draft"
        report.updated_at = datetime.now(timezone.utc)

        self._create_audit_log(
            action="REOPEN_REPORT",
            entity_id=str(report.id),
            user=user,
            payload_before={"status": "rejected"},
            payload_after={"status": "draft"}
        )

    return report
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 终态数据锁定 | `STATE_400` | 400 | "日报状态为 approved，数据已锁定" |
| 非draft状态编辑 | `BIZ_001` | 400 | "仅草稿状态的日报可编辑" |
| 非创建人编辑 | `AUTH_500` | 403 | "仅日报创建人可以编辑" |

### 测试用例 (Test Intent)

**TC-RPT-004-01: 尝试修改已审核通过的日报**
- **Given**: 日报 R1 状态为 `approved`，创建人 Alice
- **When**: Alice 尝试修改消费金额
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

**TC-RPT-004-02: 管理员添加备注（允许）**
- **Given**: 日报 R2 状态为 `approved`，管理员 Admin
- **When**: Admin 添加 `admin_notes` 字段
- **Then**: 更新成功，其他字段未修改

**TC-RPT-004-03: 重新打开被拒绝的日报**
- **Given**: 日报 R3 状态为 `rejected`，创建人 Alice
- **When**: Alice 调用 `POST /daily-reports/R3/reopen`
- **Then**: 状态恢复为 `draft`，可重新编辑

**TC-RPT-004-04: 修改pending状态日报（禁止）**
- **Given**: 日报 R4 状态为 `pending`
- **When**: 创建人尝试修改数据
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-RPT-004-05: 非创建人尝试编辑draft日报**
- **Given**: 日报 R5 状态为 `draft`，创建人 Alice，投手 Bob
- **When**: Bob 尝试编辑日报
- **Then**: 返回 HTTP 403，错误码 `AUTH_500`

---

## BR-RPT-005: 粉数确认流程规则

### 业务场景

基于BRD v3.1第4章"粉数确认状态机"，系统采用**三数据流分离设计**（raw/real/final），final粉数需经过趋势风控检查后方可锁定进入计费。本规则定义粉数确认全流程的角色权限、时效约束、状态流转与数据约束。

### 规则定义

#### 5.1 三数据流定义

**引用**: `DATA_SCHEMA.md` 3.3.1 - `daily_reports` 表, `STATE_MACHINE.md` 第8章 - 粉数确认状态机

| 数据流 | 字段名 | 类型 | 提交者 | 时效性 | 用途 |
|-------|-------|------|--------|--------|------|
| **raw数据流** | `conversions_raw`, `raw_spend` | INTEGER, DECIMAL(15,2) | `media_buyer` | T+0 23:59前 | 趋势监控，风控检查 |
| **real数据流** | `real_spend` | DECIMAL(15,2) | `data_operator` | T+1 12:00前 | 成本核算基准 |
| **final数据流** | `conversions_final` | INTEGER | `data_operator` | T+1 14:00前 | 计费基准（唯一计费数据） |

**核心业务规则**:
- ✅ `conversions_raw` ≠ `conversions_final` (允许运营调整)
- ✅ `raw_spend` ≠ `real_spend` (真实消耗以供应商后台为准)
- ✅ `conversions_final` 一旦确认，除红冲外不可修改
- ❌ 禁止使用`raw_spend`计算成本
- ❌ 禁止跳过final直接计费

#### 5.2 八状态流转规则

**引用**: `STATE_MACHINE.md` 第8章 - 粉数确认状态机 (v2.6)

```
T+0日 23:59前: 投手提交raw
├─ raw_submitted → trend_pending (系统自动)
├─ trend_pending → trend_ok (风控通过,系统自动)
├─ trend_pending → trend_flagged (风控异常,系统自动)

运营复核:
├─ trend_flagged → trend_resolved (运营确认正常)
├─ trend_flagged → raw_submitted (运营要求投手重新提交)

T+1日 12:00前: 运营录入real_spend
├─ trend_ok → final_pending (运营录入real_spend)
├─ trend_resolved → final_pending (运营录入real_spend)

T+1日 14:00前: 运营确认final
├─ final_pending → final_confirmed (运营确认final)

计费锁定:
├─ final_confirmed → final_locked (系统计费锁定,不可逆)
```

**状态详解**:

| 状态 | 说明 | 触发者 | 可修改字段 |
|-----|------|-------|-----------|
| `raw_submitted` | 投手提交原始粉数 | `media_buyer` | `conversions_raw`, `raw_spend` |
| `trend_pending` | 等待趋势风控检查 | 系统自动 | 无 |
| `trend_ok` | 趋势正常 | 系统自动 | 无 |
| `trend_flagged` | 趋势异常,需人工复核 | 系统自动 | `trend_flag_reason` |
| `trend_resolved` | 运营确认异常已解决 | `data_operator` | `trend_resolution_note` |
| `final_pending` | 等待最终粉数确认 | `data_operator` | `conversions_final`, `real_spend` |
| `final_confirmed` | 最终粉数已确认 | `data_operator` | 无 |
| `final_locked` | 已进入计费,锁定 | 系统自动 | 无(仅可红冲) |

#### 5.3 趋势风控规则 (Trend Risk Control)

**规则编号**: TF-001/002/003 (定义于 `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第2.3.1节)

| 规则编号 | 规则名称 | 判断逻辑 | 触发后果 |
|---------|---------|---------| ---------|
| **TF-001** | 粉数骤降检查 | `conversions_raw < 昨日最大值 × 0.5` | `trend_flagged` |
| **TF-002** | 粉数骤增检查 | `conversions_raw > 昨日最大值 × 3` | `trend_flagged` |
| **TF-003** | 消耗异常检查 | `raw_spend > 昨日 × 2` | `trend_flagged` |

**触发后处理**:
1. 系统自动将状态设为 `trend_flagged`
2. 填充 `trend_flag_reason` 字段 (如 "TF-001: 粉数骤降50%")
3. 通知 `data_operator` 进行人工复核
4. 运营复核后填写 `trend_resolution_note`
5. 运营确认后流转至 `trend_resolved`

**业务约束**:
- ✅ trend_flagged状态下,禁止进入final_pending
- ✅ 运营必须填写`trend_resolution_note`
- ✅ 风控检查自动执行,运营可手动重新检查
- ❌ 禁止关闭风控检查

#### 5.4 角色权限矩阵

| 操作 | 允许角色 | 说明 |
|-----|---------|------|
| 提交raw粉数 | `media_buyer` | raw_submitted状态 |
| 趋势风控检查 | 系统自动 | trend_pending → trend_ok/flagged |
| 趋势风控复核 | `data_operator`, `admin` | trend_flagged → trend_resolved |
| 录入real_spend | `data_operator`, `admin` | 填充real_spend字段 |
| 确认final粉数 | `data_operator`, `admin` | final_pending → final_confirmed |
| 计费锁定 | 系统自动 | final_confirmed → final_locked |
| 红冲修正 | `admin` | final_locked后的唯一修正方式 |

#### 5.5 时效性约束

**T+0日 23:59前** (投手提交截止):
- 投手必须提交 `conversions_raw`, `raw_spend`
- 逾期提交系统标记为"延迟提交"，需审批
- 状态自动流转至 `trend_pending` 进行风控检查

**T+1日 12:00前** (运营录入real_spend截止):
- 运营从供应商后台获取真实消耗数据
- 录入 `real_spend` 字段 (成本核算基准)
- 状态流转至 `final_pending`

**T+1日 14:00前** (运营确认final截止):
- 运营复核粉数质量，确认 `conversions_final`
- `conversions_final` 允许与 `conversions_raw` 不同
- 状态流转至 `final_confirmed`

**T+1日 14:00后** (系统计费锁定):
- 系统自动计费: `revenue = conversions_final × unit_price`
- 生成PROJECT账本记录 (entry_type=REVENUE)
- 生成SUPPLIER账本记录 (entry_type=COST, amount=real_spend)
- 状态锁定至 `final_locked` (终态)

#### 5.6 计费公式与双账本

**引用**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第2.2节, `BRD_chapter1_v3.1.md` 第7-8章

**PROJECT账本收入**:
```
revenue = conversions_final × unit_price
```

**SUPPLIER账本成本**:
```
cost = real_spend + fee  (fee通常为0)
```

**项目毛利**:
```
profit = revenue - cost
```

**示例**:
```
T+0日: 投手提交
├─ conversions_raw = 100
├─ raw_spend = 5000
└─ status = raw_submitted

T+0日: 系统风控检查
└─ status = trend_ok (或trend_flagged)

T+1日: 运营确认final
├─ conversions_final = 95  (运营调整-5)
├─ real_spend = 4800  (运营录入真实消耗)
└─ status = final_confirmed

T+1日: 系统计费锁定
├─ status = final_locked
├─ Ledger记录1 (PROJECT账本):
│   ├─ entry_type = REVENUE
│   ├─ amount = 95 × 50 = 4750.00
│   └─ project_id = 123
└─ Ledger记录2 (SUPPLIER账本):
    ├─ entry_type = COST
    ├─ amount = 4800.00
    └─ supplier_id = 456

项目毛利 = 4750 - 4800 = -50.00 (亏损)
```

#### 5.7 final_locked 红冲修正机制

**核心原则**: `final_locked`状态后,所有修正必须通过**红冲机制**完成。

**红冲流程**:
```
1. 发现final_locked数据错误
2. 创建REVERSAL记录 (entry_type=REVERSAL, amount=-原金额)
3. 冲销原Ledger记录
4. 生成新的正确Ledger记录
5. 更新项目余额
6. 记录审计日志
```

**示例**:
```
原始数据:
├─ conversions_final = 100
├─ revenue = 100 × 50 = 5000
└─ Ledger记录: entry_type=REVENUE, amount=5000

发现错误(应为95粉):
├─ Step1: 创建红冲记录
│   ├─ entry_type = REVERSAL
│   ├─ amount = -5000
│   └─ notes = "红冲原记录#12345,粉数错误"
├─ Step2: 生成新记录
│   ├─ entry_type = REVENUE
│   ├─ amount = 95 × 50 = 4750
│   └─ notes = "修正后的正确记录"
└─ Step3: 更新项目余额
    └─ balance = balance - 5000 + 4750
```

**业务规则**:
- ✅ 红冲金额 = -原金额
- ✅ 红冲后重新生成正确的Ledger记录
- ✅ 审计日志记录完整链条
- ❌ 禁止直接UPDATE daily_reports的conversions_final
- ❌ 禁止直接DELETE Ledger记录

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 投手提交逾期 | `BIZ_201` | 400 | "当前时间已超过T+0日23:59，需审批" |
| 趋势风控触发 | `TREND_001` | 200 | "粉数骤降，已标记trend_flagged" |
| 跳过风控复核 | `STATE_400` | 400 | "trend_flagged状态必须复核" |
| real_spend未录入 | `BIZ_002` | 400 | "real_spend为必填字段" |
| final确认逾期 | `BIZ_201` | 400 | "当前时间已超过T+1日14:00，需审批" |
| final_locked修改 | `STATE_400` | 400 | "final_locked状态仅可红冲修正" |

**引用**: `ERROR_CODES.md` - 业务错误码 (BIZ_*), 状态错误码 (STATE_*), 趋势风控错误码 (TREND_*)

### 测试用例 (Test Intent)

**TC-RPT-005-01: 完整粉数确认流程（正向）**
- **Given**: 投手 Alice 负责账户 #1001，今天是 2025-01-20 T+0日 23:00
- **When**:
  1. Alice 提交日报 `{conversions_raw: 100, raw_spend: 5000}`
  2. 系统风控检查通过 (trend_ok)
  3. 2025-01-21 T+1日 11:00, 运营录入 `real_spend: 4800`
  4. 2025-01-21 T+1日 13:00, 运营确认 `conversions_final: 95`
  5. 2025-01-21 T+1日 14:01, 系统自动计费锁定
- **Then**:
  - 状态流转: raw_submitted → trend_ok → final_pending → final_confirmed → final_locked
  - 生成2条Ledger记录 (PROJECT + SUPPLIER)
  - 项目毛利 = 95×50 - 4800 = -50.00

**TC-RPT-005-02: 趋势风控触发与复核**
- **Given**: 投手 Alice，昨日粉数最大值 200
- **When**: Alice 提交 `conversions_raw: 90` (骤降55%)
- **Then**:
  - 系统自动流转至 `trend_flagged`
  - `trend_flag_reason` = "TF-001: 粉数骤降55%"
  - 通知运营复核
  - 运营填写 `trend_resolution_note` 后流转至 `trend_resolved`

**TC-RPT-005-03: 投手逾期提交（禁止）**
- **Given**: 今天是 2025-01-21 T+1日 01:00
- **When**: Alice 尝试提交T+0日 (2025-01-20) 的日报
- **Then**: 返回 HTTP 400，错误码 `BIZ_201`，提示"已逾期，需审批"

**TC-RPT-005-04: 跳过风控复核（禁止）**
- **Given**: 日报 R1 状态为 `trend_flagged`
- **When**: 运营尝试直接录入 `real_spend` (跳过trend_resolved)
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

**TC-RPT-005-05: final_locked后直接修改（禁止）**
- **Given**: 日报 R2 状态为 `final_locked`
- **When**: 运营尝试修改 `conversions_final`
- **Then**: 返回 HTTP 400，错误码 `STATE_400`，提示"仅可红冲修正"

**TC-RPT-005-06: final_locked红冲修正（允许）**
- **Given**: 日报 R3 状态为 `final_locked`，发现粉数错误
- **When**: Admin 创建红冲记录并生成新Ledger
- **Then**:
  - 原Ledger记录保留 (amount=5000)
  - 新增REVERSAL记录 (amount=-5000)
  - 新增正确REVENUE记录 (amount=4750)
  - 审计日志记录完整链条

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义 (v5.1)
- `ERROR_CODES.md` - 错误码清单
- `STATE_MACHINE.md` - 粉数确认状态机 (v2.6)
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
- `BRD_chapter1_v3.1.md` - 业务需求基线

### B. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v2.0 | 2025-01-21 | **【BRD v3.1对齐更新】**<br>• 新增 BR-RPT-005: 粉数确认流程规则<br>• 对齐8状态粉数确认状态机<br>• 新增三数据流定义 (raw/real/final)<br>• 新增趋势风控规则 (TF-001/002/003)<br>• 新增时效性约束与双账本机制<br>• 新增红冲修正机制<br>• 更新文档引用至 MASTER_SPEC v2.2 | 系统架构团队 |
| v1.0 | 2025-11-20 | 初始版本，包含 BR-RPT-001, 002, 004 | 系统架构团队 |

---

**END OF DOCUMENT**
