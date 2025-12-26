# Backend 测试体系 Freeze 报告

**版本** v1.4 | **状态** Frozen | **日期** 2025-12-06

---

## Freeze 决策

**Ready to Freeze**

决策依据：

1. 三套状态机（DailyReport/Topup/Reconciliation）白名单覆盖率 100%，包括合法流转、非法流转、终态保护
2. 错误码测试覆盖 ERROR_CODES_SOT.md v2.1 全部 USED 状态定义
3. 账本不变量测试覆盖 LEDGER_SOT.md v1.2 金额方向规则
4. 所有 P0/P1 问题已关闭，测试稳定通过

---

## Scope

本次 Freeze 覆盖 `backend/tests/` 下 9 个核心测试文件，包括状态机测试、错误码测试、API 集成测试。详细文件清单见附录 A。

不在范围内：其他 test_*.py 文件、前端测试、E2E 测试。

---

## 测试覆盖率

### 总体覆盖

| 指标 | 数值 |
|------|------|
| 测试文件数 | 32 |
| 测试函数数 | 499 |
| Freeze 范围 | 10 核心文件 / 183 测试函数 |
| API Endpoint 总数 | 127 |
| 已覆盖 Endpoint | 48 (37.8%) |

### 模块覆盖率

| 模块 | Endpoint 数 | 已覆盖 | 覆盖率 | 状态 |
|------|------------|--------|--------|------|
| daily_reports | 12 | 10 | 83% | Frozen |
| topup | 13 | 8 | 62% | Frozen |
| reconciliation | 12 | 9 | 75% | Frozen |
| **finance_profit** | **1** | **1** | **100%** | **Frozen (v1.4新增)** |
| authentication | 13 | 6 | 46% | 部分覆盖 |
| projects | 12 | 5 | 42% | 部分覆盖 |
| channels | 4 | 2 | 50% | 部分覆盖 |
| ad_accounts | 4 | 2 | 50% | 部分覆盖 |
| ledger | 8 | 3 | 38% | 未覆盖 |
| ai_monitoring | 11 | 0 | 0% | 未覆盖 |
| ai_analytics | 6 | 2 | 33% | 未覆盖 |
| reports | 5 | 0 | 0% | 未覆盖 |
| reconciliation_extended | 9 | 0 | 0% | 未覆盖 |
| project_templates | 7 | 0 | 0% | 未覆盖 |
| import_jobs | 3 | 0 | 0% | 未覆盖 |
| supabase_auth | 17 | 0 | 0% | 未覆盖 |

### 覆盖漏洞区

1. **Ledger 模块**：核心财务模块仅 3/8 覆盖，缺少 budget 分配、交易状态变更测试
2. **AI 监控/分析**：17 个 endpoint 零覆盖，异常检测、预测功能未验证
3. **扩展对账**：reconciliation_extended 9 个 endpoint 未覆盖，与基础 reconciliation 存在功能重叠
4. **Supabase Auth**：17 个 endpoint 未覆盖，但已有 authentication 模块 13 个 endpoint 作为替代

---

## API Endpoint 覆盖清单

### DailyReport 模块 (Frozen)

| Endpoint | 方法 | 测试覆盖 | 异常路径 |
|----------|------|---------|---------|
| /daily-reports | GET | Yes | - |
| /daily-reports | POST | Yes | 401, 400 |
| /daily-reports/{id} | GET | Yes | 404 |
| /daily-reports/{id} | PUT | Yes | 403, 404 |
| /daily-reports/{id} | DELETE | Yes | 403, 404 |
| /daily-reports/batch-import | POST | Yes | 400 |
| /daily-reports/{id}/review | POST | Yes | 403 |
| /daily-reports/{id}/trend-review | POST | Yes | - |
| /daily-reports/{id}/final-confirm | POST | Yes | - |
| /daily-reports/{id}/lock | POST | Yes | - |
| /daily-reports/statistics | GET | No | - |
| /daily-reports/export | GET | No | - |

### Topup 模块 (Frozen)

