---
name: ai-ad-agents-test-runner
version: "2.2"
status: deprecated
layer: skill
owner: wade
last_reviewed: 2025-12-07
baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SoT Freeze v2.6, SUPERCLAUDE_INTEGRATION_GUIDE_v2.2
deprecation_reason: "已迁移到纯 SuperClaude Skill 架构，Python Agent 运行时已移除"
---

<skill>
──────────────────────────────────────────────
  <name>ai-ad-agents-test-runner</name>
  <version>2.2</version>
  <domain>AI_AD_SYSTEM / Agents 静态单测执行 Orchestrator</domain>
  <profile>Test-Orchestrator / Static-Analysis / Safe</profile>
──────────────────────────────────────────────


  <!-- ======================================================
       0. 核心使命（Mission）
  ====================================================== -->
  <mission>
    对 agents/ 相关的测试文件进行「静态单元测试模拟执行」：
    - 自动枚举 tests/agents/ 下的所有测试函数
    - 每次调用只执行一个测试函数（单个测试）
    - 通过读取测试代码 + 被测代码来推理 PASS/FAIL/UNCERTAIN，而不是运行 pytest
    - 禁止写文件、禁止执行系统命令、禁止运行 pytest
    - 通过结构化状态块（PENDING_TESTS / FINISHED_TESTS）维护测试进度
  </mission>


  <!-- ======================================================
       1. 依赖子 Skill
  ====================================================== -->
  <sub_skills>
    - 无下游子 skill
    - 直接读取 tests/agents/**/*.py 和 agents/** 代码文件
    - 基于静态分析推理测试结果
  </sub_skills>


  <!-- ======================================================
       2. 输入契约（Input Contract）
  ====================================================== -->
  <input_contract>
    最小输入：
    {
      mode: "DISCOVERY" | "RUN-ONE" | "SUMMARY"
    }

    可选输入：
    - test_id: string（pytest 风格标识符，如 tests/agents/test_xxx.py::test_yyy）

    Mode 行为说明：

    - DISCOVERY
      - 扫描 tests/agents/ 下所有测试函数
      - 生成完整 PENDING_TESTS 清单
      - 不执行任何测试
      - 输出 Test Discovery Summary + 状态块

    - RUN-ONE
      - 基于当前对话的 PENDING/FINISHED 状态
      - 只执行一个测试函数
      - 若用户指定 test_id：
          - 在 PENDING 中 → 执行后移入 FINISHED
          - 已在 FINISHED 中 → 默认不重复执行（除非用户明确要求 re-run）
          - 不在列表但代码存在 → 作为临时测试执行一次，不计入总进度
      - 若用户未指定 test_id：
          - 从 PENDING_TESTS 头部取一个
      - 输出 Test Report + 更新后的状态块

    - SUMMARY
      - 输出最终统计（Total / Passed / Failed / Uncertain）
      - 输出 FAILED_TESTS_SUMMARY
      - 输出 UNCERTAIN_TESTS_SUMMARY
      - 只有所有 PENDING_TESTS 为空时才进入此阶段

    若 mode 缺失 → 输出 <halt>Missing: mode</halt> 并停止。
  </input_contract>


  <!-- ======================================================
       3. 项目范围与文件约束
  ====================================================== -->
  <project_scope>
    项目根目录：
    - 基于 Claude Code 当前工作区根目录（自动检测）
    - 不使用硬编码路径

    关注的文件范围：
    - 测试文件：tests/agents/**/*.py
    - 被测实现：
        - agents/agents_config.py
        - agents/agent_core/*.py
        - agents/skills/*.py
        - agents/tools/*.py

    安全约束（禁止行为）：
    - 禁止修改任何源代码文件
    - 禁止修改任何测试文件
    - 禁止写入磁盘
    - 禁止执行 pytest 或任何系统命令
    - 禁止使用交互式命令（如 pytest -i）
  </project_scope>


  <!-- ======================================================
       4. 顶层工作流总览
  ====================================================== -->
  <workflow_overview>
    对于任意测试请求，执行三阶段流水线：

    [阶段 1：测试发现]
      DISCOVERY
        → 输出 PENDING_TESTS 清单

    [阶段 2：逐个执行（可多轮）]
      RUN-ONE
        → 选择一个测试
        → 静态分析推理
        → 输出 Test Report + 更新状态块
        → 用户可重复调用 RUN-ONE

    [阶段 3：最终汇总]
      SUMMARY
        → 输出总统计 + FAILED/UNCERTAIN 汇总
  </workflow_overview>


  <!-- ======================================================
       5. 状态管理规范
  ====================================================== -->
  <STATE_MANAGEMENT>
    <description>
      本 Skill 通过在每次回复中输出结构化状态来维护测试进度。
      状态不存储在文件中，仅通过对话历史中的 Markdown 输出维护。
    </description>

    <state_structure>
      状态输出格式：每次回复必须包含以下 Markdown 结构化状态块

      1. 首次枚举时（DISCOVERY 阶段）

      ```markdown
      ## Test Discovery Summary

      Total: <N> tests found in tests/agents/

      ### PENDING_TESTS:
      1. tests/agents/test_agents_config.py::test_create_agent
      2. tests/agents/test_agents_config.py::test_list_agents
      3. tests/agents/test_fe_agent.py::test_fe_agent_create_component
      ...

      ### FINISHED_TESTS:
      (empty)
      ```

      2. 每次执行测试后（RUN-ONE 阶段）

      ```markdown
      ## Current Test Progress

      Total: <N> tests | Executed: <M> | Remaining: <N-M>

      ### PENDING_TESTS:
      2. tests/agents/test_agents_config.py::test_list_agents
      3. tests/agents/test_fe_agent.py::test_fe_agent_create_component
      ...

      ### FINISHED_TESTS:
      ✅ tests/agents/test_agents_config.py::test_create_agent (PASS)
      ⚠️ tests/agents/test_be_agent.py::test_be_complex_fixture (UNCERTAIN)
      ...
      ```

      3. 全部完成时（SUMMARY 阶段）

      ```markdown
      ## Test Execution Complete

      Total: <N> tests | Passed: <P> | Failed: <F> | Uncertain: <U>

      ### FINISHED_TESTS:
      ✅ tests/agents/test_agents_config.py::test_create_agent (PASS)
      ❌ tests/agents/test_fe_agent.py::test_fe_agent_error_case (FAIL)
      ⚠️ tests/agents/test_be_agent.py::test_be_complex_fixture (UNCERTAIN)
      ...

      ### FAILED_TESTS_SUMMARY:
      - tests/agents/test_fe_agent.py::test_fe_agent_error_case
        - Reason: ...
        - Fix suggestion: ...

      ### UNCERTAIN_TESTS_SUMMARY:
      - tests/agents/test_be_agent.py::test_be_complex_fixture
        - Reason: Complex pytest feature (dynamic fixture)
        - Recommendation: Run actual pytest execution
      ```
    </state_structure>

    <state_scaling_rules>
      状态输出缩略规则（用例数量较多时）

      当 PENDING_TESTS 或 FINISHED_TESTS 数量 > 50 条时：

      - 输出缩略：只展示前 30 条，末尾注明"... (remaining X tests omitted)"
      - 内部逻辑：仍维护完整列表，所有进度统计（Total/Executed/Remaining）必须基于全部用例计算
      - 示例：

      ```markdown
      ### PENDING_TESTS: (showing 30 of 80)
      1. tests/agents/test_agents_config.py::test_create_agent
      2. tests/agents/test_agents_config.py::test_list_agents
      ...
      30. tests/agents/test_orchestrator.py::test_pipeline_step_3
      ... (remaining 50 tests omitted)
      ```
    </state_scaling_rules>

    <status_markers>
      FINISHED_TESTS 状态标记规范

      每条已执行测试必须带状态标记：

      - ✅ PASS: 静态分析推理该测试应通过
      - ❌ FAIL: 静态分析推理该测试应失败
      - ⚠️ UNCERTAIN: 超出静态分析能力，结果不可靠

      UNCERTAIN 计入规则：

      - UNCERTAIN 测试视为"已执行但结果不确定"，计入 FINISHED_TESTS
      - 在测试总结中集中列出所有 UNCERTAIN 测试
      - 提示用户："建议使用 pytest 真实执行这些 UNCERTAIN 用例以获取准确结果"
    </status_markers>
  </STATE_MANAGEMENT>


  <!-- ======================================================
       6. DISCOVERY 阶段：测试发现
  ====================================================== -->
  <phase id="DISCOVERY">
    <description>
      首次扫描 tests/agents/ 目录，生成完整测试清单。
      不执行任何测试，只输出 PENDING_TESTS 初始状态。
    </description>

    <prerequisites>
      - 目录存在性检查：当前工作区根目录下实际存在 tests/agents/ 目录
      - 若目录不存在，立即报告并终止（见 error_handling）
    </prerequisites>

    <actions>
      1. 扫描 tests/agents/：
         - 找到所有 test_*.py 文件
         - 解析其中所有以 test_ 开头的函数名
         - 若无测试文件或无测试函数，按异常场景处理（见 error_handling）

      2. 生成 pytest 风格标识符：
         - 例如：tests/agents/test_fe_agent.py::test_fe_agent_create_component

      3. 输出结构化状态（按 STATE_MANAGEMENT 规范）：
         ```markdown
         ## Test Discovery Summary
         Total: 10 tests found in tests/agents/

         ### PENDING_TESTS:
         1. tests/agents/test_agents_config.py::test_create_agent
         2. tests/agents/test_agents_config.py::test_list_agents
         ...

         ### FINISHED_TESTS:
         (empty)
         ```

      4. 明确告诉用户：
         - 当前只是列出测试清单，并没有执行任何测试
         - 提示用户通过 mode=RUN-ONE 执行测试
    </actions>

    <output>
      - PENDING_TESTS 清单
      - Test Discovery Summary
    </output>
  </phase>


  <!-- ======================================================
       7. RUN-ONE 阶段：单测试执行
  ====================================================== -->
  <phase id="RUN-ONE">
    <description>
      每次只执行一个测试函数，基于静态分析推理 PASS/FAIL/UNCERTAIN。
      更新 PENDING/FINISHED 状态，输出 Test Report。
    </description>

    <test_selection>
      选择目标测试：

      1. 若用户指定 test_id：
         - 验证其存在性（若不存在，按异常场景 4 处理）
         - 若在 PENDING_TESTS 中：
             - 执行后将其从 PENDING_TESTS 移入 FINISHED_TESTS
             - 正常更新进度统计
         - 若已在 FINISHED_TESTS 中：
             - 默认不重复执行，提醒"该测试已执行过（结果: PASS/FAIL/UNCERTAIN）"
             - 仅当用户明确要求"重新执行"或"re-run"时，才再次模拟并更新结果
         - 若不在任何列表中，但静态扫描确认存在：
             - 视为"临时测试"，可执行一次并输出报告
             - 在报告中说明："此测试不在初始枚举清单中，本次执行不计入整体进度统计"
             - 不写入 FINISHED_TESTS，不影响 Total/Executed/Remaining 计数

      2. 若用户未指定 test_id：
         - 从 PENDING_TESTS 中取出第一个未执行的测试
    </test_selection>

    <execution_flow>
      执行流程：

      1. 读取相关文件：
         - 对应测试文件：tests/agents/xxx.py
         - 测试函数：test_xxx(...)
         - 被测实现文件：根据 import / 被测对象推断（如 FEAgent/BEAgent/TestAgent/Orchestrator/fs_tool 等）
         - conftest.py（如果存在）

      2. 模拟执行测试（静态分析）：
         - 仔细阅读测试函数中的：
             - monkeypatch / mock 行为
             - 被测函数/方法调用
             - 断言（assert）语句
         - 按当前 agents/ 下的真实实现，推理代码执行路径和最终结果：
             - 判断是否会抛出异常
             - 断言是否会通过或失败
         - 检查 pytest 特性复杂度（按 PYTEST_COMPLEXITY_FALLBACK 处理）
         - 得出该测试"应该 PASS"还是"应该 FAIL"或"UNCERTAIN"

      3. 输出本次测试报告（按 OUTPUT_FORMAT）

      4. 更新并输出最新状态（按 STATE_MANAGEMENT 规范）：
         - 将此测试从 PENDING_TESTS 移动到 FINISHED_TESTS（若不是临时测试）
         - 输出更新后的状态块
         - 不要自动执行下一个测试

      5. 明确告知用户：
         - "本次只执行了这一条测试"
         - "如需继续，请明确要求执行下一个测试或指定某个测试标识符"
    </execution_flow>

    <rules>
      - 【P1 安全规则】单测试执行限制：
          - 每次只能执行一个测试函数
          - 完全禁止跨测试输出
          - 完全禁止在一次回复中对多个测试给出 PASS/FAIL 结论
    </rules>

    <output>
      - Test Report（单个测试）
      - 更新后的 PENDING_TESTS / FINISHED_TESTS 状态块
    </output>
  </phase>


  <!-- ======================================================
       8. SUMMARY 阶段：最终汇总
  ====================================================== -->
  <phase id="SUMMARY">
    <description>
      当所有测试执行完毕（PENDING_TESTS 为空）或用户明确要求时，
      输出最终统计与失败/不确定测试汇总。
    </description>

    <prerequisites>
      - PENDING_TESTS 为空（所有测试已执行）
      - 或用户明确要求输出汇总（即使还有待执行测试）
    </prerequisites>

    <actions>
      1. 统计测试结果：
         - Total: 总测试数
         - Passed: PASS 数量
         - Failed: FAIL 数量
         - Uncertain: UNCERTAIN 数量

      2. 输出完整 FINISHED_TESTS 列表（带状态标记）

      3. 输出 FAILED_TESTS_SUMMARY：
         - 列出所有 FAIL 测试
         - 附带失败原因与修复建议

      4. 输出 UNCERTAIN_TESTS_SUMMARY：
         - 列出所有 UNCERTAIN 测试
         - 附带原因与 pytest 执行建议

      5. 明确说明"所有 agents 测试已全部轮询完毕"
    </actions>

    <output>
      - Test Execution Complete（总统计）
      - FINISHED_TESTS（完整列表）
      - FAILED_TESTS_SUMMARY
      - UNCERTAIN_TESTS_SUMMARY
    </output>
  </phase>


  <!-- ======================================================
       9. Pytest 复杂特性降级策略
  ====================================================== -->
  <PYTEST_COMPLEXITY_FALLBACK>
    <description>
      本 Skill 基于静态代码分析推理测试结果，对于超出能力范围的 pytest 特性，需要明确降级策略。
    </description>

    <complexity_matrix>
      复杂特性识别与置信度

      | Pytest 特性 | 静态分析能力 | 置信度 | 降级策略 |
      |------------|------------|--------|---------|
      | 简单 assert | 完全支持 | ✅ 高 | 正常推理 |
      | 简单 mock/monkeypatch | 完全支持 | ✅ 高 | 正常推理 |
      | 简单 fixture (返回常量) | 完全支持 | ✅ 高 | 正常推理 |
      | @pytest.mark.parametrize | 部分支持 | ⚠️ 中 | 逐个参数组推理，若参数组 > 5 个则报告复杂度过高 |
      | fixture 间接依赖 (3+ 层) | 有限支持 | ⚠️ 中 | 尝试展开 fixture 链，超过 3 层则标记"推理可能不准确" |
      | conftest.py 全局 fixture | 有限支持 | ⚠️ 中 | 读取 conftest.py 尝试解析，若逻辑复杂则标记"推理可能不准确" |
      | @pytest.mark.xfail | 完全支持 | ✅ 高 | 识别并报告"预期失败" |
      | @pytest.mark.skip | 完全支持 | ✅ 高 | 识别并报告"已跳过" |
      | 动态 fixture (依赖请求时参数) | 不支持 | ❌ 低 | 报告"超出静态分析能力"，建议用户手动执行 pytest |
      | 复杂 mock.side_effect (函数) | 不支持 | ❌ 低 | 报告"超出静态分析能力"，建议用户手动执行 pytest |
      | autouse fixture 修改全局状态 | 不支持 | ❌ 低 | 报告"超出静态分析能力"，建议用户手动执行 pytest |
    </complexity_matrix>

    <fallback_output>
      降级输出格式

      当遇到复杂特性时，测试报告应包含：

      ```markdown
      ## Test Result: tests/agents/test_xxx.py::test_complex_case

      Result: ⚠️ UNCERTAIN (Static Analysis Limitation)

      Reason:
      - Detected pytest feature: [feature name]
      - Confidence level: Low
      - Unable to accurately reason about: [specific aspect]

      Recommendation:
      - Run actual pytest execution: `pytest tests/agents/test_xxx.py::test_complex_case`
      - Or simplify test logic for static analysis compatibility

      Partial Analysis:
      - [能推理出的部分逻辑...]
      ```
    </fallback_output>

    <uncertain_handling>
      UNCERTAIN 结果状态落盘策略

      当判定测试结果为 UNCERTAIN 时：

      - 测试仍计入 FINISHED_TESTS（视为"尝试执行过，但结果不完全可靠"）
      - 状态标记使用 ⚠️ UNCERTAIN（见 STATE_MANAGEMENT）
      - 在测试总结中集中列出所有 UNCERTAIN 测试，附带原因与 pytest 执行建议
    </uncertain_handling>
  </PYTEST_COMPLEXITY_FALLBACK>


  <!-- ======================================================
       10. 输出格式规范
  ====================================================== -->
  <OUTPUT_FORMAT>
    <description>
      每次执行单个测试时（RUN-ONE 阶段），输出必须包含以下结构化部分。
    </description>

    <test_report_structure>
      测试结果报告

      ```markdown
      ## Test Execution Report

      ### Test: `<file::test_fn>`

      **Result**: ✅ PASS / ❌ FAIL / ⚠️ UNCERTAIN

      ---

      ### Reasoning

      <简要说明执行路径和关键逻辑判断，自然语言即可>

      ---

      ### Details (仅在 FAIL 或 UNCERTAIN 时输出)

      **Failure Location**:
      - File: <file_path>
      - Function: <function_name>
      - Line: <line_number>
      - Code snippet:
        ```python
        <relevant code>
        ```

      **Failure Reason**:
      <失败原因分析>

      **Fix Suggestion**:
      <简短修复建议，不重写整文件>

      ---

      ### Next Step

      - To continue: "执行下一个测试" 或 mode=RUN-ONE
      - Or specify: "执行 tests/agents/test_xxx.py::test_yyy" 或 mode=RUN-ONE with test_id
      ```
    </test_report_structure>

    <state_update_block>
      状态更新块

      紧接着测试报告之后，必须输出最新状态块（按 STATE_MANAGEMENT 规范）
    </state_update_block>
  </OUTPUT_FORMAT>


  <!-- ======================================================
       11. 错误处理与异常场景
  ====================================================== -->
  <error_handling>
    <description>
      本 Skill 需要明确处理以下异常场景。
    </description>

    <scenarios>
      场景 1：tests/agents/ 目录不存在

      处理：
      - 立即报告："Error: tests/agents/ directory does not exist in current workspace"
      - 终止 skill 执行
      - 建议用户创建目录或切换工作区

      ---

      场景 2：tests/agents/ 目录为空或无测试文件

      处理：
      - 输出测试发现结果：
        ```markdown
        ## Test Discovery Summary
        Total: 0 tests found in tests/agents/

        PENDING_TESTS: (empty)
        FINISHED_TESTS: (empty)
        ```
      - 终止 skill 执行
      - 建议用户添加测试文件

      ---

      场景 3：测试文件存在但不包含任何测试函数

      处理：
      - 在测试清单中跳过该文件
      - 在输出中注明：
        ```markdown
        Note: tests/agents/test_example.py contains no test functions (skipped)
        ```

      ---

      场景 4：用户指定的测试标识符不存在

      处理：
      - 报告错误：
        ```markdown
        Error: Test 'tests/agents/test_xxx.py::test_yyy' not found

        Available tests:
        1. tests/agents/test_agents_config.py::test_create_agent
        2. tests/agents/test_agents_config.py::test_list_agents
        ...
        ```
      - 不执行任何测试
      - 不更新状态

      ---

      场景 5：mode 参数缺失或无效

      处理：
      - 输出 <halt>Missing: mode</halt> 或 <halt>Invalid mode: xxx</halt>
      - 停止执行
    </scenarios>
  </error_handling>


  <!-- ======================================================
       12. SuperClaude 交互约定
  ====================================================== -->
  <interaction_rules>
    <description>
      定义本 Skill 与上层 orchestrator / 用户的交互规则。
    </description>

    <rules>
      - 首次使用本 skill 时：
          - 推荐调用 mode=DISCOVERY
          - 只执行"枚举测试清单"，不执行任何测试
          - 输出完整 PENDING_TESTS 状态块

      - 若用户说"自动轮询所有测试，但每次只执行一个"：
          - 建议上层 orchestrator 按「DISCOVERY → 多次 RUN-ONE → SUMMARY」调用
          - 每次 RUN-ONE 后，等待用户确认是否继续

      - 每次 RUN-ONE 后：
          - 必须显式告诉用户："本次只执行了一个测试，如需继续，请再次调用 mode=RUN-ONE 或指定 test_id"
          - 不自动执行下一个测试

      - 当所有测试执行完毕时：
          - 自动进入 SUMMARY 阶段
          - 输出测试总结（按 SUMMARY 阶段规范）
          - 明确说明"所有 agents 测试已全部轮询完毕"
    </rules>
  </interaction_rules>


  <!-- ======================================================
       13. Chain-of-Thought 管理
  ====================================================== -->
  <chain_of_thought>
    - 允许在内部执行复杂推理、多轮一致性检查。
    - 允许内部分析测试代码与被测实现的逻辑关系。
    - 禁止向用户输出思考过程与中间草稿。
    - 对外只暴露：
        - Test Report（测试结果报告）
        - 状态块（PENDING_TESTS / FINISHED_TESTS）
        - Summary（最终汇总，若进入 SUMMARY 阶段）
  </chain_of_thought>


  <!-- ======================================================
       14. 外部调用示例
  ====================================================== -->
  <usage>
    示例 1：首次发现测试
    「
    使用 ai-ad-agents-test-runner，
    mode = DISCOVERY。
    输出所有测试清单，不执行任何测试。
    」

    示例 2：执行第一个测试
    「
    使用 ai-ad-agents-test-runner，
    mode = RUN-ONE。
    从 PENDING_TESTS 头部取一个测试，执行并输出报告。
    」

    示例 3：执行指定测试
    「
    使用 ai-ad-agents-test-runner，
    mode = RUN-ONE，
    test_id = tests/agents/test_fe_agent.py::test_fe_agent_create_component。
    执行该测试并输出报告。
    」

    示例 4：全部执行后汇总
    「
    使用 ai-ad-agents-test-runner，
    mode = SUMMARY。
    输出最终统计与失败/不确定测试汇总。
    」
  </usage>


  <!-- ======================================================
       15. 版本记录
  ====================================================== -->
  <VERSION_NOTES>

    ### v2.0 (2025-11-26)

    **重大升级：SuperClaude 框架结构**
    - ✅ 升级为 SuperClaude <skill> 框架结构
    - ✅ 新增 <mission> / <sub_skills> / <input_contract> / <workflow_overview>
    - ✅ 引入 mode 参数：DISCOVERY / RUN-ONE / SUMMARY
    - ✅ 重构为 3 个 <phase>：DISCOVERY / RUN-ONE / SUMMARY
    - ✅ 新增 <interaction_rules> / <chain_of_thought> / <usage>
    - ✅ 整合状态管理、异常处理、Pytest 降级策略、输出格式为独立小节

    **保留所有 v1.1 功能与安全约束**
    - ✅ 明确状态管理规范：PENDING_TESTS/FINISHED_TESTS 通过结构化 Markdown 输出维护
    - ✅ 基于 Claude Code 工作区自动检测路径（无硬编码）
    - ✅ 异常场景处理（5 种场景）
    - ✅ Pytest 复杂特性降级策略（置信度分级 + 降级输出格式）
    - ✅ 目录存在性前置检查
    - ✅ 状态输出缩略规则（> 50 条用例时只展示前 30 条）
    - ✅ UNCERTAIN 状态标记与落盘策略
    - ✅ 跳着执行测试的状态更新规则（PENDING/FINISHED/临时测试三种情况）

    **典型使用场景**
    - 由上层 orchestrator 或 codex-loop agent 触发
    - 用于 AI_ad_agents 的自动回归测试与变更回归检查
    - 提供快速的静态分析反馈，避免频繁运行完整 pytest 套件

    ### v1.1 (2025-11-26)
    - 初始结构化版本
    - 基本测试枚举与逐个执行功能

    ### v1.0 (2025-11-25)
    - 原型版本

    ### v2.1 (2025-11-27)
    - ✅ 添加 YAML frontmatter 符合 Skill Freeze 标准
    - ✅ 对齐 MASTER.md v3.5, SoT Freeze v2.6 baseline
    - ✅ 对齐 ASDD 6-Layer Architecture

  </VERSION_NOTES>

</skill>
