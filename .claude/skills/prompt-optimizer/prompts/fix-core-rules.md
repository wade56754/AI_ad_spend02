# 修复 prompt-optimizer skill 的通用规则

> 复制以下全部内容发送给 Claude

---

```
# 任务：修复 prompt-optimizer skill 的核心规则

这个 skill 是**通用提示词优化器**，可以为任意需求生成高质量提示词。

当前问题：生成的提示词缺少关键标签、代码块不闭合、有空表格行。

## 问题分析

当前 rules/signature.md 的问题：

| 问题 | 当前状态 | 应该 |
|------|----------|------|
| [constraints] 标签 | 推荐（可选） | **必需** |
| [error_handling] 标签 | 可选 | **必需** |
| [examples] 标签 | 可选 | **必需** |
| 代码块闭合规则 | 无 | **必须成对** |
| 空表格行规则 | 无 | **禁止** |

（注：用 [tag] 代替 <tag> 防止被 Markdown 隐藏）

---

## 你的任务

### 1. 输出修复后的 rules/signature.md

要求：

#### 标签规则修改
把以下标签从"推荐/可选"改为**必需**：
- [constraints] - 约束条件
- [error_handling] - 异常处理  
- [examples] - 输入输出示例

修复后的必需标签列表（共 7 个）：
```
必需标签（生成任何提示词都必须包含）：
1. [role] - 角色定义
2. [goal] - 任务目标
3. [input] - 输入说明
4. [output_format] - 输出格式
5. [constraints] - 约束条件
6. [error_handling] - 异常处理
7. [examples] - 示例
```

#### 添加格式规则
```
格式规则：
1. 每个标签必须闭合：[tag]...[/tag]
2. 代码块 ``` 必须成对出现
3. 代码块必须在 [/output_format] 之前闭合
4. 禁止表格出现空行（如 | | | |）
5. 禁止示例内容放在 [output_format] 内，必须放 [examples] 内
```

#### 更新完整模板
```
[role]
你是{expertise}专家。
- 核心能力：{abilities}
- 知识背景：{knowledge}
[/role]

[goal]
{task_description}
- 覆盖范围：{scope}
- 输出物：{deliverables}
[/goal]

[input]
请提供以下信息：
- {field1}：{description}（必填）
- {field2}：{description}（可选）
[/input]

[output_format]
## {title}

### {section1}
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| ... | ... | ... |

### {section2}
```language
代码示例（必须在 [/output_format] 前闭合）
```
[/output_format]

[constraints]
1. {数量约束}
2. {质量约束}
3. {格式约束}
[/constraints]

[error_handling]
- 如果 {condition1}: {action1}
- 如果 {condition2}: {action2}
- 如果 {condition3}: {action3}
[/error_handling]

[examples]
输入：
{example_input}

输出：
{example_output}
[/examples]
```

---

### 2. 输出修复后的 rules/quality.md 相关部分

在维度 2（结构完整性）中添加检查项：

```
必需标签检查（7 个全部存在才能得满分）：
- [role] 和 [/role]
- [goal] 和 [/goal]
- [input] 和 [/input]
- [output_format] 和 [/output_format]
- [constraints] 和 [/constraints]
- [error_handling] 和 [/error_handling]
- [examples] 和 [/examples]

格式检查：
- ``` 数量必须是偶数
- 无空表格行
```

---

### 3. 输出修复后的 SKILL.md 输出格式部分

更新输出格式示例，确保包含所有 7 个标签：

```markdown
## 输出格式

生成的提示词必须包含以下结构：

```text
[role]...[/role]
[goal]...[/goal]
[input]...[/input]
[output_format]...[/output_format]
[constraints]...[/constraints]
[error_handling]...[/error_handling]
[examples]...[/examples]
```
```

---

## 输出要求

请输出以下 3 个文件的**完整内容**（不是 diff）：

### 文件 1: rules/signature.md
```markdown
# 签名模板（修复版）

{完整内容}
```

### 文件 2: rules/quality.md 的维度 2 部分
```markdown
## 维度 2: 结构完整性 (15%)

{修复后的内容}
```

### 文件 3: SKILL.md 的输出格式部分
```markdown
## 输出格式

{修复后的内容}
```

---

## 验证

修复后，用需求"编写 API 测试用例"测试，生成的提示词必须：
- 包含 7 个必需标签且全部闭合
- 代码块 ``` 成对
- 无空表格行

---

现在开始输出修复后的文件内容。
```
