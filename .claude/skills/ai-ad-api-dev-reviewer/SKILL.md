---
name: ai-ad-api-dev-reviewer
version: v1.1
description: >
  API 开发合规审查 Skill，负责在代码改动完成后执行 SoT 合规检查。
  基于 API_DEVELOPMENT_FLOW v2.3 和 AI_CODE_DEV_ORCHESTRATION_SOT v1.0 进行审查，
  输出 P0/P1/P2 级问题列表，判定是否建议上线。
baseline:
  - API_DEVELOPMENT_FLOW.md v2.3
  - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md
  - API_SOT.md v9.0
  - AUTH_SPEC.md v2.0
  - ERROR_CODES_SOT.md v2.1
  - STATE_MACHINE.md v2.6
  - BUSINESS_RULES.md v3.1
---

# API Dev Reviewer Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 在 API 开发实现完成后，对代码改动进行 **SoT 合规审查**，
> 输出 P0/P1/P2 级问题列表，给出是否建议上线的结论。

**本 Skill 只做审查，不修改任何代码文件。**

---

## 2. 适用场景

当满足以下条件时，应调用本 Skill：

- `api-dev-impl` 或手动实现完成后
- 用户要求对 API 改动做合规检查
- CI 流水线中的 review 阶段
- PR 合并前的最终审查

---

## 3. 禁用场景

以下情况不应使用本 Skill：

- 代码尚未实现（应先调用 `api-dev-impl`）
- 仅需运行测试（应使用 `ai-ad-agents-test-orchestrator`）
- 仅需生成文档（应使用 `ai-ad-doc-orchestrator`）
- 非 API 改动（纯前端、配置文件、文档）

---

## 4. SoT 文档依赖

本 Skill 审查时必须参照以下 SoT 文档：

| 文档 | 版本 | 路径 | 审查用途 |
|------|------|------|----------|
| `API_DEVELOPMENT_FLOW.md` | v2.3 | `docs/3.dev-guides/` | 6 步流程检查、不变量定义 |
| `AI_CODE_DEV_ORCHESTRATION_SOT` | v1.0 | `docs/2.sot/` | 审查角色定义、输出规范 |
| `API_SOT.md` | v9.0 | `docs/2.sot/` | API 端点规范、路径命名 |
| `AUTH_SPEC.md` | v2.0 | `docs/2.sot/` | 角色权限、认证规范 |
| `ERROR_CODES_SOT.md` | v2.1 | `docs/2.sot/` | 错误码定义、使用规范 |
| `STATE_MACHINE.md` | v2.6 | `docs/2.sot/` | 8 状态机、流转白名单 |
| `BUSINESS_RULES.md` | v3.1 | `docs/2.sot/` | 业务规则编号、约束 |

---

## 5. 输入结构

### 5.1 完整输入 JSON

```json
{
  "module": "finance_profit",
  "change_type": "api",
  "description": "本次改动说明",
  "plan": {
    "files_to_touch": [...],
    "dev_steps": [...],
    "review_checklist": [...]
  },
  "files_changed": [
    {
      "path": "backend/services/finance_profit_service.py",
      "action": "modified",
      "diff_summary": "新增 calculate_profit 方法"
    }
  ],
  "pytest_summary": {
    "executed": true,
    "passed": 10,
    "failed": 1,
    "errors": 0,
    "skipped": 0,
    "failure_details": [
      {
        "test": "test_profit_calculation_negative",
        "error": "AssertionError: expected 100, got 99"
      }
    ]
  },
  "openspec_context": {
    "has_proposal": false,
    "proposal_id": null
  }
}
```

### 5.2 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `module` | ✅ | 目标模块名称 |
| `change_type` | ✅ | 改动类型（`api`, `api_test`, `bugfix`, `refactor`） |
| `description` | ✅ | 本次改动的目标描述 |
| `plan` | ⬚ | 来自 planner 的开发计划（可选，用于对照检查） |
| `files_changed` | ✅ | 实际改动的文件列表 |
| `pytest_summary` | ⬚ | 测试执行结果（强烈建议提供，见 §5.3） |
| `openspec_context` | ⬚ | OpenSpec 提案状态（可选，用于判断是否走了 OpenSpec） |

### 5.3 pytest_summary 与审查状态的强关联（MUST）

