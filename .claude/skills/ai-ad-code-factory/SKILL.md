---
name: ai-ad-code-factory
version: "3.5"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-24
baseline:
  - MASTER.md v3.5
  - CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
  - AI_CODE_FACTORY_REFACTOR_PROPOSAL.md v1.0
  - code-blocks-registry.md v2.0
code_sources:
  - project: Anthropic autonomous-coding
    github: https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding
    license: Internal (参考设计)
    borrowed_concepts:
      - 双 Agent 模式 (Initializer + Factory)
      - task_list.json 持久化
      - 会话管理与恢复
      - Defense-in-Depth 安全模型
  - project: MetaGPT
    github: https://github.com/geekan/MetaGPT
    license: MIT
    borrowed_concepts:
      - 多角色 Agent 协作模式
      - 标准化 SOP 流程
      - 消息传递机制
  - project: OpenHands
    github: https://github.com/All-Hands-AI/OpenHands
    license: MIT
    borrowed_concepts:
      - Agent-Computer Interface (ACI) 设计
      - 事件驱动架构
  - project: SWE-agent
    github: https://github.com/princeton-nlp/SWE-agent
    license: MIT
    borrowed_concepts:
      - 文件编辑接口设计
      - 错误修复循环
---

<skill>
══════════════════════════════════════════════════════════════════
  AI 代码工厂 v3.5 - 前端设计集成版
