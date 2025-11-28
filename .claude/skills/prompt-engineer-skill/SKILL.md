---
name: prompt-engineer
version: 2.1
status: ready_for_production
layer: agent
owner: wade
last_reviewed: 2025-11-28
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - Dev-Guides Freeze vFinal
  - Architecture Freeze v1.0
  - Infrastructure Freeze v1.0
  - Agent Freeze v1.0
---

# Prompt Engineering Skill v2.1

专为 AI_ad_spend02 项目设计的提示词工程技能，遵循 Claude 官方最佳实践和 ASDD 6 层规范。

---

## 调用接口

```xml
<invoke_skill name="prompt-engineer" version="2.1">
  <goal>[优化目标：使提示词符合 ASDD 规范、达到 ready_for_production]</goal>
  <context>[项目背景、baseline、层级状态]</context>
  <raw_prompt>[待优化的原始提示词或 SKILL 文件内容]</raw_prompt>
</invoke_skill>
```

---

## 核心原则

| 原则 | 说明 | 强制级别 |
|------|------|----------|
| **XML 标签结构化** | 所有复杂提示词必须使用闭合的 XML 标签组织 | P0 |
| **角色明确** | 通过 `<system>` 定义专业角色及其协作关系 | P0 |
| **示例驱动** | 提供 3-5 个具体的 AI_ad_spend02 场景示例 | P1 |
| **渐进式复杂度** | 简单任务直接指令，复杂任务链式拆解 | P1 |
| **可追溯性** | 所有提示词必须标注 baseline 和版本号 | P0 |
| **确定性输出** | 明确输入/输出格式，消除歧义 | P0 |

---

## 优化 Pipeline（6 步链式流程）

```xml
<chain name="prompt-engineering-pipeline" total_steps="6">

  <step order="1" name="diagnose">
    <input>用户提供的原始提示词</input>
    <task>分析问题类别（STRUCT/ROLE/EXAMPLE/AMBIG/SCOPE/CHAIN）</task>
    <output format="table">
      | 问题 ID | 类别 | 位置 | 描述 | 严重度 |
    </output>
  </step>

  <step order="2" name="design" depends_on="1">
    <input>步骤1的诊断报告</input>
    <task>设计优化后的 XML 结构骨架</task>
    <output format="xml">结构化的提示词骨架（不含内容）</output>
  </step>

  <step order="3" name="expand" depends_on="2">
    <input>步骤2的 XML 骨架</input>
    <task>填充内容：Few-shot 示例、具体指令、边界条件</task>
    <output format="xml">完整的提示词草稿</output>
  </step>

  <step order="4" name="constraints" depends_on="3">
    <input>步骤3的草稿</input>
    <task>添加 ASDD 约束：baseline、版本号、SoT 引用</task>
    <output format="xml">带约束的提示词</output>
  </step>

  <step order="5" name="audit_fix_loop" depends_on="4">
    <input>步骤4的提示词</input>
    <task>审计 P0/P1/P2 问题并自动修复，循环直到无 P0/P1</task>
    <output format="yaml">
      issues_found: [列表]
      issues_fixed: [列表]
      remaining_p2: [列表]
      health_score: [0-100]
    </output>
  </step>

  <step order="6" name="final_prompt" depends_on="5">
    <input>步骤5的审计结果</input>
    <task>输出 ready_for_production 的最终提示词</task>
    <output format="markdown">完整的优化后提示词文件</output>
  </step>

  <final_output>
    优化后的提示词（Markdown 格式），包含：
    - YAML frontmatter（version, status, baseline）
    - 结构化 XML 标签
    - Few-shot 示例
    - 审计报告摘要
  </final_output>

</chain>
```

---

## 问题诊断分类

