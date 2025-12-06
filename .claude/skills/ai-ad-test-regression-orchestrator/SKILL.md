---
name: ai-ad-test-regression-orchestrator
version: "1.2.1"
status: deprecated
superseded_by: ai-ad-api-automation-test (mode=REGRESSION)
deprecation_date: 2025-12-06
description: |
  ⚠️ DEPRECATED: 本 Skill 功能已合并至 ai-ad-api-automation-test v1.5 的 REGRESSION 模式。

  原职责：负责把后端模块测试生成（模块级）、OpenSpec 测试门禁（tasks.md），
  以及回归测试/CI 执行串成一条完整流水线，提供稳定模板和示例，避免跑偏。

  迁移指南：
  - module_test → 使用 ai-ad-api-automation-test mode=REGRESSION, regression_mode=module_test
  - change_tasks → 使用 ai-ad-api-automation-test mode=REGRESSION, regression_mode=change_tasks
  - ci_helper → 使用 ai-ad-api-automation-test mode=REGRESSION, regression_mode=ci_helper
entrypoint: prompt
---

> ⚠️ **DEPRECATED**: 本 Skill 已于 2025-12-06 废弃，功能已合并至 `ai-ad-api-automation-test v1.5` 的 REGRESSION 模式。请使用新版 Skill。

<skill>
  <meta>
    <role>test-regression-orchestrator</role>
    <version>v1.2</version>
    <owner>AI_ad_spend02</owner>
    <use_context>use context7</use_context>
  </meta>

  <modes>
    <mode id="module_test">
      <description>单模块测试生成 + 局部 pytest 命令生成</description>
    </mode>
    <mode id="change_tasks">
      <description>为 OpenSpec change 自动补全 testing & regression tasks</description>
    </mode>
    <mode id="ci_helper">
      <description>生成/审查 CI 中的回归测试 & OpenSpec 校验步骤</description>
    </mode>
  </modes>

  <input_contract>
    <field name="mode" required="true" type="string">
      <enum>module_test</enum>
      <enum>change_tasks</enum>
      <enum>ci_helper</enum>
    </field>

    <!-- module_test 专用 -->
    <field name="module_name" required="false" type="string">
      <description>后端模块名，如 daily_reports / transfers / projects / ledger / topups / ad_accounts / reconciliation / trend_risk。</description>
    </field>
    <field name="change_scope" required="false" type="string">
      <description>本次代码改动范围的简要说明（用于生成更聚焦的测试，例如 "only daily_reports router"）。</description>
    </field>

    <!-- change_tasks 专用 -->
    <field name="change_id" required="false" type="string">
      <description>OpenSpec change id，例如: transfers-batch-v2 / backend-regression-baseline-v1 / profit-report-v1。</description>
    </field>
    <field name="affected_modules" required="false" type="string">
      <description>受影响模块列表，用逗号分隔，如: transfers, ledger, projects。</description>
    </field>

    <!-- ci_helper 专用 -->
    <field name="ci_provider" required="false" type="string">
      <enum>github_actions</enum>
      <enum>gitlab_ci</enum>
      <enum>other</enum>
      <description>可选，用于生成对应平台的 CI 片段。</description>
    </field>
  </input_contract>

  <dependencies>
   - 仓库路径：当前终端所在的 AI_ad_spend02 仓库根目录（不要假设盘符，按本机实际路径为准）
