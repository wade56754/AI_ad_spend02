---
version: v4.0
status: active
layer: sot
owner: tech-lead
last_reviewed: 2025-12-24
baseline:
  - MASTER.md v4.4
  - STATE_MACHINE.md v2.6
  - DATA_SCHEMA.md v5.2
---

# 业务规则大全 (Business Rules)

> **版本**: v4.0
> **基准**: MASTER.md v4.4, STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2
> **最后更新**: 2025-12-24

---

## 第1章 文档说明

### 1.1 定位

本文档是 **AI 广告代投系统的业务规则唯一真相源 (SoT)**，定义：

- 开发铁律（不可违反的技术约束）
- 业务规则索引（按模块组织）
- Phase 边界（照亮 vs 问责）
- 术语表（业务与技术对照）

### 1.2 裁判链优先级

当文档间存在冲突时，按以下优先级裁决：

```
MASTER.md v4.4 > STATE_MACHINE.md v2.6 > DATA_SCHEMA.md v5.2
> BUSINESS_RULES.md v4.0 > API_SOT.md v9.2 > ERROR_CODES_SOT.md v2.1
```

### 1.3 角色定义 (7 角色)

来源：MASTER.md v4.4 §2.4

| 角色 | 系统值 | 职责 |
|------|--------|------|
| 老板 | `ceo` | 资金安全、公司盈亏、最终决策 |
| 项目负责人 | `project_owner` | 项目盈亏、资金使用效率 |
| 财务 | `finance` | 资金出入准确、数据真实、对账 |
| 主管 | `supervisor` | 团队产出、投手管理、日常监督 |
| 投手 | `pitcher` | CPL 达标、日报准确、执行投放 |
| 户管 | `account_manager` | 账户分配、账户状态监控 |
| 管理员 | `admin` | 系统配置（不参与业务） |

### 1.4 Phase 边界说明

来源：MASTER.md v4.4 §4

| 阶段 | 代号 | 行为原则 | 典型操作 |
|------|------|----------|----------|
| Phase 1 | 照亮 | 记录 + 提示 + 高亮 | 警告、标记、统计 |
| Phase 2 | 问责 | 强制 + 审批 + 考核 | 阻断、拒绝、惩罚 |

**Phase 1 禁止行为**：
- ❌ 自动阻断 / 自动拒绝 / 自动暂停 / 自动冻结
- ❌ 自动惩罚机制（扣分、禁用账户等）
- ❌ 强制审批流程

**Phase 1 允许行为**：
- ✅ 记录事实、展示状态、提示异常
- ✅ 高亮警告、数据统计、趋势分析

---

## 第2章 管理核心目标

### 2.1 三权清晰

来源：MASTER.md v4.4 §3

```
┌─────────────────────────────────────────────────────────────────┐
│                        三权清晰                                  │
├─────────────────────────────────────────────────────────────────┤
│  谁对钱负责：项目负责人申请 → 财务审核 → 老板批准                   │
│  谁对结果负责：项目负责人对盈亏负责                                │
│  谁能纠偏：日级主管、周级项目负责人、月级老板                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 资金管控链

```
老板批准 → 财务审核 → 项目负责人申请 → 户管分配 → 投手使用
```

**职责边界**：
- **老板 (ceo)**：最终批准权，查看全公司资金状态
- **财务 (finance)**：审核合规性，执行充值/结算
- **项目负责人 (project_owner)**：项目预算申请，消耗监控
- **户管 (account_manager)**：账户调配，状态监控
- **投手 (pitcher)**：消耗资金，提交日报

### 2.3 结果负责链

```
投手执行 → 主管日审 → 项目负责人周审 → 老板月审
```

**考核周期**：
| 周期 | 责任人 | 审核内容 |
|------|--------|----------|
| 日 | 主管 | 投手日报、CPL 达标 |
| 周 | 项目负责人 | 项目 ROAS、资金使用 |
| 月 | 老板 | 公司盈亏、资金安全 |

### 2.4 纠偏机制

| 异常类型 | 发现周期 | 纠偏责任人 | Phase 1 行为 |
|----------|----------|------------|--------------|
| CPL 超标 | 日 | 主管 | 高亮提示 |
| 预算超支 | 周 | 项目负责人 | 警告通知 |
| 盈亏异常 | 月 | 老板 | 趋势报告 |

---

## 第3章 开发铁律 (5 条)

### DEV-001 金额必须用 Decimal

**规则描述**：所有金额字段必须使用 Decimal(12,2) 类型存储，禁止使用 Float。

**原因**：Float 存在精度丢失问题，财务数据必须精确。

**后端实现**：
```python
from decimal import Decimal
from sqlalchemy import Column, Numeric

