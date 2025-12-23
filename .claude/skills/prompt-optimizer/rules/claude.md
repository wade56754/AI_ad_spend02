# Claude 4.x 优化规则

## XML 标签系统

### 核心标签

| 标签 | 优先级 | 用途 |
|------|--------|------|
| `<goal>` | 必需 | 任务目标 |
| `<output_format>` | 必需 | 输出格式 |
| `<role>` | 推荐 | 角色定义 |
| `<input>` | 推荐 | 输入说明 |
| `<constraints>` | 推荐 | 约束条件 |
| `<thinking>` | 可选 | 推理引导 |
| `<examples>` | 可选 | 示例演示 |
| `<error_handling>` | 可选 | 异常处理 |

### 标签顺序
```
<role> → <goal> → <input> → <output_format> → <constraints> → <thinking> → <examples>
```

---

## 显式指令原则

### ✅ 正向指令（推荐）
```
"按严重程度排序"
"使用 Markdown 格式"
"在报告开头提供摘要"
```

### ❌ 负向指令（避免）
```
"不要遗漏任何问题" → "列出所有发现的问题"
"不要使用术语" → "使用通俗易懂的语言"
"避免冗长" → "控制在 500 字以内"
```

---

## 预填充技术

### 强制 JSON
```python
{"role": "assistant", "content": "{"}
```

### 强制 XML
```python
{"role": "assistant", "content": "<result>"}
```

### 跳过前言
```python
{"role": "assistant", "content": "## 分析报告\n\n"}
```

### 保持角色
```python
{"role": "assistant", "content": "[角色名] "}
```

---

## 语气规范

### ❌ 避免激进语言
```
MUST, NEVER, ALWAYS, CRITICAL, 绝对, 必须, 严禁
```

### ✅ 使用正常语气
```
"请确保..." 而非 "必须!!!"
"建议..." 而非 "强制要求"
"优先..." 而非 "绝对不能不"
```

---

## "Think" 敏感性 (Opus 4.5)

### ⚠️ 谨慎使用
```
"think step by step"
"think carefully"
"think about this"
```

### ✅ 替代方案
```
"consider the following aspects"
"evaluate each factor"
"analyze step by step"
"examine the components"
```

---

## 结构化输出

### JSON 输出模板
```xml
<output_format>
返回严格 JSON 格式:
{
  "field1": "类型说明",
  "field2": ["数组项"]
}
</output_format>
```

### Markdown 输出模板
```xml
<output_format>
## 标题

### 第一部分
{内容}

### 第二部分
| 列1 | 列2 |
|-----|-----|
| ... | ... |
</output_format>
```

---

## 思维链引导

### 显式思考块
```xml
<thinking>
分析步骤:
1. 首先识别 {aspect1}
2. 然后评估 {aspect2}
3. 最后综合 {conclusion}
</thinking>
```

### 内置推理
```xml
<goal>
分析代码安全性。

请按以下步骤进行:
1. 扫描潜在漏洞点
2. 评估每个漏洞的风险
3. 提出修复建议
</goal>
```

---

## 快速检查清单

- [ ] 使用 XML 标签结构
- [ ] 包含 `<goal>` 和 `<output_format>`
- [ ] 使用正向指令
- [ ] 避免激进语言
- [ ] 避免 "think" (Opus 4.5)
- [ ] 提供清晰的输出模板
- [ ] 考虑使用预填充

---

## 生成时强制校验 (P0 级别)

### 1. 标签闭合检查
```
每个 <tag> 必须有对应 </tag>
✅ <role>内容</role>
❌ <role>内容  (缺少闭合)
```

### 2. 代码块闭合检查
```
每个 ``` 必须成对出现
✅ ```python
   code
   ```
❌ ```python
   code
   (缺少闭合)
```

### 3. 必需标签检查
```
if missing <goal>: ❌ P0 错误
if missing <output_format>: ❌ P0 错误
if missing <constraints>: ⚠️ P1 警告 → 添加默认约束
if missing <error_handling>: ⚠️ P1 警告 → 添加默认处理
```

### 4. 标签命名规范
```
❌ 禁止自创标签:
   <input_format> → 使用 <input>
   <test_categories> → 整合到 <constraints>
   <process_steps> → 整合到 <goal> 或 <thinking>

✅ 只允许核心标签:
   role, goal, input, output_format, constraints,
   thinking, examples, error_handling
```

### 5. 内容分离检查
```
❌ 示例数据混在 <output_format> 内
✅ 示例数据放在独立的 <examples> 标签中
```

### 6. 表格格式检查
```
❌ 表格末尾有空行
❌ 缺少表头分隔符 |---|
✅ 完整的 Markdown 表格格式
```