**规则 R-TEST-001**：`pytest_summary` 直接影响审查结论。

| pytest_summary 状态 | 审查行为 | 说明 |
|---------------------|----------|------|
| `executed=false` 或缺失 | **MUST** 产生至少 1 个 P1 问题 | 问题：`未执行自动化测试` |
| `failed > 0` 或 `errors > 0` | **MUST** 产生至少 1 个 P1 问题 | 问题：`测试失败/错误` |
| `failed=0` 且 `errors=0` 且 `executed=true` | 允许无测试相关问题 | 测试通过 |

**约束**：
- 若 `pytest_summary.executed == false`：`status` **MUST NOT** 为 `"pass"`
- 若 `pytest_summary.failed > 0` 或 `pytest_summary.errors > 0`：`recommend_deploy` **MUST** 为 `false`

### 5.4 change_type 驱动的检查重点

不同 `change_type` 有不同的审查严格程度：

| change_type | SoT 约束级别 | 审查重点 |
|-------------|--------------|----------|
| `api` | ✅ **强制约束** | 必须检查 schema + service + router + test + doc 全链路 |
| `api_test` | ✅ **强制约束** | 允许业务代码变化很小，但测试覆盖与断言必须达到 SoT 要求 |
| `bugfix` | ⚠️ 实验性 | 重点检查 INV-001/002/003，其他项 best-effort |
| `refactor` | ⚠️ 实验性 | 重点检查行为等价性，其他项 best-effort |

**约束**：
- 对于 `api` 和 `api_test`，审查结论具有 SoT 违规判定效力
- 对于其他 `change_type`，审查结论为建议性质，不构成 SoT 违规依据

---

## 6. 输出结构

### 6.1 输出 JSON 格式

```json
{
  "module": "finance_profit",
  "status": "fail",
  "p0_issues": [
    {
      "id": "P0-001",
      "category": "invariant_violation",
      "rule": "INV-001",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.4.1",
      "file": "backend/services/finance_profit_service.py",
      "line": 45,
      "message": "直接修改 ledger_entries 表的 amount 字段，违反账务只追加原则",
      "fix_suggestion": "删除 UPDATE 语句，改用 INSERT 新增冲正分录"
    }
  ],
  "p1_issues": [
    {
      "id": "P1-001",
      "category": "error_code_mismatch",
      "rule": "ERROR_CODES_SOT §3",
      "sot_ref": "ERROR_CODES_SOT.md v2.1",
      "file": "backend/routers/finance_profit.py",
      "line": 78,
      "message": "使用未定义的错误码 BIZ-999",
      "fix_suggestion": "查阅 ERROR_CODES_SOT.md v2.1，使用已定义的错误码"
    }
  ],
  "p2_issues": [
    {
      "id": "P2-001",
      "category": "style_suggestion",
      "message": "建议为 calculate_profit 方法添加类型注解"
    }
  ],
  "review_summary": "发现 1 个 P0 阻塞问题（INV-001 违规），1 个 P1 问题。修复 P0 后方可上线。",
  "recommend_deploy": false,
  "requires_openspec": false
}
```

### 6.2 status / recommend_deploy 与 P0/P1 的强绑定规则（MUST）

以下是 **硬性规则**，任何审查输出 **MUST** 遵守：

| 条件 | status | recommend_deploy |
|------|--------|------------------|
| `p0_issues` 非空 | **MUST** 为 `"fail"` | **MUST** 为 `false` |
| `p0_issues` 空 且 `p1_issues` 非空 | **MUST** 为 `"warning"` 或更严重 | **MUST** 为 `false`（默认） |
| `p0_issues` 空 且 `p1_issues` 空 | 可以为 `"pass"` | 可以为 `true` |

**决策逻辑伪代码**：

```python
def determine_status_and_deploy(p0_issues, p1_issues, pytest_summary):
    # 规则 1: P0 非空 → fail + 不可上线
    if len(p0_issues) > 0:
        return status="fail", recommend_deploy=False

    # 规则 2: P1 非空 → warning + 不可上线（默认）
    if len(p1_issues) > 0:
        return status="warning", recommend_deploy=False

    # 规则 3: 测试未执行或失败 → 不可 pass
    if not pytest_summary.executed or pytest_summary.failed > 0:
        return status="warning", recommend_deploy=False

    # 规则 4: 全部通过
    return status="pass", recommend_deploy=True
```