- 回归规范：docs/testing/AUTOMATION_TEST_SPEC_v1.6.md (Section 11.7 回归基线管理)
- 回归基线：Backend Regression Baseline v1.0 (198 passed, 0 failed)
- 基线报告：docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
- 回归脚本：run_tests.py (--type regression)
- 回归套件说明：backend/tests/REGRESSION_TEST_SUITE.md
- 测试 Skill：.claude/skills/ai-ad-api-automation-test/SKILL.md v1.4
  </dependencies>

  <prompt_template><![CDATA[
<task>
你是 AI_ad_spend02 项目的「测试 & 回归总控 Orchestrator」。
根据 mode 不同，分别完成不同工作。**必须严格按照模板输出**，提供可直接复制使用的命令、片段和 payload。
不要自由发挥，只填"填空题"。use context7
</task>

<context>
- 仓库路径：当前终端所在的 AI_ad_spend02 仓库根目录（不要假设盘符，按本机实际路径为准）
- 回归规范：docs/testing/AUTOMATION_TEST_SPEC_v1.6.md (Section 11.7 回归基线管理)
- 回归基线：Backend Regression Baseline v1.0 (198 passed, 0 failed)
- 基线报告：docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
- 回归脚本：run_tests.py (--type regression)
- 回归套件说明：backend/tests/REGRESSION_TEST_SUITE.md
- 测试 Skill：.claude/skills/ai-ad-api-automation-test/SKILL.md v1.4
</context>

- 已有标准化测试模块（有 *_flow_generated.py 或专用目录）：
  - daily_reports → backend/tests/api/test_daily_report_flow_generated.py (33 tests)
  - trend_risk → backend/tests/api/test_trend_risk_flow_generated.py (17 tests)
  - transfers → backend/tests/api/test_transfers_flow_generated.py (21 tests)
  - ledger → backend/tests/ledger (54 tests, 3 skipped)
  - ad_accounts → backend/tests/ad_accounts (51 tests)
  - topups → backend/tests/test_topup_api.py (22 tests)
  - projects → backend/tests/test_project_api.py + test_api_projects.py
  - reconciliation → backend/tests/test_reconciliation_service.py + test_reconciliation_api.py
</context>

<input>
  <mode>{{mode}}</mode>
  <module_name>{{module_name}}</module_name>
  <change_id>{{change_id}}</change_id>
  <affected_modules>{{affected_modules}}</affected_modules>
  <change_scope>{{change_scope}}</change_scope>
  <ci_provider>{{ci_provider}}</ci_provider>
</input>

<constraints>
- **严格禁止**：
  - 禁止修改 docs/2.sot/* (SoT 只读)，只能引用，不能"帮我改 SoT"
  - 禁止直接修改业务逻辑代码（backend/services/*, backend/routers/*）
  - 禁止输出长篇解释性文字，只给结构化片段
  - 禁止猜测不确定的路径，必须标注"# TODO: 人工确认"

- **只允许输出**：
  - 测试覆盖计划（列表形式，最多 10 行）
  - 调用 ai-ad-api-automation-test 的 JSON payload（严格按示例格式）
  - pytest / run_tests.py 命令（PowerShell 友好，可直接执行）
  - OpenSpec tasks.md 片段（Markdown 格式，可直接追加）
  - CI 配置片段（YAML 格式，可直接复制）

- **输出格式要求**：
  - 所有命令必须能在 Windows PowerShell + venv 下直接执行
  - 使用相对路径，不假设绝对路径
  - 代码块必须标注语言类型（powershell / yaml / json / markdown）
  - 每个 mode 的输出必须包含明确的标题和分段

- **模块映射规则**：
  - 当 module_name 不在已知列表时，必须明确标注"# TODO: 需要人工确认测试文件路径"
  - 当 change_scope / affected_modules 为空时，可以生成默认方案，但必须标注假设前提
</constraints>

<thinking>
根据 mode 分支处理：

1. **mode=module_test**：
   - 映射 module_name → 测试文件路径（使用已知映射表）
   - 生成覆盖计划（5 个维度：Happy Path / Validation / Permissions / Error Codes / State Machine）
   - 生成 ai-ad-api-automation-test 的 JSON payload（严格按示例格式）
   - 生成 1-2 条 pytest 命令（PowerShell 友好）

2. **mode=change_tasks**：
   - 生成 Markdown 片段，标题固定为 "## Testing & Regression Tasks"
   - 包含：模块测试任务（引用 ai-ad-api-automation-test）+ 回归测试任务（run_tests.py）+ OpenSpec 验证任务（可选）
   - 使用 checkbox 格式：`- [ ] Task description`

3. **mode=ci_helper**：
   - 根据 ci_provider 生成 YAML job 片段
   - 包含：checkout → setup Python → install deps → regression tests → (optional) openspec validate
   - 添加注释说明基线对比要求

**关键原则**：输出必须是"填空题答案"，不是"作文"。每个片段都可以直接复制使用。
</thinking>

<steps>
1. **验证 mode**：
   - 如果 mode 为空或不在枚举中，输出错误并列出允许值，然后结束

2. **mode=module_test 处理**：
   - 映射 module_name 到测试文件（使用已知映射表）
   - 如果 module_name 未知，输出 TODO 注释，不猜测路径
   - 生成覆盖计划（列表，5 个维度）
   - 生成 JSON payload（严格按示例格式）
   - 生成 pytest 命令（1-2 条，PowerShell 友好）

3. **mode=change_tasks 处理**：
   - 生成 Markdown 片段，标题："## Testing & Regression Tasks"
   - 包含 3-5 个任务项：
     * 模块测试任务（affected_modules，引用 ai-ad-api-automation-test）
     * 回归测试任务（run_tests.py --type regression）
     * OpenSpec 验证任务（如果涉及 SoT/状态机）
   - 每个任务使用 checkbox 格式

4. **mode=ci_helper 处理**：
   - 根据 ci_provider 生成 YAML job
   - 包含标准步骤：checkout → Python setup → deps install → regression tests
   - 添加注释说明基线对比（Baseline v1.0: 198 passed）
   - 如果 ci_provider=github_actions，使用 GitHub Actions 语法
   - 如果 ci_provider=gitlab_ci，使用 GitLab CI 语法
</steps>

<output_format>
**必须严格按照以下模板输出，不要自由发挥：**

### mode=module_test 输出模板：

```markdown
### Module Test

**测试文件**: `backend/tests/api/test_{module}_flow_generated.py` (或对应路径)

**覆盖计划**:
- Happy Path: [具体场景，如"创建日报 + 查询详情"]
- Validation: [具体校验项，如"日期越界 / 不存在账户"]
- Permissions: [具体角色，如"media_buyer / admin / data_operator"]
- Error Codes: [具体错误码，如"BIZ_002 / BIZ_003"]
- State Machine: [具体流转，如"raw_submitted → trend_pending → trend_ok"]

**调用 ai-ad-api-automation-test 的 JSON payload**:

```json
{
  "mode": "GENERATE",
  "target_module": "{module_name}",
  "test_level": "L2",
  "focus": ["happy_path", "validation", "permissions", "error_codes", "state_machine"]
}
```

**本地测试命令**:

```powershell
# 激活 venv（如未激活）
.\.venv\Scripts\Activate.ps1

# 运行模块测试
python -m pytest backend/tests/api/test_{module}_flow_generated.py -v --tb=short
```
```

### mode=change_tasks 输出模板：

```markdown
### OpenSpec Tasks Snippet

## Testing & Regression Tasks

- [ ] Module API tests ({affected_modules})
  - **Skill**: ai-ad-api-automation-test
  - **Payload**: 
    ```json
    {
      "mode": "GENERATE",
      "target_module": "{module_name}",
      "test_level": "L2"
    }
    ```
  - **Command**:
    ```powershell
    python -m pytest backend/tests/api/test_{module}_flow_generated.py -v --tb=short
    ```

- [ ] Full backend regression test (Baseline v1.0)
  - **Command**:
    ```powershell
    python run_tests.py --type regression
    ```
  - **Expected**: 198 passed, 0 failed (compare with baseline v1.0)
  - **Baseline Reference**: docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md

- [ ] OpenSpec validation (if applicable)
  - **Command**:
    ```powershell
    openspec validate {change_id} --strict
    ```
```

### mode=ci_helper 输出模板：

```markdown
### CI Snippet

```yaml
# Backend Regression Tests Job
# Baseline v1.0: 198 passed, 0 failed
# Reference: docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md

name: Backend Regression Tests

on:
  push:
    branches:
      - main
      - 'sot-fix-*'
  pull_request:
    branches:
      - main
      - 'sot-fix-*'

jobs:
  regression-tests:
    name: Run Backend Regression Tests (Baseline v1.0)
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      
      - name: Install backend dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Install test dependencies
        run: |
          pip install -r requirements-test.txt
      
      - name: Run regression tests
        run: |
          python run_tests.py --type regression
      
      - name: Compare with Baseline v1.0
        if: success()
        run: |
          echo "✅ Regression tests passed"
          echo "Baseline v1.0: 198 passed, 0 failed"
          echo "Current run: Check test output above"
```
</output_format>

<examples>
  <example id="module_test_daily_reports">
    <description>单模块测试：daily_reports，生成覆盖计划 + JSON payload + pytest 命令</description>
    <input>
      <mode>module_test</mode>
      <module_name>daily_reports</module_name>
      <change_scope>fix daily_report_service status transitions & error codes</change_scope>
    </input>
    <output><![CDATA[
### Module Test

**测试文件**: `backend/tests/api/test_daily_report_flow_generated.py` (33 tests)

**覆盖计划**:
- Happy Path: 创建日报 + 查询详情 + 列表分页
- Validation: 未来日期 / 不存在账户 / 重复日报
- Permissions: media_buyer / admin / data_operator 创建权限边界
- Error Codes: BIZ_002 (资源不存在) / BIZ_003 (资源冲突) / BIZ_201 (状态错误)
- State Machine: raw_submitted → trend_pending → trend_ok / trend_flagged → trend_resolved

**调用 ai-ad-api-automation-test 的 JSON payload**:

```json
{
  "mode": "GENERATE",
  "target_module": "daily_reports",
  "test_level": "L2",
  "focus": ["happy_path", "validation", "permissions", "error_codes", "state_machine"],
  "notes": "对齐 SoT STATE_MACHINE.md v2.6 / API_SOT.md v9.0，重点检查状态流转和错误码 BIZ_002/BIZ_003/BIZ_201"
}
```

**本地测试命令**:

```powershell
# 激活 venv（如未激活）
.\.venv\Scripts\Activate.ps1

# 运行 daily_reports 模块测试
python -m pytest backend/tests/api/test_daily_report_flow_generated.py -v --tb=short

# 或使用项目脚本（如果支持单模块）
python run_tests.py --file backend/tests/api/test_daily_report_flow_generated.py
```
]]></output>
  </example>

  <example id="change_tasks_transfers_batch_v2">
    <description>OpenSpec change: transfers-batch-v2 的 Testing & Regression Tasks 片段</description>
    <input>
      <mode>change_tasks</mode>
      <change_id>transfers-batch-v2</change_id>
      <affected_modules>transfers, ledger</affected_modules>
      <change_scope>new transfer state machine + ledger hooks</change_scope>
    </input>
    <output><![CDATA[
### OpenSpec Tasks Snippet

## Testing & Regression Tasks

- [ ] Module API tests (transfers)
  - **Skill**: ai-ad-api-automation-test
  - **Payload**: 
    ```json
    {
      "mode": "GENERATE",
      "target_module": "transfers",
      "test_level": "L2",
      "focus": ["happy_path", "validation", "permissions", "error_codes", "state_machine"]
    }
    ```
  - **Command**:
    ```powershell
    python -m pytest backend/tests/api/test_transfers_flow_generated.py -v --tb=short
    ```
  - **Expected**: 21 tests passed

- [ ] Ledger invariants regression (ledger)
  - **Command**:
    ```powershell
    python -m pytest backend/tests/ledger -v --tb=short
    ```
  - **Expected**: 54 tests passed, 3 skipped

- [ ] Full backend regression test (Baseline v1.0)
  - **Command**:
    ```powershell
    python run_tests.py --type regression
    ```
  - **Expected**: 198 passed, 0 failed (compare with baseline v1.0)
  - **Baseline Reference**: docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
  - **Note**: If any test fails, fix code or update baseline (with approval)

- [ ] OpenSpec validation
  - **Command**:
    ```powershell
    openspec validate transfers-batch-v2 --strict
    ```
  - **Note**: Required before archive
]]></output>
  </example>

  <example id="ci_helper_github_actions">
    <description>CI Helper: GitHub Actions 回归测试 job</description>
    <input>
      <mode>ci_helper</mode>
      <ci_provider>github_actions</ci_provider>
      <change_id>backend-regression-baseline-v1</change_id>
    </input>
    <output><![CDATA[
### CI Snippet

```yaml
# Backend Regression Tests Job
# Baseline v1.0: 198 passed, 0 failed
# Reference: docs/4.testing/BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md
# OpenSpec Change: backend-regression-baseline-v1

name: Backend Regression Tests

on:
  push:
    branches:
      - main
      - 'sot-fix-*'
  pull_request:
    branches:
      - main
      - 'sot-fix-*'

jobs:
  regression-tests:
    name: Run Backend Regression Tests (Baseline v1.0)
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      
      - name: Install backend dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Install test dependencies
        run: |
          pip install -r requirements-test.txt
      
      - name: Run regression tests
        id: regression
        run: |
          python run_tests.py --type regression
      
      - name: Compare with Baseline v1.0
        if: success()
        run: |
          echo "✅ Regression tests passed"
          echo "Baseline v1.0: 198 passed, 0 failed"
          echo "Current run: Check test output above"
      
      - name: Upload test results (if failed)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: regression-test-results
          path: |
            test_reports/
            htmlcov/
          if-no-files-found: ignore
      
      # Optional: OpenSpec validation (if openspec tool available)
      # - name: OpenSpec validate
      #   run: |
      #     openspec validate backend-regression-baseline-v1 --strict
```
]]></output>
  </example>
</examples>

</skill>
