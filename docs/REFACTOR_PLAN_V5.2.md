# 广告投放业务管理系统 - V5.2 重构方案

> 基于《广告投放业务管理系统-V5.2-最终版》与当前系统实现的差距分析
> 版本: v1.0 | 日期: 2025-12-22

---

## 一、执行摘要

### 1.1 差距总览

| 模块 | V5.2 要求 | 当前状态 | 差距级别 | 重构优先级 |
|------|----------|---------|---------|-----------|
| **期间锁 (Period Lock)** | 完整实现 | ❌ 未实现 | **P0** | 🔴 紧急 |
| **状态迁移强制校验** | DB 触发器 + 存储过程 | Python 层校验 | **P0** | 🔴 紧急 |
| **冲正锁定期间禁止** | 默认禁止 + 特批通道 | 无此检查 | **P0** | 🔴 紧急 |
| **冲正幂等键** | REV_{id}_v1 稳定格式 | 含时间戳 | **P0** | 🟡 高 |
| **代理商余额口径** | current_balance vs total_cost | 单一余额字段 | **P1** | 🟡 高 |
| **对账符号约定** | 配置化 | 硬编码 | **P1** | 🟢 中 |

### 1.2 风险评估

```
┌─────────────────────────────────────────────────────────────────────┐
│                        风险矩阵                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  【P0 风险 - 会出事故】                                              │
│  1. 期间锁失效 → 关账后数据被修改 → 财务报表不可信                   │
│  2. 状态可绕过 → 未审批流水入账 → 资金风险                           │
│  3. 锁定期冲正 → 已关账月份数据变动 → 审计问题                       │
│  4. 冲正重复 → 重试产生多条冲正 → 余额错误                           │
│                                                                     │
│  【P1 风险 - 会扯皮】                                                │
│  1. 余额口径不清 → 业务与财务理解不一致 → 对账困难                   │
│  2. 符号硬编码 → 新代理商接入困难 → 手工对账                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、详细差距分析

### 2.1 期间锁 (Period Lock) - P0

#### V5.2 要求
```sql
-- 期间锁表
CREATE TABLE period_locks (
    entity_type     VARCHAR(30) NOT NULL,
    entity_scope    VARCHAR(50) NOT NULL DEFAULT 'GLOBAL',
    entity_scope_id INT NOT NULL DEFAULT 0,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    lock_status     VARCHAR(20) NOT NULL DEFAULT 'UNLOCKED',
    -- ...
);

-- 检查函数
CREATE FUNCTION is_period_locked(entity_type, date, scope, scope_id);
```

#### 当前实现
```python
# ❌ 完全未实现
# 依赖 STATE_MACHINE.md 中日报的 final_locked 状态
# 但无独立的 period_locks 表和检查机制
```

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 创建 `period_locks` 表 (Alembic) | 2h | 无 |
| 2. 实现 `PeriodLockService` | 4h | 任务1 |
| 3. 集成到 `LedgerPostingService` | 2h | 任务2 |
| 4. 添加管理 API (`/api/v1/period-locks`) | 3h | 任务2 |
| 5. 前端期间锁管理页面 | 4h | 任务4 |

---

### 2.2 状态迁移强制校验 - P0

#### V5.2 要求
```sql
-- 触发器禁止直接 UPDATE txn_status
CREATE TRIGGER trg_ledger_prevent_direct_status
BEFORE UPDATE ON ledger
FOR EACH ROW EXECUTE FUNCTION trg_prevent_direct_status_update();

-- 只能通过存储过程变更
CREATE FUNCTION transition_ledger_status(ledger_id, to_status, user_id, comment);
```

#### 当前实现
```python
# backend/models/finance/financial_event.py
class FinancialEvent:
    TRANSITIONS = {
        'raw': ['pending'],
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['posted'],
        'posted': ['reversed'],
    }

    def can_transition_to(self, new_status):
        return new_status in self.TRANSITIONS.get(self.event_status, [])