### 6.3 requires_openspec 与其他字段的组合语义

| requires_openspec | status | recommend_deploy | 语义 |
|-------------------|--------|------------------|------|
| `false` | `pass` | `true` | ✅ 可直接上线 |
| `false` | `warning` | `false` | ⚠️ 有 P1 问题，修复后可上线 |
| `false` | `fail` | `false` | ❌ 有 P0 问题，必须修复 |
| `true` | `pass` | `false` | ⚠️ 代码无问题，但需先走 OpenSpec |
| `true` | `warning`/`fail` | `false` | ❌ 代码有问题 + 需走 OpenSpec |

**约束**：
- 若 `requires_openspec=true` 且未检测到 OpenSpec proposal，`recommend_deploy` **MUST** 为 `false`
- 即使代码本身无 P0/P1 问题，缺少 OpenSpec 也阻止上线

### 6.4 issue 结构规范

每个 issue **SHOULD** 包含以下字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 问题编号（如 P0-001, P1-002） |
| `category` | ✅ | 问题分类（见 §7） |
| `rule` | ✅ (P0/P1) | 违反的规则编号（如 INV-001, ERROR_CODES_SOT） |
| `sot_ref` | ⬚ | SoT 文档引用（如 `API_DEVELOPMENT_FLOW.md v2.3 §3.4.1`） |
| `file` | ⬚ | 问题所在文件路径 |
| `line` | ⬚ | 问题所在行号 |
| `message` | ✅ | 问题描述 |
| `fix_suggestion` | ✅ (P0) | 修复建议（P0 问题必须提供） |

---

## 7. 问题分级定义

### 7.1 P0 阻塞问题（必须修复）

以下情况 **MUST** 判定为 P0：

| 类别 | 说明 | 示例 | 规则依据 |
|------|------|------|----------|
| `invariant_violation` | 违反不变量 INV-001/002/003 | 直接 UPDATE ledger、终态记录被删除 | API_DEV_FLOW §3.4.1 |
| `security_breach` | 安全漏洞 | SQL 注入、未校验权限 | AUTH_SPEC §4 |
| `state_machine_violation` | 违反 8 状态机 | 非法状态跳转、终态回退 | STATE_MACHINE §8 |
| `data_integrity` | 数据完整性破坏 | 外键约束缺失、必填字段为空 | DATA_SCHEMA §5 |
| `envelope_missing` | 完全不使用 Envelope 响应格式 | 直接返回裸 dict/string | API_SOT §4.3 |
| `exception_raw` | 抛出裸 Exception 未使用 custom_exceptions | 无法映射到正确错误码 | API_DEV_FLOW §4.1 |
| `response_structure_mismatch` | 响应结构与 API_SOT 定义严重冲突 | 缺少必填字段、类型错误 | API_SOT §4 |

### 7.2 P1 高危问题（强烈建议修复）

以下情况 **SHOULD** 判定为 P1：

| 类别 | 说明 | 示例 | 规则依据 |
|------|------|------|----------|
| `error_code_mismatch` | 错误码不符合规范 | 使用未定义错误码、发明短码 | ERROR_CODES_SOT §3 |
| `error_code_semantic_mismatch` | 错误码与业务含义不匹配 | 权限错误使用 VALIDATION_001 | ERROR_CODES_SOT §3 |
| `envelope_partial` | Envelope 不完整 | 缺少 request_id 或 timestamp | API_SOT §4.3 |
| `permission_bypass` | 权限检查不完整 | 缺少角色校验 | AUTH_SPEC §3 |
| `sot_drift` | 与 SoT 定义不一致 | 字段类型、命名、约束不符 | DATA_SCHEMA |
| `openspec_required` | 应走 OpenSpec 但未走 | 新增端点、修改数据结构 | API_DEV_FLOW §3.8 |
| `test_not_executed` | 未执行自动化测试 | pytest_summary.executed=false | ORCH_SOT §7.4 |
| `test_failure` | 测试失败（非核心逻辑） | 边界用例失败 | API_DEV_FLOW §3.6 |
| `plan_file_mismatch` | 计划与实际改动不一致 | 见 §8.7 | ORCH_SOT §4.2 |

### 7.3 P2 优化建议（可选修复）

