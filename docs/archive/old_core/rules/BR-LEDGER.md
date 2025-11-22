# BR-LEDGER: 账本业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-01-21
> **所属模块**: 账本管理 (Ledger & Financial Accounting)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
> - `BRD_chapter1_v3.1.md` - 业务需求基线
> - `STATE_MACHINE.md` - 粉数确认状态机

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-LEDGER-001 | 双账本体系定义 | P0 | ✅ Active |
| BR-LEDGER-002 | Entry类型与方向规则 | P0 | ✅ Active |
| BR-LEDGER-003 | 粉数计费与final_locked规则 | P0 | ✅ Active |
| BR-LEDGER-004 | 死号迁移对称规则 | P0 | ✅ Active |
| BR-LEDGER-005 | 毛利计算与余额定义 | P0 | ✅ Active |

---

## BR-LEDGER-001: 双账本体系定义

### 业务场景

AI广告代投系统采用双账本设计，**PROJECT账本**记录项目收入（粉数计费），**SUPPLIER账本**记录供应商成本（FB消耗），两者分离核算，确保项目毛利清晰可追溯。

### 规则定义

#### 1.1 双账本隔离原则

**引用**: `BRD_chapter1_v3.1.md` 第7-8章 - 双账本设计, `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` 第2.2节

| 账本类型 | 用途 | 数据来源 | 主键关联 |
|---------|------|---------|---------|
| **PROJECT账本** | 项目收入核算 | `conversions_final × unit_price` | `project_id` |
| **SUPPLIER账本** | 供应商成本核算 | `real_spend` (真实消耗) | `supplier_id` |

**核心原则**:
- ✅ 两个账本**物理隔离**，分别记录
- ✅ PROJECT账本仅记录 `REVENUE` (收入)
- ✅ SUPPLIER账本仅记录 `COST` (成本)
- ✅ 项目毛利 = PROJECT收入 - SUPPLIER成本
- ❌ 禁止在同一账本中同时记录收入和成本

#### 1.2 数据表结构

**引用**: `DATA_SCHEMA.md` 3.4.3 - `ledger_entries` 表

```sql
CREATE TABLE ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    ledger_type VARCHAR(20) NOT NULL,                -- 'PROJECT' 或 'SUPPLIER'
    project_id BIGINT REFERENCES projects(id) ON DELETE RESTRICT,    -- PROJECT账本必填
    supplier_id UUID REFERENCES suppliers(id) ON DELETE RESTRICT,    -- SUPPLIER账本必填
    entry_type VARCHAR(50) NOT NULL,                 -- 'REVENUE', 'COST', 'TRANSFER_IN', 'TRANSFER_OUT', 'REVERSAL'
    amount DECIMAL(15,2) NOT NULL,                   -- 金额（有正负）
    balance_after DECIMAL(15,2) NOT NULL,            -- 操作后余额
    related_type VARCHAR(50),                        -- 关联资源类型 ('daily_report', 'topup_request', etc.)
    related_id BIGINT,                               -- 关联资源ID
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- 发生时间 (UTC)
    notes TEXT,                                      -- 备注
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE RESTRICT,

    -- 约束: PROJECT账本必须有 project_id
    CHECK ((ledger_type = 'PROJECT' AND project_id IS NOT NULL AND supplier_id IS NULL)
        OR (ledger_type = 'SUPPLIER' AND supplier_id IS NOT NULL AND project_id IS NULL))
);

-- 索引
CREATE INDEX idx_ledger_entries_project_id ON ledger_entries(project_id);
CREATE INDEX idx_ledger_entries_supplier_id ON ledger_entries(supplier_id);
CREATE INDEX idx_ledger_entries_occurred_at ON ledger_entries(occurred_at DESC);
```

#### 1.3 账本隔离示例

**PROJECT账本记录** (仅收入):
```sql
INSERT INTO ledger_entries (
    ledger_type, project_id, entry_type, amount, balance_after,
    related_type, related_id, notes, occurred_at
) VALUES (
    'PROJECT',        -- PROJECT账本
    101,              -- 项目ID
    'REVENUE',        -- 收入类型
    4750.00,          -- conversions_final(95) × unit_price(50)
    10750.00,         -- 操作后余额
    'daily_report',   -- 关联日报
    12345,            -- 日报ID
    '粉数计费: 95 × 50',
    '2025-01-21T14:00:00Z'
);
```