```

**问题**: Python 层校验可被绕过（直接 SQL UPDATE）

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 创建 `state_transitions` 配置表 | 1h | 无 |
| 2. 创建 DB 触发器 `trg_prevent_direct_status_update` | 2h | 任务1 |
| 3. 创建存储过程 `transition_ledger_status` | 3h | 任务1 |
| 4. 修改 Python Service 调用存储过程 | 2h | 任务3 |
| 5. 添加审计日志记录 | 2h | 任务3 |

---

### 2.3 冲正在锁定期间默认禁止 - P0

#### V5.2 要求
```sql
-- 默认禁止锁定期间冲正
-- 特批需要 CEO/CFO 角色 + force_override + 详细原因
CREATE FUNCTION reverse_ledger_entry(
    original_id,
    reason,
    operator_id,
    force_override DEFAULT FALSE,  -- 特批参数
    use_original_date DEFAULT FALSE
);
```

#### 当前实现
```python
# backend/services/ledger_posting_service.py
def reverse_event(self, event_id, reason, operator_id):
    # ❌ 无期间锁检查
    # ❌ 无角色权限检查
    # ❌ 无特批通道
```

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 添加期间锁检查到 `reverse_event` | 2h | 期间锁实现 |
| 2. 添加角色权限检查 (CEO/CFO) | 1h | 无 |
| 3. 实现 `force_override` 特批参数 | 2h | 任务1,2 |
| 4. 强制审计日志记录 | 1h | 任务3 |
| 5. 前端特批流程 UI | 3h | 任务3 |

---

### 2.4 冲正幂等键 - P0

#### V5.2 要求
```sql
-- 稳定格式：REV_{original_id}_v1
v_txn_id := 'REV_' || p_original_id || '_v1';

-- 幂等处理：重试返回已存在记录
EXCEPTION
    WHEN unique_violation THEN
        SELECT id INTO v_new_id FROM ledger WHERE txn_id = v_txn_id;
        RETURN v_new_id;  -- 幂等返回
```

#### 当前实现
```python
# backend/services/ledger_posting_service.py
idempotency_key = f"REVERSAL:{original_key}:{timestamp}"
# ❌ 含时间戳，重试会产生不同 ID
```

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 修改幂等键格式为 `REV_{id}_v1` | 1h | 无 |
| 2. 添加唯一约束冲突处理（返回已存在记录） | 1h | 任务1 |
| 3. 编写单元测试验证幂等性 | 1h | 任务2 |

---

### 2.5 代理商余额口径 - P1

#### V5.2 要求
```sql
-- 两个明确定义的字段
current_balance  -- 代理商广告账户可用余额（不含手续费）
total_cost       -- 公司支付给代理商的总成本（含手续费）

-- 余额公式
余额 = AGENCY_TRANSFER(取反) + PLATFORM_SPEND + AGENCY_REFUND(取反) + ADJUSTMENT
-- 手续费不影响余额，但影响总成本
```

#### 当前实现
```python
# backend/models/finance/ledger.py
class LedgerEntry:
    balance_after = Column(Numeric(20, 4))  # 单一余额字段
    # ❌ 无 total_cost 区分
    # ❌ AGENCY_FEE 处理不明确
```

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 创建 `v_agency_balance` 视图 | 2h | 无 |
| 2. 添加 AGENCY_FEE 分录类型 | 2h | 任务1 |
| 3. 更新余额计算服务 | 2h | 任务1,2 |
| 4. 前端展示两种余额口径 | 2h | 任务3 |

---

### 2.6 对账符号约定配置化 - P1

#### V5.2 要求
```sql
-- 配置字段
ALTER TABLE recon_runs ADD COLUMN
    their_amount_convention VARCHAR(20) DEFAULT 'THEIR_EXPENSE';

