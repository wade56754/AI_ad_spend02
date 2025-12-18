---
name: ai-ad-code-verifier
version: "2.0"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-18
baseline:
  - MASTER.md v3.5
  - CODE_FACTORY_REFERENCE_PROJECTS.md v1.0
code_sources:
  - project: HallOumi
    github: https://github.com/vectara/hallucination-leaderboard
    license: Apache-2.0
    borrowed_concepts:
      - 幻觉检测理念
      - 事实验证方法论
  - project: tree-sitter
    github: https://github.com/tree-sitter/tree-sitter
    license: MIT
    borrowed_concepts:
      - AST 解析策略
      - 多语言支持架构
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
  - project: Qodo Cover
    github: https://github.com/qodo-ai/qodo-cover
    license: AGPL-3.0
    borrowed_concepts:
      - 测试生成策略
      - 覆盖率分析方法
---

<skill>
──────────────────────────────────────────────
  <name>ai-ad-code-verifier</name>
  <version>2.0</version>
  <domain>AI_AD_SYSTEM / 代码工厂 / 代码验证</domain>
  <profile>Enhanced-Verifier / Anti-Hallucination / Auto-Fix</profile>
──────────────────────────────────────────────


  <!-- ======================================================
       0. 核心架构 (Architecture)
  ====================================================== -->
  <architecture>
    增强版验证器采用 5 层验证流水线:

    ```
    ┌─────────────────────────────────────────────────────────┐
    │                  EnhancedCodeVerifier                    │
    │                    (主编排器)                            │
    └───────────────────────┬─────────────────────────────────┘
                            │
    ┌───────────────────────▼─────────────────────────────────┐
    │  Layer 1: HallucinationDetector (优先级 10)              │
    │  - 检测 AI 幻觉: 不存在的 API/函数/模块                   │
    │  - 验证导入是否真实存在                                   │
    │  - 检查 API 端点是否在项目中定义                          │
    └───────────────────────┬─────────────────────────────────┘
                            │
    ┌───────────────────────▼─────────────────────────────────┐
    │  Layer 2: ASTVerifier (优先级 20)                        │
    │  - 语法正确性验证                                        │
    │  - 代码结构完整性                                        │
    │  - 括号/缩进匹配                                         │
    └───────────────────────┬─────────────────────────────────┘
                            │
    ┌───────────────────────▼─────────────────────────────────┐
    │  Layer 3: SpecComplianceVerifier (优先级 30)             │
    │  - SoT 合规验证                                          │
    │  - 状态机 8 状态验证                                     │
    │  - 角色/字段/错误码验证                                   │
    └───────────────────────┬─────────────────────────────────┘
                            │
    ┌───────────────────────▼─────────────────────────────────┐
    │  Layer 4: IntegrationVerifier (优先级 40)                │
    │  - 导入路径验证                                          │
    │  - 依赖可用性检查                                        │
    │  - 循环导入检测                                          │
    └───────────────────────┬─────────────────────────────────┘
                            │
    ┌───────────────────────▼─────────────────────────────────┐
    │  Layer 5: TestVerifier (优先级 50)                       │
    │  - 测试文件存在性                                        │
    │  - 测试覆盖率检查                                        │
    │  - 测试质量验证                                          │
    └─────────────────────────────────────────────────────────┘
    ```

    实现文件位置:
    - `agents/skills/verifiers/__init__.py` - 模块导出
    - `agents/skills/verifiers/base.py` - 基础类型和接口
    - `agents/skills/verifiers/hallucination_detector.py` - 幻觉检测
    - `agents/skills/verifiers/ast_verifier.py` - AST 验证
    - `agents/skills/verifiers/spec_compliance_verifier.py` - SoT 合规
    - `agents/skills/verifiers/integration_verifier.py` - 集成验证
    - `agents/skills/verifiers/test_verifier.py` - 测试验证
    - `agents/skills/verifiers/enhanced_verifier.py` - 主编排器
  </architecture>


  <!-- ======================================================
       1. 核心使命 (Mission)
  ====================================================== -->
  <mission>
    作为代码工厂的质量守门员，防止 AI 幻觉并确保代码质量。

    核心原则:
    - 🎯 防幻觉: 检测 AI 生成的虚假 API/函数/模块
    - ✅ 多维验证: 语法 + SoT 合规 + 集成 + 测试
    - 🔄 自动修复: 对可自动修复的问题直接修复
    - 📊 报告聚合: 统一格式的验证报告
    - 🔁 迭代修复: 支持最多 3 次自动修复迭代
  </mission>


  <!-- ======================================================
       2. 错误码体系 (Error Codes)
  ====================================================== -->
  <error_codes>
    幻觉检测 (HALL):
    - HALL-001: 导入不存在的模块
    - HALL-002: 导入不存在的名称
    - HALL-003: 调用不存在的第三方函数
    - HALL-004: 调用不存在的项目函数
    - HALL-005: 使用不存在的 API 端点
    - HALL-006: 引用不存在的项目模块
    - HALL-007: 导入不存在的项目对象

    语法验证 (SYN):
    - SYN-001: 语法错误
    - SYN-002: 意外的 EOF
    - SYN-003: 缩进错误
    - SYN-004: 括号不匹配
    - SYN-005: 引号不匹配
    - SYN-006: 混合缩进
    - SYN-007: 字符串多行未闭合
    - SYN-008: TypeScript 语法错误

    结构验证 (STR):
    - STR-001: 函数体为空
    - STR-002: 类体为空
    - STR-003: 缺少函数定义
    - STR-004: 缺少类定义
    - STR-005: 代码被截断
    - STR-006: 导入后无代码
    - STR-007: 缺少返回语句

    SoT 合规 (SOT):
    - SOT-001: 使用未定义的状态
    - SOT-002: 使用旧状态名 (如 DRAFT)
    - SOT-003: 使用非法角色
    - SOT-004: 使用旧角色名
    - SOT-005: 使用未知字段
    - SOT-006: 使用非标准错误码
    - SOT-007: 使用未知错误前缀
    - SOT-008: 直接修改 balance

    集成验证 (INT):
    - INT-001: 未识别的模块
    - INT-002: 相对导入路径不存在
    - INT-003: 第三方库未安装
    - INT-004: 项目模块不存在
    - INT-005: 潜在循环导入
    - INT-006: 导入分组缺少空行
    - INT-007: 使用 star import
    - INT-008: 代码位置不正确

    测试验证 (TST):
    - TST-001: 缺少测试文件
    - TST-002: 缺少测试覆盖
    - TST-003: 测试失败
    - TST-004: 测试缺少断言
    - TST-005: 空测试函数
    - TST-006: 测试名称不够描述性
  </error_codes>


  <!-- ======================================================
       3. 输入契约 (Input Contract)
  ====================================================== -->
  <input_contract>
    必填:
    {
      assembled_files: AssembledFile[],  // 组装后的文件列表
      requirement: string                 // 原始需求描述
    }

    可选:
    {
      config: {
        enable_hallucination: boolean,   // 幻觉检测 (默认 true)
        enable_ast: boolean,             // AST 验证 (默认 true)
        enable_spec: boolean,            // SoT 合规 (默认 true)
        enable_integration: boolean,     // 集成验证 (默认 true)
        enable_test: boolean,            // 测试验证 (默认 false)
        auto_fix: boolean,               // 自动修复 (默认 true)
        max_fix_iterations: number,      // 最大修复次数 (默认 3)
        strict_mode: boolean,            // 严格模式 (默认 false)
        run_tests: boolean               // 运行测试 (默认 false)
      },
      context: {                         // 验证上下文
        valid_states: string[],          // 合法状态列表
        valid_roles: string[],           // 合法角色列表
        valid_error_codes: string[],     // 合法错误码列表
        existing_modules: string[],      // 项目现有模块
        existing_functions: string[],    // 项目现有函数
        existing_endpoints: string[]     // 项目现有 API 端点
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
        verified_files: [
          {
            path: string,
            original_content: string,
            verified_content: string,
            status: "passed" | "fixed" | "failed" | "skipped",
            issues: VerifyIssue[],
            fixes_applied: number
          }
        ],
        summary: {
          total_files: number,
          passed: number,
          fixed: number,
          failed: number,
          skipped: number
        },
        all_issues: VerifyIssue[]
      },
      error: string | null
    }

    VerifyIssue:
    {
      file_path: string,
      line: number,
      column: number,
      category: string,           // "hallucination" | "syntax" | ...
      severity: "error" | "warning" | "info",
      code: string,               // "HALL-001", "SOT-003", etc.
      message: string,
      suggestion: string,
      evidence: string | null,
      auto_fixable: boolean,
      fix_applied: boolean
    }
  </output_contract>


  <!-- ======================================================
       5. 使用示例 (Usage Examples)
  ====================================================== -->
  <usage>
    示例 1: Python 代码使用
    ```python
    from agents.skills.verifiers import (
        EnhancedCodeVerifier,
        VerifyContext,
        VerifierConfig,
    )
    from pathlib import Path

    # 创建上下文
    context = VerifyContext(
        project_root=Path("/path/to/project"),
        requirement="实现用户注册 API",
        valid_states={"pending", "active", "disabled"},
        valid_roles={"admin", "finance", "media_buyer"},
    )

    # 配置验证器
    config = VerifierConfig(
        enable_hallucination=True,
        enable_ast=True,
        enable_spec=True,
        enable_integration=True,
        enable_test=False,
        auto_fix=True,
    )

    # 创建验证器
    verifier = EnhancedCodeVerifier(context, config)

    # 验证文件
    result = verifier.verify_file("path/to/file.py", file_content)

    # 检查结果
    if result.status == "passed":
        print("验证通过!")
    elif result.status == "fixed":
        print(f"已自动修复 {result.fixes_applied} 个问题")
        print(result.verified_content)
    else:
        print("验证失败:")
        for issue in result.issues:
            print(f"  [{issue.code}] {issue.message}")
    ```

    示例 2: 快速验证
    ```python
    from agents.skills.verifiers import quick_verify

    result = quick_verify(
        file_path="backend/services/user_service.py",
        content=code_content,
        project_root="/path/to/project",
    )

    if result["passed"]:
        print("验证通过")
    else:
        for error in result["errors"]:
            print(f"错误: {error['message']}")
    ```

    示例 3: 批量验证并生成报告
    ```python
    from agents.skills.verifiers import create_verifier_from_project

    # 从项目自动加载 SoT 定义
    verifier = create_verifier_from_project(
        project_root="/path/to/project",
        requirement="重构用户模块",
    )

    # 批量验证
    files = [
        ("file1.py", content1),
        ("file2.py", content2),
    ]
    results = verifier.verify_files(files)

    # 生成 Markdown 报告
    report = verifier.generate_report(results, format="markdown")
    print(report)
    ```
  </usage>


  <!-- ======================================================
       6. SoT 合规验证详情
  ====================================================== -->
  <sot_compliance_details>
    日报 8 状态机 (STATE_MACHINE.md v2.6):
    ```
    合法状态:
    - raw_submitted
    - trend_pending
    - trend_ok
    - trend_flagged
    - trend_resolved
    - final_pending
    - final_confirmed
    - final_locked

    已废弃状态 (会触发 SOT-002):
    - draft
    - pending_review
    - approved
    - rejected
    ```

    充值状态机:
    ```
    合法状态: pending, approved, rejected, settled
    ```

    转账状态机:
    ```
    合法状态: pending, completed, failed, cancelled
    ```

    合法角色 (仅 5 个):
    ```
    - admin           # 系统管理员
    - finance         # 财务
    - data_operator   # 数据运营
    - account_manager # 账户管理员
    - media_buyer     # 广告投手

    已废弃角色 (会触发 SOT-004):
    - super_admin → admin
    - accountant → finance
    - operator → data_operator
    ```

    错误码前缀 (ERROR_CODES_SOT.md):
    ```
    - VAL: 验证错误
    - AUTH: 认证/授权错误
    - BIZ: 业务逻辑错误
    - DB: 数据库错误
    - INT: 集成错误
    - SYS: 系统错误
    ```
  </sot_compliance_details>


  <!-- ======================================================
       7. 禁止行为 (Forbidden Actions)
  ====================================================== -->
  <forbidden_actions>
    <forbidden id="VER-001">
      <action>忽略幻觉检测结果</action>
      <correct_action>必须修复所有 HALL-xxx 错误</correct_action>
    </forbidden>

    <forbidden id="VER-002">
      <action>使用已废弃的状态/角色</action>
      <correct_action>使用 SoT 定义的合法值</correct_action>
    </forbidden>

    <forbidden id="VER-003">
      <action>自动修复超过 3 次仍失败时继续</action>
      <correct_action>返回失败报告，需要人工介入</correct_action>
    </forbidden>

    <forbidden id="VER-004">
      <action>修改测试以通过验证</action>
      <correct_action>修复代码，而非修改测试</correct_action>
    </forbidden>

    <forbidden id="VER-005">
      <action>直接修改 balance 字段</action>
      <correct_action>通过 ledger_entries 记录</correct_action>
    </forbidden>
  </forbidden_actions>


  <!-- ======================================================
       8. 版本记录 (Version Notes)
  ====================================================== -->
  <VERSION_NOTES>
    ### v2.0 (2025-12-18)
    - 新增幻觉检测层 (HallucinationDetector)
      - 检测不存在的 API/函数/模块
      - 验证第三方库导入
      - 检查项目内部引用
    - 增强 AST 验证
      - 支持 Python 和 TypeScript
      - 结构完整性检查
      - 括号/缩进/引号匹配
    - 增强 SoT 合规检查
      - 日报 8 状态机验证
      - 充值/转账状态机验证
      - 角色/错误码验证
      - balance 直接修改检测
    - 新增集成验证层
      - 导入路径验证
      - 循环导入检测
      - 第三方依赖检查
    - 新增测试验证层
      - 测试文件存在性检查
      - 测试覆盖率分析
      - 测试质量检查
    - 统一错误码体系
    - 支持多种报告格式 (text/json/markdown)

    ### v1.0 (2025-12-17)
    - 初始版本
    - 四维验证: 类型/Lint/SoT合规/测试
    - 借鉴 mypy 的类型检查架构
    - 借鉴 ruff 的快速 Linting 和自动修复
    - 自研 SoT 合规检查器
    - 最多 3 次自动修复迭代
  </VERSION_NOTES>

</skill>
