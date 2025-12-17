# 后端回归测试结果摘要

> **执行时间**: 2025-12-02  
> **执行命令**: `python run_tests.py --type regression`  
> **执行环境**: Windows, Python 3.11

---

## 1. 回归总体结论

✅ **本次回归：5/5 测试套件全部通过（无失败）**

所有回归测试套件均通过，无失败用例。总计 **177 个测试用例**，其中 **174 个通过**，**3 个跳过**（Ledger 模块中的预期跳过用例）。

---

## 2. 各测试套件统计表

| 测试套件 | 测试文件 | 用例总数 | 通过 | 失败 | 跳过 | 状态 |
|---------|---------|---------|------|------|------|------|
| **Daily Reports API** | `test_daily_report_flow_generated.py` | 33 | 33 | 0 | 0 | ✅ PASS |
| **Trend Risk API** | `test_trend_risk_flow_generated.py` | 17 | 17 | 0 | 0 | ✅ PASS |
| **Ledger** | `backend/tests/ledger/` | 57 | 54 | 0 | 3 | ✅ PASS |
| **Ad Accounts** | `backend/tests/ad_accounts/` | 51 | 51 | 0 | 0 | ✅ PASS |
| **Topup API** | `test_topup_api.py` | 22 | 22 | 0 | 0 | ✅ PASS |
| **总计** | - | **180** | **177** | **0** | **3** | ✅ **ALL PASS** |

### 详细统计

#### Daily Reports API
- **测试用例**: 33
- **通过**: 33 (100%)
- **失败**: 0
- **跳过**: 0
- **警告**: 9 (主要是 `pytest.mark.api` 未注册警告和 Pydantic 弃用警告)

#### Trend Risk API
- **测试用例**: 17
- **通过**: 17 (100%)
- **失败**: 0
- **跳过**: 0
- **警告**: 7 (主要是 `pytest.mark.api` 未注册警告和 Pydantic 弃用警告)

#### Ledger
- **测试用例**: 57
- **通过**: 54 (94.7%)
- **失败**: 0
- **跳过**: 3 (预期跳过，非错误)
- **警告**: 2 (Pydantic 弃用警告)

#### Ad Accounts
- **测试用例**: 51
- **通过**: 51 (100%)
- **失败**: 0
- **跳过**: 0
- **警告**: 2 (Pydantic 弃用警告)

#### Topup API
- **测试用例**: 22
- **通过**: 22 (100%)
- **失败**: 0
- **跳过**: 0
- **警告**: 2 (Pydantic 弃用警告)

---

## 3. 失败用例详情

**无失败用例**

所有测试用例均通过，无失败情况。

---

## 4. 警告信息汇总

### 非阻塞性警告

1. **PytestUnknownMarkWarning** (16 个)
   - **位置**: `test_daily_report_flow_generated.py`, `test_trend_risk_flow_generated.py`
   - **原因**: `@pytest.mark.api` marker 未在 `pytest.ini` 中注册
   - **影响**: 不影响测试执行，仅为警告
   - **建议**: 在 `pytest.ini` 中添加 `api` marker 注册

2. **PydanticDeprecatedSince20** (多次)
   - **位置**: `backend/schemas/daily_report.py:98`
   - **原因**: `max_items` 在 Pydantic V2 中已弃用，应使用 `max_length`
   - **影响**: 不影响当前功能，但未来版本可能移除
   - **建议**: 将 `max_items=100` 替换为 `max_length=100`

3. **PendingDeprecationWarning** (多次)
   - **位置**: `starlette/formparsers.py:12`
   - **原因**: Starlette 建议使用 `python_multipart` 替代 `multipart`
   - **影响**: 不影响当前功能，为依赖库警告
   - **建议**: 可忽略，或等待依赖库更新

---

## 5. 回归测试覆盖范围

本次回归测试覆盖了以下核心业务模块：

- ✅ **Daily Reports**: 8 状态机流程、权限验证、错误码校验
- ✅ **Trend Risk**: 风控检测流程、状态流转、权限控制
- ✅ **Ledger**: 账本服务、不变量验证（LEDGER_SOT.md）
- ✅ **Ad Accounts**: API CRUD、状态更新、权限验证
- ✅ **Topup**: 充值流程、7 状态机、权限控制

---

## 6. 结论

**回归测试状态**: ✅ **全部通过**

- 所有 5 个测试套件均通过
- 177 个测试用例通过，0 个失败
- 3 个预期跳过用例（Ledger 模块）
- 无阻塞性问题

**建议后续操作**:
1. 可安全合并相关 PR
2. 建议修复非阻塞性警告（`pytest.mark.api` 注册、Pydantic `max_items` 替换）
3. 回归测试门槛规则已生效，后续修改相关代码必须通过回归测试

---

**报告生成时间**: 2025-12-02  
**报告生成工具**: AI_ad_spend02 回归守门员助手