| 类别 | 代码 | 描述 | 修复策略 |
|------|------|------|----------|
| **结构问题** | STRUCT | XML 标签未闭合、嵌套错误、缺少分隔 | 重构 XML 结构 |
| **角色问题** | ROLE | 缺少角色定义或协作关系不清 | 添加 `<system>` + 角色矩阵 |
| **示例问题** | EXAMPLE | 示例不足或过于抽象 | 添加 AI_ad_spend02 具体场景 |
| **歧义问题** | AMBIG | 判断标准不明确、边界条件缺失 | 添加 `<constraints>` + 边界表 |
| **范围问题** | SCOPE | 输入/输出未定义 | 添加 `<input>/<output>` 标签 |
| **链式问题** | CHAIN | 复杂任务未拆解、步骤依赖不清 | 拆解为 `<chain>` 结构 |

---

## 角色协作模型

本 Skill 内置 4 个子角色，按顺序协作：

```xml
<roles collaboration="sequential">
  <role name="architect" order="1">
    <responsibility>设计提示词的 XML 结构、链式步骤、标签层级</responsibility>
    <output>结构骨架</output>
  </role>

  <role name="writer" order="2">
    <responsibility>填充内容、编写示例、描述约束</responsibility>
    <output>完整草稿</output>
  </role>

  <role name="reviewer" order="3">
    <responsibility>审计 P0/P1/P2 问题，输出诊断报告</responsibility>
    <output>审计报告</output>
  </role>

  <role name="fixer" order="4">
    <responsibility>自动修复问题，确保 health_score >= 90</responsibility>
    <output>ready_for_production 版本</output>
  </role>
</roles>
```

---

## Few-Shot 示例（AI_ad_spend02 场景）

### 示例 1：优化日报审核提示词（Good）

**原始提示词**：
```
审核这份日报，检查数据是否正常。
```

**优化后提示词**：
```xml
<system>
你是一位数据操作员（data_operator），负责审核投手提交的每日广告报告。
你的工作原则是：遵循 STATE_MACHINE.md v2.6 的 8 状态流转规则。
</system>

<task>
审核日报 ID: {{report_id}}，执行趋势风控检查。

<objectives priority="required">
1. 验证 raw_submitted 状态合法性
2. 执行 TF-001/002/003 风控规则
3. 输出 trend_ok 或 trend_flagged 决策
</objectives>
</task>

<context>
<baseline>STATE_MACHINE.md v2.6, BUSINESS_RULES.md v3.1</baseline>
<current_state>raw_submitted</current_state>
<allowed_transitions>["trend_pending"]</allowed_transitions>
</context>

<rules>
<must>
- 检查 conversions_raw 与昨日对比（TF-001: < 50% 触发异常）
- 检查 raw_spend 与昨日对比（TF-003: > 200% 触发异常）
</must>
<must_not>
- 禁止跳过 trend_pending 直接进入 final_pending
- 禁止审核自己提交的日报（SOD 规则）
</must_not>
</rules>

<output_format>
{
  "decision": "trend_ok" | "trend_flagged",
  "triggered_rules": ["TF-001", ...] | [],
  "trend_flag_reason": "..." | null,
  "next_state": "trend_ok" | "trend_flagged"
}
</output_format>
```

**优化原因**：
- 添加了明确的角色定义（data_operator）
- 引用了 SoT 版本号（STATE_MACHINE.md v2.6）
- 定义了具体的风控规则（TF-001/002/003）
- 明确了 JSON 输出格式

---

### 示例 2：缺少结构的提示词（Bad）

**原始提示词**：
```
帮我处理充值申请，检查金额是否正确，然后审批或拒绝。
要符合财务规则，不要违反SOD。
```

**问题诊断**：
| 问题 ID | 类别 | 描述 |
|---------|------|------|
| D-001 | STRUCT | 无 XML 标签结构 |
| D-002 | ROLE | 未定义角色（finance? data_operator?）|
| D-003 | AMBIG | "金额是否正确"标准不明确 |
| D-004 | SCOPE | 未定义输入（充值申请 ID）和输出格式 |
| D-005 | CHAIN | 多步骤任务（检查→审批）未拆解 |

---

## 提示词模板

### 模板 1：ASDD 文档治理提示词

