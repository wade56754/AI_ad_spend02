# Prompt Optimizer

> 将自然语言需求转化为高质量 Claude 提示词

## 触发方式

```bash
/pc <需求描述>              # 简化命令（推荐）
/prompt/create <需求>       # 完整命令
```

**自动触发关键词**: "帮我写提示词"、"优化 prompt"、"让 Claude..."

---

## 工作流程

```
用户需求 → [1]意图解析 → [2]签名构建 → [3]生成提示词 → [4]质量评估 → 输出
```

### Phase 1: 意图解析
**读取**: `rules/intent.md`

### Phase 2: 签名构建
**读取**: `rules/signature.md`

### Phase 3: 生成提示词
**读取**: `rules/claude.md`

### Phase 4: 质量评估
**读取**: `rules/quality.md`

---

## 7 必需标签

生成的提示词必须包含以下 7 个标签，且全部闭合：

| # | 标签 | 用途 | 要求 |
|---|------|------|------|
| 1 | `<role>` | 角色定义 | 专业身份 + 核心能力 + 知识背景 |
| 2 | `<goal>` | 任务目标 | 动作 + 对象 + 范围 + 输出物 |
| 3 | `<input>` | 输入说明 | 字段列表 + 必填/可选标注 |
| 4 | `<output_format>` | 输出格式 | 完整模板 + 代码块闭合 |
| 5 | `<constraints>` | 约束条件 | 数量 + 质量 + 格式约束 |
| 6 | `<error_handling>` | 异常处理 | ≥3 种异常情况及处理方式 |
| 7 | `<examples>` | 示例 | 完整输入 + 完整输出 |

---

## 输出格式

```xml
<role>
[角色定义]
</role>

<goal>
[任务目标]
</goal>

<input>
[输入说明]
</input>

<output_format>
[输出模板，代码块必须闭合]
</output_format>

<constraints>
[约束条件]
</constraints>

<error_handling>
[异常处理]
</error_handling>

<examples>
[示例]
</examples>
```

---

## 格式检查清单

生成提示词后必须验证：

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 7 必需标签 | 全部存在 |
| 2 | 标签闭合 | 每个 `<tag>` 有 `</tag>` |
| 3 | ``` 配对 | 数量为偶数 |
| 4 | 空表格行 | 不存在 |
| 5 | 示例位置 | 在 `<examples>` 内 |

---

## 质量评估

8 维度评分（总分 80）：

| 评级 | 分数范围 |
|------|----------|
| 🟢 优秀 | ≥70 |
| 🟡 良好 | 60-69 |
| 🟠 及格 | 50-59 |
| 🔴 需改进 | <50 |

---

## MCP 增强（可选）

| 工具 | 触发词 | 用途 |
|------|--------|------|
| Sequential Thinking | "使用 sequential thinking" | 复杂问题分解 |
| Context7 | "use context7" | 获取最新库文档 |
| Fetch | 提供 URL | 参考外部资料 |

---

## 文件依赖

```
prompt-optimizer/
├── SKILL.md
├── rules/
│   ├── intent.md
│   ├── signature.md
│   ├── quality.md
│   └── claude.md
├── templates/
│   └── standard.md
├── examples/
│   └── showcase.md
└── mcp.md
```