| 类别 | 说明 | 示例 |
|------|------|------|
| `style_suggestion` | 代码风格建议 | 类型注解、命名规范 |
| `doc_missing` | 文档缺失 | docstring 不完整 |
| `test_coverage` | 测试覆盖建议 | 边界用例未覆盖 |
| `performance_hint` | 性能优化提示 | N+1 查询、大循环 |

---

## 8. 审查清单

本 Skill 执行时 **MUST** 逐项检查以下内容：

### 8.1 6 步流程检查

| 检查项 | 说明 | 问题级别 |
|--------|------|----------|
| C1: SoT 一致性 | 代码是否与 SoT 文档定义一致 | P0/P1 |
| C2: Schema 定义 | Pydantic schema 是否符合 DATA_SCHEMA | P1 |
| C3: Service 逻辑 | 业务逻辑是否符合 BUSINESS_RULES | P0/P1 |
| C4: Router 规范 | 路径、方法、权限是否符合 API_SOT + AUTH | P1 |
| C5: 测试覆盖 | 单元测试是否覆盖核心逻辑 | P1/P2 |
| C6: 文档完整 | 是否更新了必要文档 | P2 |

### 8.2 不变量检查（INV-001/002/003）

| 不变量 | 检查内容 | 问题级别 | SoT 依据 |
|--------|----------|----------|----------|
| INV-001 | 账务只追加：禁止 UPDATE/DELETE ledger_entries | P0 | API_DEV_FLOW §3.4.1 |
| INV-002 | 终态不可逆：final_locked 记录禁止任何修改 | P0 | API_DEV_FLOW §3.4.1 |
| INV-003 | 状态单向流转：禁止违反 STATE_MACHINE 白名单 | P0 | STATE_MACHINE §8 |

### 8.3 异常与错误码检查

| 检查项 | 说明 | P0 条件 | P1 条件 |
|--------|------|---------|---------|
| E1 | 错误码是否定义于 ERROR_CODES_SOT.md | - | 使用未定义错误码 |
| E2 | 是否使用 custom_exceptions 体系 | 抛裸 Exception | 异常类型不匹配 |
| E3 | 是否使用统一 Envelope 格式 | 完全不使用 | 格式不完整 |
| E4 | 错误码与业务含义是否匹配 | - | 语义不匹配 |
| E5 | HTTP 状态码是否符合 API_SOT | - | 状态码错误 |

### 8.4 权限与安全检查

| 检查项 | 说明 | 问题级别 |
|--------|------|----------|
| S1 | 是否有 `Depends(get_current_user)` | P0/P1 |
| S2 | 角色权限是否符合 AUTH_SPEC | P1 |
| S3 | 输入是否有 SQL 注入风险 | P0 |
| S4 | 敏感数据是否脱敏 | P1 |

### 8.5 测试检查

| 检查项 | 说明 | 问题级别 | 触发条件 |
|--------|------|----------|----------|
| T1 | 是否执行了测试 | P1 | `pytest_summary.executed=false` |
| T2 | 核心测试是否通过 | P0/P1 | `failed > 0` 且涉及核心逻辑 |
| T3 | 测试覆盖率是否足够 | P2 | 低于阈值 |
| T4 | 断言是否有效（非空断言） | P1 | 发现空断言 |

### 8.6 OpenSpec 检查

**触发规则**（API_DEVELOPMENT_FLOW §3.8）：

| 场景 | 是否需要 OpenSpec | 检测方法 |
|------|-------------------|----------|
| 新增 API 端点 | ✅ 必须 | files_changed 包含新 router 文件 |
| 修改数据表结构 | ✅ 必须 | files_changed 包含 models/ 或 migrations/ |
| 新增状态枚举值 | ✅ 必须 | 代码中出现新状态值 |
| 修改业务规则 | ✅ 必须 | 业务逻辑变更且影响外部行为 |
| Bug 修复 | ❌ 不需要 | change_type="bugfix" |
| 测试补充 | ❌ 不需要 | change_type="api_test" 且无业务代码变更 |
| 代码重构（无行为变更） | ❌ 不需要 | change_type="refactor" |

**检测逻辑**：

