# Backend 测试体系 Freeze 报告

**版本** v1.2 | **状态** Frozen | **日期** 2025-11-30

---

## Freeze 决策

**Ready to Freeze**

决策依据：

1. 三套状态机（DailyReport/Topup/Reconciliation）白名单覆盖率 100%，包括合法流转、非法流转、终态保护
2. 错误码测试覆盖 ERROR_CODES_SOT.md v2.1 全部 USED 状态定义
3. 账本不变量测试覆盖 LEDGER_SOT.md v1.1 金额方向规则
4. 所有 P0/P1 问题已关闭，测试稳定通过

---

## Scope

本次 Freeze 覆盖 `backend/tests/` 下 9 个核心测试文件，包括状态机测试、错误码测试、API 集成测试。详细文件清单见附录 A。

不在范围内：其他 test_*.py 文件、前端测试、E2E 测试。

---

## SoT 对齐

| SoT 文档 | 版本 | 对齐内容 |
|----------|------|---------|
| STATE_MACHINE.md | v2.6 | 8/7/5 状态机白名单、终态定义 |
| ERROR_CODES_SOT.md | v2.1 | 7 类错误码前缀、HTTP 映射 |
| LEDGER_SOT.md | v1.1 | 金额正负方向、账本类型约束 |

详细覆盖矩阵见附录 B。

---

## 限制与风险

| 限制 | 风险评估 | 缓解措施 |
|------|---------|---------|
| 测试使用 SQLite，生产使用 PostgreSQL | 中。部分 PG 特性（UUID 函数、CHECK 约束行为）未覆盖 | 后续补充 PG 集成测试 |
| 无 E2E 测试 | 低。API 层已覆盖核心流程 | 中期建立 E2E 框架 |
| 无性能测试 | 低。当前阶段非瓶颈 | 按需补充 |

---

## 解冻条件

以下任一条件触发时，必须解冻并重新审计：

- STATE_MACHINE.md 版本升级（当前 v2.6）
- ERROR_CODES_SOT.md 版本升级（当前 v2.1）
- LEDGER_SOT.md 版本升级（当前 v1.1）
- 任一状态机新增或删除状态枚举值

---

## 后续行动

| 行动项 | Owner | 时间窗口 |
|--------|-------|---------|
| 添加 PostgreSQL 集成测试 | Backend Team | Sprint +1 |
| 补充账本分录 CRUD 测试 | Backend Team | Sprint +1 |
| 建立 E2E 测试框架 | QA Team | Sprint +2 |
| 拆分 conftest.py | Backend Team | Sprint +2 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-11-30 | 初始 Freeze |
| v1.1 | 2025-11-30 | 结构重构 |
| v1.2 | 2025-11-30 | 精简主文档，增加风险评估与 Owner |

---

# 附录

## A. Freeze 文件清单

```
backend/tests/
├── conftest.py
├── test_state_machine_transitions.py
├── test_state_machine_p2.py
├── test_error_codes_coverage.py
├── test_daily_report_api.py
├── test_daily_report_service.py
├── test_topup_api.py
├── test_reconciliation_api.py
└── test_reconciliation_service.py
```

---

## B. SoT 对齐详情

### B.1 状态机覆盖

| 状态机 | SoT 章节 | 状态数 | 测试覆盖 |
|--------|---------|--------|---------|
| DailyReport | 第8章 | 8 | Happy path + 3 异常路径 + 终态保护 |
| Topup | 第9章 | 7 | Happy path + reject/cancel + 终态保护 |
| Reconciliation | 第11章 | 5 | Happy path + needs_adjustment + 终态保护 |

StateHelper 类提供白名单验证：
- `is_valid_transition()` 检查合法流转
- `is_terminal_state()` 检查终态
- `get_invalid_transitions()` 生成非法流转测试用例

### B.2 错误码覆盖

| 前缀 | 覆盖数 |
|------|-------|
| AUTH_ | 9 |
| BIZ_ | 9 |
| VALIDATION_ | 3 |
| SYS_ | 2 |
| DB_ | 1 |
| STATE_ | 6 |
| TREND_ | 3 |

测试内容：前缀规范、HTTP 映射、场景验证、反模式检测。

### B.3 账本不变量覆盖

| 规则 | 验证方法 |
|------|---------|
| REVENUE/TOPUP/TRANSFER_IN 正向 | LedgerInvariantHelper.validate_amount_direction() |
| COST/TRANSFER_OUT/REVERSAL 负向 | LedgerInvariantHelper.validate_amount_direction() |
| PROJECT 账本类型约束 | LedgerInvariantHelper.get_project_ledger_types() |
| SUPPLIER 账本类型约束 | LedgerInvariantHelper.get_supplier_ledger_types() |

---

## C. 测试架构

### C.1 conftest.py 结构