**SUPPLIER账本记录** (仅成本):
```sql
INSERT INTO ledger_entries (
    ledger_type, supplier_id, entry_type, amount, balance_after,
    related_type, related_id, notes, occurred_at
) VALUES (
    'SUPPLIER',       -- SUPPLIER账本
    'uuid-meta',      -- 供应商ID (Meta/Facebook)
    'COST',           -- 成本类型
    -4800.00,         -- 负数表示成本
    -15800.00,        -- 操作后余额（累计消耗）
    'daily_report',   -- 关联日报
    12345,            -- 日报ID
    'FB真实消耗',
    '2025-01-21T14:00:00Z'
);
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 账本类型错误 | `BIZ_200` | 400 | "ledger_type 必须为 PROJECT 或 SUPPLIER" |
| 缺少project_id | `BIZ_200` | 400 | "PROJECT账本必须指定 project_id" |
| 缺少supplier_id | `BIZ_200` | 400 | "SUPPLIER账本必须指定 supplier_id" |
| 账本混用 | `BIZ_200` | 400 | "禁止在同一条记录中同时指定 project_id 和 supplier_id" |

### 测试用例 (Test Intent)

**TC-LEDGER-001-01: 创建PROJECT账本记录**
- **Given**: 项目 #101，粉数计费 revenue = 4750
- **When**: 创建 PROJECT 账本记录
- **Then**:
  - `ledger_type` = `"PROJECT"`
  - `project_id` = 101
  - `supplier_id` = NULL
  - `entry_type` = `"REVENUE"`

**TC-LEDGER-001-02: 创建SUPPLIER账本记录**
- **Given**: 供应商 Meta，真实消耗 cost = 4800
- **When**: 创建 SUPPLIER 账本记录
- **Then**:
  - `ledger_type` = `"SUPPLIER"`
  - `supplier_id` = uuid-meta
  - `project_id` = NULL
  - `entry_type` = `"COST"`

**TC-LEDGER-001-03: 禁止账本混用**
- **Given**: 尝试创建记录同时指定 `project_id` 和 `supplier_id`
- **When**: 提交到数据库
- **Then**: 返回 CHECK 约束错误

---

## BR-LEDGER-002: Entry类型与方向规则

### 业务场景

账本记录通过 `entry_type` 区分业务类型，通过 `amount` 的正负值区分资金流向，系统必须强制执行方向规则。

### 规则定义

#### 2.1 Entry类型定义

**引用**: `BRD_chapter1_v3.1.md` 第7.2节 - Ledger Entry类型

| entry_type | 中文名称 | 账本类型 | 金额方向 | 业务场景 |
|-----------|---------|---------|---------|---------|
| `REVENUE` | 收入 | PROJECT | **正数** | 粉数计费（conversions_final × unit_price） |
| `COST` | 成本 | SUPPLIER | **负数** | FB真实消耗（real_spend） |
| `TRANSFER_IN` | 转入 | PROJECT | **正数** | 死号迁移转入余额 |
| `TRANSFER_OUT` | 转出 | PROJECT | **负数** | 死号迁移转出余额 |
| `REVERSAL` | 红冲 | PROJECT / SUPPLIER | **负数** | 冲销错误记录 |
| `TOPUP_IN` | 充值 | PROJECT | **正数** | 客户充值到账 |

#### 2.2 金额方向规则

**核心规则**: `amount` 的正负值必须与 `entry_type` 一致。

| entry_type | amount 符号 | balance_after 变化 | 示例 |
|-----------|-------------|-------------------|------|
| `REVENUE` | **正数** | 增加 | `amount: +4750, balance: 10000 → 14750` |
| `COST` | **负数** | 减少（累计消耗） | `amount: -4800, balance: -10000 → -14800` |
| `TRANSFER_IN` | **正数** | 增加 | `amount: +1000, balance: 5000 → 6000` |
| `TRANSFER_OUT` | **负数** | 减少 | `amount: -1000, balance: 5000 → 4000` |
| `REVERSAL` | **负数** (红冲原金额) | 减少 | `amount: -4750, balance: 14750 → 10000` |
| `TOPUP_IN` | **正数** | 增加 | `amount: +10000, balance: 0 → 10000` |

#### 2.3 Service层实现

```python
# backend/services/ledger_service.py
class LedgerService:
    def create_entry(
        self,
        ledger_type: str,
        entry_type: str,
        amount: Decimal,
        project_id: Optional[int] = None,
        supplier_id: Optional[UUID] = None,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
        notes: Optional[str] = None,
        user: Dict = None
    ) -> LedgerEntry:
        """创建账本记录"""
        # 验证账本类型
        if ledger_type not in ["PROJECT", "SUPPLIER"]:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="ledger_type 必须为 PROJECT 或 SUPPLIER"
            )

        # 验证 project_id / supplier_id
        if ledger_type == "PROJECT" and not project_id:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="PROJECT账本必须指定 project_id"
            )

        if ledger_type == "SUPPLIER" and not supplier_id:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="SUPPLIER账本必须指定 supplier_id"
            )

        # 验证金额方向
        self._validate_amount_direction(entry_type, amount)

        # 计算操作后余额
        if ledger_type == "PROJECT":
            current_balance = self._get_project_balance(project_id)
        else:
            current_balance = self._get_supplier_balance(supplier_id)

        balance_after = current_balance + amount

        # 创建记录
        entry = LedgerEntry(
            ledger_type=ledger_type,
            project_id=project_id,
            supplier_id=supplier_id,
            entry_type=entry_type,
            amount=amount,
            balance_after=balance_after,
            related_type=related_type,
            related_id=related_id,
            notes=notes,
            occurred_at=datetime.now(timezone.utc),
            created_by=user.get("user", {}).id if user else None
        )

        self.db.add(entry)
        self.db.flush()

        # 审计日志
        self._create_audit_log(
            action="CREATE_LEDGER_ENTRY",
            resource_type="ledger_entry",
            resource_id=str(entry.id),
            actor_id=user.get("user", {}).id if user else UUID("00000000-0000-0000-0000-000000000000"),
            actor_role=user.get("profile", {}).get("role") if user else "system",
            payload_after={
                "ledger_type": ledger_type,
                "entry_type": entry_type,
                "amount": str(amount),
                "balance_after": str(balance_after)
            },
            tags=["LEDGER_OPERATION"]
        )

        return entry

    def _validate_amount_direction(self, entry_type: str, amount: Decimal):
        """验证金额方向是否正确"""
        # REVENUE / TRANSFER_IN / TOPUP_IN 必须为正数
        if entry_type in ["REVENUE", "TRANSFER_IN", "TOPUP_IN"]:
            if amount <= 0:
                raise ValidationException(
                    code=BusinessErrorCodes.INVALID_INPUT.code,
                    message=f"{entry_type} 的金额必须为正数"
                )

        # COST / TRANSFER_OUT / REVERSAL 必须为负数
        if entry_type in ["COST", "TRANSFER_OUT", "REVERSAL"]:
            if amount >= 0:
                raise ValidationException(
                    code=BusinessErrorCodes.INVALID_INPUT.code,
                    message=f"{entry_type} 的金额必须为负数"
                )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 金额方向错误 | `BIZ_200` | 400 | "REVENUE 的金额必须为正数" |
