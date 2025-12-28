# Skill 强制修复提示词 v4（转义格式版）

> 复制以下全部内容发送给 Claude

---

```
# 任务：修复 prompt-optimizer skill

## ⚠️ 重要：使用转义格式

因为 XML 标签在 Markdown 中会被隐藏，本任务要求：
- 用 `[tag]` 代替 `<tag>`
- 用 `[/tag]` 代替 `</tag>`

这样可以确保标签可见，防止作弊。

---

## Step 1: 生成提示词（使用转义格式）

需求："生成 API 测试用例"

### 格式要求

用 `[tag]` 格式输出，必须包含 7 个标签：

```
[role]...[/role]
[goal]...[/goal]
[input]...[/input]
[output_format]...[/output_format]
[constraints]...[/constraints]
[error_handling]...[/error_handling]
[examples]...[/examples]
```

### 输出提示词

```text
[role]
你是一位资深 QA 工程师...
[/role]

[goal]
...
[/goal]

...继续输出完整内容...
```

---

## Step 2: 逐行编号

复制 Step 1 的内容，每行加行号：

```
001: [role]
002: 你是一位资深 QA 工程师...
003: [/role]
004: 
005: [goal]
...
```

---

## Step 3: 验证

在 Step 2 中找到每个闭合标签的行号：

| # | 搜索内容 | 行号 | 该行内容 | ✓/✗ |
|---|----------|------|----------|-----|
| 1 | `[/role]` | | | |
| 2 | `[/goal]` | | | |
| 3 | `[/input]` | | | |
| 4 | `[/output_format]` | | | |
| 5 | `[/constraints]` | | | |
| 6 | `[/error_handling]` | | | |
| 7 | `[/examples]` | | | |

### 代码块检查

找出所有 ``` 的行号，确认是偶数。

### 空表格行检查

搜索 `| |`，确认未找到。

---

## Step 4: 转换回 XML 格式

验证通过后，把 `[tag]` 转换回 `<tag>` 格式，输出最终提示词：

```xml
<role>
...
</role>

<goal>
...
</goal>

...
</examples>
```

---

## Step 5: 输出修复后的 signature.md

把 Step 4 的模板整合到 `rules/signature.md` 文件中：

1. 添加 "API 测试任务模板"
2. 把 `<constraints>`、`<error_handling>`、`<examples>` 改为**必需标签**

输出完整的 signature.md 文件内容。

---

## 禁止行为

⛔ 禁止在 Step 1 使用 `<tag>` 格式（必须用 `[tag]`）
⛔ 禁止 Step 2 省略任何 `[tag]` 或 `[/tag]`
⛔ 禁止 Step 3 声称找到但 Step 2 中实际没有

---

## 示例

### Step 1 正确格式
```text
[role]
你是专家。
[/role]

[goal]
完成任务。
[/goal]
```

### Step 2 正确编号
```
001: [role]
002: 你是专家。
003: [/role]
004: 
005: [goal]
006: 完成任务。
007: [/goal]
```

### Step 1 错误格式（禁止）
```xml
<role>
你是专家。
</role>
```
↑ 这是错误的！标签会被隐藏。

---

现在开始执行 Step 1，使用 `[tag]` 格式输出。
```