class AdAccount(Base):
    # 正确：使用 Numeric
    balance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # 错误：使用 Float
    # balance = Column(Float)

# 正确：Decimal 计算
new_balance = account.balance + Decimal("1000.00")

# 错误：浮点数计算
# new_balance = account.balance + 1000.0
```

**前端实现**：
```typescript
// 正确：使用字符串传输，前端转换显示
interface Amount {
  value: string;  // "1234.56"
}

const formatAmount = (value: string): string => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(parseFloat(value));
};

// 错误：直接用 number 计算
// const total = amount1 + amount2;
```

**违规检测**：
```bash
# 检测后端 Float 用于金额
grep -rn "Column(Float" backend/models/ | grep -i "balance\|amount\|cost\|spend"
```

---

### DEV-002 时间必须用 UTC

**规则描述**：所有时间字段使用 TIMESTAMPTZ 存储，统一使用 UTC 时区。

**后端实现**：
```python
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime

class BaseModel(Base):
    # 正确：TIMESTAMPTZ + UTC
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # 错误：不带时区
    # created_at = Column(DateTime, default=datetime.now)

# 正确：获取当前 UTC 时间
now = datetime.now(timezone.utc)

# 错误：使用本地时间
# now = datetime.now()
```

**前端处理**：
```typescript
// 正确：UTC 传输，本地显示
const formatDateTime = (utcString: string): string => {
  const date = new Date(utcString);
  return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
};

// API 传输格式：ISO 8601
// "2025-12-24T08:00:00Z"
```

**违规检测**：
```bash
# 检测不带时区的 DateTime
grep -rn "DateTime(" backend/models/ | grep -v "timezone=True"
```

---

### DEV-003 禁止物理删除核心数据

**规则描述**：核心业务数据（日报、充值、账户）禁止物理删除，必须使用软删除。

**核心数据定义**：
- `daily_reports` - 日报记录
- `topup_requests` - 充值申请
- `ledger_entries` - 账本记录
- `ad_accounts` - 广告账户

**后端实现**：
```python
from sqlalchemy import Column, Boolean, DateTime

