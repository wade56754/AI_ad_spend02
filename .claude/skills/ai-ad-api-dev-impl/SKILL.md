---
name: ai-ad-api-dev-impl
description: >
  API 实现工程师 Skill，在已明确 SoT 的前提下，根据需求说明和开发计划，
  对后端代码进行"最小必要修改"，完成 API 的实现和测试代码补全。
  本 Skill 只做两件事：生成/修改代码文件 + 验证改动是否符合预期。
---

# API Dev Impl Skill

## 1. Skill 概要

本 Skill 的唯一职责：

> 根据 SoT（API_DEVELOPMENT_FLOW v2.2 + API_SOT v9.0）+ 需求/计划，
> 生成/修改 schema、service、router、tests 等代码文件，
> 并在需要时调用 pytest 验证改动。

**本 Skill 通常由 `api-dev-orchestrator` 调用**，也可由用户直接调用。

---

## 2. 适用场景

当满足以下条件时使用本 Skill：

- 已有明确的 API 开发需求（new_endpoint / modify_endpoint / bugfix）
- 已确定目标模块（module）
- 需要实际生成或修改后端代码
- 可选：已有来自 `api-dev-planner` 的开发计划

---

## 3. 禁用场景

出现以下情况时，不要使用本 Skill：

- 仅需要生成开发计划（应使用 `api-dev-planner`）
- 仅需要 SoT 合规审查（应使用 `api-dev-reviewer`）
- 仅需要运行测试（应使用 `ap_run_pytest` 或 `ai-ad-agents-test-orchestrator`）
- 需求不明确，尚需探索和规划

---

## 4. SoT 文档依赖（只读，最高优先级）

| 文档 | 版本 | 用途 |
|------|------|------|
| `docs/3.dev-guides/API_DEVELOPMENT_FLOW.md` | v2.2 | API 开发 6 步流程、Envelope 规范 |
| `docs/2.sot/API_SOT.md` | v9.0 | API 端点契约、路径、响应码 |
| `docs/2.sot/ERROR_CODES_SOT.md` | v2.1 | 错误码定义 |
| `docs/2.sot/STATE_MACHINE.md` | v2.6 | 8 状态机定义 |
| `docs/2.sot/DATA_SCHEMA.md` | v5.2 | 数据模型字段定义 |

**原则**：任何"规范是什么"的问题，以 SoT 文档为唯一真相来源。

---

## 5. 项目结构

本 Skill 主要操作以下目录：

```
backend/
├── schemas/          # Pydantic Schema 定义
│   └── {module}.py
├── services/         # 业务逻辑层
│   └── {module}_service.py
├── routers/          # FastAPI Router 定义
│   └── {module}.py
├── exceptions/       # 异常类定义
│   └── custom_exceptions.py
├── core/             # 核心模块
│   └── error_codes.py
└── tests/
    └── api/          # API 集成测试
        └── test_{module}.py
```

---

## 6. 输入字段定义

```json
{
  "api_change_type": "new_endpoint" | "modify_endpoint" | "bugfix" | "refactor",
  "module": "finance_profit" | "daily_reports" | "topups" | "...",
  "description": "自然语言描述这次 API 改动的需求/问题",
  "plan": {
    "files_to_touch": ["backend/schemas/...", "backend/services/...", "..."],
    "dev_steps": [
      "Step 1: 更新 schema: ...",
      "Step 2: 修改 service: ...",
      "Step 3: 修改 router: ...",
      "Step 4: 补全 tests: ..."
    ],
    "review_checklist": [
      "使用 Envelope 成功/失败响应",
      "只使用 custom_exceptions 中的异常类型",
      "错误码来自 ERROR_CODES_SOT",
      "Router 使用 require_permission('resource:action')",
      "测试断言 Envelope（success + data/error）"
    ]
  },
  "auto_write": true | false,
  "run_tests": true | false,
  "pytest_path": "backend/tests/api"
}
```

**默认值**：
- `plan`: null（无计划时自行推导）
- `auto_write`: false（只给出建议，不写文件）
- `run_tests`: true
- `pytest_path`: "backend/tests/api"

---

## 7. 硬性约束（Constraints）

### 7.1 SoT 对齐

- API 行为必须符合 API_DEVELOPMENT_FLOW v2.2、API_SOT v9.0、ERROR_CODES_SOT v2.1
- 不得发明新的错误码、权限字符串、状态枚举
- 如确需新增，必须在输出中标记为"需要 SoT 更新"

### 7.2 响应格式（Envelope）

所有 HTTP API 返回必须使用统一 Envelope：

```python
{
    "success": bool,
    "data": object | null,      # 成功时填充
    "error": {                   # 失败时填充
        "code": str,
        "message": str,
        "details": object | null
    } | null,
    "request_id": str,
    "timestamp": str  # ISO8601
}
```

**规则**：
- 成功场景只写 `data`，失败只写 `error`，二者互斥
- 不允许在路由中手写裸 JSON
- 统一通过 `success_response()` / `error_response()` helper

### 7.3 异常与错误码

只使用 `backend.exceptions.custom_exceptions` 中的异常类型：

