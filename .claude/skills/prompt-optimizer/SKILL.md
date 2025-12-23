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

从需求中提取：
- 任务类型（分类/生成/提取/转换/分析）
- 输入输出字段
- 显式+隐式约束

### Phase 2: 签名构建
**读取**: `rules/signature.md`

将意图转化为结构化契约：
```
docstring → <goal>
InputField → <input>
OutputField → <output_format>
```

### Phase 3: 生成提示词
**读取**: `rules/claude.md`

应用 Claude 4.x 最佳实践：
- XML 标签结构
- 显式正向指令
- 预填充技术

### Phase 4: 质量评估
**读取**: `rules/quality.md`

8 维度评分（总分 80）：
- ≥70: 🟢 优秀
- 60-69: 🟡 良好
- <60: 🟠 需改进

---

## 输出格式

```markdown
# 🎯 生成的提示词

## 提示词内容
\`\`\`xml
<role>
[角色定义]
</role>

<goal>
[任务目标]
</goal>

<input>
[输入格式说明]
</input>

<output_format>
[输出模板 - 所有代码块必须闭合]
</output_format>

<constraints>
1. [约束1 - 必须有数量/范围定义]
2. [约束2]
</constraints>

<error_handling>
- 如果[条件]: [处理方式]
</error_handling>

<examples>
**输入**: ...
**输出**: ...
</examples>
\`\`\`

## 📊 质量评估
| 维度 | 分数 | 状态 |
|------|------|------|
| 意图清晰度 | X/10 | ✅/⚠️/❌ |
| 结构完整性 | X/10 | ✅/⚠️/❌ |
| 具体性 | X/10 | ✅/⚠️/❌ |
| 输出可控性 | X/10 | ✅/⚠️/❌ |
| 示例有效性 | X/10 | ✅/⚠️/❌ |
| 约束明确性 | X/10 | ✅/⚠️/❌ |
| 异常处理 | X/10 | ✅/⚠️/❌ |
| 可测试性 | X/10 | ✅/⚠️/❌ |
| **总分** | **XX/80** | 🟢/🟡/🔴 |

## 💡 使用建议
- ...
```

### 强制检查清单 (生成前必须验证)

- [ ] 所有 XML 标签成对闭合 (`<tag>` 必须有 `</tag>`)
- [ ] 所有代码块 ``` 成对闭合
- [ ] 包含 7 个必需标签（全部必须存在且闭合）:
  - `<role>` - 角色定义
  - `<goal>` - 任务目标
  - `<input>` - 输入说明
  - `<output_format>` - 输出模板
  - `<constraints>` - 约束条件
  - `<error_handling>` - 异常处理
  - `<examples>` - 输入输出示例
- [ ] `<examples>` 独立于 `<output_format>`
- [ ] 表格无空行，格式完整

---

## MCP 增强（可选）

| 工具 | 触发词 | 用途 |
|------|--------|------|
| Sequential Thinking | "使用 sequential thinking" | 复杂问题分解 |
| Context7 | "use context7" | 获取最新库文档 |
| Fetch | 提供 URL | 参考外部资料 |

**示例**: `/pc 使用 sequential thinking 设计多角色客服系统提示词`

详见: `mcp.md`

---

## 文件依赖

```
prompt-optimizer/
├── SKILL.md           # 本文件
├── rules/
│   ├── intent.md      # 意图解析规则
│   ├── signature.md   # 签名模板
│   ├── quality.md     # 8 维度评分
│   └── claude.md      # Claude 4.x 优化
├── templates/
│   └── standard.md    # 标准提示词模板 (含 API 测试完整示例)
├── examples/
│   └── showcase.md    # 转换示例
├── self-optimize.md   # 自优化指南
├── mcp.md             # MCP 使用指南
└── scripts/
    └── validate.py    # 验证脚本
```

---

## 自检清单 (生成后必须验证)

### 7 个必需标签

| # | 标签 | 要求 | 必需 |
|---|------|------|------|
| 1 | `<role>` | 专业身份 + 核心能力 + 知识背景 | ✅ |
| 2 | `<goal>` | 动作 + 对象 + 范围 | ✅ |
| 3 | `<input>` | 字段说明 + 必填/可选标注 | ✅ |
| 4 | `<output_format>` | 完整模板 + 代码块闭合 | ✅ |
| 5 | `<constraints>` | 数量 + 质量 + 格式约束 | ✅ |
| 6 | `<error_handling>` | ≥ 3 种异常情况 | ✅ |
| 7 | `<examples>` | 完整输入 + 完整输出 | ✅ |

### 格式检查

| # | 检查项 | 要求 |
|---|--------|------|
| 8 | 所有标签闭合 | `<tag>` 有 `</tag>` |
| 9 | 代码块闭合 | ``` 成对出现 |
| 10 | 无空表格行 | 无 `\| \| \| \|` |

详见: `self-optimize.md`
