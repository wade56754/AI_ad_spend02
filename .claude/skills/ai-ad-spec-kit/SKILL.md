---
name: ai-ad-spec-kit
version: "1.0"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-17
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - PROJECT_RULES.md v3.4
source_reference:
  - name: "GitHub Spec-Kit"
    url: "https://github.com/github/spec-kit"
    license: "MIT"
    adapted_features:
      - "Constitution → Specification → Planning → Tasks → Implementation 工作流"
      - "命令化接口设计"
      - "多 AI Agent 支持架构"
---

<skill>
<name>ai-ad-spec-kit</name>
<version>1.0</version>
<domain>AI_AD_SYSTEM / 规范驱动开发工具包</domain>
<profile>Spec-Driven / Multi-Phase / SoT-Aligned</profile>

<!-- ======================================================
     代码来源说明 (Source Attribution)
====================================================== -->
<source_attribution>
  本 Skill 借鉴自 GitHub 官方开源项目 Spec-Kit:
  - GitHub: https://github.com/github/spec-kit
  - License: MIT
  - 核心理念: 规范先行，代码后行

  适配改动:
  - 将 Constitution 概念对齐到 MASTER.md
  - 将 Specification 对齐到 SoT 文档体系
  - 添加 ASDD 4 层架构合规检查
  - 集成 OpenSpec 变更流程
</source_attribution>

<!-- ======================================================
     0. 核心使命 (Mission)
====================================================== -->
<mission>
  作为规范驱动开发的命令中心，提供从规范定义到代码实现的完整工作流。

  核心原则:
  - 📜 规范先行: 先写规范，再写代码
  - 🔗 SoT 对齐: 所有规范必须与 SoT 文档一致
  - 📝 任务分解: 大需求拆分为可验证的小任务
  - ✅ 持续验证: 每个阶段都有明确的验证点
</mission>

<!-- ======================================================
     1. 五阶段工作流 (5-Phase Workflow)
====================================================== -->
<workflow>
  <phase id="1-CONSTITUTION" command="/speckit.constitution">
    <description>
      定义或确认项目宪法级原则
      对应: MASTER.md + PROJECT_RULES.md
    </description>

    <actions>
      - 读取 docs/1.overview/MASTER.md
      - 读取 .claude/PROJECT_RULES.md
      - 确认业务边界和不变量
      - 确认永久禁止行为
      - 输出: constitution_context
    </actions>

    <output_format>
      ## 🏛️ Constitution 确认

      ### 业务边界
      - [从 MASTER.md 提取]

      ### 核心不变量
      - [从 PROJECT_RULES.md 提取]

      ### 禁止行为
      - [列出与当前需求相关的禁止项]

      ### 下一步
      - 执行 `/speckit.specify` 进入规范阶段
    </output_format>
  </phase>

  <phase id="2-SPECIFY" command="/speckit.specify">
    <description>
      描述需求规范，关注 "做什么"，而非 "怎么做"
      对应: SoT 文档层
    </description>

    <inputs>
      - requirement: 需求描述 (自然语言)
      - constitution_context: 上一阶段输出
    </inputs>

    <actions>
      - 识别涉及的业务域
      - 查询对应 SoT 文档:
        - STATE_MACHINE.md (状态相关)
        - DATA_SCHEMA.md (数据相关)
        - API_SOT.md (API 相关)
        - BUSINESS_RULES.md (规则相关)
      - 提取相关约束条件
      - 生成: specification_doc
    </actions>

    <output_format>
      ## 📋 Specification 规范

      ### 需求摘要
      [用户需求的结构化描述]

      ### 涉及 SoT 文档
      | 文档 | 版本 | 相关章节 |
      |------|------|---------|
      | STATE_MACHINE.md | v2.6 | §X |
      | DATA_SCHEMA.md | v5.2 | §X |

      ### 约束条件
      - [从 SoT 提取的约束]

      ### 成功标准
      - [可验证的成功条件]

      ### 下一步
      - 执行 `/speckit.plan` 进入规划阶段
    </output_format>
  </phase>

  <phase id="3-PLAN" command="/speckit.plan">
    <description>
      制定技术实现方案，关注架构和设计决策
      对应: Dev-Guides + Architecture 层
    </description>

    <inputs>
      - specification_doc: 上一阶段输出
    </inputs>

    <actions>
      - 分析技术栈约束 (FastAPI, Pydantic v2, SQLAlchemy 2.x)
      - 确定文件结构和模块划分
      - 设计 API 接口 (如适用)
      - 设计数据模型 (如适用)
      - 识别潜在风险
      - 生成: implementation_plan
    </actions>

    <output_format>
      ## 🗺️ Implementation Plan 实现方案

      ### 技术方案
      - 后端: [Router/Service/Schema 设计]
      - 前端: [Hook/API/Component 设计]

      ### 文件清单
      | 文件 | 操作 | 说明 |
      |------|------|------|
      | backend/routers/xxx.py | 新建/修改 | ... |

      ### 依赖关系
      ```
      [依赖图]
      ```

      ### 风险识别
      - [潜在风险及缓解措施]

      ### 下一步
      - 执行 `/speckit.tasks` 生成任务清单
    </output_format>
  </phase>

  <phase id="4-TASKS" command="/speckit.tasks">
    <description>
      将实现方案分解为可执行的小任务
      每个任务应该是可独立验证的单元
    </description>

    <inputs>
      - implementation_plan: 上一阶段输出
    </inputs>

    <actions>
      - 分解为原子任务 (每个 < 30 分钟)
      - 定义每个任务的验收标准
      - 排列任务优先级和依赖
      - 生成: task_list
    </actions>

    <output_format>
      ## ✅ Task List 任务清单

      ### 任务列表

      #### Task 1: [任务名称]
      - **文件**: `path/to/file.py`
      - **操作**: 新建/修改
      - **描述**: [具体操作]
      - **验收标准**: [如何验证完成]
      - **依赖**: [前置任务]

      #### Task 2: ...

      ### 执行顺序
      ```
      Task 1 → Task 2 → Task 3
                   ↘
                    Task 4
      ```

      ### 下一步
      - 执行 `/speckit.implement` 开始实现
      - 或执行 `/speckit.implement task=1` 实现特定任务
    </output_format>
  </phase>

  <phase id="5-IMPLEMENT" command="/speckit.implement">
    <description>
      执行任务，生成代码
      支持全量执行或单任务执行
    </description>

    <inputs>
      - task_list: 上一阶段输出
      - task: 可选，指定执行的任务编号
    </inputs>

    <actions>
      - 按顺序执行任务
      - 每个任务完成后验证
      - 调用 CodeFactory Skills (如已实现):
        - CodeSearcherSkill (搜索参考代码)
        - CodeAdapterSkill (适配代码)
        - CodeAssemblerSkill (组装代码)
        - CodeVerifierSkill (验证代码)
      - 生成: implementation_result
    </actions>

    <output_format>
      ## 🚀 Implementation Result 实现结果

      ### 已完成任务
      - [x] Task 1: [描述] ✅
      - [x] Task 2: [描述] ✅
      - [ ] Task 3: [描述] ⏳

      ### 生成的文件
      | 文件 | 状态 | 行数 |
      |------|------|------|
      | backend/routers/xxx.py | 新建 | 150 |

      ### 验证结果
      - mypy: ✅ 通过
      - ruff: ✅ 通过
      - SoT Guard: ✅ 通过

      ### 下一步
      - 运行测试: `pytest backend/tests/xxx`
      - 或继续: `/speckit.implement task=3`
    </output_format>
  </phase>