| entry_type无效 | `BIZ_200` | 400 | "entry_type 必须为 REVENUE/COST/TRANSFER_IN/TRANSFER_OUT/REVERSAL/TOPUP_IN" |

### 测试用例 (Test Intent)

**TC-LEDGER-002-01: REVENUE 金额为正数**
- **Given**: 粉数计费 revenue = 4750
- **When**: 创建 ledger_entry `{entry_type: "REVENUE", amount: 4750}`
- **Then**: 创建成功，`balance_after` 增加

**TC-LEDGER-002-02: REVENUE 金额为负数（禁止）**
- **Given**: 尝试创建 `{entry_type: "REVENUE", amount: -4750}`
- **When**: 提交到服务
- **Then**: 返回 HTTP 400，错误码 `BIZ_200`

**TC-LEDGER-002-03: COST 金额为负数**
- **Given**: FB消耗 cost = 4800
- **When**: 创建 ledger_entry `{entry_type: "COST", amount: -4800}`
- **Then**: 创建成功，`balance_after` 减少

---

## BR-LEDGER-003: 粉数计费与final_locked规则

### 业务场景

粉数确认流程完成后（`final_confirmed` → `final_locked`），系统自动计费并生成账本记录，**final_locked 后禁止直接修改**，仅允许红冲修正。