-- 三种约定
-- THEIR_EXPENSE: 对方账单表示对方支出，匹配时取反
-- THEIR_INCOME: 对方账单表示对方收入，直接匹配
-- OUR_PERSPECTIVE: 对方账单已转换为我方视角
```

#### 当前实现
```python
# backend/services/reconciliation_service.py
# ❌ 符号转换硬编码
# ❌ 无配置化支持
```

#### 重构任务
| 任务 | 工作量 | 依赖 |
|------|--------|------|
| 1. 添加 `their_amount_convention` 字段 | 1h | 无 |
| 2. 修改匹配逻辑使用配置 | 2h | 任务1 |
| 3. 前端对账批次创建时选择约定 | 1h | 任务1 |

---

## 三、重构执行计划

### 3.1 阶段划分

```
┌─────────────────────────────────────────────────────────────────────┐
│                     重构阶段规划                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  【Phase 1: P0 核心修复】                                            │
│  预计: 3-4 天                                                        │
│  ├─ 1.1 期间锁表 + 服务 + API                                       │
│  ├─ 1.2 状态迁移触发器 + 存储过程                                    │
│  ├─ 1.3 冲正锁定期间禁止 + 特批通道                                  │
│  └─ 1.4 冲正幂等键修复                                               │
│                                                                     │
│  【Phase 2: P1 业务完善】                                            │
│  预计: 2 天                                                          │
│  ├─ 2.1 代理商余额口径明确                                          │
│  └─ 2.2 对账符号约定配置化                                          │
│                                                                     │
│  【Phase 3: 前端 + 测试】                                            │
│  预计: 2-3 天                                                        │
│  ├─ 3.1 期间锁管理页面                                              │
│  ├─ 3.2 冲正特批流程 UI                                              │
│  ├─ 3.3 余额双口径展示                                               │
│  └─ 3.4 E2E 测试覆盖                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 详细任务清单

#### Phase 1: P0 核心修复

| 序号 | 任务 | 类型 | 工作量 | 输出物 |
|------|------|------|--------|--------|
| 1.1.1 | 创建 `period_locks` 表迁移 | Backend | 2h | `migrations/xxx_add_period_locks.py` |
| 1.1.2 | 创建 `PeriodLockService` | Backend | 4h | `services/period_lock_service.py` |
| 1.1.3 | 创建 `is_period_locked` 存储过程 | DB | 2h | SQL 函数 |
| 1.1.4 | 期间锁管理 API | Backend | 3h | `routers/period_locks.py` |
| 1.2.1 | 创建 `state_transitions` 表 | Backend | 1h | Alembic 迁移 |
| 1.2.2 | 创建 DB 触发器 | DB | 2h | SQL 触发器 |
| 1.2.3 | 创建 `transition_ledger_status` 存储过程 | DB | 3h | SQL 函数 |
| 1.2.4 | 修改 Service 调用存储过程 | Backend | 2h | Service 更新 |
| 1.3.1 | 修改 `reverse_event` 添加期间锁检查 | Backend | 2h | Service 更新 |
| 1.3.2 | 添加角色权限检查 | Backend | 1h | Service 更新 |
| 1.3.3 | 实现 `force_override` 特批 | Backend | 2h | Service 更新 |
| 1.4.1 | 修改冲正幂等键格式 | Backend | 1h | Service 更新 |
| 1.4.2 | 添加幂等返回逻辑 | Backend | 1h | Service 更新 |

#### Phase 2: P1 业务完善

| 序号 | 任务 | 类型 | 工作量 | 输出物 |
|------|------|------|--------|--------|
| 2.1.1 | 创建 `v_agency_balance` 视图 | DB | 2h | SQL 视图 |
| 2.1.2 | 添加 AGENCY_FEE 分录类型 | Backend | 2h | Model 更新 |
| 2.1.3 | 更新余额计算服务 | Backend | 2h | Service 更新 |
| 2.2.1 | 添加 `their_amount_convention` 字段 | Backend | 1h | Alembic 迁移 |
| 2.2.2 | 修改对账匹配逻辑 | Backend | 2h | Service 更新 |

#### Phase 3: 前端 + 测试

| 序号 | 任务 | 类型 | 工作量 | 输出物 |
|------|------|------|--------|--------|
| 3.1.1 | 期间锁管理页面 | Frontend | 4h | `PeriodLocksPage.tsx` |
| 3.2.1 | 冲正特批流程 UI | Frontend | 3h | 对话框组件 |
| 3.3.1 | 余额双口径展示 | Frontend | 2h | 组件更新 |
| 3.4.1 | P0 功能 E2E 测试 | Test | 4h | Playwright 测试 |
| 3.4.2 | P1 功能单元测试 | Test | 2h | pytest 用例 |

---

## 四、数据库变更汇总