```python
from backend.exceptions import (
    ValidationError,
    BusinessLogicError,
    ResourceNotFoundError,
    PermissionDeniedError,
    AuthenticationError
)
```

**使用示例**：

```python
# 状态转换错误
raise BusinessLogicError(
    message=f"非法状态转换: {current} → {target}",
    error_code='BIZ_301',  # STATUS_TRANSITION_NOT_ALLOWED
    status_code=400,
    details={'current_status': current, 'target_status': target}
)

# 资源不存在
raise ResourceNotFoundError(
    message=f"报表 {report_id} 不存在",
    error_code='BIZ_404',
    status_code=404,
    details={'report_id': report_id}
)

# 权限不足
raise PermissionDeniedError(
    message="缺少 daily_report:submit 权限",
    error_code='AUTH_003',
    status_code=403,
    details={'required_permission': 'daily_report:submit'}
)
```

**禁止**：
- 直接抛 `ValueError` / `HTTPException` 作为业务错误
- 使用不在 ERROR_CODES_SOT 中的错误码

### 7.4 权限与鉴权

Router 层权限检查规范：

```python
# ✅ 正确
@router.post("/{report_id}/submit")
async def submit_report(
    report_id: int,
    current_user = Depends(require_permission('daily_report:submit'))
):
    ...

# ❌ 错误
@router.post("/{report_id}/submit")
async def submit_report(report_id: int, current_user = Depends(get_current_user)):
    if current_user.role != 'admin':  # 禁止直接判断角色
        raise PermissionDeniedError(...)
```

**权限字符串格式**：`{resource}:{action}`
- 示例：`daily_report:submit`, `finance_profit:view_summary`, `topup:approve`

### 7.5 测试要求

所有新增/修改的 API 必须有测试用例：

```python
# 测试断言必须通过 Envelope 访问
def test_submit_report_success(client, auth_headers):
    response = client.post("/api/v1/daily-reports/1/submit", ...)
    assert response.status_code == 200

    envelope = response.json()
    assert envelope["success"] is True
    assert envelope["data"]["status"] == "raw_submitted"
    assert envelope["error"] is None

def test_submit_locked_report_fails(client, auth_headers, locked_report):
    response = client.post(f"/api/v1/daily-reports/{locked_report.id}/submit", ...)
    assert response.status_code == 400

    envelope = response.json()
    assert envelope["success"] is False
    assert envelope["error"]["code"] == "BIZ_301"
```

**覆盖要求**：
- 至少 1 个 happy path
- 1~2 个错误路径（权限不足、状态非法、字段校验失败）

### 7.6 文件变更范围

- 优先在 `plan.files_to_touch` 范围内修改
- 若需新增文件/模块，必须说明理由并标注"超出原 plan"
- 不修改与本次 API 无关的模块

---

## 8. 执行流程

### Step 1: 解析输入

```python
# 解析输入 JSON，设置默认值
api_change_type = input.get("api_change_type")
module = input.get("module")
description = input.get("description")
plan = input.get("plan")  # 可能为 null
auto_write = input.get("auto_write", False)
run_tests = input.get("run_tests", True)
pytest_path = input.get("pytest_path", "backend/tests/api")
```

### Step 2: 对齐 SoT

使用 context7 或 ap_read_sot_file 读取：
1. `API_DEVELOPMENT_FLOW.md` - 定位对应流程章节
2. `API_SOT.md` - 找到 module + endpoint 相关契约
3. `ERROR_CODES_SOT.md` - 确认需要的错误码

### Step 3: 推导/修正开发计划

**如果有 plan**：
- 检查与 SoT 是否冲突
- 必要时修正步骤顺序

**如果无 plan**：
- 基于 SoT 推导最小必要 plan：
  1. Schema 定义/更新
  2. Service 业务逻辑
  3. Router 路由定义
  4. Tests 测试用例

### Step 4: 代码修改

对每个 `files_to_touch`：

```python
# 1. 读取现有实现
current_content = ap_read_file(file_path)

# 2. 分析应如何变化（对照 SoT + plan）

# 3. 生成最小差异修改
if auto_write:
    ap_write_file(file_path, new_content)
else:
    # 输出补丁/建议
```

### Step 5: 测试验证

```python
if run_tests:
    if ap_run_pytest 可用:
        result = ap_run_pytest(test_paths=[pytest_path])
        # 收集并总结结果
    else:
        # 生成推荐的 pytest 命令
        print(f"pytest {pytest_path} -v --tb=short")
```

### Step 6: 生成报告

输出结构化报告（见 Section 9）

---

## 9. 输出格式

使用 Markdown 输出以下结构：