```python
def check_openspec_required(change_type, files_changed, description):
    # 免除场景
    if change_type in ["bugfix", "refactor"]:
        return False
    if change_type == "api_test" and not has_business_code_change(files_changed):
        return False

    # 触发场景
    triggers = [
        any(f.path.startswith("backend/routers/") and f.action == "created" for f in files_changed),
        any(f.path.startswith("backend/models/") for f in files_changed),
        any(f.path.contains("migrations/") for f in files_changed),
        "新增" in description and ("端点" in description or "API" in description),
    ]
    return any(triggers)
```

**审查行为**：

- 若 `check_openspec_required() == True` 且 `openspec_context.has_proposal == False`：
  - `requires_openspec` **MUST** 为 `true`
  - **MUST** 产生至少 1 个 P1 问题（category: `openspec_required`）
  - `recommend_deploy` **MUST** 为 `false`
  - `status` **MUST** 至少为 `"warning"`

### 8.7 计划与实际改动一致性检查

当 `plan` 字段存在时，**MUST** 检查计划与实际改动的一致性：

| 检查项 | 说明 | 问题级别 |
|--------|------|----------|
| PF1 | plan.files_to_touch 中的核心文件是否都出现在 files_changed 中 | P1（遗漏关键文件） |
| PF2 | files_changed 中是否出现不在 plan.files_to_touch 内的"额外关键文件" | P1（计划外改动） |

**核心文件定义**：
- `backend/schemas/*.py`
- `backend/services/*.py`
- `backend/routers/*.py`
- `tests/api/*.py` 或 `tests/test_*.py`

**检测逻辑**：

```python
def check_plan_file_consistency(plan, files_changed):
    issues = []

    if plan is None:
        return issues  # 无计划则跳过此检查

    planned = set(plan.files_to_touch)
    actual = set(f.path for f in files_changed)
    core_patterns = ["backend/schemas/", "backend/services/", "backend/routers/", "tests/"]

    # 检查遗漏
    for p in planned:
        if any(pat in p for pat in core_patterns) and p not in actual:
            issues.append({
                "category": "plan_file_mismatch",
                "message": f"计划中的核心文件 {p} 未在实际改动中出现"
            })

    # 检查计划外改动
    for a in actual:
        if any(pat in a for pat in core_patterns) and a not in planned:
            issues.append({
                "category": "plan_file_mismatch",
                "message": f"实际改动包含计划外的核心文件 {a}"
            })

    return issues
```

---

## 9. 主提示词

当调用本 Skill 时，使用以下提示词：