### 规则定义

#### 3.1 粉数计费公式

**引用**: `BRD_chapter1_v3.1.md` 第7.1节 - 粉数计费规则

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

#### 3.2 final_locked 计费流程

**引用**: `STATE_MACHINE.md` 第8章 - 粉数确认状态机 (v2.6)

**触发条件**: T+1日 14:00 后，系统自动执行

**流程**:
```
1. 日报状态: final_confirmed → final_locked
2. 创建 PROJECT 账本记录:
   - entry_type = REVENUE
   - amount = conversions_final × unit_price
3. 创建 SUPPLIER 账本记录:
   - entry_type = COST
   - amount = -(real_spend)
4. 更新项目余额
5. 锁定日报，禁止修改
```

**代码示例**:
```python
# backend/services/daily_report_service.py
def lock_for_billing(self, report_id: int):
    """计费锁定 (系统自动)"""
    report = self._get_report_or_404(report_id)

    # 状态验证
    if report.status != "final_confirmed":
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message="仅 final_confirmed 状态可计费锁定"
        )

    # 计算 revenue
    revenue = report.conversions_final * report.unit_price

    with self.db.begin():
        # 1. 创建 PROJECT 账本记录 (REVENUE)
        project_entry = self.ledger_service.create_entry(
            ledger_type="PROJECT",
            entry_type="REVENUE",
            amount=revenue,
            project_id=report.project_id,
            related_type="daily_report",
            related_id=report.id,
            notes=f"粉数计费: {report.conversions_final} × {report.unit_price}",
            user={"user": {"id": UUID("00000000-0000-0000-0000-000000000000")}, "profile": {"role": "system"}}
        )

        # 2. 创建 SUPPLIER 账本记录 (COST)
        supplier_entry = self.ledger_service.create_entry(
            ledger_type="SUPPLIER",
            entry_type="COST",
            amount=-report.real_spend,
            supplier_id=report.supplier_id,
            related_type="daily_report",
            related_id=report.id,
            notes=f"FB真实消耗",
            user={"user": {"id": UUID("00000000-0000-0000-0000-000000000000")}, "profile": {"role": "system"}}
        )

        # 3. 更新日报状态
        report.status = "final_locked"
        report.locked_at = datetime.now(timezone.utc)

        # 4. 审计日志
        self._create_system_audit_log(
            action="BILLING_LOCK_AUTO",
            resource_type="daily_report",
            resource_id=str(report_id),
            payload_before={"status": "final_confirmed"},
            payload_after={
                "status": "final_locked",
                "locked_at": report.locked_at.isoformat(),
                "project_entry_id": project_entry.id,
                "supplier_entry_id": supplier_entry.id,
                "revenue": str(revenue),
                "cost": str(report.real_spend)
            },
            notes=f"系统自动计费锁定"
        )

    return report
```

#### 3.3 final_locked 后禁止修改规则

**核心规则**: 日报进入 `final_locked` 状态后，禁止修改以下字段：

- ❌ `conversions_final` (粉数)
- ❌ `real_spend` (真实消耗)
- ❌ `unit_price` (单价)
- ❌ `status` (状态)

**唯一修正方式**: 红冲 (REVERSAL)

```python
def update_report(self, report_id: int, updates: DailyReportUpdate, user: Dict) -> DailyReport:
    """更新日报数据"""
    report = self._get_report_or_404(report_id)

    # 终态保护检查
    if report.status == "final_locked":
        raise BusinessRuleException(
            code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,
            message="final_locked 状态的日报数据已锁定，仅可通过红冲修正"
        )

    # 允许编辑...
```