| Endpoint | 方法 | 测试覆盖 | 异常路径 |
|----------|------|---------|---------|
| /topups | GET | Yes | - |
| /topups | POST | Yes | 401, 400 |
| /topups/{id} | GET | Yes | 404 |
| /topups/{id} | PUT | Yes | - |
| /topups/{id}/submit | PUT | Yes | - |
| /topups/{id}/approve | PUT | Yes | 403 |
| /topups/{id}/reject | PUT | Yes | - |
| /topups/{id}/cancel | POST | No | - |
| /topups/statistics | GET | No | - |
| /topups/pending | GET | No | - |
| /topups/export | GET | No | - |
| /topups/by-account/{id} | GET | No | - |
| /topups/by-project/{id} | GET | No | - |

### Reconciliation 模块 (Frozen)

| Endpoint | 方法 | 测试覆盖 | 异常路径 |
|----------|------|---------|---------|
| /reconciliations | GET | Yes | - |
| /reconciliations/batches | POST | Yes | 403, 400 |
| /reconciliations/batches/{id} | GET | Yes | 404 |
| /reconciliations/batches/{id}/run | POST | Yes | - |
| /reconciliations/batches/{id}/details | GET | Yes | - |
| /reconciliations/details/{id}/review | PUT | Yes | - |
| /reconciliations/details/{id}/adjust | POST | Yes | - |
| /reconciliations/statistics | GET | Yes | - |
| /reconciliations/export | GET | Yes | - |
| /reconciliations/reports | GET | No | - |
| /reconciliations/reports | POST | No | - |
| /reconciliations/differences | GET | No | - |

详细覆盖清单见附录 H。

---

## 未覆盖风险 Ledger

以下为未来必须监控的测试盲区，按风险等级排序：

### 高风险 (必须在 Sprint +1 覆盖)

| 风险项 | 模块 | 影响 | 缓解措施 |
|--------|------|------|---------|
| RISK-LED-001 | ledger | 交易状态变更未验证，可能导致资金流转错误 | 添加 transactions/{id}/status PUT 测试 |
| RISK-LED-002 | ledger | budget 分配逻辑未覆盖，可能超支 | 添加 budget POST/GET 测试 |
| RISK-DB-001 | 全局 | SQLite 与 PostgreSQL 行为差异 | 添加 PG 集成测试 |
| RISK-SM-001 | daily_reports | statistics/export endpoint 未覆盖 | 补充统计导出测试 |

### 中风险 (Sprint +2 覆盖)

| 风险项 | 模块 | 影响 | 缓解措施 |
|--------|------|------|---------|
| RISK-AI-001 | ai_monitoring | 异常检测功能完全未验证 | 建立 AI 模块测试框架 |
| RISK-AI-002 | ai_analytics | 预测分析未验证 | 与 AI 团队协作补充 |
| RISK-AUTH-001 | supabase_auth | Supabase 集成未验证 | 评估是否需要单独测试 |
| RISK-TPL-001 | project_templates | 模板功能未验证 | 补充模板 CRUD 测试 |

### 低风险 (按需覆盖)

| 风险项 | 模块 | 影响 | 缓解措施 |
|--------|------|------|---------|
| RISK-EXT-001 | reconciliation_extended | 与基础模块功能重叠 | 评估是否废弃 |
| RISK-IMP-001 | import_jobs | 导入任务管理 | 补充异步任务测试 |
| RISK-RPT-001 | reports | 报表生成 | 与前端联调时补充 |

---

## SoT 对齐

| SoT 文档 | 版本 | 对齐内容 |
|----------|------|---------|
| STATE_MACHINE.md | v2.7 | 8/7/5 状态机白名单、终态定义 |
| ERROR_CODES_SOT.md | v2.1 | 7 类错误码前缀、HTTP 映射 |
| LEDGER_SOT.md | v1.2 | 金额正负方向、账本类型约束 |

详细覆盖矩阵见附录 B。

---

## 限制与风险