### 4.1 新增表

```sql
-- 1. 期间锁表
CREATE TABLE period_locks (
    id              SERIAL PRIMARY KEY,
    entity_type     VARCHAR(30) NOT NULL,
    entity_scope    VARCHAR(50) NOT NULL DEFAULT 'GLOBAL',
    entity_scope_id INT NOT NULL DEFAULT 0,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    period_name     VARCHAR(50),
    lock_status     VARCHAR(20) NOT NULL DEFAULT 'UNLOCKED',
    lock_reason     VARCHAR(200),
    locked_by       INT REFERENCES users(id),
    locked_at       TIMESTAMP,
    unlocked_by     INT REFERENCES users(id),
    unlocked_at     TIMESTAMP,
    created_by      INT NOT NULL REFERENCES users(id),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_lock_status CHECK (lock_status IN ('UNLOCKED', 'LOCKED', 'FROZEN')),
    CONSTRAINT chk_period CHECK (period_end >= period_start),
    CONSTRAINT chk_entity_scope CHECK (entity_scope IN ('GLOBAL', 'AGENCY', 'PROJECT', 'PITCHER'))
);

CREATE UNIQUE INDEX uq_period_lock ON period_locks(
    entity_type, entity_scope, entity_scope_id, period_start, period_end
);

-- 2. 状态迁移配置表
CREATE TABLE state_transitions (
    id              SERIAL PRIMARY KEY,
    entity_type     VARCHAR(50) NOT NULL,
    from_state      VARCHAR(50) NOT NULL,
    to_state        VARCHAR(50) NOT NULL,
    allowed_roles   TEXT[] NOT NULL,
    requires_reason BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,

    UNIQUE(entity_type, from_state, to_state)
);
```

### 4.2 表字段变更

```sql
-- recon_runs 表增加符号约定字段
ALTER TABLE recon_runs ADD COLUMN
    their_amount_convention VARCHAR(20) DEFAULT 'THEIR_EXPENSE';
```

### 4.3 新增存储过程/函数

```sql
-- 1. 检查期间是否锁定
CREATE FUNCTION is_period_locked(entity_type, date, scope, scope_id) RETURNS BOOLEAN;

-- 2. 状态迁移（唯一入口）
CREATE FUNCTION transition_ledger_status(ledger_id, to_status, user_id, comment) RETURNS BOOLEAN;

-- 3. 冲正（带期间锁检查）
CREATE FUNCTION reverse_ledger_entry(original_id, reason, operator_id, force_override, use_original_date) RETURNS BIGINT;
```

### 4.4 新增触发器

```sql
-- 禁止直接 UPDATE txn_status
CREATE TRIGGER trg_ledger_prevent_direct_status
BEFORE UPDATE ON ledger
FOR EACH ROW EXECUTE FUNCTION trg_prevent_direct_status_update();
```

### 4.5 新增视图

```sql
-- 代理商余额视图（含 current_balance 和 total_cost）
CREATE VIEW v_agency_balance AS
SELECT
    agency_id,
    agency_name,
    -- current_balance: 不含手续费
    -- total_cost: 含手续费
    ...
FROM agencies LEFT JOIN ledger ...;
```

---

## 五、API 变更汇总

### 5.1 新增 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/period-locks` | GET | 获取期间锁列表 |
| `/api/v1/period-locks` | POST | 创建期间锁 |
| `/api/v1/period-locks/{id}/lock` | POST | 锁定期间 |
| `/api/v1/period-locks/{id}/unlock` | POST | 解锁期间 |
| `/api/v1/ledger/{id}/reverse` | POST | 冲正（支持 force_override） |

### 5.2 修改 API

| 端点 | 变更内容 |
|------|---------|
| `POST /api/v1/recon-runs` | 新增 `their_amount_convention` 参数 |
| `GET /api/v1/agencies/{id}/balance` | 返回 `current_balance` 和 `total_cost` 双字段 |

---

## 六、测试策略

### 6.1 P0 功能测试用例

