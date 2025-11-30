# TESTING.md - AI 广告代投系统测试规范

> **文档性质**: 测试策略与质量保证规范
> **约束级别**: 项目级，所有测试实现必须遵循本文档定义的策略与约束
> **版本**: v1.0
> **status**: frozen
> **基准**: MASTER.md v3.4, ARCHITECTURE.md v1.0, PATTERNS.md v1.0
> **owner**: wade
> **last_reviewed**: 2025-11-27

---

## 第一章 文档定位与约束

### 1.1 本文档职责

TESTING.md 定义系统测试策略与质量约束：

- 测试分层与覆盖率目标
- 状态机测试策略（核心）
- 账务与账本测试策略（核心）
- Mock 与 Fixture 规范
- CI/CD 集成要求

> 引用: MASTER.md 第九章 文档索引

### 1.2 本文档不做

本文档不承担以下职责：

- 不定义业务规则（属于 BUSINESS_RULES.md）
- 不定义 API 接口（属于 API_SOT.md）
- 不定义部署流程（属于 DEPLOYMENT.md）
- 不包含具体测试用例代码（属于 tests/ 目录）

### 1.3 约束强制级别

| 级别 | 说明 | 违反后果 |
|-----|------|---------|
| MUST | 强制要求 | PR 拒绝 |
| SHOULD | 推荐要求 | 需说明理由 |
| MAY | 可选建议 | 自由选择 |

---

## 第二章 测试策略概述

### 2.1 测试金字塔

```
             /\
            /E2E\           (5%)  - 端到端测试
           /------\
          /集成测试\         (20%) - Integration Tests
         /----------\
        /  单元测试  \       (75%) - Unit Tests
       /--------------\
```

### 2.2 覆盖率目标

| 测试类型 | 覆盖率目标 | 级别 | 说明 |
|---------|-----------|------|------|
| 单元测试 | >= 80% | MUST | 所有 Service/Domain 逻辑 |
| 集成测试 | >= 60% | SHOULD | API 端点与数据库交互 |
| E2E 测试 | 关键路径 100% | MUST | 账务流程、状态流转 |

> 引用: MASTER.md 第七章 §7.2「测试覆盖率 80%+」

### 2.3 测试分类

| 分类 | 范围 | 工具 | 执行频率 |
|-----|------|------|---------|
| 单元测试 | 函数/方法级别 | pytest | 每次提交 |
| 集成测试 | 模块交互 | pytest + TestClient | 每次 PR |
| E2E 测试 | 完整业务流程 | pytest + 实际数据库 | 每日/发布前 |

---

## 第三章 状态机测试策略

### 3.1 测试覆盖要求

状态机是系统核心，测试必须覆盖：

| 覆盖项 | 级别 | 说明 |
|-------|------|------|
| 所有允许的状态转换 | MUST | 8 状态机的 10 条合法路径 |
| 所有禁止的状态转换 | MUST | 验证拒绝非法流转 |
| 前置条件校验 | MUST | 每个状态转换的必要条件 |
| 终态保护 | MUST | final_locked 后拒绝任何修改 |

> 引用: STATE_MACHINE.md v2.6 §8

### 3.2 必测状态转换路径

**正常路径（MUST 测试）**

```
null → raw_submitted → trend_pending → trend_ok → final_pending
     → final_confirmed → final_locked
```

**异常路径（MUST 测试）**

```
trend_pending → trend_flagged → trend_resolved → final_pending
```

### 3.3 禁止的状态转换测试

以下转换必须验证被拒绝：

| 禁止转换 | 测试断言 | 引用 |
|---------|---------|------|
| trend_flagged → final_pending | 抛出 SM-002 错误 | STATE_MACHINE.md |
| raw_submitted → final_pending | 抛出 SM-002 错误 | STATE_MACHINE.md |
| final_locked → 任何状态 | 抛出 SM-003 错误 | MASTER.md INV-003 |
| 任何状态 → null | 抛出 SM-002 错误 | STATE_MACHINE.md |

### 3.4 状态测试模板

