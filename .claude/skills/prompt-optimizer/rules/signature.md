# 签名模板（修复版）

## 必需标签（全部必须包含且闭合）

| 标签 | 用途 |
|------|------|
| `<role>` | 角色定义 |
| `<goal>` | 任务目标 |
| `<input>` | 输入说明 |
| `<output_format>` | 输出模板 |
| `<constraints>` | 约束条件 |
| `<error_handling>` | 异常处理 |
| `<examples>` | 输入输出示例 |

## 可选标签

| 标签 | 用途 |
|------|------|
| `<thinking>` | 推理引导 |

## 规则

1. 每个标签必须闭合：`<tag>...</tag>`
2. 代码块 ``` 必须成对
3. 代码块必须在 `</output_format>` 之前闭合
4. 禁止示例内容放在 `<output_format>` 内
5. 禁止空表格行 `| | |`

## 完整模板

```xml
<role>
你是{expertise}专家，擅长{skills}。
- 核心能力：{core_skills}
- 知识背景：{knowledge}
</role>

<goal>
{task_description}
- 覆盖范围：{scope}
- 输出物：{deliverables}
</goal>

<input>
请提供以下信息：
- {field_1}：[说明]（必填）
- {field_2}：[说明]（可选）
</input>

<output_format>
## {标题}

### {部分1}

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |

### {部分2}

```python
def example():
    pass
```

</output_format>

<constraints>
1. {数量约束}
2. {质量约束}
3. {格式约束}
</constraints>

<error_handling>
- 如果{情况1}: {处理}
- 如果{情况2}: {处理}
- 如果{情况3}: {处理}
</error_handling>

<examples>
**输入**：
{示例输入}

**输出**：
{示例输出}
</examples>
```