#### 3.4 红冲修正机制

**引用**: `BRD_chapter1_v3.1.md` 第7.3节 - 红冲修正规则

**红冲流程**:
```
1. 发现 final_locked 数据错误
2. 创建 REVERSAL 记录 (冲销原记录)
   - entry_type = REVERSAL
   - amount = -原金额
3. 生成新的正确 REVENUE/COST 记录
4. 更新项目余额
5. 记录审计日志
```

**示例**:
```python
def create_reversal(
    self,
    original_entry_id: int,
    reason: str,
    user: Dict
) -> Tuple[LedgerEntry, LedgerEntry]:
    """创建红冲记录对"""
    # 验证权限: 仅 admin 可红冲
    if user.get("profile", {}).get("role") != "admin":
        raise AuthorizationException(
            code=AuthErrorCodes.PERMISSION_DENIED.code,
            message="仅管理员可以执行红冲操作"
        )

    # 验证原因
    if not reason or len(reason) < 10:
        raise ValidationException(
            code=BusinessErrorCodes.INVALID_INPUT.code,
            message="红冲操作必须提供原因（至少10字符）"
        )

    # 获取原记录
    original = self.db.query(LedgerEntry).filter_by(id=original_entry_id).first()
    if not original:
        raise ResourceNotFoundException(
            code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,
            message="原账本记录不存在"
        )

    with self.db.begin():
        # 1. 创建红冲记录（负值）
        reversal_entry = LedgerEntry(
            ledger_type=original.ledger_type,
            project_id=original.project_id,
            supplier_id=original.supplier_id,
            entry_type="REVERSAL",
            amount=-original.amount,  # 红冲金额 = -原金额
            balance_after=self._calculate_balance_after(original, -original.amount),
            related_type=original.related_type,
            related_id=original.related_id,
            notes=f"红冲原记录#{original_entry_id}: {reason}",
            occurred_at=datetime.now(timezone.utc),
            created_by=user.get("user", {}).id
        )

        self.db.add(reversal_entry)
        self.db.flush()

        # 2. 审计日志
        self._create_audit_log(
            action="CREATE_REVERSAL",
            resource_type="ledger_entry",
            resource_id=str(reversal_entry.id),
            actor_id=user.get("user", {}).id,
            actor_role="admin",
            payload_before={
                "original_entry_id": original_entry_id,
                "original_amount": str(original.amount)
            },
            payload_after={
                "reversal_entry_id": reversal_entry.id,
                "reversal_amount": str(-original.amount)
            },
            reason=reason,
            tags=["REVERSAL", "ADMIN_OVERRIDE"]
        )

    return (reversal_entry, original)
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 修改final_locked数据 | `STATE_400` | 400 | "final_locked 状态的日报数据已锁定" |
| 非admin执行红冲 | `AUTH_500` | 403 | "仅管理员可以执行红冲操作" |
| 红冲原因过短 | `BIZ_002` | 400 | "红冲操作必须提供原因（至少10字符）" |

### 测试用例 (Test Intent)

**TC-LEDGER-003-01: 系统自动计费锁定**
- **Given**: 日报 R1 状态为 `final_confirmed`，`conversions_final=95`, `unit_price=50`, `real_spend=4800`
- **When**: 系统执行计费锁定
- **Then**:
  - 创建 PROJECT 账本记录: `entry_type=REVENUE, amount=4750`
  - 创建 SUPPLIER 账本记录: `entry_type=COST, amount=-4800`
  - 日报状态变为 `final_locked`

**TC-LEDGER-003-02: 尝试修改final_locked日报（禁止）**
- **Given**: 日报 R2 状态为 `final_locked`
- **When**: 尝试修改 `conversions_final`
- **Then**: 返回 HTTP 400，错误码 `STATE_400`

**TC-LEDGER-003-03: 管理员红冲修正**
- **Given**: 账本记录 L1 `{entry_type: "REVENUE", amount: 5000}` 需修正
- **When**: Admin 创建红冲 `{original_entry_id: L1, reason: "粉数错误"}`
- **Then**:
  - 创建红冲记录: `entry_type=REVERSAL, amount=-5000`
  - 审计日志包含 `REVERSAL` 标签

---

## BR-LEDGER-004: 死号迁移对称规则

### 业务场景

广告账户被封禁后，需要将余额迁移到新账户继续投放，系统必须确保迁移的**对称性**（A转出 = B转入）和**原子性**（同时成功或失败）。

### 规则定义

#### 4.1 迁移对称原则

**引用**: `BRD_chapter1_v3.1.md` 第9章 - 死号迁移流程

**核心规则**:
- ✅ A账户 TRANSFER_OUT 金额 = B账户 TRANSFER_IN 金额（绝对值相等）
- ✅ 迁移操作必须在同一事务中完成（原子性）
- ✅ 迁移后 A账户余额归零，B账户增加对应金额
- ✅ 两条账本记录的 `related_id` 必须相同（关联同一迁移批次）

#### 4.2 迁移流程实现

```python
# backend/services/transfer_service.py
class TransferService:
    def execute_transfer(
        self,
        from_project_id: int,
        to_project_id: int,
        amount: Decimal,
        reason: str,
        user: Dict
    ) -> Tuple[LedgerEntry, LedgerEntry]:
        """执行死号迁移"""
        # 权限验证: 仅 admin/finance 可执行
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "finance"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅管理员和财务人员可以执行死号迁移"
            )

        # 金额验证
        if amount <= 0:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="迁移金额必须大于0"
            )

        # 验证 from_project 余额充足
        from_balance = self.ledger_service.get_project_balance(from_project_id)
        if from_balance < amount:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message=f"项目 {from_project_id} 余额不足（当前: {from_balance}, 需要: {amount}）"
            )

        # 生成迁移批次号
        transfer_batch_no = f"TRANSFER-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        with self.db.begin():
            # 1. A账户转出 (TRANSFER_OUT, 负数)
            transfer_out = self.ledger_service.create_entry(
                ledger_type="PROJECT",
                entry_type="TRANSFER_OUT",
                amount=-amount,
                project_id=from_project_id,
                related_type="transfer",
                related_id=None,  # 后续关联
                notes=f"死号迁移转出 → 项目#{to_project_id}: {reason}",
                user=user
            )

            # 2. B账户转入 (TRANSFER_IN, 正数)
            transfer_in = self.ledger_service.create_entry(
                ledger_type="PROJECT",
                entry_type="TRANSFER_IN",
                amount=amount,
                project_id=to_project_id,
                related_type="transfer",
                related_id=None,  # 后续关联
                notes=f"死号迁移转入 ← 项目#{from_project_id}: {reason}",
                user=user
            )

            # 3. 创建迁移记录（关联两条账本记录）
            transfer_record = TransferRecord(
                batch_no=transfer_batch_no,
                from_project_id=from_project_id,
                to_project_id=to_project_id,
                amount=amount,
                reason=reason,
                transfer_out_entry_id=transfer_out.id,
                transfer_in_entry_id=transfer_in.id,
                created_by=user.get("user", {}).id,
                created_at=datetime.now(timezone.utc)
            )

            self.db.add(transfer_record)
            self.db.flush()

            # 4. 更新 ledger_entries 的 related_id
            transfer_out.related_id = transfer_record.id
            transfer_in.related_id = transfer_record.id

            # 5. 审计日志
            self._create_audit_log(
                action="EXECUTE_TRANSFER",
                resource_type="transfer",
                resource_id=str(transfer_record.id),
                actor_id=user.get("user", {}).id,
                actor_role=user_role,
                payload_before={
                    "from_balance": str(from_balance),
                    "to_balance": str(self.ledger_service.get_project_balance(to_project_id))
                },
                payload_after={
                    "from_balance": str(from_balance - amount),
                    "to_balance": str(self.ledger_service.get_project_balance(to_project_id) + amount),
                    "amount": str(amount)
                },
                reason=reason,
                tags=["TRANSFER", "ADMIN_OPERATION"]
            )

        return (transfer_out, transfer_in)