```python
# 测试框架结构（伪代码）
class TestStateMachine:
    """状态机测试类"""

    def test_valid_transition_raw_to_trend_pending(self):
        """测试: raw_submitted → trend_pending 允许"""
        # Arrange: 创建 raw_submitted 状态的日报
        # Act: 调用状态流转方法
        # Assert: 状态变为 trend_pending
        pass

    def test_invalid_transition_flagged_to_final_pending(self):
        """测试: trend_flagged → final_pending 禁止"""
        # Arrange: 创建 trend_flagged 状态的日报
        # Act: 尝试流转到 final_pending
        # Assert: 抛出 SM-002 错误，状态不变
        pass

    def test_final_locked_immutable(self):
        """测试: final_locked 后拒绝任何修改"""
        # Arrange: 创建 final_locked 状态的日报
        # Act: 尝试修改任意字段
        # Assert: 抛出 SM-003 错误
        pass
```

---

## 第四章 账务与账本测试策略

### 4.1 测试覆盖要求

账本是系统审计核心，测试必须覆盖：

| 覆盖项 | 级别 | 说明 |
|-------|------|------|
| 余额计算公式 | MUST | balance = SUM(ledger_entries.amount) |
| 双账本隔离 | MUST | PROJECT 只有 REVENUE，SUPPLIER 只有 COST |
| 账本只追加 | MUST | 验证 UPDATE/DELETE 被拒绝 |
| 红冲机制 | MUST | REVERSAL 正确抵消原记录 |

> 引用: MASTER.md INV-001, LEDGER_SOT.md v1.1

### 4.2 账本隔离测试

| 测试场景 | 预期结果 | 引用 |
|---------|---------|------|
| PROJECT 账本写入 REVENUE | 成功 | LEDGER_SOT.md §2 |
| PROJECT 账本写入 COST | 拒绝，抛出 LED-003 | MASTER.md INV-001 |
| SUPPLIER 账本写入 COST | 成功 | LEDGER_SOT.md §2 |
| SUPPLIER 账本写入 REVENUE | 拒绝，抛出 LED-003 | MASTER.md INV-001 |

### 4.3 余额一致性测试

```python
# 测试框架结构（伪代码）
class TestLedgerBalance:
    """账本余额测试类"""

    def test_balance_equals_sum_of_entries(self):
        """测试: 余额 = SUM(账本记录)"""
        # Arrange: 创建多条账本记录
        # Act: 计算余额
        # Assert: balance == SUM(ledger_entries.amount)
        pass

    def test_reversal_cancels_original(self):
        """测试: 红冲后净值为零"""
        # Arrange: 创建 REVENUE 记录
        # Act: 执行红冲
        # Assert: 原 REVENUE + REVERSAL = 0
        pass
```

### 4.4 账本不可变性测试

| 测试场景 | 操作 | 预期结果 |
|---------|------|---------|
| UPDATE ledger_entries | 尝试更新 amount | 拒绝，抛出 LED-001 |
| DELETE ledger_entries | 尝试删除记录 | 拒绝，抛出 LED-001 |
| UPDATE balance 直接 | 尝试直接修改 balance | 拒绝，抛出 LED-002 |

### 4.5 日报-账本关联测试

| 测试场景 | 预期结果 | 引用 |
|---------|---------|------|
| final_locked 触发 REVENUE 生成 | conversions_final > 0 时生成 | MASTER.md INV-001 |
| final_locked 触发 COST 生成 | real_spend > 0 时生成 | MASTER.md INV-001 |
| 无日报直接写账本 | 拒绝，抛出 LED-004 | MASTER.md BI-04 |

---

## 第五章 API 测试策略

### 5.1 测试覆盖要求

| 覆盖项 | 级别 | 说明 |
|-------|------|------|
| 响应格式 Envelope | MUST | success/data/code/message/request_id/timestamp |
| 权限校验 | MUST | 每个端点的角色限制 |
| 错误码一致性 | MUST | 使用 ERROR_CODES_SOT.md 定义的错误码 |
| 分页参数 | MUST | page 1-based, size <= 100 |

> 引用: API_SOT.md v9.0, ERROR_CODES_SOT.md v2.1