```python
# tests/test_period_lock.py
class TestPeriodLock:
    def test_create_period_lock(self): ...
    def test_lock_period(self): ...
    def test_unlock_period(self): ...
    def test_is_period_locked(self): ...
    def test_unique_constraint_with_defaults(self): ...  # P0-1

# tests/test_state_transition.py
class TestStateTransition:
    def test_valid_transition(self): ...
    def test_invalid_transition_rejected(self): ...
    def test_direct_update_blocked(self): ...  # P0-2
    def test_role_permission_check(self): ...

# tests/test_reversal.py
class TestReversal:
    def test_reversal_blocked_in_locked_period(self): ...  # P0-3
    def test_force_override_requires_ceo_cfo(self): ...
    def test_reversal_idempotent(self): ...  # P0-4
    def test_reversal_txn_id_format(self): ...
```

### 6.2 P1 功能测试用例

```python
# tests/test_agency_balance.py
class TestAgencyBalance:
    def test_current_balance_excludes_fee(self): ...  # P1-1
    def test_total_cost_includes_fee(self): ...

# tests/test_recon_matching.py
class TestReconMatching:
    def test_their_expense_convention(self): ...  # P1-2
    def test_their_income_convention(self): ...
    def test_our_perspective_convention(self): ...
```

---

## 七、回滚方案

### 7.1 数据库回滚

```sql
-- 1. 删除触发器
DROP TRIGGER IF EXISTS trg_ledger_prevent_direct_status ON ledger;

-- 2. 删除函数
DROP FUNCTION IF EXISTS transition_ledger_status;
DROP FUNCTION IF EXISTS reverse_ledger_entry;
DROP FUNCTION IF EXISTS is_period_locked;

-- 3. 删除表
DROP TABLE IF EXISTS period_locks CASCADE;
DROP TABLE IF EXISTS state_transitions CASCADE;

-- 4. 回滚字段
ALTER TABLE recon_runs DROP COLUMN IF EXISTS their_amount_convention;
```

### 7.2 代码回滚

```bash
# Git 回滚到重构前版本
git revert --no-commit <refactor-commit-range>
git commit -m "Revert V5.2 refactor"
```

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 存储过程性能问题 | 高并发下延迟增加 | 1. 预先压测 2. 索引优化 3. 连接池调优 |
| 迁移数据丢失 | 历史数据不一致 | 1. 备份 2. 分步迁移 3. 验证脚本 |
| 角色权限冲突 | CEO/CFO 无法特批 | 1. 提前配置角色 2. 灰度发布 |
| 前端兼容性 | 旧版本无法操作 | 1. 强制更新 2. 版本检查 API |

---

## 九、验收标准

### 9.1 P0 验收

- [ ] 期间锁：锁定后无法修改该期间的 ledger 记录
- [ ] 状态迁移：直接 UPDATE txn_status 被触发器拒绝
- [ ] 冲正禁止：锁定期间冲正返回错误，除非 CEO/CFO + force_override
- [ ] 冲正幂等：相同原始记录重试冲正返回同一个冲正记录 ID

### 9.2 P1 验收

- [ ] 余额口径：API 返回 `current_balance` 和 `total_cost` 两个字段
- [ ] 对账符号：不同 `their_amount_convention` 设置产生正确的匹配结果

---

## 十、附录

### 10.1 参考文档

| 文档 | 位置 |
|------|------|
| V5.2 最终版 | `C:\Users\user\Downloads\广告投放业务管理系统-V5.2-最终版.md` |
| 当前 LEDGER_SOT | `docs/2.sot/LEDGER_SOT.md` v1.1 |
| 当前 STATE_MACHINE | `docs/2.sot/STATE_MACHINE.md` v2.6 |
| 当前 DATA_SCHEMA | `docs/2.sot/DATA_SCHEMA.md` v5.2 |

### 10.2 关键代码位置

| 模块 | 文件 |
|------|------|
| 账本模型 | `backend/models/finance/ledger.py` |
| 财务事件 | `backend/models/finance/financial_event.py` |
| 对账模型 | `backend/models/finance/reconciliation.py` |
| 账本过账服务 | `backend/services/ledger_posting_service.py` |
| 对账服务 | `backend/services/reconciliation_service.py` |

---

> 文档版本：v1.0
> 创建日期：2025-12-22
> 基于：广告投放业务管理系统-V5.2-最终版
