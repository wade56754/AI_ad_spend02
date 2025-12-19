---
name: ai-ad-prompt-structurer
version: "4.0"
status: production
layer: skill
owner: wade
last_reviewed: 2025-12-18
core_principle: "约束优于指令 (Constraints Over Instructions)"
design_philosophy: "做得越少，错得越少"
mcp_tools:
  - sequential-thinking
  - context7
baseline:
  - SuperClaude Framework (github.com/SuperClaude-Org/SuperClaude_Framework)
  - Claude Code System Prompts
  - LangGPT
  - DSPy
---

<skill>
══════════════════════════════════════════════════════════════════════
  AI 提示词结构化器 v4.0 - Prompt Structurer

  核心理念：约束优于指令 (Constraints Over Instructions)
  MCP 工具：sequential-thinking + context7
══════════════════════════════════════════════════════════════════════

  <name>ai-ad-prompt-structurer</name>
  <version>4.0</version>
  <domain>AI_AD_SYSTEM / 代码工厂 / 提示词工程</domain>


  <!-- ======================================================
       1. v4.0 核心创新
  ====================================================== -->
  <whats_new version="4.0">
    ## v4.0 核心创新 (整合 SuperClaude Framework)

    | 特性 | v3.0 | v4.0 |
    |------|------|------|
    | MCP 工具 | 无 | ✅ sequential-thinking + context7 |
    | 行为模式 | 无 | ✅ 7 种 Behavioral Modes |
    | 深度研究 | 无 | ✅ Deep Research 策略 |
    | 工作流 | 静态 | ✅ Sequential Thinking 动态工作流 |

    ### MCP 工具集成
    - **sequential-thinking**: 顺序化思考，分解复杂问题为步骤
    - **context7**: 实时查询最新库文档

    ### 行为模式 (来自 SuperClaude)
    - deep-research: 深度研究模式
    - implementation: 实现模式
    - orchestration: 工具编排模式
    - introspection: 元认知分析模式
  </whats_new>


  <!-- ======================================================
       2. MCP 工具定义
  ====================================================== -->
  <mcp_tools>
    ## Sequential Thinking

    ```
    use mcp__sequential-thinking__sequentialthinking
    ```

    ### 何时使用
    - 分解复杂问题为步骤
    - 规划和设计需要修订
    - 需要多步骤解决方案
    - 需要维护上下文

    ### 参数
    - thought: 当前思考步骤
    - nextThoughtNeeded: 是否需要下一步
    - thoughtNumber: 当前步骤编号 (1-6)
    - totalThoughts: 预估总步骤数
    - isRevision: 是否修订之前的思考
    - needsMoreThoughts: 是否需要更多步骤

    ---

    ## Context7

    ```
    use mcp__context7__resolve-library-id
    use mcp__context7__get-library-docs
    ```

    ### 使用步骤
    1. 调用 resolve-library-id 获取库 ID
    2. 调用 get-library-docs 获取文档

    ### 参数
    - libraryName: 库名称 (如 "fastapi")
    - context7CompatibleLibraryID: 库 ID (如 "/tiangolo/fastapi")
    - topic: 聚焦主题 (可选)
    - mode: "code" (API 参考) 或 "info" (概念指南)
  </mcp_tools>


  <!-- ======================================================
       3. 约束三层模型
  ====================================================== -->
  <constraint_model>
    ## Layer 1: 安全约束 (Security) - 绝对红线

    - ❌ 暴露密钥、凭证、secrets
    - ❌ 提交 .env、credentials.json 到仓库
    - ❌ 编写恶意代码
    - ❌ SQL 注入、XSS、命令注入
    - ❌ 删除用户未指定的文件

    ## Layer 2: 行为约束 (Behavior) - 工作方式

    ### 极简主义原则
    - 只做被直接要求的更改
    - 三行代码胜过一个抽象
    - 不要"顺便"改进周围代码

    ### 先读后改原则
    - 修改前必须先读取目标文件
    - 查看相邻文件了解项目约定
    - 推断并遵循现有代码风格

    ## Layer 3: 任务约束 (Task) - 具体边界

    按任务类型定义，如：
    - REFACTOR: 保留业务语义，不改 API 合同
    - BUGFIX: 只修复报告的问题
    - FEATURE: 只实现被要求的功能
  </constraint_model>


  <!-- ======================================================
       4. Sequential Thinking 工作流
  ====================================================== -->
  <workflow>
    ## Sequential Thinking 工作流

    ```
    Step 1: 理解任务
    - 分析原始需求
    - 识别关键约束
    - 确定任务类型

    Step 2: 探索上下文 (Explore)
    - 读取目标文件
    - 读取相邻文件
    - 推断项目风格

    Step 3: 制定计划 (Plan)
    - 分解为子任务
    - 确定执行顺序
    - 定义验收标准

    Step 4: 执行变更 (Execute)
    - 按计划逐步执行
    - 每步输出 git diff
    - 遵循 patch 限制

    Step 5: 验证结果 (Verify)
    - 运行测试命令
    - 检查验收标准
    - 失败则回到 Step 4

    Step 6: 总结输出
    - 输出变更清单
    - 输出验证结果
    - 输出回滚方案
    ```
  </workflow>


  <!-- ======================================================
       5. 子代理定义
  ====================================================== -->
  <sub_agents>
    <agent id="EXPLORE">
      <name>Explore Agent</name>
      <mission>探索代码库，理解上下文</mission>
      <constraints>只读不写, 输出包含路径和行号</constraints>
    </agent>

    <agent id="PLAN">
      <name>Plan Agent</name>
      <mission>制定执行计划</mission>
      <constraints>计划可分步验证, 每步有回滚方案</constraints>
    </agent>

    <agent id="EXECUTE">
      <name>Execute Agent</name>
      <mission>按计划执行变更</mission>
      <constraints>严格按计划, 每 patch ≤5 文件</constraints>
    </agent>

    <agent id="VERIFY">
      <name>Verify Agent</name>
      <mission>验证变更结果</mission>
      <constraints>运行验证命令, 失败回到 Execute</constraints>
    </agent>

    <agent id="RESEARCH">
      <name>Research Agent</name>
      <mission>深度研究，使用 context7 获取文档</mission>
      <constraints>只读不写, 使用 context7</constraints>
    </agent>
  </sub_agents>


  <!-- ======================================================
       6. 任务类型 → 行为模式映射
  ====================================================== -->
  <behavioral_modes>
    | 任务类型 | 行为模式 | MCP 工具 | 子代理链 |
    |----------|----------|----------|----------|
    | REFACTOR | implementation | sequential-thinking, context7 | Explore→Plan→Execute→Verify |
    | FEATURE | implementation | sequential-thinking, context7 | Explore→Plan→Execute→Verify |
    | BUGFIX | implementation | - | Explore→Execute→Verify |
    | MIGRATION | orchestration | sequential-thinking | Explore→Plan→Execute→Verify |
    | RESEARCH | deep-research | sequential-thinking, context7 | Research |
    | REVIEW | introspection | - | Explore→Verify |
  </behavioral_modes>


  <!-- ======================================================
       7. 输出模板
  ====================================================== -->
  <output_template>
    ```xml
    <task>
      {任务描述}
      原始需求：{用户原始输入}
      行为模式：{behavioral_mode}
    </task>

    <mcp_tools>
      # MCP 工具集成

      ## Sequential Thinking
      use mcp__sequential-thinking__sequentialthinking
      用于：分解复杂问题、多步推理

      ## Context7
      use mcp__context7__resolve-library-id
      use mcp__context7__get-library-docs
      用于：查询最新库文档
    </mcp_tools>

    <context>
      # 项目上下文

      ## SoT 裁判链
      1. STATE_MACHINE.md v2.6
      2. DATA_SCHEMA.md v5.2
      ...

      ## 项目路径
      - repo_root: ...
      - backend_dir: ...
    </context>

    <constraints>
      # 约束系统

      ### 🔴 Layer 1: 安全约束
      {安全约束}

      ### 🟡 Layer 2: 行为约束
      {行为约束}

      ### 🟢 Layer 3: 任务约束
      {任务约束}
    </constraints>

    <workflow>
      ## Sequential Thinking 工作流
      Step 1-6...
    </workflow>

    <delegation>
      执行链：{Agent 链}
      ...
    </delegation>

    <execution>
      1. 使用 sequential-thinking 进行顺序化思考
      2. 按 Agent 链顺序执行
      3. 需要查文档时使用 context7
      4. Verify 失败则回到 Execute 修复

      **记住：做得越少，错得越少。**
    </execution>

    <acceptance_criteria>
      - [ ] 所有测试通过
      - [ ] API 合同未变更
      - [ ] 每个 patch ≤ 5 文件、≤ 200 行
    </acceptance_criteria>
    ```
  </output_template>


  <!-- ======================================================
       8. 使用示例
  ====================================================== -->
  <examples>
    <example>
      <input>重构后端代码</input>
      <output>
        任务类型: refactor
        行为模式: implementation
        MCP 工具: [sequential-thinking, context7]
        子代理链: explore → plan → execute → verify
      </output>
    </example>

    <example>
      <input>研究 FastAPI 最佳实践</input>
      <output>
        任务类型: research
        行为模式: deep-research
        MCP 工具: [sequential-thinking, context7]
        子代理链: research
      </output>
    </example>

    <example>
      <input>修复充值状态转换的 bug</input>
      <output>
        任务类型: bugfix
        行为模式: implementation
        MCP 工具: []
        子代理链: explore → execute → verify
      </output>
    </example>
  </examples>


  <!-- ======================================================
       9. 版本历史
  ====================================================== -->
  <version_history>
    ### v4.0 (2025-12-18) - MCP 工具集成
    整合 SuperClaude Framework:
    - ✅ sequential-thinking MCP 工具
    - ✅ context7 MCP 工具
    - ✅ 7 种 Behavioral Modes
    - ✅ Sequential Thinking 6 步工作流
    - ✅ Research Agent (深度研究)

    ### v3.0 (2025-12-18) - 约束驱动重构
    - 约束三层模型: Security → Behavior → Task
    - 先读后改原则
    - 极简主义约束
    - 模块化委托

    ### v2.1 (2025-12-18)
    - 修复 6 个问题

    ### v1.0 (2025-12-18)
    - 初始版本
  </version_history>


  <!-- ======================================================
       10. 实现代码
  ====================================================== -->
  <implementation>
    Python 实现: agents/skills/prompt_structurer.py

    核心类: PromptStructurer
    主入口: structure_prompt(user_request) -> Dict

    使用方式:
    ```python
    from agents.skills.prompt_structurer import structure_prompt

    result = structure_prompt("重构后端代码")
    print(result["rendered_prompt"])
    ```
  </implementation>

</skill>