```markdown
## Task

你是 API 开发合规审查员，负责对 API 改动进行 SoT 合规检查。

## Context

- 审查依据：API_DEVELOPMENT_FLOW v2.3 + AI_CODE_DEV_ORCHESTRATION_SOT v1.0
- SoT 裁判链：STATE_MACHINE → DATA_SCHEMA → BUSINESS_RULES → API_SOT → ERROR_CODES_SOT → AUTH_SPEC
- 问题分级：P0（阻塞上线）→ P1（强烈建议修复）→ P2（可选优化）

## Input

{input_json}

## Constraints（硬性规则）

1. **只做审查，不修改代码**

2. **status / recommend_deploy 强绑定**：
   - 若 `p0_issues` 非空：`status` MUST 为 `"fail"`，`recommend_deploy` MUST 为 `false`
   - 若 `p0_issues` 空但 `p1_issues` 非空：`status` MUST 为 `"warning"` 或更严重，`recommend_deploy` MUST 为 `false`
   - 仅当 `p0_issues` 和 `p1_issues` 都为空时，`status` 才能为 `"pass"`，`recommend_deploy` 才能为 `true`

3. **pytest_summary 关联规则**：
   - 若 `pytest_summary.executed == false` 或缺失：MUST 产生至少 1 个 P1 问题，`status` MUST NOT 为 `"pass"`
   - 若 `pytest_summary.failed > 0` 或 `errors > 0`：MUST 产生至少 1 个 P1 问题，`recommend_deploy` MUST 为 `false`

4. **OpenSpec 检测规则**：
   - 若改动属于"应触发 OpenSpec 的变更类型"（新增端点、改表结构、新状态）且未检测到 OpenSpec proposal：
     - `requires_openspec` MUST 为 `true`
     - MUST 产生至少 1 个 P1 问题（category: `openspec_required`）
     - `recommend_deploy` MUST 为 `false`

5. **plan vs files_changed 一致性**：
   - 若 plan 存在，MUST 检查计划与实际改动的一致性
   - 核心文件遗漏或计划外改动 MUST 产生 P1 问题

6. **P0 问题必须提供具体的修复建议**

7. **所有 P0/P1 判定必须引用具体 SoT 文档和规则编号**

8. **change_type 约束**：
   - `api` 和 `api_test`：审查结论具有 SoT 违规判定效力
   - 其他类型：审查结论为建议性质

## Thinking

1. 解析输入，确认 module、change_type、files_changed
2. 读取相关 SoT 文档
3. 根据 change_type 确定检查重点
4. 逐项执行审查清单（8.1 ~ 8.7）
5. 对每个发现的问题进行分级（P0/P1/P2）
6. 应用强绑定规则，确定 status 和 recommend_deploy
7. 汇总结论

## Steps

### Step 1: 解析输入
- 确认模块名称和改动类型
- 列出所有改动文件
- 确认是否有测试结果和 plan

### Step 2: 读取 SoT 文档
- 使用 `Read` 工具读取相关 SoT 文档
- 提取本次改动涉及的规则定义

### Step 3: 执行审查清单
- 逐项检查 C1~C6（6 步流程）
- 逐项检查 INV-001/002/003（不变量）
- 逐项检查 E1~E5（错误码与异常）
- 逐项检查 S1~S4（安全）
- 逐项检查 T1~T4（测试）
- 检查 OpenSpec 触发条件
- 检查 plan vs files_changed 一致性（若 plan 存在）

### Step 4: 问题分级
- 将所有发现的问题分为 P0/P1/P2
- 为 P0 问题生成 fix_suggestion
- 为每个 P0/P1 问题标注 sot_ref

### Step 5: 应用强绑定规则
- 根据 p0_issues 和 p1_issues 确定 status
- 根据 status 和 pytest_summary 确定 recommend_deploy
- 确定 requires_openspec

### Step 6: 生成审查报告
- 输出 JSON 格式的审查结果
- 确保 status/recommend_deploy/requires_openspec 符合约束

## Output Format

严格输出以下 JSON 结构：

```json
{
  "module": "{{module}}",
  "status": "pass" | "warning" | "fail",
  "p0_issues": [
    {
      "id": "P0-XXX",
      "category": "分类",
      "rule": "规则编号",
      "sot_ref": "SoT文档 版本 §章节",
      "file": "文件路径",
      "line": 行号,
      "message": "问题描述",
      "fix_suggestion": "修复建议"
    }
  ],
  "p1_issues": [...],
  "p2_issues": [...],
  "review_summary": "总体结论（中文）",
  "recommend_deploy": true | false,
  "requires_openspec": true | false
}
```
```

---

## 10. 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `ai-ad-api-dev-planner` | planner 输出的 review_checklist 和 files_to_touch 可作为本 Skill 的对照参考 |
| `ai-ad-api-dev-impl` | impl 完成后调用本 Skill 做审查 |
| `ai-ad-api-dev-orchestrator` | orchestrator 在 Step 4 调用本 Skill |
| `ai-ad-agents-test-orchestrator` | 测试结果可作为本 Skill 的 pytest_summary 输入 |

---

## 11. 错误处理

### 11.1 输入不完整

如果缺少必填字段，返回：

```json
{
  "status": "error",
  "error_code": "REVIEWER_INPUT_INCOMPLETE",
  "missing_fields": ["files_changed"],
  "message": "审查输入不完整，请补充 files_changed 字段"
}
```

### 11.2 无法读取 SoT

如果无法读取 SoT 文档，返回：

```json
{
  "status": "error",
  "error_code": "SOT_READ_FAILED",
  "sot_file": "API_SOT.md",
  "message": "无法读取 SoT 文档，请检查文件路径"
}
```

### 11.3 改动范围无法审查

如果改动超出 API 开发范围（如前端、基础设施），返回：

```json
{
  "status": "skipped",
  "reason": "本次改动不属于 API 开发范围，跳过审查",
  "recommend_deploy": null
}
```

---

## 12. 示例

### 12.1 审查通过示例