</workflow>

<!-- ======================================================
     2. 辅助命令 (Auxiliary Commands)
====================================================== -->
<auxiliary_commands>
  <command id="/speckit.clarify">
    <description>澄清规范中的模糊点</description>
    <usage>/speckit.clarify "状态转换规则不明确"</usage>
  </command>

  <command id="/speckit.analyze">
    <description>分析跨阶段一致性</description>
    <usage>/speckit.analyze</usage>
  </command>

  <command id="/speckit.checklist">
    <description>生成验证检查清单</description>
    <usage>/speckit.checklist</usage>
  </command>

  <command id="/speckit.status">
    <description>显示当前工作流状态</description>
    <usage>/speckit.status</usage>
  </command>
</auxiliary_commands>

<!-- ======================================================
     3. 与 ASDD 集成 (ASDD Integration)
====================================================== -->
<asdd_integration>
  <mapping>
    | Spec-Kit 阶段 | ASDD 对应层 | 文档 |
    |---------------|------------|------|
    | Constitution | Layer 1: Overview | MASTER.md, PROJECT_RULES.md |
    | Specification | Layer 2: SoT | STATE_MACHINE.md, DATA_SCHEMA.md, etc. |
    | Plan | Layer 3: Dev-Guides | API_DEVELOPMENT_FLOW.md |
    | Tasks | Layer 3: Dev-Guides | 任务清单 |
    | Implement | Layer 4: Architecture | 代码实现 |
  </mapping>

  <rules>
    - 所有规范必须与 SoT 文档一致
    - 涉及 SoT 变更必须走 OpenSpec 流程
    - 代码生成前必须通过 SoT Guard 验证
  </rules>
</asdd_integration>

<!-- ======================================================
     4. 使用示例 (Usage Examples)
====================================================== -->
<usage>
  示例 1: 完整工作流
  「
  我要添加日报批量导出 Excel 功能。

  /speckit.constitution
  [确认宪法约束]

  /speckit.specify
  [生成规范文档]

  /speckit.plan
  [制定技术方案]

  /speckit.tasks
  [分解任务清单]

  /speckit.implement
  [执行实现]
  」

  示例 2: 从中间阶段开始
  「
  我已经有需求规范了，直接进入规划阶段。

  /speckit.plan
  requirement = "添加日报批量导出，支持按状态和日期筛选，输出 xlsx 格式"
  」

  示例 3: 单任务执行
  「
  /speckit.implement task=2
  只执行任务清单中的第 2 个任务
  」
</usage>

<!-- ======================================================
     5. 版本记录 (Version Notes)
====================================================== -->
<VERSION_NOTES>
  ### v1.0 (2025-12-17)
  - 初始版本
  - 基于 GitHub Spec-Kit 适配
  - 五阶段工作流: Constitution → Specify → Plan → Tasks → Implement
  - 与 ASDD 4 层架构集成
  - 添加辅助命令: clarify, analyze, checklist, status
</VERSION_NOTES>

</skill>
