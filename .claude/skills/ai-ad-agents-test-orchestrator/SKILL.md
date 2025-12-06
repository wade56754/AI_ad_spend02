---
name: ai-ad-agents-test-orchestrator
version: "2.4"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-06
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - Dev-Guides Freeze vFinal
  - Architecture Freeze v1.0
  - Infrastructure Freeze v1.0
  - Agent Freeze v1.0
  - AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md  # Phase 2c: P1 fix - added missing baseline
absorbs:
  - ai-ad-agents-test-runner v2.2 (merged as internal_runner_module)
---

<skill>
──────────────────────────────────────────────
  <name>ai-ad-agents-test-orchestrator</name>
  <version>2.4</version>
  <status>active</status>
  <domain>AI_AD_SYSTEM / Agents 测试巡检工作流协调</domain>
  <profile>Test-Orchestrator / Quality-Gate / Auto-Regression / Internal-Runner</profile>
──────────────────────────────────────────────


  <!-- ======================================================
       0. 核心使命（Mission）
  ====================================================== -->
  <mission>
    Summary: Agents 测试巡检 Orchestrator，在 agents/ 代码或 skills/ 发生变更后，自动执行静态测试巡检作为上线质量闸门。

    职责：
    - 分析本次代码改动范围，映射到相关测试文件
    - **内部执行** 静态测试分析（原 ai-ad-agents-test-runner 功能已内嵌为 internal_runner_module）
    - 逐个执行测试（一次一条），监控 PASS/FAIL/UNCERTAIN 状态
    - 生成测试巡检报告，判定是否允许上线

    v2.3 变更：
    - 原 ai-ad-agents-test-runner v2.2 功能已完全内嵌
    - 不再调用外部 Skill，所有测试执行由内部 runner 模块完成
    - 对外行为保持不变（test_scope / changed_files / verdict 等）

    只读约束（Inviolable）：
    - 永远不实际运行 pytest 或任何系统命令
    - 不修改源代码或测试代码
    - 不虚构测试用例或测试结果
    - 只执行静态分析，不写入任何文件

    非目标（Non-Goals）：
    - 真实执行 pytest → 由 CI/CD 流程负责
    - 修复失败的测试 → 由开发者手动修复
    - 生成新测试用例 → 由开发者编写
    - 修改被测代码 → 由开发者根据报告修复
  </mission>


  <!-- ======================================================
       1. 何时使用（When to Use）
  ====================================================== -->
  <when_to_use>
    适用场景：

    1. Agents 代码变更后自动巡检
       - agents/agent_core/*.py 修改后
       - agents/skills/*.py 修改后
       - agents/tools/*.py 修改后
       - agents/agents_config.py 修改后

    2. 快速质量门检查
       - PR 合并前的静态测试巡检
       - 本地开发时的快速回归验证
       - 避免频繁运行完整 pytest 套件

    3. 自动化测试覆盖评估
       - 评估本次改动的测试覆盖情况
       - 识别缺少测试的组件
       - 生成测试覆盖缺口报告

    4. CI/CD 前置闸门
       - 在实际 CI 运行前提供快速反馈
       - 阻塞明显失败的提交
       - 减少 CI 资源浪费
  </when_to_use>


  <!-- ======================================================
       2. 何时不使用（When NOT to Use）
  ====================================================== -->
  <when_not_to_use>
    不适用场景：

    1. 需要真实执行 pytest
       → 使用 CI/CD pipeline 或手动执行 pytest

    2. 需要测试代码覆盖率统计
       → 使用 pytest-cov 插件

    3. 需要修复失败的测试
       → 手动修改源代码或测试代码

    4. 需要生成新测试用例
       → 手动编写测试代码

    5. 测试涉及复杂 fixture 或动态行为
       → 静态分析无法准确推理，需真实执行 pytest
  </when_not_to_use>


  <!-- ======================================================
       3. 输入契约（Input Contract）
  ====================================================== -->
  <input_contract>
    最小输入：
    {
      changed_files: [文件相对路径列表],
      test_scope: "auto" | "all" | "smoke"
    }

    changed_files 说明：
    - 本次改动的文件相对路径列表
    - 可由 git diff 或目录扫描推断
    - 用于映射到相关测试文件

    test_scope 说明：

    - auto（推荐默认）
      - 只跑与改动文件直接相关的测试
      - 根据 changed_files 自动映射测试文件
      - 若无法映射，降级为 smoke 模式

    - all
      - 跑所有 agents/tests/ 下的测试
      - 完整回归测试，耗时较长

    - smoke
      - 只跑 test_agents_smoke.py + 关键 agents_config 测试
      - 快速烟雾测试，最小集

    可选输入：
    - max_tests: number (默认 20) - 最大执行测试条数
    - stop_on_fail: boolean (默认 true) - 遇到 FAIL 是否立即停止

    校验规则（Fail Fast）：
    - 若 test_scope 缺失 → 默认使用 "auto"
    - 若 changed_files 缺失 → 默认使用 "all" 模式
    - 若 test_scope 为无效值 → 输出 <halt>Invalid: test_scope must be auto/all/smoke</halt>
  </input_contract>


  <!-- ======================================================
       4. 禁止行为（Forbidden Actions）
  ====================================================== -->
  <forbidden_actions>
    严格禁止以下行为：

    1. 系统命令执行
       - 禁止实际运行 pytest
       - 禁止执行 bash/shell 命令
       - 禁止运行测试脚本

    2. 文件修改
       - 禁止修改源代码
       - 禁止修改测试代码
       - 禁止写入任何文件

    3. 结果虚构
       - 禁止虚构测试用例
       - 禁止虚构测试结果
       - 禁止推测未执行测试的结果

    4. 自动修复
       - 禁止自动修复失败测试
       - 禁止生成修复补丁
       - 禁止修改被测代码

    5. 跨范围执行
       - 禁止执行 agents/tests/ 以外的测试
       - 禁止超出 test_scope 范围
       - 禁止动态扩展测试范围
  </forbidden_actions>


  <!-- ======================================================
       5. 工作流总览（Workflow Overview）
  ====================================================== -->
  <workflow_overview>
    对于任意测试巡检请求，执行五阶段流水线：

    [阶段 1：变更分析]
      ANALYZE-CHANGES
        → 分析本次改动范围
        → 映射到测试文件列表

    [阶段 2：测试发现]
      INIT-DISCOVERY
        → 调用 test-runner 的 DISCOVERY
        → 获取完整 PENDING_TESTS

    [阶段 3：测试筛选]
      SELECT-TESTS
        → 从 PENDING_TESTS 中筛选
        → 基于 test_scope 决定执行哪些测试

    [阶段 4：循环执行]
      RUN-LOOP
        → 使用 RUN-ONE 逐个执行
        → 任意 FAIL → 立即停止（若 stop_on_fail=true）
        → 执行到配额/列表末尾 → 输出总结

    [阶段 5：最终汇总]
      SUMMARY
        → 汇总 PASS/FAIL/UNCERTAIN
        → 判定是否允许上线
        → 输出放行结论
  </workflow_overview>


  <!-- ======================================================
       6. ANALYZE-CHANGES：变更分析
  ====================================================== -->
  <phase id="ANALYZE-CHANGES">
    <goal>
      根据 changed_files 决定应该跑哪些测试文件。
    </goal>

    <inputs>
      - changed_files: 本次改动的文件相对路径列表
      - test_scope: auto | all | smoke
    </inputs>

    <actions>
      1. 将 changed_files 中位于 agents/ 的文件映射到 agents/tests/ 下的对应测试：
         - agents/agents_config.py → agents/tests/test_agents_config.py
         - agents/agent_core/fe_agent.py → agents/tests/test_fe_agent.py
         - agents/agent_core/be_agent.py → agents/tests/test_be_agent.py
         - agents/agent_core/test_agent.py → agents/tests/test_test_agent.py
         - agents/agent_core/orchestrator_agent.py → agents/tests/test_orchestrator_agent.py
         - agents/tools/fs_tool.py → agents/tests/test_fs_tool.py
         - agents/tools/validation.py → agents/tests/test_validation.py
         - agents/skills/fe_dev_skill.py → agents/tests/test_fe_dev_skill.py
         - agents/skills/be_dev_skill.py → agents/tests/test_be_dev_skill.py
         - agents/skills/db_test_skill.py → agents/tests/test_db_test_skill.py

      2. 处理不同 test_scope：
         - smoke: 只选择 test_agents_smoke.py + 关键 agents_config 测试
         - all: 在后续 SELECT-TESTS 阶段直接使用所有 PENDING_TESTS
         - auto: 使用映射结果

      3. 若 auto 模式下 changed_files 无法映射到任何测试文件：
         - 降级为 smoke 模式
         - 在 SUMMARY 中说明这是降级行为
    </actions>

    <rules>
      - 只映射 agents/ 目录下的文件
      - 忽略非 Python 文件（*.md / *.json 等）
      - 若 changed_files 为空，默认使用 smoke 模式
    </rules>

    <output>
      - mapped_test_files: 映射到的测试文件列表
      - effective_scope: 实际生效的测试范围（可能降级）
    </output>
  </phase>


  <!-- ======================================================
       7. INIT-DISCOVERY：测试发现
  ====================================================== -->
  <phase id="INIT-DISCOVERY">
    <goal>
      获取当前 agents/tests/ 下所有可执行测试的完整列表。
    </goal>

    <inputs>
      - 无（直接调用 test-runner）
    </inputs>

    <actions>
      1. 调用 ai-ad-agents-test-runner：
         - mode = "DISCOVERY"

      2. 解析其输出中的：
         - 测试文件清单
         - PENDING_TESTS 列表
         - 总测试数

      3. 若 DISCOVERY 报告"目录不存在"或"无有效测试"：
         - 立即结束工作流
         - 输出错误报告
         - 判定为「不能放行上线」
    </actions>

    <rules>
      - 必须等待 DISCOVERY 完成才进入下一阶段
      - 不得跳过 DISCOVERY 直接执行测试
      - 若 DISCOVERY 失败，整个工作流终止
    </rules>

    <output>
      - all_pending_tests: 完整 PENDING_TESTS 列表
      - total_test_count: 总测试数
    </output>
  </phase>


  <!-- ======================================================
       8. SELECT-TESTS：测试筛选
  ====================================================== -->
  <phase id="SELECT-TESTS">
    <goal>
      在 PENDING_TESTS 里筛选出本轮要执行的 test_id 列表。
    </goal>

    <inputs>
      - all_pending_tests: 完整 PENDING_TESTS 列表
      - mapped_test_files: 映射到的测试文件列表
      - effective_scope: 实际生效的测试范围
    </inputs>

    <actions>
      1. 根据 effective_scope 筛选：
         - all: selected_tests = 所有 PENDING_TESTS
         - auto: selected_tests = PENDING_TESTS 中，文件名属于 mapped_test_files
         - smoke: selected_tests = PENDING_TESTS 中 test_agents_smoke.py + 关键 agents_config 测试

      2. 若 auto 模式下筛选结果为空：
         - 降级为 smoke
         - 添加烟雾测试 test_agents_smoke.py 下的全部用例

      3. 对 selected_tests 排序：
         - 先 agents_config 相关
         - 再 OrchestratorAgent 相关
         - 再 FE/BEAgent
         - 最后 skill/工具层测试
    </actions>

    <rules>
      - selected_tests 数量不超过 max_tests
      - 若超过，只取前 max_tests 个
      - 在 SUMMARY 中说明"只执行了部分测试"
    </rules>

    <output>
      - selected_tests: 本轮要执行的 test_id 列表
      - selected_count: 筛选后的测试数量
    </output>
  </phase>


  <!-- ======================================================
       9. RUN-LOOP：循环执行
  ====================================================== -->
  <phase id="RUN-LOOP">
    <goal>
      循环执行 selected_tests，但每次只跑一个，用 RUN-ONE。
    </goal>

    <inputs>
      - selected_tests: 本轮要执行的 test_id 列表
      - stop_on_fail: 是否遇到 FAIL 立即停止
    </inputs>

    <actions>
      每次迭代：

      1. 取出 selected_tests 中下一个尚未执行的 test_id

      2. 调用 ai-ad-agents-test-runner：
         - mode = "RUN-ONE"
         - test_id = 当前 test_id

      3. 解析结果：
         - 若 result = PASS：
           - 记录为 pass
           - 继续下一条

         - 若 result = FAIL：
           - 记录失败详情
           - 若 stop_on_fail = true：
             - 立即停止整个 RUN-LOOP
             - 标记本次巡检为「阻塞上线」
           - 若 stop_on_fail = false：
             - 记录失败但继续执行

         - 若 result = UNCERTAIN：
           - 记录为 uncertain
           - 继续执行下一条
           - 在 SUMMARY 中必须单独列出

      4. 若 selected_tests 提前执行完：
         - 结束 RUN-LOOP
         - 进入 SUMMARY
    </actions>

    <rules>
      - 【P1 安全规则】单测试执行限制：
          - 每次只能执行一个测试函数
          - 完全禁止跨测试输出
          - 完全禁止在一次迭代中执行多个测试

      - 可以设置最大执行条数上限（max_tests）
      - 超过则提前停止，并在 SUMMARY 中说明"只执行了部分测试"
    </rules>

    <output>
      - pass_count: PASS 数量
      - fail_count: FAIL 数量
      - uncertain_count: UNCERTAIN 数量
      - failed_tests: 失败测试详情列表
      - uncertain_tests: 不确定测试列表
    </output>
  </phase>


  <!-- ======================================================
       10. SUMMARY：最终汇总
  ====================================================== -->
  <phase id="SUMMARY">
    <goal>
      输出本轮测试巡检的最终结论，决定是否允许上线。
    </goal>

    <inputs>
      - total_test_count: 总测试数
      - selected_count: 实际执行数
      - pass_count: PASS 数量
      - fail_count: FAIL 数量
      - uncertain_count: UNCERTAIN 数量
      - failed_tests: 失败测试详情列表
      - uncertain_tests: 不确定测试列表
    </inputs>

    <actions>
      1. 生成总览统计

      2. 生成分类统计（按组件）：
         - agents_config 覆盖情况
         - OrchestratorAgent 覆盖情况
         - FEAgent 覆盖情况
         - BEAgent 覆盖情况
         - skills 覆盖情况
         - fs_tool 覆盖情况
         - smoke 覆盖情况

      3. 生成失败列表：
         - 对每个 FAIL 的 test_id，列出：
           - 期望行为
           - 实际静态分析结论
           - 建议修复方向（指向具体文件/函数）

      4. 生成不确定列表：
         - 列出所有 UNCERTAIN 测试
         - 明显标注："需要真实运行 pytest 验证"
         - 给出建议的 pytest 命令

      5. 生成放行结论：
         - 若 FAIL > 0：
           - verdict = "BLOCK"
           - 原则：阻塞上线，必须先修复失败测试

         - 若 FAIL = 0 且 UNCERTAIN = 0：
           - verdict = "ALLOW"
           - 可以作为自动写文件 / 合并代码的前置条件

         - 若 FAIL = 0 且 UNCERTAIN > 0：
           - verdict = "WARN"
           - 不直接阻塞，但强烈建议在 CI 中真实跑 pytest
    </actions>

    <rules>
      - 总览必须包含：总测试数 / 实际执行数 / PASS / FAIL / UNCERTAIN 数量
      - 失败测试必须包含具体修复建议
      - 放行结论必须明确（BLOCK / ALLOW / WARN）
    </rules>

    <output>
      - test_inspection_report: 完整的测试巡检报告（Markdown）
      - verdict: BLOCK | ALLOW | WARN
    </output>
  </phase>


  <!-- ======================================================
       11. 输出格式（Output Format）
  ====================================================== -->
  <output_format>
    # Agents 测试巡检报告（ai-ad-agents-test-orchestrator v2.0）

    ## 0. 总览
    - 总测试数: {total_test_count}
    - 实际执行数: {selected_count}
    - PASS: {pass_count}
    - FAIL: {fail_count}
    - UNCERTAIN: {uncertain_count}
    - 平均置信度: {confidence}%

    ## 1. 分类统计
    ### agents_config
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ### OrchestratorAgent
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ### FEAgent / BEAgent
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ### Skills
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ### Tools (fs_tool / validation)
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ### Smoke Tests
    - 覆盖测试: {count}
    - 状态: PASS / FAIL / UNCERTAIN

    ## 2. 失败列表（若存在）
    ### ❌ agents/tests/test_xxx.py::test_yyy
    - **期望行为**: ...
    - **实际结论**: ...
    - **失败原因**: ...
    - **修复建议**: 修改 agents/xxx.py 的 yyy 函数，确保 ...

    ## 3. 不确定列表（若存在）
    ### ⚠️ agents/tests/test_zzz.py::test_complex
    - **原因**: 超出静态分析能力（复杂 fixture / 动态行为）
    - **建议**: 真实运行 pytest
    - **命令**: `pytest agents/tests/test_zzz.py::test_complex -q`

    ## 4. 放行结论
    - **Verdict**: BLOCK | ALLOW | WARN

    ### BLOCK（阻塞上线）
    - 存在 {fail_count} 个失败测试
    - 必须先修复失败测试才能合并代码
    - 建议：根据上述"失败列表"逐个修复

    ### ALLOW（允许上线）
    - 所有测试通过（PASS={pass_count}，UNCERTAIN=0）
    - 可以作为自动写文件 / 合并代码的前置条件
    - 建议：在 CI 中仍运行完整 pytest 套件

    ### WARN（警告放行）
    - 无失败测试，但存在 {uncertain_count} 个不确定测试
    - 不直接阻塞，但强烈建议在 CI 中真实跑 pytest
    - 建议：根据上述"不确定列表"手动执行 pytest 验证
  </output_format>


  <!-- ======================================================
       12. Chain-of-Thought 管理
  ====================================================== -->
  <chain_of_thought>
    - 允许内部进行详细的代码+测试路径分析
    - 允许内部执行复杂推理、多轮交叉检查
    - 禁止向用户输出思考过程或中间标记
    - 对外只暴露：
      - 测试巡检报告
      - 失败/不确定条目的关键分析和修复建议
      - 放行结论（BLOCK / ALLOW / WARN）
  </chain_of_thought>


  <!-- ======================================================
       13. 使用示例（Usage Examples）
  ====================================================== -->
  <usage>
    示例 1：自动模式（根据改动文件）
    「
    使用 ai-ad-agents-test-orchestrator，
    changed_files = ["agents/agent_core/fe_agent.py", "agents/tools/fs_tool.py"]，
    test_scope = "auto"。
    只执行与 FEAgent 和 fs_tool 相关的测试。
    」

    示例 2：烟雾测试模式
    「
    使用 ai-ad-agents-test-orchestrator，
    test_scope = "smoke"。
    快速执行最小测试集（test_agents_smoke.py + 关键 agents_config 测试）。
    」

    示例 3：完整回归测试
    「
    使用 ai-ad-agents-test-orchestrator，
    test_scope = "all"，
    max_tests = 50，
    stop_on_fail = false。
    执行所有测试（最多50个），即使失败也继续执行完所有测试。
    」

    示例 4：快速验证特定组件
    「
    使用 ai-ad-agents-test-orchestrator，
    changed_files = ["agents/agent_core/orchestrator_agent.py"]，
    test_scope = "auto"，
    stop_on_fail = true。
    只执行 OrchestratorAgent 相关测试，遇到失败立即停止。
    」
  </usage>


  <!-- ======================================================
       14. 依赖子 Skill（已废弃，功能已内嵌）
  ====================================================== -->
  <sub_skills>
    > **v2.3 变更**: 原 ai-ad-agents-test-runner v2.2 已合并为内部模块，不再作为外部依赖。
    > 详见 <internal_runner_module> 章节。

    - 无外部子 Skill 依赖
    - 测试执行功能由内部 runner 模块完成
    - 保持与 v2.2 相同的测试能力（DISCOVERY / RUN-ONE / SUMMARY）
  </sub_skills>


  <!-- ======================================================
       14.5 内部 Runner 模块（合并自 ai-ad-agents-test-runner v2.2）
  ====================================================== -->
  <internal_runner_module>
    <description>
      原 ai-ad-agents-test-runner v2.2 的完整功能已内嵌于此。
      本模块负责「静态单元测试模拟执行」，不再作为独立 Skill 调用。

      v2.4 新增（Phase 2c）：
      - RUN-PYTEST: 真实执行单个测试（调用 pytest 命令）
      - RUN-SUITE: 真实执行测试套件（批量 pytest 执行）
    </description>

    <capabilities>
      <!-- 静态分析模式（只读，不执行 pytest） -->
      - DISCOVERY: 扫描 agents/tests/ 下所有测试函数，生成 PENDING_TESTS 清单
      - RUN-ONE: 每次执行一个测试函数，静态推理 PASS/FAIL/UNCERTAIN
      - SUMMARY: 输出最终统计与失败/不确定测试汇总

      <!-- v2.4 新增：真实执行模式（Phase 2c） -->
      - RUN-PYTEST: 调用 pytest 真实执行单个测试，返回实际结果
      - RUN-SUITE: 调用 pytest 真实执行测试套件，支持 markers 和 scope 筛选
    </capabilities>

    <internal_modes>
      <!-- ===== 静态分析模式（保持只读语义） ===== -->
      <mode id="DISCOVERY">
        扫描 agents/tests/ 目录，生成完整测试清单。
        输出 PENDING_TESTS 初始状态，不执行任何测试。
        【只读】不调用 pytest，不修改任何文件。
      </mode>

      <mode id="RUN-ONE">
        每次只执行一个测试函数，基于静态分析推理 PASS/FAIL/UNCERTAIN。
        读取测试代码 + 被测代码，分析断言和执行路径。
        更新 PENDING/FINISHED 状态。
        【只读】不调用 pytest，不修改任何文件。
      </mode>

      <mode id="SUMMARY">
        当所有测试执行完毕（PENDING_TESTS 为空）时，
        输出最终统计与失败/不确定测试汇总。
        【只读】不调用 pytest，不修改任何文件。
      </mode>

      <!-- ===== v2.4 新增：真实执行模式（Phase 2c） ===== -->
      <mode id="RUN-PYTEST">
        真实调用 pytest 执行单个测试函数。

        输入参数：
        - test_id: string (pytest 风格，如 agents/tests/test_factory.py::test_create_agent)
        - verbose: boolean (默认 false，若 true 则输出 -v)
        - capture: "no" | "sys" | "fd" (默认 "sys")

        执行命令：
        ```bash
        pytest {test_id} -v --tb=short -q
        ```

        输出：
        - result: PASS | FAIL | ERROR | SKIPPED
        - stdout: string (pytest 标准输出)
        - stderr: string (pytest 标准错误)
        - duration_ms: number (执行耗时)
        - traceback: string (若失败，包含完整 traceback)

        安全约束：
        - 只执行 agents/tests/ 下的测试
        - 禁止执行非测试命令
        - 禁止修改源代码
      </mode>

      <mode id="RUN-SUITE">
        真实调用 pytest 执行测试套件。

        输入参数：
        - scope: "all" | "smoke" | "auto" | string[] (测试文件列表)
        - markers: string[] (pytest markers，如 ["unit", "not slow"])
        - max_failures: number (默认 5，最大失败数后停止)
        - parallel: boolean (默认 false，若 true 使用 pytest-xdist -n auto)

        执行命令（scope=all）：
        ```bash
        pytest agents/tests/ -v --tb=short -x --maxfail={max_failures}
        ```

        执行命令（scope=smoke）：
        ```bash
        pytest agents/tests/test_factory.py agents/tests/test_types.py -v --tb=short
        ```

        输出：
        - total: number (总测试数)
        - passed: number
        - failed: number
        - skipped: number
        - errors: number
        - duration_ms: number (总执行耗时)
        - failed_tests: [{ test_id, reason, traceback }]
        - coverage: { lines: number, branches: number } (若启用 --cov)

        安全约束：
        - 只执行 agents/tests/ 下的测试
        - 禁止注入任意命令参数
        - 最大并发数限制为 4
      </mode>
    </internal_modes>

    <state_management>
      通过结构化 Markdown 输出维护测试进度：
      - PENDING_TESTS: 待执行测试列表
      - FINISHED_TESTS: 已完成测试列表（带 ✅/❌/⚠️ 状态标记）

      状态标记：
      - ✅ PASS: 静态分析推理该测试应通过
      - ❌ FAIL: 静态分析推理该测试应失败
      - ⚠️ UNCERTAIN: 超出静态分析能力，结果不可靠
    </state_management>

    <complexity_fallback>
      Pytest 复杂特性降级策略（v2.4 增强）：

      | Pytest 特性 | 静态分析能力 | 置信度 | 静态模式策略 | 执行模式策略 (Phase 2c) |
      |------------|------------|--------|-------------|------------------------|
      | 简单 assert | 完全支持 | ✅ 高 | 正常推理 | 直接执行 |
      | 简单 mock/monkeypatch | 完全支持 | ✅ 高 | 正常推理 | 直接执行 |
      | 简单 fixture | 完全支持 | ✅ 高 | 正常推理 | 直接执行 |
      | @pytest.mark.parametrize | 部分支持 | ⚠️ 中 | 逐个参数组推理 | RUN-PYTEST 逐个验证 |
      | fixture 间接依赖 (3+ 层) | 有限支持 | ⚠️ 中 | 尝试展开 fixture 链 | RUN-PYTEST 直接验证 |
      | 动态 fixture | 不支持 | ❌ 低 | 报告 UNCERTAIN | **自动升级为 RUN-PYTEST** |
      | 复杂 mock.side_effect | 不支持 | ❌ 低 | 报告 UNCERTAIN | **自动升级为 RUN-PYTEST** |

      v2.4 执行模式自动升级规则：
      1. 当 RUN-ONE 返回 UNCERTAIN 且 auto_escalate=true 时，自动切换为 RUN-PYTEST
      2. 当 complexity_score > 0.7 时，建议使用 RUN-SUITE 替代批量 RUN-ONE
      3. TODO: 实现 conftest.py 全局 fixture 解析
      4. TODO: 实现 autouse fixture 副作用检测
    </complexity_fallback>

    <execution_strategies>
      <!-- v2.4 新增：执行策略选择器 (Phase 2c) -->
      <strategy id="static_first">
        优先使用静态分析（RUN-ONE），仅在 UNCERTAIN 时升级为真实执行。
        适用场景：快速 PR 审查、本地开发反馈。
        命令：mode=RUN-ONE, auto_escalate=true
      </strategy>

      <strategy id="hybrid">
        静态分析 + 真实执行混合模式。
        步骤：
        1. DISCOVERY 获取测试清单
        2. 对高置信度测试使用 RUN-ONE
        3. 对低置信度测试使用 RUN-PYTEST
        4. SUMMARY 汇总所有结果
        适用场景：CI/CD 前置闸门。
      </strategy>

      <strategy id="full_execution">
        跳过静态分析，直接使用 RUN-SUITE 真实执行所有测试。
        适用场景：发布前回归测试、主分支合并。
        命令：mode=RUN-SUITE, scope=all
      </strategy>
    </execution_strategies>

    <constraints>
      安全约束（分模式区分）：

      【静态分析模式 (DISCOVERY / RUN-ONE / SUMMARY)】
      - 禁止实际运行 pytest 或任何系统命令
      - 禁止修改源代码或测试代码
      - 禁止写入任何文件
      - 禁止虚构测试用例或测试结果
      - 只执行静态分析，不执行真实测试

      【真实执行模式 (RUN-PYTEST / RUN-SUITE)】(v2.4 新增)
      - 允许运行 pytest 命令
      - 仅限执行 agents/tests/ 目录下的测试
      - 禁止执行非 pytest 命令
      - 禁止修改源代码或测试代码
      - 禁止注入任意命令行参数
      - 最大并发数限制为 4
      - 单次执行超时限制为 300 秒
    </constraints>
  </internal_runner_module>


  <!-- ======================================================
       15. 版本记录
  ====================================================== -->
  <VERSION_NOTES>
    ### v2.4 (2025-12-06)
    **Phase 2c: P1 修复 + 真实执行模式**

    P1 修复内容：
    - ✅ 路径统一：`tests/agents/` → `agents/tests/` (18 处修复)
    - ✅ 添加缺失 baseline：`AI_CODE_DEV_ORCHESTRATION_SOT_v1.0.md`

    新增功能：
    - ✅ 新增 `RUN-PYTEST` 模式：真实调用 pytest 执行单个测试
    - ✅ 新增 `RUN-SUITE` 模式：真实调用 pytest 执行测试套件
    - ✅ 新增 `execution_strategies`：static_first / hybrid / full_execution
    - ✅ 增强 `complexity_fallback`：新增执行模式策略列
    - ✅ 新增自动升级规则：UNCERTAIN 测试自动升级为 RUN-PYTEST

    安全约束更新：
    - 静态分析模式保持只读语义不变
    - 真实执行模式新增独立安全约束
    - 最大并发数限制为 4，单次执行超时 300 秒

    TODO 待实现：
    - conftest.py 全局 fixture 解析
    - autouse fixture 副作用检测

    ---

    ### v2.3 (2025-12-06)
    **测试域合并 (Phase 2b)：内嵌 ai-ad-agents-test-runner**

    合并内容：
    - 原 ai-ad-agents-test-runner v2.2 功能完全内嵌为 <internal_runner_module>
    - 新增 Section 14.5: internal_runner_module 章节
    - 包含完整的 DISCOVERY / RUN-ONE / SUMMARY 能力
    - 包含 state_management 和 complexity_fallback 策略
    - 保持原有安全约束（禁止执行 pytest、禁止修改代码）

    架构变更：
    - 不再调用外部 ai-ad-agents-test-runner Skill
    - 所有测试执行由内部 runner 模块完成
    - 对外行为保持完全向后兼容

    标记废弃：
    - ai-ad-agents-test-runner v2.2 标记为 deprecated
    - 该 Skill 保留作为历史参考，但不应被直接调用

    ---

    ### v2.2 (2025-11-28)
    - ✅ 添加 YAML frontmatter 符合 Skill Freeze 标准
    - ✅ 对齐 MASTER.md v3.5, SoT Freeze v2.6 baseline

    ---

    ### v2.1 (2025-11-27)
    - ✅ 添加 YAML frontmatter 符合 Skill Freeze 标准
    - ✅ 对齐 MASTER.md v3.5, SoT Freeze v2.6 baseline
    - ✅ 对齐 ASDD 6-Layer Architecture

    ---

    ### v2.0 (2025-11-26)
    **重大升级：SuperClaude 框架结构**
    - ✅ 升级为 SuperClaude <skill> 框架结构
    - ✅ 明确声明 <name>, <version>, <status>, <domain>, <profile>
    - ✅ 新增 <mission> / <when_to_use> / <when_not_to_use>
    - ✅ 新增 <forbidden_actions> 禁止行为清单
    - ✅ 重构为 5 个 <phase>：ANALYZE-CHANGES / INIT-DISCOVERY / SELECT-TESTS / RUN-LOOP / SUMMARY
    - ✅ 标准化 <input_contract> / <output_format>
    - ✅ 明确依赖 ai-ad-agents-test-runner v2.0

    **职责边界明确**
    - 只做工作流协调，不做具体测试分析
    - 只读不写，不修改任何代码
    - 不执行真实 pytest，只做静态分析

    ### v1.x (历史版本)
    - 使用非标准根标签（SYSTEM_ROLE）
    - 无明确边界定义
    - 已废弃

    ### v2.1 (2025-11-27)
    - ✅ 添加 YAML frontmatter 符合 Skill Freeze 标准
    - ✅ 对齐 MASTER.md v3.5, SoT Freeze v2.6 baseline
    - ✅ 对齐 ASDD 6-Layer Architecture
  </VERSION_NOTES>

</skill>