══════════════════════════════════════════════════════════════════

  <name>ai-ad-code-factory</name>
  <version>3.5</version>
  <domain>AI_AD_SYSTEM / 代码工厂 / 自主编码</domain>
  <profile>Autonomous-Coding / Search-First / Session-Persistent / Design-Aware</profile>


  <!-- ======================================================
       0. 代码来源说明 (Code Sources)
  ====================================================== -->
  <code_sources>
    本 Skill 是代码工厂的主编排器，整合了以下项目的核心设计：

    **核心架构 (v3.0 新增)**:
    1. **Anthropic autonomous-coding** - https://github.com/anthropics/claude-quickstarts
       - 双 Agent 模式 (Initializer + Coding Agent)
       - task_list.json 持久化 (任务只能 pending → completed)
       - 会话管理与自动恢复
       - Defense-in-Depth 安全模型 (白名单 + 沙箱)

    **多角色协作**:
    2. **MetaGPT** (MIT) - https://github.com/geekan/MetaGPT
       - 多角色 Agent 协作模式
       - 标准化 SOP (Standard Operating Procedure)
       - Stars: 45k+

    3. **OpenHands** (MIT) - https://github.com/All-Hands-AI/OpenHands
       - Agent-Computer Interface (ACI) 设计
       - 事件驱动架构
       - Stars: 38k+

    4. **SWE-agent** (MIT) - https://github.com/princeton-nlp/SWE-agent
       - 文件编辑接口
       - 错误修复循环
       - Stars: 13k+

    **子 Skill 来源**:
    - CodeSearcherSkill: code-graph-rag, Aider
    - CodeSelectorSkill: MetaGPT, Devika (自研规则引擎)
    - CodeAdapterSkill: astx, refactor
    - CodeAssemblerSkill: Aider, Copier
    - CodeVerifierSkill: mypy, ruff
  </code_sources>


  <!-- ======================================================
       0.1 v3.0 架构图 (Architecture)
  ====================================================== -->
  <architecture>
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    AI 代码工厂 v3.0 (集成版)                      │
    │                 借鉴 Anthropic Autonomous Coding                 │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  ┌───────────────────────────────────────────────────────────┐ │
    │  │                Session 1: INITIALIZER                      │ │
    │  │  ┌──────────────────────────────────────────────────────┐ │ │
    │  │  │ 1. 解析需求 (PromptStructurer)                       │ │ │
    │  │  │ 2. 搜索参考代码 (CodeSearcher)                       │ │ │
    │  │  │ 3. 生成 task_list.json (N 个子任务)                  │ │ │
    │  │  │ 4. 初始化项目结构 + Git                               │ │ │
    │  │  └──────────────────────────────────────────────────────┘ │ │
    │  └───────────────────────────────────────────────────────────┘ │
    │                              │                                  │
    │                              ▼ (3秒自动继续)                     │
    │                                                                 │
    │  ┌───────────────────────────────────────────────────────────┐ │
    │  │                Session 2+: FACTORY AGENT                   │ │
    │  │  ┌──────────────────────────────────────────────────────┐ │ │
    │  │  │                  6 阶段流水线 (每个任务)               │ │ │
    │  │  │                                                      │ │ │
    │  │  │   SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM │ │
    │  │  │     │        │        │         │         │        │  │ │ │
    │  │  │     ▼        ▼        ▼         ▼         ▼        ▼  │ │ │
    │  │  │  Searcher Selector Adapter Assembler Verifier Confirmer │ │
    │  │  │                                                      │ │ │
    │  │  │  ✅ 任务完成 → 更新 task_list.json → Git commit      │ │ │
    │  │  └──────────────────────────────────────────────────────┘ │ │
    │  └───────────────────────────────────────────────────────────┘ │
    │                                                                 │
    │  ┌───────────────────────────────────────────────────────────┐ │
    │  │                    安全模型 (Defense-in-Depth)              │ │
    │  │  Layer 1: 命令白名单 (security.py)                         │ │
    │  │  Layer 2: 文件系统限制 (project_dir only)                  │ │
    │  │  Layer 3: SoT 合规验证 (CodeVerifier)                      │ │
    │  └───────────────────────────────────────────────────────────┘ │
    │                                                                 │
    │  ┌───────────────────────────────────────────────────────────┐ │
    │  │                    持久化 (Persistence)                     │ │
    │  │  - task_list.json: 任务进度 (只能 pending → completed)     │ │
    │  │  - factory-progress.txt: 会话进度笔记                      │ │
    │  │  - Git commits: 每个任务一次提交                            │ │
    │  └───────────────────────────────────────────────────────────┘ │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
    ```

    **实现文件**:
    ```
    agents/skills/code_factory/
    ├── __init__.py      # 模块导出
    ├── factory.py       # 主编排器 (CodeFactory)
    ├── task_list.py     # 任务管理 (TaskList)
    ├── session.py       # 会话管理 (SessionManager)
    └── security.py      # 安全验证 (SecurityValidator)
    ```
  </architecture>


  <!-- ======================================================
       1. 核心使命 (Mission)
  ====================================================== -->
  <mission>
    作为代码组装器，通过"搜索→选型→适配→组装→验证"的流程生成代码。

    核心原则：
    - 🔍 搜索优先: 先找现有代码，不从零写
    - 🔧 适配改良: 基于参考代码修改，而非凭空生成
    - 🧩 组装集成: 将多个片段组装成完整功能
    - ✅ 标注来源: 所有代码都标注参考来源
    - 🔄 验证修复: 自动验证并修复问题

    预期收益：
    - 代码接受率: ~50% → >80% (+60%)
    - 幻觉发生率: ~30% → <5% (-83%)
    - 代码可追溯性: 0% → 100%
  </mission>


  <!-- ======================================================
       2. 子 Skill 依赖
  ====================================================== -->
  <sub_skills>
    <skill name="ai-ad-prompt-structurer" priority="0">
      职责: 将用户自然语言需求转换为结构化提示词
      来源: LangChain, DSPy, Guidance
      说明: 前置处理器，提高任务执行准确性
    </skill>

    <skill name="ai-ad-code-searcher" priority="1">
      职责: 从多个来源搜索参考代码
      来源: code-graph-rag, Aider
    </skill>

    <skill name="ai-ad-code-selector" priority="2">
      职责: 评估候选代码，选择最佳参考
      来源: MetaGPT, Devika (自研)
    </skill>

    <skill name="ai-ad-code-adapter" priority="3">
      职责: 适配参考代码到项目规范
      来源: astx, refactor
    </skill>

    <skill name="ai-ad-code-assembler" priority="4">
      职责: 组装成完整功能模块
      来源: Aider, Copier
    </skill>

    <skill name="ai-ad-code-verifier" priority="5">
      职责: 验证代码质量并自动修复
      来源: mypy, ruff
    </skill>

    <skill name="frontend-design" priority="3.5">
      职责: 前端 UI/UX 设计指导，确保设计系统一致性
      来源: shadcn/ui, Tailwind CSS, WCAG 2.1
      触发条件: scope="frontend" 或 scope="fullstack"
      核心功能:
        - 设计系统一致性检查 (颜色、间距、字体)
        - 组件复用性审查 (使用 COMPONENT_REGISTRY.md)
        - 响应式设计验证 (断点策略)
        - 可访问性检查 (a11y, WCAG 2.1 AA)
    </skill>
  </sub_skills>


  <!-- ======================================================
       2.1 AI 防幻觉原则 (Anti-Hallucination Principles)
       来源: MASTER.md v4.4 §7
  ====================================================== -->
  <anti_hallucination_principles>
    **核心原则 (AH-01 ~ AH-05)** - BLOCKING 级别

    每次代码生成前必须检查:

    | 原则 | 标题 | 规则 | 违反后果 |
    |------|------|------|---------|
    | AH-01 | 禁止假设数据一致 | 遇到数据缺失，标记"待确认"，禁止自动填充 | BLOCKING |
    | AH-02 | 禁止自动做管理裁决 | 禁止生成自动拒绝/暂停/终止/冻结代码 | BLOCKING |
    | AH-03 | 禁止引入 SoT 未定义概念 | 发现缺失 → 立即停止 → 询问用户 | BLOCKING |
    | AH-04 | 必须遵循 Phase 1 软性原则 | 仅提示+高亮+记录，不阻断 | WARNING |
    | AH-05 | 遇到歧义必须停止并询问 | 停止 → 列出歧义点 → 询问用户 | BLOCKING |

    **SoT 裁判链优先级** (高 → 低):
    ```
    MASTER.md v4.4 → DATA_SCHEMA.md v5.2 → STATE_MACHINE.md v2.6
    → BUSINESS_RULES.md v3.2 → API_SOT.md v9.0 → ERROR_CODES_SOT.md v2.1
    ```

    **常量白名单**:
    - 日报状态: 8 个 (raw_submitted...final_locked)
    - 业务层角色: 6 个 (ceo, project_owner, finance, pitcher, account_manager, admin) - PRD v2.2
    - 技术层角色: 4 个 (admin, finance, account_manager, media_buyer) - MASTER.md v4.6
    - 错误码前缀: 16 个 (VAL, AUTH, BIZ, DB, INT, SYS, FIN, RPT, ACC, PRJ, PIT, TOP, IMP, EXP, REC, SET)

    **Phase 1 行为约束**:
    - ✅ 允许: 记录、提示、高亮、统计
    - ❌ 禁止: 阻断、拒绝、暂停、冻结、自动批准/拒绝

    **知识库详情**: knowledge/anti-hallucination-rules.md
  </anti_hallucination_principles>

  <!-- ======================================================
       2.2 代码块优先原则 (Code Blocks First) [v3.4 新增]
       来源: knowledge/code-blocks-registry.md v2.0
  ====================================================== -->
  <code_blocks_first>
    **核心原则**: 代码块优先，减少重复编写

    ### 强制规则 (BLOCKING)

    | 规则 | 描述 | 违反后果 |
    |------|------|---------|
    | CB-001 | 生成代码前，必须先查询代码块注册表 | BLOCKING |
    | CB-002 | 如果存在匹配的代码块，必须使用代码块，禁止重新编写 | BLOCKING |
    | CB-003 | 代码块只能扩展，不能修改核心逻辑 | WARNING |
    | CB-004 | 使用代码块时必须标注 `# CodeBlock: {block_id}` | WARNING |

    ### 代码块优先查询流程

    ```
    用户需求 --> 提取关键词 --> 查询代码块注册表 --> 匹配成功?
                                                    |
                                               是 --> 使用代码块
                                               否 --> 进入搜索流程
    ```

    ### 代码块注册表索引 (16 个代码块)

    **前端代码块 (8个)**:
    | ID | 名称 | 关键词 |
    |----|------|--------|
    | CB-FE-001 | DataTable | 表格, 列表, table, 分页, 排序 |
    | CB-FE-002 | StatusBadge | 状态, 徽章, badge, 标签 |
    | CB-FE-003 | DataState | 加载, loading, empty, skeleton |
    | CB-FE-004 | ActionButtons | 操作, 按钮, action, 确认 |
    | CB-FE-005 | GlobalFilters | 筛选, filter, 日期, select |
    | CB-FE-006 | PageHeader | 页面标题, header, 面包屑 |
    | CB-FE-007 | ApprovalTimeline | 时间线, timeline, 审批流程 |
    | CB-FE-008 | FormDialog | 表单, form, 弹窗, dialog |

    **后端代码块 (8个)**:
    | ID | 名称 | 关键词 |
    |----|------|--------|
    | CB-BE-001 | Pagination | 分页, pagination, list |
    | CB-BE-002 | ResponseEnvelope | 响应, response, 封装 |
    | CB-BE-003 | ErrorCodes | 错误, error, 异常 |
    | CB-BE-004 | PermissionFilter | 权限, permission, 过滤, role |
    | CB-BE-005 | StateMachine | 状态机, state, transition |
    | CB-BE-006 | AuditLog | 审计, audit, 日志, history |
    | CB-BE-007 | LedgerEntry | 账本, ledger, 余额, balance |
    | CB-BE-008 | KPICalculator | KPI, ROAS, CPL, CPA, 指标 |

    **详细代码模板**: knowledge/code-blocks-registry.md
  </code_blocks_first>




  <!-- ======================================================
       3. 输入契约 (Input Contract)
  ====================================================== -->
  <input_contract>
    必填:
    {
      requirement: string,  // 需求描述
      module: "pitcher" | "finance" | "ad_account" | "project"  // 核心模块 (必填!)
    }

    可选:
    {
      scope: "backend" | "frontend" | "fullstack",  // 技术范围 (默认 fullstack)
      search_sources: {                              // 搜索来源
        local_project: boolean,                      // 默认 true
        code_library: boolean,                       // 默认 true
        github: boolean                              // 默认 false
      },
      auto_fix_iterations: number,                   // 自动修复次数 (默认 3)
      output_mode: "files" | "diff" | "preview"      // 输出模式 (默认 files)
    }

    模块边界定义 (STATE_MACHINE.md v2.6 §2 角色与模块权限):
    {
      pitcher: {
        可写表: [daily_reports, pitchers(仅自己)],
        只读表: [account_ownership_history, ad_accounts, projects],
        禁止表: [ledger, period_locks, recon_*]
      },
      finance: {
        可写表: [ledger(仅INSERT), period_locks, recon_*],
        只读表: [daily_reports, ad_accounts, agencies],
        禁止表: [pitchers(写)]
      },
      ad_account: {
        可写表: [ad_accounts, agencies, account_ownership_history, attribution_*, spend_*],
        只读表: [pitchers, projects],
        禁止表: [ledger, daily_reports(写), period_locks]
      },
      project: {
        可写表: [projects, clients],
        只读表: [pitchers, ad_accounts],
        禁止表: [ledger, daily_reports(写), account_ownership_history(写)]
      }
    }
  </input_contract>


  <!-- ======================================================
       4. 输出契约 (Output Contract)
  ====================================================== -->
  <output_contract>
    {
      success: boolean,
      data: {
        // Phase 1: 搜索结果
        search_results: {
          candidates: SearchCandidate[],
          search_stats: SearchStats
        },

        // Phase 2: 选型结果
        selection: {
          selected: SearchCandidate,
          scores: EvaluationScores,
          adaptation_plan: AdaptationPlan
        },

        // Phase 3: 适配结果
        adaptation: {
          adapted_files: AdaptedFile[],
          summary: AdaptationSummary
        },

        // Phase 4: 组装结果
        assembly: {
          module: AssembledModule,
          repo_map: RepoMap,
          integration_guide: IntegrationGuide
        },

        // Phase 5: 验证结果
        verification: {
          verified_files: VerifiedFile[],
          report: VerificationReport,
          remaining_issues: Issue[]
        },

        // 最终输出
        final_files: [
          {
            path: string,
            content: string,
            action: "create" | "modify",
            source_refs: string[]
          }
        ]
      },
      error: string | null
    }
  </output_contract>


  <!-- ======================================================
       5. 工作流程 (Workflow)
  ====================================================== -->
  <workflow>
    ┌─────────────────────────────────────────────────────────────────┐
    │                    代码工厂工作流程                               │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  输入: requirement = "添加日报批量导出 Excel 功能"               │
    │                                                                 │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 1: SEARCH (搜索)                                   │   │
    │  │ Skill: ai-ad-code-searcher                               │   │
    │  │ 来源: code-graph-rag, Aider                              │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 提取关键词: [导出, export, excel, 批量, batch]        │   │
    │  │ 2. 搜索本项目: → 找到 batch_import 可参考                │   │
    │  │ 3. 搜索代码资料库: → 找到 fastapi-excel 参考实现         │   │
    │  │ 4. 搜索 GitHub (可选): → 补充搜索                        │   │
    │  │                                                         │   │
    │  │ 输出: 候选代码列表 (按相关度排序)                        │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 2: SELECT (选型)                                   │   │
    │  │ Skill: ai-ad-code-selector                               │   │
    │  │ 来源: MetaGPT, Devika                                    │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 技术栈匹配度评估 (30%)                                │   │
    │  │ 2. 功能覆盖度评估 (30%)                                  │   │
    │  │ 3. 适配成本评估 (25%)                                    │   │
    │  │ 4. 代码质量评估 (15%)                                    │   │
    │  │                                                         │   │
    │  │ 输出: 最佳参考 + 适配方案                                │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 3: ADAPT (适配)                                    │   │
    │  │ Skill: ai-ad-code-adapter                                │   │
    │  │ 来源: astx, refactor                                     │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 技术栈适配 (Pydantic v2, SQLAlchemy 2.x)             │   │
    │  │ 2. 项目规范适配 (响应格式, 错误码, 命名)                 │   │
    │  │ 3. SoT 合规适配 (字段/状态/类型)                         │   │
    │  │ 4. 功能定制 (按需求调整)                                 │   │
    │  │                                                         │   │
    │  │ 输出: 适配后的代码 (标注所有改动点)                      │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 4: ASSEMBLE (组装)                                 │   │
    │  │ Skill: ai-ad-code-assembler + frontend-design            │   │
    │  │ 来源: Aider, Copier, shadcn/ui                           │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 生成 Repo Map (项目结构图)                            │   │
    │  │ 2. 后端组装: Schema → Service → Router                   │   │
    │  │ 3. 前端组装: Types → API → Hooks → Components → Page     │   │
    │  │ 4. [前端] 调用 frontend-design 进行设计审查              │   │
    │  │    - 设计系统一致性 (颜色/间距/字体)                     │   │
    │  │    - 组件复用性验证                                      │   │
    │  │    - 响应式布局检查                                      │   │
    │  │    - 可访问性 (a11y) 验证                                │   │
    │  │ 5. 生成集成指南                                          │   │
    │  │                                                         │   │
    │  │ 输出: 完整功能模块 + 设计审查报告                        │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 5: VERIFY (验证)                                   │   │
    │  │ Skill: ai-ad-code-verifier                               │   │
    │  │ 来源: mypy, ruff                                         │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 类型检查 (mypy/tsc)                                  │   │
    │  │ 2. Lint 检查 (ruff/eslint)                              │   │
    │  │ 3. SoT 合规检查                                          │   │
    │  │ 4. 自动修复 (最多 3 次迭代)                              │   │
    │  │                                                         │   │
    │  │ 失败 → 回到 ADAPT 修复                                   │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  ┌─────────────────────────────────────────────────────────┐   │
    │  │ Phase 6: CONFIRM (幻觉抑制最终确认) [v3.1 新增]          │   │
    │  │                                                         │   │
    │  │ 动作:                                                    │   │
    │  │ 1. 遍历生成的每个状态值 → 追溯到 STATE_MACHINE.md       │   │
    │  │ 2. 遍历生成的每个角色值 → 追溯到 frozenset 白名单       │   │
    │  │ 3. 遍历生成的每个字段 → 追溯到 DATA_SCHEMA.md           │   │
    │  │ 4. 遍历调用的每个 API → 确认在项目中存在                 │   │
    │  │ 5. 生成来源追溯报告 (source_traceability_report)        │   │
    │  │                                                         │   │
    │  │ 任何追溯失败 → BLOCKING，必须人工介入                    │   │
    │  └─────────────────────────────────────────────────────────┘   │
    │                              │                                  │
    │                              ▼                                  │
    │  输出:                                                          │
    │  - 可用代码文件                                                 │
    │  - 参考来源说明                                                 │
    │  - 改动说明                                                     │
    │  - 集成指南                                                     │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
  </workflow>


  <!-- ======================================================
       5.1 代码来源标注规范 (Source Annotation Standard) [v3.2 新增]
  ====================================================== -->
  <source_annotation_standard>
    所有生成的代码必须使用统一的来源标注格式:

    **标准格式**: `# SoT: {DOC}#{SECTION}`

    示例:
    ```python
    # SoT: STATE_MACHINE.md#daily_report
    class ReportStatus(str, Enum):
        DRAFT = "DRAFT"
        SUBMITTED = "SUBMITTED"
        ...

    # SoT: DATA_SCHEMA.md#daily_reports.amount
    amount: Decimal = Field(..., description="消耗金额")

    # SoT: BUSINESS_RULES.md#BR-RPT-001
    def validate_report_date(self, date: date) -> bool:
        ...

    # SoT: ERROR_CODES_SOT.md#RPT-001
    raise BusinessError(code="RPT-001", message="日报日期不能是未来")

    # SoT: API_SOT.md#POST /daily-reports
    @router.post("/daily-reports")
    async def create_daily_report(...):
        ...
    ```

    **TypeScript/TSX 格式**:
    ```typescript
    // SoT: STATE_MACHINE.md#daily_report
    type ReportStatus = "DRAFT" | "SUBMITTED" | "CONFIRMED";

    // SoT: API_SOT.md#GET /daily-reports
    export async function fetchDailyReports(): Promise<DailyReport[]> {
        ...
    }
    ```

    **禁止的格式** (会触发 SUP-007):
    - `# 来源: xxx` ❌
    - `// Source: xxx` ❌
    - `/* Ref: xxx */` ❌
    - 无来源标注 ❌

    **验证规则**:
    - 每个状态枚举必须有 SoT 标注
    - 每个业务规则实现必须有 BR-XXX 引用
    - 每个 API 端点必须有 API_SOT 引用
    - 每个错误码必须有 ERROR_CODES_SOT 引用
  </source_annotation_standard>


  <!-- ======================================================
       6. 禁止行为 (Forbidden Actions)
  ====================================================== -->
  <forbidden_actions>
    <!-- 模块边界规则 (STATE_MACHINE.md v2.6 §2) -->
    <forbidden id="CF-001">
      <action>不指定 module 参数直接生成代码</action>
      <correct_action>必须指定 module: pitcher | finance | ad_account | project</correct_action>
      <reason>模块边界是防止 AI 幻觉的核心约束</reason>
    </forbidden>

    <forbidden id="CF-002">
      <action>跨模块写入数据表</action>
      <correct_action>只能写入所属模块的可写表</correct_action>
      <reason>模块隔离是系统完整性的保障 (ZT-06)</reason>
    </forbidden>

    <forbidden id="CF-003">
      <action>在没有搜索的情况下直接生成代码</action>
      <correct_action>必须先执行 SEARCH Phase</correct_action>
      <reason>搜索优先是减少幻觉的核心原则</reason>
    </forbidden>

    <forbidden id="CF-004">
      <action>不标注代码来源</action>
      <correct_action>所有代码必须标注来源</correct_action>
      <reason>来源追溯是代码可信度的基础</reason>
    </forbidden>

    <forbidden id="CF-005">
      <action>发明新的字段/状态/错误码/角色</action>
      <correct_action>仅使用 SoT 白名单中已定义的值</correct_action>
      <reason>SoT 合规是系统一致性的保障 (ZT-02)</reason>
    </forbidden>

    <forbidden id="CF-006">
      <action>跳过验证阶段</action>
      <correct_action>必须执行 VERIFY Phase</correct_action>
      <reason>验证是代码质量的最后防线</reason>
    </forbidden>

    <forbidden id="CF-007">
      <action>无限循环修复</action>
      <correct_action>最多 3 次修复迭代，失败则人工介入</correct_action>
      <reason>避免死循环，及时发现根本问题</reason>
    </forbidden>

    <!-- 财务模块特殊规则 -->
    <forbidden id="CF-008">
      <action>UPDATE/DELETE ledger 表</action>
      <correct_action>只能 INSERT，错误修正使用冲正机制</correct_action>
      <reason>账本不可变是财务合规的基础 (ZT-01)</reason>
    </forbidden>

    <forbidden id="CF-009">
      <action>直接修改 balance 字段</action>
      <correct_action>通过 ledger 流水计算余额</correct_action>
      <reason>余额必须可追溯 (ZT-05)</reason>
    </forbidden>
  </forbidden_actions>


  <!-- ======================================================
       7. 使用示例 (Usage Examples)
  ====================================================== -->
  <usage>
    **Claude Code 使用方式** (推荐):

    示例 1: 基础使用
    「
    使用 ai-ad-code-factory，
    requirement = "添加日报批量导出 Excel 功能，支持按日期和状态筛选"
    」

    示例 2: 仅后端
    「
    使用 ai-ad-code-factory，
    requirement = "添加日报导出 API 接口"，
    scope = "backend"
    」

    示例 3: 仅搜索本项目
    「
    使用 ai-ad-code-factory，
    requirement = "参考现有批量导入实现批量导出"，
    search_sources = {
      local_project: true,
      code_library: false,
      github: false
    }
    」

    **Python 代码使用** (v3.0 新增):

    ```python
    from agents.skills.code_factory import CodeFactory, FactoryConfig
    from pathlib import Path

    # 创建配置
    config = FactoryConfig(
        project_dir=Path("./my_project"),
        max_iterations=10,      # 最多执行 10 轮
        auto_continue=True,     # 自动继续
        enable_security=True,   # 启用安全检查
        enable_sot_check=True,  # 启用 SoT 合规检查
    )

    # 创建工厂实例
    factory = CodeFactory(config)

    # 运行 (首次会进入初始化会话)
    result = factory.run(requirement="添加用户登录 API")

    # 检查结果
    if result["success"]:
        print(f"完成 {result['tasks_executed']} 个任务")
    else:
        print(f"错误: {result['error']}")

    # 恢复执行 (中断后再次运行)
    result = factory.run()  # 无需 requirement，自动从 task_list.json 恢复
    ```

    **快捷函数**:
    ```python
    from agents.skills.code_factory import run_factory

    result = run_factory(
        project_dir="./my_project",
        requirement="添加日报导出功能",
        max_iterations=5,
    )
    ```

    **单独使用组件**:
    ```python
    from agents.skills.code_factory import TaskList, SecurityValidator

    # 任务列表管理
    tasks = TaskList(Path("./my_project"))
    next_task = tasks.get_next_task()
    tasks.complete_task(next_task.id, output_files=["file.py"])

    # 安全验证
    validator = SecurityValidator(Path("./my_project"))
    result = validator.validate_command("rm -rf /")
    # result.allowed = False, result.reason = "命令 'rm -rf' 被禁止执行"
    ```
  </usage>


  <!-- ======================================================
       8. 版本记录 (Version Notes)
  ====================================================== -->
  <VERSION_NOTES>
    ### v3.5 (2026-01-02) - 前端设计集成版
    - 新增 `frontend-design` 子技能 (priority="3.5")
    - 触发条件: scope="frontend" 或 scope="fullstack"
    - Phase 4 ASSEMBLE 阶段新增前端设计审查:
      - 设计系统一致性检查 (颜色/间距/字体)
      - 组件复用性验证 (使用 COMPONENT_REGISTRY.md)
      - 响应式设计验证 (断点策略)
      - 可访问性检查 (a11y, WCAG 2.1 AA)
    - Profile 更新: 新增 Design-Aware 标签
    - 输出新增: 设计审查报告

    ### v3.4 (2025-12-24) - 代码块优先版
    - 新增 `<code_blocks_first>` 章节
    - 新增 Phase 0: CODE BLOCKS CHECK (代码块检查)
    - 集成代码块注册表 (knowledge/code-blocks-registry.md)
    - 16 个代码块索引 (前端 8 个 + 后端 8 个)
    - 强制规则: CB-001 ~ CB-004
    - 核心原则: 代码块优先，减少重复编写

    ### v3.3 (2025-12-24) - 防幻觉规则集成版
    - 新增 `<anti_hallucination_principles>` 章节
    - 集成 MASTER.md v4.4 §7 的 AI 防幻觉原则 (AH-01 ~ AH-05)
    - 添加 SoT 裁判链优先级说明
    - 添加常量白名单快速参考
    - 添加 Phase 1 行为约束
    - 知识库: knowledge/anti-hallucination-rules.md

    ### v3.2 (2025-12-22) - P2 优化版
    - 新增代码来源标注规范 (source_annotation_standard)
    - 统一格式: `# SoT: {DOC}#{SECTION}`
    - 新增 SUP-007 错误码 (非标准来源标注)

    ### v3.1 (2025-12-22) - P1 修复版
    - 新增 Phase 6: CONFIRM (幻觉抑制最终确认)
    - 6 阶段流水线: SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM
    - 来源追溯报告 (source_traceability_report)
    - 任何追溯失败为 BLOCKING 级别

    ### v3.0 (2025-12-18) - 自主编码集成版
    - **核心改进**: 集成 Anthropic autonomous-coding 架构
      - 双 Agent 模式 (Initializer + Factory)
      - task_list.json 持久化 (任务只能 pending → completed)
      - 会话管理与自动恢复 (Ctrl+C 中断后可继续)
      - Defense-in-Depth 安全模型

    - **新增组件**:
      - `factory.py` - 主编排器 (CodeFactory)
      - `task_list.py` - 任务管理 (TaskList)
      - `session.py` - 会话管理 (SessionManager)
      - `security.py` - 安全验证 (SecurityValidator)

    - **核心设计原则**:
      - 任务只能 `pending → completed`，禁止删除/修改
      - 每个会话使用新的上下文窗口
      - 3 秒自动继续延迟
      - 最多 3 次自动修复迭代

    ### v2.0 (2025-12-17)
    - 重构为组装器架构 (SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY)
    - 添加详细代码来源标注
    - 借鉴开源项目:
      - MetaGPT: 多角色协作
      - OpenHands: ACI 设计
      - SWE-agent: 错误修复循环
      - code-graph-rag: 语义搜索
      - Aider: Repo Map + 多文件编辑
      - astx/refactor: 代码转换
      - mypy/ruff: 代码验证

    ### v1.0 (2024-xx-xx)
    - 初始版本 (从零生成模式)
  </VERSION_NOTES>

</skill>