```

#### 4.3 对称性校验

```python
def verify_transfer_symmetry(transfer_out: LedgerEntry, transfer_in: LedgerEntry):
    """验证迁移对称性"""
    # 金额绝对值必须相等
    if abs(transfer_out.amount) != abs(transfer_in.amount):
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message=f"迁移金额不对称: OUT={transfer_out.amount}, IN={transfer_in.amount}"
        )

    # 方向必须相反
    if transfer_out.amount >= 0 or transfer_in.amount <= 0:
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message="迁移方向错误: OUT必须为负数, IN必须为正数"
        )

    # related_id 必须相同
    if transfer_out.related_id != transfer_in.related_id:
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,
            message="迁移记录关联ID不一致"
        )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 余额不足 | `BIZ_001` | 400 | "项目余额不足" |
| 金额不对称 | `BIZ_001` | 400 | "迁移金额不对称" |
| 非admin/finance执行 | `AUTH_500` | 403 | "仅管理员和财务人员可以执行死号迁移" |

### 测试用例 (Test Intent)

**TC-LEDGER-004-01: 正常死号迁移**
- **Given**: 项目A余额 5000，项目B余额 0
- **When**: 执行迁移 `{from: A, to: B, amount: 1000, reason: "账户封禁"}`
- **Then**:
  - 创建2条账本记录: TRANSFER_OUT(-1000), TRANSFER_IN(+1000)
  - 项目A余额变为 4000
  - 项目B余额变为 1000
  - `related_id` 相同

