---
name: ai-ad-code-verifier
version: "1.0"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-17
baseline:
  - MASTER.md v3.5
  - CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
code_sources:
  - project: mypy
    github: https://github.com/python/mypy
    license: MIT
    borrowed_concepts:
      - 静态类型检查架构
      - 类型错误报告格式
  - project: ruff
    github: https://github.com/astral-sh/ruff
    license: MIT
    borrowed_concepts:
      - 快速 Linting 架构
      - 规则配置系统
      - 自动修复模式
  - project: static-analysis-tools
    github: https://github.com/analysis-tools-dev/static-analysis
    license: MIT
    borrowed_concepts:
      - 多工具集成策略
      - 报告聚合模式
---

<skill>
──────────────────────────────────────────────
  <name>ai-ad-code-verifier</name>
  <version>1.0</version>
  <domain>AI_AD_SYSTEM / 代码工厂 / 代码验证</domain>
  <profile>Code-Verifier / Multi-Check / Auto-Fix</profile>
──────────────────────────────────────────────


  <!-- ======================================================
       0. 代码来源说明 (Code Sources)
  ====================================================== -->
  <code_sources>
    本 Skill 的设计和实现借鉴了以下开源项目：

    1. **mypy** (MIT License)
       - GitHub: https://github.com/python/mypy
       - Stars: 18k+
       - 借鉴内容:
         - 静态类型检查架构
         - 类型错误报告格式
         - 渐进式类型检查策略

    2. **ruff** (MIT License)
       - GitHub: https://github.com/astral-sh/ruff
       - Stars: 32k+
       - 借鉴内容:
         - 快速 Linting 架构 (Rust 实现)
         - 规则配置系统
         - 自动修复模式

    3. **static-analysis-tools** (MIT License)
       - GitHub: https://github.com/analysis-tools-dev/static-analysis
       - 借鉴内容:
         - 多工具集成策略
         - 报告聚合模式

    验证工具链:
    - Python: mypy (类型) + ruff (lint) + pytest (测试)
    - TypeScript: tsc (类型) + eslint (lint) + jest (测试)
    - SoT: 自研合规检查器
  </code_sources>


  <!-- ======================================================
       1. 核心使命 (Mission)
  ====================================================== -->
  <mission>
    作为代码工厂的质量守门员，负责验证组装后的代码质量。

    核心原则:
    - ✅ 多维验证: 类型检查 + Lint + SoT 合规 + 测试
    - 🔄 自动修复: 对可自动修复的问题直接修复
    - 📊 报告聚合: 统一格式的验证报告
    - 🔁 迭代修复: 支持最多 3 次自动修复迭代
  </mission>


  <!-- ======================================================
       2. 输入契约 (Input Contract)
  ====================================================== -->
  <input_contract>
    必填:
    {
      assembled_files: AssembledFile[],  // 组装后的文件列表
      requirement: string                 // 原始需求描述
    }

    可选:
    {
      checks: {                          // 启用的检查项
        type_check: boolean,             // 类型检查 (默认 true)
        lint: boolean,                   // Lint 检查 (默认 true)
        sot_compliance: boolean,         // SoT 合规检查 (默认 true)
        test: boolean                    // 运行测试 (默认 false)
      },
      auto_fix: boolean,                 // 自动修复 (默认 true)
      max_fix_iterations: number,        // 最大修复迭代次数 (默认 3)
      strict_mode: boolean               // 严格模式 (默认 false)
    }
  </input_contract>


  <!-- ======================================================
       3. 输出契约 (Output Contract)
  ====================================================== -->
  <output_contract>
    {
      success: boolean,                  // 所有检查是否通过
      data: {
        verified_files: [                // 验证后的文件
          {
            path: string,
            content: string,             // 修复后的内容 (如有修复)
            status: "passed" | "fixed" | "failed",
            fixes_applied: number
          }
        ],
        verification_report: {
          summary: {
            total_issues: number,
            fixed: number,
            remaining: number,
            passed: boolean
          },
          by_check: {
            type_check: CheckResult,
            lint: CheckResult,
            sot_compliance: CheckResult,
            test: CheckResult
          }
        },
        remaining_issues: [              // 未解决的问题
          {
            file: string,
            line: number,
            check_type: string,
            severity: "error" | "warning",
            message: string,
            suggestion: string
          }
        ]
      },
      error: string | null
    }

    CheckResult:
    {
      passed: boolean,
      issues_found: number,
      issues_fixed: number,
      details: string[]
    }
  </output_contract>


  <!-- ======================================================
       4. 验证检查项 (Verification Checks)
  ====================================================== -->
  <verification_checks>
    <check id="TYPE_CHECK" priority="1">
      <name>类型检查</name>
      <tool>mypy (Python) / tsc (TypeScript)</tool>
      <description>检查类型标注是否正确</description>

      <common_issues>
        - 缺少类型标注
        - 类型不匹配
        - Optional 未处理
        - Any 类型滥用
      </common_issues>

      <auto_fix>
        - 添加缺失的类型标注 (基于推断)
        - 添加 Optional 包装
        - 添加类型转换
      </auto_fix>
    </check>

    <check id="LINT" priority="2">
      <name>代码风格检查</name>
      <tool>ruff (Python) / eslint (TypeScript)</tool>
      <description>检查代码风格和最佳实践</description>

      <common_issues>
        - 未使用的导入
        - 行过长
        - 命名不规范
        - 缺少文档字符串
      </common_issues>

      <auto_fix>
        - 移除未使用的导入
        - 格式化代码
        - 排序导入
      </auto_fix>
    </check>

    <check id="SOT_COMPLIANCE" priority="3">
      <name>SoT 合规检查</name>
      <tool>自研检查器</tool>
      <description>检查代码是否符合 SoT 文档定义</description>

      <checks>
        - 字段名是否在 DATA_SCHEMA 中
        - 状态值是否在 STATE_MACHINE 中
        - 错误码是否在 ERROR_CODES_SOT 中
        - 业务规则是否符合 BUSINESS_RULES
      </checks>

      <auto_fix>
        - 替换错误的字段名
        - 替换错误的状态值
        - 替换错误的错误码
      </auto_fix>
    </check>

    <check id="TEST" priority="4">
      <name>测试执行</name>
      <tool>pytest (Python) / jest (TypeScript)</tool>
      <description>运行单元测试验证功能正确性</description>

      <auto_fix>
        不支持自动修复，需要人工处理
      </auto_fix>
    </check>
  </verification_checks>


  <!-- ======================================================
       5. 修复迭代流程 (Fix Iteration)
  ====================================================== -->
  <fix_iteration>
    Phase 1: INITIAL_CHECK
      - 运行所有启用的检查
      - 收集问题列表

    Phase 2: AUTO_FIX (if auto_fix=true)
      - 对可自动修复的问题应用修复
      - 记录修复操作

    Phase 3: RE_CHECK
      - 重新运行检查
      - 更新问题列表

    Phase 4: ITERATE_OR_REPORT
      - 如果还有问题且未达到 max_fix_iterations:
        - 回到 Phase 2
      - 否则:
        - 生成最终报告

    最大迭代: 3 次 (可配置)
  </fix_iteration>


  <!-- ======================================================
       6. SoT 合规检查器 (自研)
  ====================================================== -->
  <sot_compliance_checker>
    检查逻辑:

    1. 字段检查 (DATA_SCHEMA)
       - 提取代码中使用的字段名
       - 与 DATA_SCHEMA 对比
       - 标记不存在的字段

    2. 状态检查 (STATE_MACHINE)
       - 提取代码中的状态常量
       - 与 STATE_MACHINE 8 状态对比
       - 标记不存在的状态

    3. 错误码检查 (ERROR_CODES_SOT)
       - 提取代码中的错误码
       - 与 ERROR_CODES_SOT 对比
       - 标记自定义的错误码

    4. 规则检查 (BUSINESS_RULES)
       - 检查是否实现了必要的业务规则
       - 标记遗漏的规则
  </sot_compliance_checker>


  <!-- ======================================================
       7. 禁止行为 (Forbidden Actions)
  ====================================================== -->
  <forbidden_actions>
    <forbidden id="VER-001">
      <action>跳过类型检查</action>
      <correct_action>必须通过类型检查或明确标注 type: ignore</correct_action>
    </forbidden>

    <forbidden id="VER-002">
      <action>忽略 SoT 合规问题</action>
      <correct_action>必须使用 SoT 中定义的字段/状态/错误码</correct_action>
    </forbidden>

    <forbidden id="VER-003">
      <action>自动修复超过 3 次仍失败时继续</action>
      <correct_action>返回失败报告，需要人工介入</correct_action>
    </forbidden>

    <forbidden id="VER-004">
      <action>修改测试以通过验证</action>
      <correct_action>修复代码，而非修改测试</correct_action>
    </forbidden>
  </forbidden_actions>


  <!-- ======================================================
       8. 使用示例 (Usage Examples)
  ====================================================== -->
  <usage>
    示例 1: 基础验证
    「
    使用 ai-ad-code-verifier，
    assembled_files = [组装后的文件列表],
    requirement = "添加日报批量导出 Excel 功能"
    」

    示例 2: 严格模式 (无自动修复)
    「
    使用 ai-ad-code-verifier，
    assembled_files = [...],
    requirement = "...",
    auto_fix = false,
    strict_mode = true
    」

    示例 3: 包含测试执行
    「
    使用 ai-ad-code-verifier，
    assembled_files = [...],
    requirement = "...",
    checks = {
      type_check: true,
      lint: true,
      sot_compliance: true,
      test: true
    }
    」
  </usage>


  <!-- ======================================================
       9. 版本记录 (Version Notes)
  ====================================================== -->
  <VERSION_NOTES>
    ### v1.0 (2025-12-17)
    - 初始版本
    - 四维验证: 类型/Lint/SoT合规/测试
    - 借鉴 mypy 的类型检查架构
    - 借鉴 ruff 的快速 Linting 和自动修复
    - 自研 SoT 合规检查器
    - 最多 3 次自动修复迭代
  </VERSION_NOTES>

</skill>