```
conftest.py
├── GUID TypeDecorator       # SQLite UUID 兼容
├── 数据库配置                # SQLite + StaticPool
├── Fixtures
│   ├── db_session / client
│   ├── test_user / finance_user / data_operator_user / media_buyer_user
│   ├── auth_headers_*
│   └── sample_*_data
├── StateHelper Classes
│   ├── DailyReportStateHelper
│   ├── TopupStateHelper
│   ├── ReconciliationStateHelper
│   └── LedgerInvariantHelper
└── StatusMappings
```

### C.2 StateHelper 接口

```python
class StateHelper:
    VALID_TRANSITIONS: Dict[Status, List[Status]]
    TERMINAL_STATES: List[Status]

    @classmethod
    def is_valid_transition(cls, from_status, to_status) -> bool
    @classmethod
    def is_terminal_state(cls, status) -> bool
    @classmethod
    def get_happy_path(cls) -> List[Status]
    @classmethod
    def get_exception_paths(cls) -> Dict[str, List[Status]]
    @classmethod
    def get_invalid_transitions(cls) -> List[Tuple[Status, Status]]
```

### C.3 Fixture 依赖

```
db_session
├── test_user (admin) → auth_headers_admin
├── finance_user → auth_headers_finance
├── data_operator_user → auth_headers_operator
├── media_buyer_user → auth_headers_user
├── test_channel
├── test_project
└── test_ad_account
```

---

## D. 测试用例清单

### D.1 状态机测试

**test_state_machine_transitions.py**
- TestDailyReportStateMachine
- TestTopupStateMachine
- TestReconciliationStateMachine
- TestFinalStateImmutability
- TestStateHelperConsistency
- TestLedgerInvariants

**test_state_machine_p2.py**
- TestDailyReportStateMachineIntegration
- TestTopupStateMachineIntegration
- TestReconciliationStateMachineIntegration

### D.2 错误码测试

**test_error_codes_coverage.py**
- TestErrorCodeDefinitions
- TestErrorCodeUsageScenarios
- TestErrorCodeAntiPatterns
- TestErrorCodeHTTPMapping
- TestTrendErrorCodeSpecialCases

### D.3 API 测试

- test_daily_report_api.py: 创建、查询、审核、删除、批量导入
- test_topup_api.py: 创建、审核流程、统计
- test_reconciliation_api.py: 批次创建、执行、导出

---

## E. 修复记录

### E.1 P0 修复

| ID | 问题 | 修复 |
|----|------|------|
| P0-FIXTURE-001 | 角色使用字符串 | 改用 UserRole 枚举 |
| P0-DR-001 | async 测试不兼容 | 转为 sync TestClient |
| P0-TP-001 | async 测试不兼容 | 转为 sync TestClient |
| P0-RA-001 | async 测试不兼容 | 转为 sync TestClient |

### E.2 P1 修复

| ID | 问题 | 修复 |
|----|------|------|
| P1-DR-001 | 旧状态名断言 | 对齐 STATE_MACHINE.md v2.6 |
| P1-TP-001 | pending → pending_review | 对齐 STATE_MACHINE.md v2.6 |
| P1-TP-002 | SYS_004 误用 | 修正为 BIZ_002 |
| P1-RA-001 | pending → draft | 对齐 STATE_MACHINE.md v2.6 |
| P1-RA-002 | timedelta 未导入 | 添加导入 |

### E.3 P2 修复

| ID | 问题 | 修复 |
|----|------|------|
| P2-FIXTURE-002 | 缺少角色 fixtures | 添加 finance_user 等 |
| P2-FIXTURE-003 | 缺少 StateHelper | 添加三套 StateHelper |
| P2-SM-001 | 状态机测试不完整 | 添加完整路径测试 |
| P2-EC-001 | 错误码覆盖不完整 | 添加完整覆盖测试 |

---

## F. 运维参考

### F.1 测试命令

```bash
pytest backend/tests/ -v                              # 全量
pytest backend/tests/test_state_machine_*.py -v       # 状态机
pytest backend/tests/test_error_codes_coverage.py -v  # 错误码
pytest backend/tests/test_*_api.py -v                 # API
pytest backend/tests/ --cov=backend --cov-report=html # 覆盖率
```

### F.2 CI 配置

```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --tb=short
```

---

## G. 相关文档

| 文档 | 路径 |
|------|------|
| STATE_MACHINE.md | docs/2.sot/STATE_MACHINE.md |
| ERROR_CODES_SOT.md | docs/2.sot/ERROR_CODES_SOT.md |
| LEDGER_SOT.md | docs/2.sot/LEDGER_SOT.md |
| AUTH_SPEC.md | docs/2.sot/AUTH_SPEC.md |
| DATA_SCHEMA.md | docs/2.sot/DATA_SCHEMA.md |