**TC-LEDGER-004-02: 余额不足（禁止）**
- **Given**: 项目A余额 500
- **When**: 尝试迁移 `{from: A, amount: 1000}`
- **Then**: 返回 HTTP 400，错误码 `BIZ_001`

**TC-LEDGER-004-03: 迁移对称性校验**
- **Given**: 迁移记录 OUT=-1000, IN=+1000
- **When**: 调用 `verify_transfer_symmetry`
- **Then**: 验证通过

---

## BR-LEDGER-005: 毛利计算与余额定义

### 业务场景

项目盈利能力的核心指标是**毛利** (Gross Profit)，系统必须清晰区分**项目余额**和**账户余额**，并提供准确的毛利计算。

### 规则定义

#### 5.1 毛利计算公式

**引用**: `BRD_chapter1_v3.1.md` 第8章 - 毛利核算规则

**公式**:
```
项目毛利 = PROJECT账本累计收入 - SUPPLIER账本累计成本

即：
profit = Σ(REVENUE) - |Σ(COST)|
```

**示例**:
```
PROJECT账本:
├─ REVENUE: +4750 (粉数计费)
├─ TOPUP_IN: +10000 (客户充值)
└─ 累计收入: 14750

SUPPLIER账本:
├─ COST: -4800 (FB消耗)
└─ 累计成本: 4800

项目毛利 = 14750 - 4800 = 9950
```

#### 5.2 项目余额 vs 账户余额

| 概念 | 定义 | 计算方式 | 用途 |
|-----|------|---------|------|
| **项目余额** | 项目可用资金总额 | PROJECT账本 `balance_after` 最新值 | 判断是否需要充值 |
| **账户余额** | 单个广告账户可用额度 | 项目余额 - 已分配额度 | 控制账户消费上限 |
| **项目毛利** | 项目盈利金额 | REVENUE总和 - COST总和 | 评估项目盈利能力 |

**项目余额计算**:
```python
def get_project_balance(project_id: int) -> Decimal:
    """获取项目当前余额"""
    latest_entry = db.query(LedgerEntry).filter(
        LedgerEntry.ledger_type == "PROJECT",
        LedgerEntry.project_id == project_id
    ).order_by(LedgerEntry.occurred_at.desc()).first()

    return latest_entry.balance_after if latest_entry else Decimal("0.00")
```

**项目毛利计算**:
```python
def calculate_project_profit(project_id: int) -> Decimal:
    """计算项目毛利"""
    # PROJECT账本总收入
    revenue_sum = db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.ledger_type == "PROJECT",
        LedgerEntry.project_id == project_id,
        LedgerEntry.entry_type.in_(["REVENUE", "TOPUP_IN", "TRANSFER_IN"])
    ).scalar() or Decimal("0.00")

    # SUPPLIER账本总成本（绝对值）
    cost_sum = db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.ledger_type == "SUPPLIER",
        LedgerEntry.project_id == project_id,
        LedgerEntry.entry_type == "COST"
    ).scalar() or Decimal("0.00")

    # 毛利 = 收入 - |成本|
    profit = revenue_sum - abs(cost_sum)

    return profit
```