### 5.2 API 响应格式测试

```python
# 测试框架结构（伪代码）
class TestAPIResponse:
    """API 响应格式测试"""

    def test_success_response_envelope(self):
        """测试: 成功响应包含标准字段"""
        # Assert: response 包含 success, data, request_id, timestamp
        pass

    def test_error_response_envelope(self):
        """测试: 错误响应包含错误码"""
        # Assert: response 包含 success=false, code, message
        pass
```

### 5.3 权限测试矩阵

| API 端点 | AD_OPERATOR | OPERATIONS | FINANCE | ADMIN |
|---------|-------------|------------|---------|-------|
| POST /daily-reports | ✅ | ❌ | ❌ | ❌ |
| PATCH /daily-reports/{id}/confirm | ❌ | ✅ | ❌ | ❌ |
| POST /ledger/reversal | ❌ | ❌ | ✅ | ❌ |
| GET /audit/logs | ❌ | ❌ | ❌ | ✅ |

> 引用: AUTH_SPEC.md v2.0, MASTER.md INV-004

---

## 第六章 数据流测试策略

### 6.1 三数据流分离测试

| 数据流 | 录入角色 | 测试验证 |
|-------|---------|---------|
| Raw (conversions_raw, raw_spend) | 投手 | 运营无法修改 |
| Real (real_spend) | 运营 | 投手无法修改 |
| Final (conversions_final) | 运营 | 投手无法修改 |

> 引用: MASTER.md INV-002, DAILY_REPORT_SOT.md v1.0

### 6.2 数据流冻结测试

| 测试场景 | 状态 | 预期结果 |
|---------|------|---------|
| 修改 conversions_raw | trend_ok 后 | 拒绝修改 |
| 修改 real_spend | final_locked 后 | 拒绝修改 |
| 修改 conversions_final | final_locked 后 | 拒绝修改 |

---

## 第七章 Mock 与 Fixture 规范

> **后端单测环境健康度与兼容性说明**: 见 [docs/testing/BACKEND_TEST_ENV_HEALTH_v1.0.md](../testing/BACKEND_TEST_ENV_HEALTH_v1.0.md)

### 7.1 Mock 使用原则

| 原则 | 级别 | 说明 |
|-----|------|------|
| 单元测试必须 Mock 外部依赖 | MUST | 数据库、外部 API |
| 集成测试使用真实数据库 | MUST | 测试数据库实例 |
| 禁止 Mock 状态机逻辑 | MUST | 状态流转必须真实执行 |
| 禁止 Mock 账本计算 | MUST | 余额计算必须真实执行 |

### 7.2 Fixture 规范

| Fixture 类型 | 用途 | 命名规范 |
|-------------|------|---------|
| 实体工厂 | 创建测试实体 | `create_<entity>()` |
| 状态工厂 | 创建特定状态实体 | `create_<entity>_<state>()` |
| 数据集 | 预设测试数据 | `fixtures/<entity>.json` |

### 7.3 测试数据隔离

| 约束 | 级别 | 说明 |
|-----|------|------|
| 每个测试独立数据 | MUST | 禁止测试间共享状态 |
| 测试后清理数据 | MUST | 使用事务回滚或 truncate |
| 禁止依赖测试顺序 | MUST | 测试可随机执行 |

---

## 第八章 CI/CD 集成

### 8.1 CI 流水线测试阶段

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Lint   │ → │  Unit   │ → │ Integ   │ → │  E2E    │
│ (Ruff)  │   │ Tests   │   │ Tests   │   │ Tests   │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

> 引用: DEPLOYMENT.md v1.0 §3

### 8.2 测试门禁

| 门禁 | 级别 | 通过条件 |
|-----|------|---------|
| Lint | MUST | 0 errors |
| 单元测试 | MUST | 100% 通过，覆盖率 >= 80% |
| 集成测试 | MUST | 100% 通过 |
| E2E 测试 | MUST | 关键路径 100% 通过 |

### 8.3 测试报告要求