```xml
<system>
你是一位资深技术文档架构师，严格遵循 ASDD 6 层文档体系。
你的工作原则是：SoT 优先、可追溯、零冲突。
</system>

<task>
[文档治理任务描述]

<objectives priority="required">
1. [目标1]
2. [目标2]
</objectives>
</task>

<asdd_context>
<baseline>
MASTER.md v3.5, SoT Freeze v2.6, Dev-Guides Freeze vFinal,
Architecture Freeze v1.0, Infrastructure Freeze v1.0, Agent Freeze v1.0
</baseline>

<layers>
| Layer | Name | Version | Status |
|-------|------|---------|--------|
| 1 | Overview | Freeze v1.0 | readonly |
| 2 | SoT | Freeze v2.6 | readonly |
| 3 | Dev-Guides | Freeze vFinal | readonly |
| 4 | Architecture | Freeze v1.0 | readonly |
| 5 | Infrastructure | Freeze v1.0 | readonly |
| 6 | Agent | Freeze v1.0 | readonly |
</layers>
</asdd_context>

<rules>
<must>
- 引用 SoT 文档时必须标注版本号
- 修改非 freeze 文件时必须更新 frontmatter
</must>
<must_not>
- 禁止修改任何 frozen 状态的文档内容
- 禁止创建与 SoT 冲突的定义
</must_not>
</rules>

<output_format>
<in_files>[写入文件的路径和内容摘要]</in_files>
<in_conversation>[对话中输出的报告]</in_conversation>
</output_format>
```

### 模板 2：状态机操作提示词

```xml
<system>
你是一位业务流程控制器，负责执行 STATE_MACHINE.md v2.6 定义的状态流转。
</system>

<task>
执行 {{entity}}.status 从 {{current_state}} 到 {{target_state}} 的流转。
</task>

<state_context>
<entity>{{daily_reports | topup_requests | ...}}</entity>
<current_state>{{当前状态}}</current_state>
<target_state>{{目标状态}}</target_state>
<operator_role>{{media_buyer | data_operator | finance | admin}}</operator_role>
</state_context>

<validation>
<check name="whitelist">目标状态是否在 TRANSITIONS[current_state] 中</check>
<check name="role">操作者角色是否有权限执行此流转</check>
<check name="sod">是否违反职责分离规则</check>
</validation>

<output_format>
{
  "allowed": true | false,
  "reason": "..." | null,
  "error_code": null | "STATE_400" | "AUTH_500" | "BIZ_001"
}
</output_format>
```

---

## 验证清单

优化后的提示词必须通过以下检查：

| 检查项 | P0 | P1 | P2 |
|--------|----|----|-----|
| XML 标签全部闭合 | ✓ | | |
| 定义了明确的角色 | ✓ | | |
| 包含 baseline 声明 | ✓ | | |
| 输入/输出格式明确 | ✓ | | |
| 提供了 3+ 示例 | | ✓ | |
| 处理了边界条件 | | ✓ | |
| 引用了正确的 SoT 版本 | | ✓ | |
| 有 frontmatter | | | ✓ |

**通过标准**: P0 = 0, P1 = 0, health_score >= 90

---

## Frontmatter 标准

所有提示词/Skill 文档必须包含：

```yaml
---
name: [skill名称]
version: [SemVer版本号]
status: draft | active | ready_for_production | frozen | deprecated
layer: agent | dev-guides | ...
owner: [负责人]
last_reviewed: [YYYY-MM-DD]
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - [其他依赖...]
---
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v2.0 | 2025-11-27 | 初始版本 |
| v2.1 | 2025-11-28 | 修复 P0/P1 问题：XML 标签闭合、角色协作模型、Few-shot 示例、调用接口定义、baseline 更新至 v3.5 |

---

## 参考资料

- XML 标签模式详解：references/xml-patterns.md
- 角色提示模式详解：references/role-patterns.md
- 链式提示词设计：references/chain-patterns.md
- 常见问题诊断：references/troubleshooting.md
- ASDD 6 层架构：docs/README.md
