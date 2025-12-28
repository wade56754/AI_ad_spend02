---
description: "提示词优化: 将自然语言需求转化为高质量 Claude 提示词"
argument-hint: "<需求描述>"
---

# Prompt Create (提示词创建)

将自然语言需求转化为高质量、结构化的 Claude 提示词。

## 参数

用户输入: `$ARGUMENTS`

## 7 必需标签

生成的提示词**必须包含以下 7 个标签**，且全部闭合：

| # | 标签 | 用途 | 要求 |
|---|------|------|------|
| 1 | `<role>` | 角色定义 | 专业身份 + 核心能力 + 知识背景 |
| 2 | `<goal>` | 任务目标 | 动作 + 对象 + 范围 + 输出物 |
| 3 | `<input>` | 输入说明 | 字段列表 + 必填/可选标注 |
| 4 | `<output_format>` | 输出格式 | 完整模板 + 代码块闭合 |
| 5 | `<constraints>` | 约束条件 | 数量 + 质量 + 格式约束 |
| 6 | `<error_handling>` | 异常处理 | ≥3 种异常情况及处理方式 |
| 7 | `<examples>` | 示例 | 完整输入 + 完整输出 |

## 格式规则

1. 每个 `<tag>` 必须有 `</tag>` 闭合
2. 所有 ``` 必须成对出现
3. 代码块必须在 `</output_format>` 前闭合
4. 禁止空表格行
5. 示例必须在 `<examples>` 内

## 工作流程

```
用户需求 → [1]意图解析 → [2]签名构建 → [3]生成提示词 → [4]质量评估 → 输出
```

### Phase 1: 意图解析
读取: `.claude/skills/prompt-optimizer/rules/intent.md`

从需求中提取：
- 任务类型（分类/生成/提取/转换/分析）
- 输入输出字段
- 显式+隐式约束

### Phase 2: 签名构建
读取: `.claude/skills/prompt-optimizer/rules/signature.md`

将意图转化为 7 个必需标签结构。

### Phase 3: 生成提示词
读取: `.claude/skills/prompt-optimizer/rules/claude.md`

应用 Claude 4.x 最佳实践：
- XML 标签结构（7 必需标签）
- 显式正向指令
- 预填充技术

### Phase 4: 质量评估
读取: `.claude/skills/prompt-optimizer/rules/quality.md`

8 维度评分（总分 80）：

| 维度 | 权重 | 说明 |
|------|------|------|
| 意图清晰度 | 15% | 准确表达用户意图 |
| 结构完整性 | 15% | 7 必需标签 + 格式规则 |
| 具体性 | 15% | 指令明确具体 |
| 输出可控性 | 15% | 输出格式定义 |
| 示例有效性 | 10% | 高质量示例 |
| 约束明确性 | 10% | 约束条件清晰 |
| 异常处理 | 10% | ≥3 种异常情况 |
| 可测试性 | 10% | 可验证可测试 |

评级：≥70 🟢优秀 | 60-69 🟡良好 | <60 🟠需改进

## 输出格式

```xml
<role>
[角色定义：专业身份 + 核心能力 + 知识背景]
</role>

<goal>
[任务目标：动作 + 对象 + 范围 + 输出物]
</goal>

<input>
[输入说明：字段列表 + 必填/可选标注]
</input>

<output_format>
[输出模板：完整格式，代码块必须闭合]
</output_format>

<constraints>
[约束条件：数量 + 质量 + 格式约束]
</constraints>

<error_handling>
[异常处理：≥3 种情况及处理方式]
</error_handling>

<examples>
[示例：完整输入 + 完整输出]
</examples>
```

## 生成后验证

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 7 必需标签 | 全部存在且闭合 |
| 2 | ``` 配对 | 数量为偶数 |
| 3 | 空表格行 | 不存在 |
| 4 | 示例位置 | 在 `<examples>` 内 |

## 示例

```bash
# 基础用法
/pc 编写 API 测试用例

# 代码审查
/pc Python 代码安全审查，重点关注 SQL 注入和 XSS

# 数据提取
/pc 从客户反馈中提取姓名、问题类型和联系方式

# 分类任务
/pc 对用户评论进行情感分析（积极/消极/中性）
```

## 知识依赖

读取以下 Skill 文件:
- `.claude/skills/prompt-optimizer/rules/intent.md`
- `.claude/skills/prompt-optimizer/rules/signature.md`
- `.claude/skills/prompt-optimizer/rules/claude.md`
- `.claude/skills/prompt-optimizer/rules/quality.md`
