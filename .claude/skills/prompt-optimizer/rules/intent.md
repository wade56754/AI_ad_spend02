# 意图解析规则

## 任务类型识别

| 类型 | 关键词 | 典型输出 |
|------|--------|----------|
| **分类** | 判断、分类、识别、是否 | label, confidence, reasoning |
| **生成** | 写、生成、创建、编写 | content, format |
| **提取** | 提取、抽取、找出 | extracted_data, metadata |
| **转换** | 转换、翻译、改写 | transformed_content |
| **分析** | 分析、评估、审查 | findings, recommendations |

**默认**: 无法匹配时选择"分析"

---

## 签名提取

### 输入字段
```yaml
显式输入: 用户明确提到的对象
  "审查 Python 代码" → code: str, language: str = "Python"

隐式输入: 可推断的可选参数
  "代码审查" → focus_areas: list (可选)
```

### 输出字段（按任务类型）
```yaml
分类: [label, confidence, reasoning]
生成: [content, word_count]
提取: [extracted_info, metadata]
转换: [result, original_format, target_format]
分析: [findings, severity, recommendations]
```

---

## 约束识别

| 类型 | 识别模式 | 示例 |
|------|----------|------|
| 长度 | "不超过"、"至少" | "500 字以内" |
| 格式 | "用...格式" | "JSON 格式" |
| 风格 | "专业的"、"简洁的" | "正式语气" |
| 领域 | "关于"、"针对" | "面向初学者" |
| 禁止 | "不要"、"避免" | "不使用术语" |

---

## 澄清策略

**触发条件** (confidence < 0.7):
- 多个任务类型匹配
- 缺少关键输入
- 约束冲突
- 领域不明确

**澄清模板**:
```
我理解你想创建 {task_type} 提示词。确认几点：

1. **{维度}**: {问题}？（选项 A/B/C）
2. ...

如需通用版本，我可以先创建再调整。
```

---

## 输出格式

```yaml
intent:
  task_type: analysis
  domain: code-security
  confidence: 0.95

signature:
  inputs:
    - name: code
      type: str
      required: true
  outputs:
    - name: vulnerabilities
      type: list

constraints:
  explicit: ["找出安全漏洞"]
  implicit: ["按严重程度排序", "提供修复建议"]

clarification_needed: false
```