#### 5.3 对账校验规则

**引用**: `BRD_chapter1_v3.1.md` 第8.2节 - 对账规则

**公式**:
```
总资产 = Σ(PROJECT账本余额) + Σ(SUPPLIER账本余额)

验证: 总资产 应等于 系统初始资金 + 所有充值 - 所有提现
```

```python
def verify_ledger_balance():
    """验证账本余额一致性"""
    # 所有 PROJECT 账本余额总和
    total_project_balance = db.query(func.sum(LedgerEntry.balance_after)).filter(
        LedgerEntry.ledger_type == "PROJECT"
    ).distinct(LedgerEntry.project_id).scalar() or Decimal("0.00")

    # 所有 SUPPLIER 账本余额总和（负数）
    total_supplier_balance = db.query(func.sum(LedgerEntry.balance_after)).filter(
        LedgerEntry.ledger_type == "SUPPLIER"
    ).distinct(LedgerEntry.supplier_id).scalar() or Decimal("0.00")

    # 总资产
    total_assets = total_project_balance + total_supplier_balance

    # 所有充值总和
    total_topup = db.query(func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.entry_type == "TOPUP_IN"
    ).scalar() or Decimal("0.00")

    # 理论余额 = 充值总和
    expected_balance = total_topup

    # 允许误差: 0.01 元
    if abs(total_assets - expected_balance) > Decimal("0.01"):
        raise SystemException(
            code="LEDGER_MISMATCH",
            message=f"账本余额不一致: 实际={total_assets}, 预期={expected_balance}"
        )

    return {
        "total_assets": total_assets,
        "total_project_balance": total_project_balance,
        "total_supplier_balance": total_supplier_balance,
        "total_topup": total_topup,
        "is_balanced": True
    }
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|--------------|
| 账本余额不一致 | `LEDGER_MISMATCH` | 500 | "账本余额不一致" |

### 测试用例 (Test Intent)

**TC-LEDGER-005-01: 计算项目余额**
- **Given**: 项目 #101 有3条账本记录: TOPUP_IN(+10000), REVENUE(+4750), TRANSFER_OUT(-1000)
- **When**: 调用 `get_project_balance(101)`
- **Then**: 返回 `13750.00`

**TC-LEDGER-005-02: 计算项目毛利**
- **Given**:
  - PROJECT账本: REVENUE(+4750), TOPUP_IN(+10000)
  - SUPPLIER账本: COST(-4800)
- **When**: 调用 `calculate_project_profit(101)`
- **Then**: 返回 `9950.00` (14750 - 4800)

**TC-LEDGER-005-03: 对账校验通过**
- **Given**:
  - 系统总充值: 100000
  - PROJECT账本总余额: 60000
  - SUPPLIER账本总余额: -40000
- **When**: 调用 `verify_ledger_balance()`
- **Then**: 返回 `{is_balanced: true}`

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册
- `BRD_chapter1_v3.1.md` - 业务需求基线
- `STATE_MACHINE.md` - 粉数确认状态机

### B. Ledger Entry类型速查表

| entry_type | 账本类型 | 金额方向 | 业务场景 |
|-----------|---------|---------|---------|
| REVENUE | PROJECT | 正 | 粉数计费 |
| COST | SUPPLIER | 负 | FB消耗 |
| TOPUP_IN | PROJECT | 正 | 客户充值 |
| TRANSFER_IN | PROJECT | 正 | 死号迁移转入 |
| TRANSFER_OUT | PROJECT | 负 | 死号迁移转出 |
| REVERSAL | PROJECT/SUPPLIER | 负 | 红冲错误记录 |

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-01-21 | 初始版本，包含 BR-LEDGER-001~005 | 系统架构团队 |

---

**END OF DOCUMENT**