class SoftDeleteMixin:
    """软删除混入"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID, nullable=True)

class DailyReport(Base, SoftDeleteMixin):
    # 正确：软删除
    def soft_delete(self, user_id: UUID):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    # 禁止：物理删除
    # def delete(self):
    #     session.delete(self)

# 查询时过滤已删除
def get_reports(db: Session):
    return db.query(DailyReport).filter(DailyReport.is_deleted == False).all()
```

**例外情况**：
- `draft` 状态的日报可物理删除（由创建者本人删除）
- 测试数据可物理删除

**违规检测**：
```bash
# 检测直接 delete 操作
grep -rn "\.delete(" backend/services/ | grep -v "soft_delete"
```

---

### DEV-004 角色不可变更

**规则描述**：用户角色在创建后不可修改，只能通过 admin 账户操作。

**设计原因**：
- 防止权限提升攻击
- 保证审计追溯完整性
- 简化权限模型

**后端实现**：
```python
class UserService:
    def update_user(self, user_id: UUID, update_data: dict):
        # 正确：禁止修改角色
        if "role" in update_data:
            raise BusinessError(
                code="AUTH-003",
                message="角色不可修改，请联系管理员"
            )

        # 正常更新其他字段
        return self.repo.update(user_id, update_data)

    def admin_change_role(self, admin_id: UUID, user_id: UUID, new_role: str):
        """仅 admin 可调用"""
        # 记录审计日志
        self.audit_log.record(
            action="change_role",
            operator_id=admin_id,
            target_id=user_id,
            old_value=user.role,
            new_value=new_role
        )
        return self.repo.update_role(user_id, new_role)
```

**API 层保护**：
```python
@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    # Schema 层面排除 role 字段
    if hasattr(update, 'role'):
        raise HTTPException(403, "Role modification not allowed via this endpoint")
```

---

### DEV-005 终态不可回退

**规则描述**：状态机的终态 (`final_locked`) 不可回退到任何前置状态。

**终态定义**（来源：STATE_MACHINE.md v2.6）：
- `final_locked` - 日报最终锁定
- `approved` - 充值已批准
- `settled` - 月度已结算

**后端实现**：
```python
from backend.core.state_machine import StateMachine

class DailyReportService:
    def transition_status(self, report_id: UUID, new_status: str, user: User):
        report = self.get_report(report_id)

        # 状态机自动阻止终态回退
        if not StateMachine.can_transition(report.status, new_status):
            raise BusinessError(
                code="STATE-002",
                message=f"无法从 {report.status} 转换到 {new_status}"
            )

        report.status = new_status
        return report

# 状态机定义
DAILY_REPORT_TRANSITIONS = {
    "raw_submitted": ["trend_pending"],
    "trend_pending": ["trend_ok", "trend_flagged"],
    "trend_ok": ["final_pending"],
    "trend_flagged": ["trend_resolved"],
    "trend_resolved": ["final_pending"],
    "final_pending": ["final_confirmed"],
    "final_confirmed": ["final_locked"],
    "final_locked": [],  # 终态，无后续状态
}
```

**违规检测**：
```python
# 单元测试
def test_final_locked_cannot_transition():
    """终态不可回退测试"""
    report = DailyReport(status="final_locked")

    with pytest.raises(BusinessError) as exc:
        service.transition_status(report.id, "final_confirmed", admin_user)

    assert exc.value.code == "STATE-002"
```

---

## 第4章 业务规则模块索引

### 4.1 日报模块 (BR-RPT-*)

| 编号 | 规则名称 | 级别 | 参考 |
|------|----------|------|------|
| BR-RPT-001 | 日报提交时间限制 | P1 | STATE_MACHINE.md §2.1 |
| BR-RPT-002 | CPL 计算公式 | P0 | 本文档 §4.1.1 |
| BR-RPT-003 | 零转化日报处理 | P1 | STATE_MACHINE.md §2.3 |
| BR-RPT-004 | 日报锁定条件 | P0 | STATE_MACHINE.md §2.5 |

#### 4.1.1 BR-RPT-002 CPL 计算公式

```
CPL = spend / conversions

边界条件：
- conversions = 0 → CPL = null（非 Infinity）
- spend = 0 → CPL = 0
- 保留 2 位小数
```

**实现代码**：
```python
def calculate_cpl(spend: Decimal, conversions: int) -> Decimal | None:
    if conversions == 0:
        return None  # 不是 float('inf')
    if spend == 0:
        return Decimal("0.00")
    return (spend / conversions).quantize(Decimal("0.01"))
```

### 4.2 充值模块 (BR-TOP-*)

| 编号 | 规则名称 | 级别 | 参考 |
|------|----------|------|------|
| BR-TOP-001 | 充值审批流程 | P0 | STATE_MACHINE.md §3 |
| BR-TOP-002 | 充值金额限制 | P1 | LEDGER_SOT.md §2 |
| BR-TOP-003 | 账户余额更新 | P0 | 本文档 §4.2.1 |

#### 4.2.1 BR-TOP-003 账户余额更新

**规则**：账户余额只能通过 `ledger_entries` 记录更新，禁止直接修改 `balance` 字段。

```python
# 正确：通过账本记录更新
def add_balance(account_id: UUID, amount: Decimal, reason: str):
    entry = LedgerEntry(
        account_id=account_id,
        amount=amount,
        balance_after=account.balance + amount,
        reason=reason
    )
    db.add(entry)
    account.balance += amount
    db.commit()

# 错误：直接修改余额
# account.balance += 1000
# db.commit()
```

### 4.3 账户模块 (BR-ACC-*)

| 编号 | 规则名称 | 级别 | 参考 |
|------|----------|------|------|
| BR-ACC-001 | 账户分配规则 | P1 | DATA_SCHEMA.md §3 |
| BR-ACC-002 | 账户状态管理 | P1 | STATE_MACHINE.md §4 |
| BR-ACC-003 | 负余额处理 | P0 | LEDGER_SOT.md §3 |

### 4.4 项目模块 (BR-PRJ-*)

| 编号 | 规则名称 | 级别 | 参考 |
|------|----------|------|------|
| BR-PRJ-001 | 项目成员角色限制 | P1 | DATA_SCHEMA.md §2.5 |
| BR-PRJ-002 | 项目预算分配 | P1 | LEDGER_SOT.md §4 |
| BR-PRJ-003 | 项目状态流转 | P1 | STATE_MACHINE.md §5 |

### 4.5 结算模块 (BR-STL-*)

| 编号 | 规则名称 | 级别 | 参考 |
|------|----------|------|------|
| BR-STL-001 | 月度结算周期 | P0 | BUSINESS_FLOW_MANAGEMENT.md §3 |
| BR-STL-002 | 结算锁定规则 | P0 | STATE_MACHINE.md §6 |
| BR-STL-003 | 利润计算公式 | P0 | 本文档 §4.5.1 |

#### 4.5.1 BR-STL-003 利润计算公式

```
项目利润 = 收入 - 消耗 - 返点
ROAS = 收入 / 消耗
```

---

## 第5章 规则与测试映射

### 5.1 映射表

| 规则编号 | 测试文件 | 测试用例 |
|----------|----------|----------|
| DEV-001 | `test_models.py` | `test_amount_decimal_precision` |
| DEV-002 | `test_models.py` | `test_datetime_timezone` |
| DEV-003 | `test_services.py` | `test_soft_delete_only` |
| DEV-004 | `test_auth.py` | `test_role_immutable` |
| DEV-005 | `test_state_machine.py` | `test_final_state_no_transition` |
| BR-RPT-002 | `test_daily_report.py` | `test_cpl_calculation` |
| BR-TOP-003 | `test_ledger.py` | `test_balance_via_ledger` |

### 5.2 测试覆盖要求

| 规则级别 | 单元测试 | 集成测试 | E2E 测试 |
|----------|----------|----------|----------|
| P0 | 必须 | 必须 | 推荐 |
| P1 | 必须 | 推荐 | 可选 |
| P2 | 推荐 | 可选 | 可选 |

---

## 第6章 术语表

| 业务术语 | 技术实现 | 说明 |
|----------|----------|------|
| 投手 | `pitcher` | 执行广告投放的操作员 |
| 主管 | `supervisor` | 管理投手的团队负责人 |
| 日报 | `daily_reports` | 每日消耗数据记录 |
| 充值 | `topup_requests` | 账户资金补充申请 |
| CPL | `cost_per_lead` | 每线索成本 = 消耗 / 转化数 |
| ROAS | `return_on_ad_spend` | 广告支出回报率 = 收入 / 消耗 |
| 账本 | `ledger_entries` | 资金流水记录 |
| 草稿 | `draft` | 未提交状态（仅前端使用） |
| 终态 | `final_locked` | 不可回退的最终状态 |

---

## 第7章 维护指南

### 7.1 规则变更流程

```
1. 提交 RFC → 2. 技术评审 → 3. 更新 SoT 文档 → 4. 实现 + 测试 → 5. 发布
```

### 7.2 版本兼容性

| 本文档版本 | 兼容的 MASTER.md | 兼容的 STATE_MACHINE.md |
|------------|------------------|-------------------------|
| v4.0 | v4.4 | v2.6 |
| v3.2 | v3.6 | v2.5 |

### 7.3 AI 防幻觉原则

来源：MASTER.md v4.4 §7

| 编号 | 原则 | 说明 |
|------|------|------|
| AH-01 | 禁止假设数据一致 | 遇到数据缺失，标记"待确认" |
| AH-02 | 禁止自动做管理裁决 | 禁止生成自动拒绝/暂停/终止代码 |
| AH-03 | 禁止引入 SoT 未定义概念 | 发现缺失 → 停止 → 询问 |
| AH-04 | 必须遵循 Phase 1 软性原则 | Phase 1 = 提示 + 高亮 + 记录 |
| AH-05 | 遇到歧义必须停止并询问 | 停止 → 列出歧义 → 询问 |

---

## 附录 A：变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v4.0 | 2025-12-24 | 重构：从索引文档升级为完整业务规则大全；升级 7 角色；添加完整铁律定义 |
| v3.2 | 2025-12-20 | 对齐 MASTER.md v3.6，更新裁判链 |
| v3.1 | 2025-12-15 | 添加 BR-STL 结算模块规则 |
| v3.0 | 2025-12-10 | 初始版本，作为规则索引 |

---

**维护者**: AI 广告代投系统技术团队
**关联文档**:
- `docs/1.overview/MASTER.md` - 系统宪法
- `docs/2.sot/STATE_MACHINE.md` - 状态机规范
- `docs/2.sot/DATA_SCHEMA.md` - 数据模型
- `docs/2.sot/LEDGER_SOT.md` - 账本规则
