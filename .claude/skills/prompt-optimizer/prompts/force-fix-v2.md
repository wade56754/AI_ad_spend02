# Skill 强制修复提示词 v2（防作弊版）

> 复制以下全部内容发送给 Claude

---

```
# 任务：修复 prompt-optimizer skill

## ⛔ 防作弊机制

本任务采用"先输出，后验证"机制。你必须：
1. 先完整输出提示词
2. 再逐行编号复制
3. 最后基于编号行验证

禁止边输出边声称"已验证通过"。

---

## Step 1: 识别当前 skill 的问题

当前 skill 的 `rules/signature.md` 模板不完整，缺少：
- `<constraints>` 不是必需标签
- `<error_handling>` 是可选标签
- `<examples>` 是可选标签
- 没有强制代码块闭合的规则

---

## Step 2: 输出修复后的 signature.md

输出完整的修复后文件内容：

```markdown
# 签名模板（修复版）

## 标签规则

### 必需标签（生成时必须包含）
| 标签 | 用途 | 闭合要求 |
|------|------|----------|
| `<role>` | 角色定义 | 必须有 `</role>` |
| `<goal>` | 任务目标 | 必须有 `</goal>` |
| `<input>` | 输入说明 | 必须有 `</input>` |
| `<output_format>` | 输出模板 | 必须有 `</output_format>` |
| `<constraints>` | 约束条件 | 必须有 `</constraints>` |
| `<error_handling>` | 异常处理 | 必须有 `</error_handling>` |
| `<examples>` | 示例 | 必须有 `</examples>` |

### 代码块规则
- 每个 ``` 必须成对出现
- 代码块必须在 `</output_format>` 之前闭合

### 禁止事项
- 禁止把示例内容放在 `<output_format>` 内
- 禁止表格出现空行 `| | | |`
- 禁止标签不闭合

---

## 完整模板

<role>
你是{expertise}专家。
- 核心能力：{abilities}
- 知识背景：{knowledge}
</role>

<goal>
{task_description}
- 覆盖范围：{scope}
- 输出物：{deliverables}
</goal>

<input>
请提供以下信息：
- {field1}：{description}（必填）
- {field2}：{description}（可选）
</input>

<output_format>
## {title}

### {section1}
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| ... | ... | ... |

### {section2}
```language
代码示例
```
</output_format>

<constraints>
1. {数量约束}
2. {质量约束}
3. {格式约束}
</constraints>

<error_handling>
- 如果 {condition1}: {action1}
- 如果 {condition2}: {action2}
- 如果 {condition3}: {action3}
</error_handling>

<examples>
输入：
{example_input}

输出：
{example_output}
</examples>
```

---

## Step 3: 用修复后的 skill 生成提示词

需求："生成 API 测试用例"

用上面修复后的模板，生成完整提示词。

### 输出要求

用 xml 代码块输出，确保：
- 从 `<role>` 开始
- 到 `</examples>` 结束
- 中间所有标签都闭合

```xml
在这里输出完整提示词
```

---

## Step 4: 逐行编号

把 Step 3 输出的提示词复制一遍，每行加上行号：

```
001: <role>
002: 你是一位资深 QA 工程师...
003: ...
...
050: </examples>
```

---

## Step 5: 基于行号验证

在 Step 4 的编号内容中搜索，填写结果：

| # | 搜索内容 | 在第几行找到 | ✓/✗ |
|---|----------|--------------|-----|
| 1 | `</role>` | 行号 X | |
| 2 | `</goal>` | 行号 X | |
| 3 | `</input>` | 行号 X | |
| 4 | `</output_format>` | 行号 X | |
| 5 | `</constraints>` | 行号 X | |
| 6 | `</error_handling>` | 行号 X | |
| 7 | `</examples>` | 行号 X | |
| 8 | 空表格行 `\| \|` 或 `\|  \|` | 未找到 / 行号 X | |

### ``` 配对检查
列出所有 ``` 的行号：
- 行 X: ``` (开始)
- 行 Y: ``` (结束)
- ...

总数：X 个（必须是偶数）

---

## Step 6: 验证结果

| 检查项 | 结果 |
|--------|------|
| 7 个必需标签全部闭合 | ✓ 或 ✗ |
| ``` 数量是偶数 | ✓ 或 ✗ |
| 无空表格行 | ✓ 或 ✗ |

如果有任何 ✗：
1. 说明问题
2. 回到 Step 3 重新生成
3. 重复 Step 4-6

如果全部 ✓：输出"验证通过 ✅"

---

## 禁止行为

⛔ 禁止在 Step 3 之后直接说"验证通过"
⛔ 禁止跳过 Step 4 的逐行编号
⛔ 禁止在 Step 5 填写"行号 X"但 Step 4 中实际没有该内容
⛔ 禁止 Step 4 的内容与 Step 3 不一致

---

## 检验方法

我会核对：
- Step 4 的编号内容是否与 Step 3 完全一致
- Step 5 填写的行号是否在 Step 4 中真的有对应内容

如果发现不一致，视为作弊，任务失败。

---

现在开始执行。从 Step 2 开始输出修复后的 signature.md。
```