**输入**:
```json
{
  "module": "finance_profit",
  "change_type": "api",
  "description": "新增利润查询 API",
  "files_changed": [
    {"path": "backend/schemas/finance_profit.py", "action": "created"},
    {"path": "backend/services/finance_profit_service.py", "action": "created"},
    {"path": "backend/routers/finance_profit.py", "action": "created"},
    {"path": "tests/api/test_finance_profit.py", "action": "created"}
  ],
  "pytest_summary": {
    "executed": true,
    "passed": 12,
    "failed": 0,
    "errors": 0
  },
  "openspec_context": {
    "has_proposal": true,
    "proposal_id": "add-finance-profit-api"
  }
}
```

**输出**:
```json
{
  "module": "finance_profit",
  "status": "pass",
  "p0_issues": [],
  "p1_issues": [],
  "p2_issues": [
    {
      "id": "P2-001",
      "category": "doc_missing",
      "message": "建议为 ProfitQueryRequest 添加字段注释"
    }
  ],
  "review_summary": "审查通过，无阻塞问题。建议补充 schema 字段注释。",
  "recommend_deploy": true,
  "requires_openspec": false
}
```

### 12.2 审查失败示例（P0 + 测试失败）

**输入**:
```json
{
  "module": "ledger",
  "change_type": "bugfix",
  "description": "修复账本金额错误",
  "files_changed": [
    {"path": "backend/services/ledger_service.py", "action": "modified"}
  ],
  "pytest_summary": {
    "executed": true,
    "passed": 8,
    "failed": 2,
    "errors": 0
  }
}
```

**输出**:
```json
{
  "module": "ledger",
  "status": "fail",
  "p0_issues": [
    {
      "id": "P0-001",
      "category": "invariant_violation",
      "rule": "INV-001",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.4.1",
      "file": "backend/services/ledger_service.py",
      "line": 123,
      "message": "检测到 UPDATE ledger_entries SET amount = ... 语句，违反账务只追加原则",
      "fix_suggestion": "删除 UPDATE 语句，改用 INSERT 新增冲正分录（REVERT 类型）"
    }
  ],
  "p1_issues": [
    {
      "id": "P1-001",
      "category": "test_failure",
      "rule": "T2",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.6",
      "message": "2 个测试用例失败：test_ledger_balance_calculation, test_ledger_rollback",
      "fix_suggestion": "修复失败的测试用例后重新提交"
    }
  ],
  "p2_issues": [],
  "review_summary": "发现 1 个 P0 阻塞问题（INV-001 违规）和 1 个 P1 问题（测试失败）。必须修复后才能上线。",
  "recommend_deploy": false,
  "requires_openspec": false
}
```

### 12.3 需要 OpenSpec 示例

**输入**:
```json
{
  "module": "transfer",
  "change_type": "api",
  "description": "新增转账 API",
  "files_changed": [
    {"path": "backend/routers/transfer.py", "action": "created"},
    {"path": "backend/services/transfer_service.py", "action": "created"}
  ],
  "pytest_summary": {
    "executed": true,
    "passed": 5,
    "failed": 0
  },
  "openspec_context": {
    "has_proposal": false
  }
}
```

**输出**:
```json
{
  "module": "transfer",
  "status": "warning",
  "p0_issues": [],
  "p1_issues": [
    {
      "id": "P1-001",
      "category": "openspec_required",
      "rule": "OPENSPEC",
      "sot_ref": "API_DEVELOPMENT_FLOW.md v2.3 §3.8.1",
      "message": "新增 API 端点（transfer.py）必须先创建 OpenSpec proposal",
      "fix_suggestion": "执行 /openspec:proposal 创建变更提案，获得审批后再提交代码"
    }
  ],
  "p2_issues": [],
  "review_summary": "代码本身无 P0 问题，但新增 API 端点必须先走 OpenSpec 流程。请先创建 proposal。",
  "recommend_deploy": false,
  "requires_openspec": true
}
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.1 | 2025-12-06 | 补丁升级：(1) status/recommend_deploy 与 P0/P1 强绑定规则；(2) pytest_summary 与 status 关联规则；(3) OpenSpec 触发逻辑与 requires_openspec 判定；(4) plan vs files_changed 一致性检查项；(5) change_type 驱动的检查重点说明；(6) 错误码/Envelope/异常体系细化到 P0/P1 分级；(7) 输出字段组合语义表；(8) issue 结构增加 sot_ref 字段 |
| v1.0 | 2025-12-06 | 初始版本，基于 API_DEVELOPMENT_FLOW v2.3 设计 |