| 限制 | 风险评估 | 缓解措施 |
|------|---------|---------|
| 测试使用 SQLite，生产使用 PostgreSQL | 中。部分 PG 特性（UUID 函数、CHECK 约束行为）未覆盖 | 后续补充 PG 集成测试 |
| 无 E2E 测试 | 低。API 层已覆盖核心流程 | 中期建立 E2E 框架 |
| 无性能测试 | 低。当前阶段非瓶颈 | 按需补充 |
| API 整体覆盖率 37.3% | 中。非核心模块未覆盖 | 按风险 Ledger 分批补充 |

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
| 补充 Ledger 模块测试 (RISK-LED-001/002) | Backend Team | Sprint +1 |
| 补充 DailyReport statistics/export 测试 | Backend Team | Sprint +1 |
| 建立 AI 模块测试框架 | AI Team | Sprint +2 |
| 拆分 conftest.py | Backend Team | Sprint +2 |
| 建立 E2E 测试框架 | QA Team | Sprint +2 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-11-30 | 初始 Freeze |
| v1.1 | 2025-11-30 | 结构重构 |
| v1.2 | 2025-11-30 | 精简主文档，增加风险评估与 Owner |
| v1.3 | 2025-11-30 | 添加覆盖率数据、API 覆盖清单、风险 Ledger |
| v1.4 | 2025-12-06 | 新增 Finance Profit API 模块测试基线（13 用例），更新覆盖率统计 |

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
├── test_reconciliation_service.py
└── test_finance_profit_api.py         # v1.4 新增
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
conftest.py (~1011 lines)
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

**拆分建议**：
- `conftest_db.py` - 数据库配置、GUID TypeDecorator
- `conftest_fixtures.py` - 用户、认证、示例数据 fixtures
- `conftest_helpers.py` - StateHelper、LedgerInvariantHelper 类

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

**test_state_machine_transitions.py** (36 tests)
- TestDailyReportStateMachine
- TestTopupStateMachine
- TestReconciliationStateMachine
- TestFinalStateImmutability
- TestStateHelperConsistency
- TestLedgerInvariants

**test_state_machine_p2.py** (40 tests)
- TestDailyReportStateMachineIntegration
- TestTopupStateMachineIntegration
- TestReconciliationStateMachineIntegration

### D.2 错误码测试

**test_error_codes_coverage.py** (22 tests)
- TestErrorCodeDefinitions
- TestErrorCodeUsageScenarios
- TestErrorCodeAntiPatterns
- TestErrorCodeHTTPMapping
- TestTrendErrorCodeSpecialCases

### D.3 API 测试

- test_daily_report_api.py: 24 tests - 创建、查询、审核、删除、批量导入
- test_topup_api.py: 12 tests - 创建、审核流程、统计
- test_reconciliation_api.py: 16 tests - 批次创建、执行、导出

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
| P1-DR-001 | 旧状态名断言 | 对齐 STATE_MACHINE.md v2.7 |
| P1-TP-001 | pending → pending_review | 对齐 STATE_MACHINE.md v2.7 |
| P1-TP-002 | SYS_004 误用 | 修正为 BIZ_002 |
| P1-RA-001 | pending → draft | 对齐 STATE_MACHINE.md v2.7 |
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

### F.3 测试执行时长基准

| 测试套件 | 预估时长 | 备注 |
|---------|---------|------|
| 状态机测试 | ~15s | 76 tests |
| 错误码测试 | ~5s | 22 tests |
| API 测试 | ~30s | 52 tests |
| 全量测试 | ~2min | 486 tests |

注：基于 SQLite 内存数据库，实际 PG 测试可能增加 50%。

---

## G. 相关文档

| 文档 | 路径 |
|------|------|
| STATE_MACHINE.md | docs/sot/STATE_MACHINE.md |
| ERROR_CODES_SOT.md | docs/sot/ERROR_CODES_SOT.md |
| LEDGER_SOT.md | docs/sot/LEDGER_SOT.md |
| AUTH_SPEC.md | docs/sot/AUTH_SPEC.md |
| DATA_SCHEMA.md | docs/sot/DATA_SCHEMA.md |

---

## H. 完整 API Endpoint 覆盖清单

### H.1 Authentication 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /auth/login | POST | Yes |
| /auth/register | POST | Yes |
| /auth/refresh | POST | Yes |
| /auth/logout | POST | Yes |
| /auth/logout-all | POST | No |
| /auth/me | GET | Yes |
| /auth/change-password | POST | Yes |
| /auth/forgot-password | POST | No |
| /auth/reset-password | POST | No |
| /auth/verify-email | POST | No |
| /auth/resend-verification | POST | No |
| /auth/verify-token | POST | No |
| /auth/login/oauth | POST | No |

### H.2 Projects 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /projects | GET | Yes |
| /projects | POST | Yes |
| /projects/{id} | GET | Yes |
| /projects/{id} | PUT | Yes |
| /projects/{id} | DELETE | Yes |
| /projects/{id}/members | POST | No |
| /projects/{id}/members | GET | No |
| /projects/{id}/members/{uid} | DELETE | No |
| /projects/{id}/archive | POST | No |
| /projects/{id}/statistics | GET | No |
| /projects/my | GET | No |
| /projects/search | GET | No |