```markdown
# API 实现报告

## 1. 开发上下文摘要

- **api_change_type**: new_endpoint / modify_endpoint / bugfix
- **module**: finance_profit
- **description**: ...
- **SoT 依赖**: API_DEVELOPMENT_FLOW v2.2, API_SOT v9.0, ERROR_CODES_SOT v2.1

## 2. 计划摘要

### files_to_touch
- backend/schemas/finance_profit.py
- backend/services/finance_profit_service.py
- backend/routers/finance_profit.py
- backend/tests/api/test_finance_profit.py

### dev_steps
1. 更新 schema: 添加 ProfitQueryRequest/Response
2. 修改 service: 实现 get_profit_summary() 方法
3. 修改 router: 添加 GET /api/v1/finance/profit/summary 端点
4. 补全 tests: 添加 happy path + 错误路径测试

## 3. 代码改动概览

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| backend/schemas/finance_profit.py | 新增 | 添加 Request/Response Schema |
| backend/services/finance_profit_service.py | 修改 | 添加 get_profit_summary 方法 |
| backend/routers/finance_profit.py | 修改 | 添加 /summary 端点 |
| backend/tests/api/test_finance_profit.py | 新增 | 添加 3 个测试用例 |

## 4. 关键代码片段

### Schema (backend/schemas/finance_profit.py)
```python
class ProfitQueryRequest(BaseModel):
    project_id: int = Field(..., description="项目 ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")

class ProfitSummaryResponse(BaseModel):
    total_revenue: float
    total_cost: float
    profit: float
    profit_rate: float
```

### Service (backend/services/finance_profit_service.py)
```python
def get_profit_summary(self, project_id: int, start_date: date, end_date: date):
    # 业务逻辑实现
    ...
```

### Router (backend/routers/finance_profit.py)
```python
@router.get("/summary", response_model=Envelope[ProfitSummaryResponse])
async def get_profit_summary(
    request: ProfitQueryRequest = Depends(),
    service: FinanceProfitService = Depends(get_service),
    current_user = Depends(require_permission('finance_profit:view_summary'))
):
    result = service.get_profit_summary(...)
    return success_response(data=result)
```

## 5. 测试与验证

### tests_added_or_updated
- `test_get_profit_summary_success`
- `test_get_profit_summary_no_permission`
- `test_get_profit_summary_invalid_date_range`

### pytest_summary
- **执行**: ✅ 已执行
- **通过**: 3
- **失败**: 0
- **跳过**: 0
- **耗时**: 1.2s

## 6. 风险与待决事项

| 优先级 | 事项 | 建议处理方式 |
|--------|------|--------------|
| P1 | 需新增权限 `finance_profit:view_summary` | 更新 AUTH_SPEC.md |
| P2 | 考虑添加分页支持 | 下一迭代处理 |

## 7. 下一步建议

1. 更新 AUTH_SPEC.md 登记新权限 `finance_profit:view_summary`
2. 运行完整回归测试 `pytest backend/tests/ -m "not slow"`
3. 更新 API_SOT.md 记录新端点
```

---

## 10. 安全约束

本 Skill 不得：

- 输出真实密钥、令牌或敏感配置
- 修改与本次 API 无关的模块
- 在 `auto_write=false` 时写入文件
- 发明不在 SoT 中的错误码、权限、状态

---

## 11. 错误处理

### 11.1 plan 与 SoT 冲突

- 在输出的"计划修正建议"中指出冲突
- 以 SoT 为准进行调整

### 11.2 缺少必要文件

- 标注"需要新建文件"
- 如超出 plan 范围，说明理由

### 11.3 测试失败

- 列出失败用例和错误信息
- 在"风险与待决事项"中标注
- 建议修复方案

---

## 12. 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `api-dev-orchestrator` | 调用本 Skill 执行实现 |
| `api-dev-planner` | 为本 Skill 提供开发计划 |
| `api-dev-reviewer` | 对本 Skill 的输出进行审查 |
| `ai-ad-agents-test-orchestrator` | 可替代本 Skill 的测试步骤 |

---

## 13. 示例：新增 finance_profit 利润查询 API

### 输入

```json
{
  "api_change_type": "new_endpoint",
  "module": "finance_profit",
  "description": "新增利润查询 API，支持按项目和时间范围查询利润汇总",
  "plan": {
    "files_to_touch": [
      "backend/schemas/finance_profit.py",
      "backend/services/finance_profit_service.py",
      "backend/routers/finance_profit.py",
      "backend/tests/api/test_finance_profit.py"
    ],
    "dev_steps": [
      "Step 1: 定义 ProfitQueryRequest 和 ProfitSummaryResponse",
      "Step 2: 实现 FinanceProfitService.get_profit_summary()",
      "Step 3: 添加 GET /api/v1/finance/profit/summary 端点",
      "Step 4: 添加测试用例"
    ],
    "review_checklist": [
      "使用 Envelope 响应",
      "使用 require_permission('finance_profit:view_summary')",
      "错误码来自 ERROR_CODES_SOT"
    ]
  },
  "auto_write": false,
  "run_tests": true
}
```

### 执行步骤

1. 读取 API_SOT.md 确认端点规范
2. 读取现有 finance_profit 相关文件
3. 生成 Schema 定义
4. 生成 Service 方法
5. 生成 Router 端点
6. 生成测试用例
7. 运行 pytest 验证
8. 输出结构化报告

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-12-05 | 初始版本，基于 API_DEVELOPMENT_FLOW v2.2 设计 |
