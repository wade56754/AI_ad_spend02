# 签名模板

## 必需标签（7 个）

| 标签 | 用途 | 要求 |
|------|------|------|
| `<role>` | 角色定义 | 专业身份 + 核心能力 + 知识背景 |
| `<goal>` | 任务目标 | 动作 + 对象 + 范围 |
| `<input>` | 输入说明 | 字段列表 + 必填/可选标注 |
| `<output_format>` | 输出格式 | 精简模板，代码块必须闭合 |
| `<constraints>` | 约束条件 | 数量 + 质量 + 格式约束 |
| `<error_handling>` | 异常处理 | ≥3 种异常情况及处理方式 |
| `<examples>` | 示例 | 简洁的输入 + 输出 |

## 格式规则

1. 每个 `<tag>` 必须有 `</tag>` 闭合
2. 所有 ``` 必须成对出现
3. 代码块必须在 `</output_format>` 前闭合
4. 禁止空表格行
5. 示例必须在 `<examples>` 内
6. **精简原则**: 避免多余的标题和前缀

---

## 完整模板

```xml
<role>
你是一位{expertise}专家，专精于{specialty}。
- 核心能力：{abilities}
- 知识背景：{knowledge}
</role>

<goal>
{task_description}
- 覆盖范围：{scope}
- 输出物：{deliverables}
</goal>

<input>
- {field1}：[说明]（必填）
- {field2}：[说明]（可选）
</input>

<output_format>
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| {占位} | {占位} | {占位} |

```python
class Example:
    def method(self):
        pass
```
</output_format>

<constraints>
1. {数量约束，含具体数字}
2. {质量约束}
3. {格式约束}
</constraints>

<error_handling>
- 如果{condition1}：{action1}
- 如果{condition2}：{action2}
- 如果{condition3}：{action3}
</error_handling>

<examples>
输入：
- 字段1：值1
- 字段2：值2

输出：
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 具体值 | 具体值 | 具体值 |
</examples>
```

---

## 精简原则

| 避免 | 推荐 |
|------|------|
| `## API: {端点名称}` | 直接写表格 |
| `### 测试用例清单` | 省略子标题 |
| `请提供以下信息：` | 直接列字段 |
| 冗长的占位符说明 | 用 `{...}` |

---

## 生成检查清单

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | 7 必需标签 | 全部存在且闭合 |
| 2 | ``` 配对 | 数量为偶数 |
| 3 | 空表格行 | 不存在 |
| 4 | 示例位置 | 在 `<examples>` 内 |
| 5 | 精简度 | 无多余标题和前缀 |