### H.3 Channels 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /channels | GET | Yes |
| /channels/{id} | GET | Yes |
| /channels | POST | No |
| /channels/{id} | PUT | No |

### H.4 Ad Accounts 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /ad-accounts | GET | Yes |
| /ad-accounts/{id} | GET | Yes |
| /ad-accounts | POST | No |
| /ad-accounts/{id}/status | POST | No |

### H.5 Ledger 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /ledger/transactions | POST | Yes |
| /ledger/transactions | GET | Yes |
| /ledger/transactions/{id}/status | PUT | No |
| /ledger/balance | GET | Yes |
| /ledger/projects/{id}/budget | GET | No |
| /ledger/budget | POST | No |
| /ledger/statistics | GET | No |
| /ledger/export | GET | No |

### H.6 AI Monitoring 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /ai-monitoring/anomalies | POST | No |
| /ai-monitoring/anomalies | GET | No |
| /ai-monitoring/anomalies/{id}/status | PUT | No |
| /ai-monitoring/predictions | POST | No |
| /ai-monitoring/predictions | GET | No |
| /ai-monitoring/rules | POST | No |
| /ai-monitoring/rules | GET | No |
| /ai-monitoring/simulate-detection | POST | No |
| /ai-monitoring/dashboard | GET | No |
| /ai-monitoring/statistics | GET | No |

### H.7 AI Analytics 模块

| Endpoint | 方法 | 测试覆盖 |
|----------|------|---------|
| /ai-analytics/trend-analysis | POST | Yes |
| /ai-analytics/spend-prediction | POST | Yes |
| /ai-analytics/summary | GET | No |
| /ai-analytics/history | GET | No |
| /ai-analytics/alerts | GET | No |
| /ai-analytics/recommendations | GET | No |

### H.8 Finance Profit 模块 (v1.4 新增)

| Endpoint | 方法 | 测试覆盖 | 异常路径 |
|----------|------|---------|---------|
| /finance/profit/summary | GET | Yes | 401, 403, 404, 400 |

**测试文件**: `backend/tests/test_finance_profit_api.py`

**测试用例清单** (13 用例):

| 测试类 | 测试用例 | 场景类型 | SoT 引用 |
|--------|----------|----------|----------|
| `TestFinanceProfitApiSmoke` | `test_profit_summary_no_project_id_returns_all` | Happy Path | API_SOT 11A |
| `TestFinanceProfitApiSmoke` | `test_profit_summary_with_project_id` | Happy Path | API_SOT 11A |
| `TestFinanceProfitApiSmoke` | `test_profit_summary_invalid_project_returns_404` | 错误码校验 | ERROR_CODES BIZ_002 |
| `TestFinanceProfitApiSmoke` | `test_profit_summary_invalid_date_range_returns_400` | 错误码校验 | ERROR_CODES BIZ_001 |
| `TestFinanceProfitApiSmoke` | `test_profit_summary_unauthorized_returns_403` | 权限校验 | AUTH_SPEC v2.0 |
| `TestFinanceProfitApiAuthorization` | `test_admin_can_access` | 权限校验 | AUTH_SPEC v2.0 |
| `TestFinanceProfitApiAuthorization` | `test_finance_can_access` | 权限校验 | AUTH_SPEC v2.0 |
| `TestFinanceProfitApiAuthorization` | `test_data_operator_can_access` | 权限校验 | AUTH_SPEC v2.0 |
| `TestFinanceProfitApiAuthorization` | `test_no_token_returns_401` | 认证校验 | ERROR_CODES AUTH_400 |
| `TestFinanceProfitApiDateFilters` | `test_with_start_date_only` | 日期过滤 | API_SOT 11A |
| `TestFinanceProfitApiDateFilters` | `test_with_end_date_only` | 日期过滤 | API_SOT 11A |
| `TestFinanceProfitApiDateFilters` | `test_with_valid_date_range` | 日期过滤 | API_SOT 11A |
| `TestFinanceProfitApiResponseFormat` | `test_response_contains_required_fields` | 响应格式 | schemas/finance.py |