| 报告项 | 级别 | 说明 |
|-------|------|------|
| 覆盖率报告 | MUST | 每次 PR 生成 |
| 失败日志 | MUST | 详细错误信息 |
| 性能指标 | SHOULD | 执行时间统计 |

---

## 第九章 特殊场景测试

### 9.1 并发测试

| 测试场景 | 预期结果 | 引用 |
|---------|---------|------|
| 同一日报并发确认 | 仅一个成功 | TRANSFER_SOT.md §6 |
| 同一账本并发写入 | 事务隔离，数据一致 | LEDGER_SOT.md §5 |

### 9.2 边界条件测试

| 测试场景 | 边界值 | 预期结果 |
|---------|-------|---------|
| conversions_final = 0 | 零值 | 不生成 REVENUE |
| real_spend = 0 | 零值 | 不生成 COST |
| 金额精度 | Decimal(10,2) | 四舍五入 ROUND_HALF_UP |

### 9.3 红冲流程测试

| 测试步骤 | 验证点 |
|---------|-------|
| 1. 创建终态日报 | 生成 REVENUE/COST 记录 |
| 2. 执行红冲 | 生成 REVERSAL 记录 |
| 3. 验证净值 | 原记录 + REVERSAL = 0 |
| 4. 验证状态 | 日报状态仍为 final_locked |

> 引用: MASTER.md INV-003「红冲机制」

---

## 第十章 测试命名与组织

### 10.1 测试文件组织

```
tests/
├── unit/                    # 单元测试
│   ├── domain/              # Domain 层测试
│   │   ├── test_state_machine.py
│   │   └── test_ledger_service.py
│   └── application/         # Application 层测试
│       └── test_daily_report_service.py
├── integration/             # 集成测试
│   ├── test_api_daily_reports.py
│   └── test_api_ledger.py
├── e2e/                     # 端到端测试
│   ├── test_daily_report_flow.py
│   └── test_reversal_flow.py
└── fixtures/                # 测试数据
    ├── daily_reports.json
    └── ledger_entries.json
```

### 10.2 测试命名规范

| 命名模式 | 示例 |
|---------|------|
| `test_<action>_<scenario>` | `test_create_daily_report_success` |
| `test_<action>_<error_condition>` | `test_create_daily_report_invalid_status` |
| `test_<entity>_<invariant>` | `test_ledger_balance_equals_sum` |

### 10.3 测试描述规范

```python
def test_final_locked_prevents_modification():
    """
    测试: final_locked 状态后禁止修改

    前置条件: 日报处于 final_locked 状态
    操作: 尝试修改 conversions_final
    预期: 抛出 SM-003 错误，数据不变
    引用: MASTER.md INV-003
    """
    pass
```

---

## 附录 A: 必测清单

### A.1 状态机必测项

| 编号 | 测试项 | 级别 |
|-----|-------|------|
| SM-T001 | 正常路径完整流转 | MUST |
| SM-T002 | 异常路径（trend_flagged）流转 | MUST |
| SM-T003 | 所有禁止转换被拒绝 | MUST |
| SM-T004 | 终态 final_locked 不可逆 | MUST |
| SM-T005 | 前置条件校验 | MUST |

### A.2 账本必测项

| 编号 | 测试项 | 级别 |
|-----|-------|------|
| LED-T001 | 余额 = SUM(entries) | MUST |
| LED-T002 | UPDATE/DELETE 被拒绝 | MUST |
| LED-T003 | 双账本隔离 | MUST |
| LED-T004 | 红冲抵消验证 | MUST |
| LED-T005 | 日报-账本关联 | MUST |

### A.3 权限必测项

| 编号 | 测试项 | 级别 |
|-----|-------|------|
| AUTH-T001 | 角色权限矩阵 | MUST |
| AUTH-T002 | 越权访问拒绝 | MUST |
| AUTH-T003 | RLS 策略生效 | MUST |

---

## 附录 B: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-25 | 初始版本 | AI Doc Orchestrator |

---

**文档版本**: v1.0
**最后更新**: 2025-11-25
**对齐文档**: MASTER.md v3.4, ARCHITECTURE.md v1.0, PATTERNS.md v1.0
**维护者**: QA Lead
