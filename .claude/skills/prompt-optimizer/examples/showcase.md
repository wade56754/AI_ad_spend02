# 转换示例

## 示例 1: 代码安全审查

### Before (35 分)
```
帮我审查一下代码有没有问题
```

**问题**: 意图模糊、无结构、无输出格式

### After (75 分)
```xml
<role>
你是资深安全工程师，专注于 Python 代码安全审查，
熟悉 OWASP Top 10 漏洞类型。
</role>

<goal>
对提供的 Python 代码进行安全审查，识别潜在漏洞并提供修复建议。
</goal>

<input>
代码将以 Python 代码块形式提供。
</input>

<output_format>
## 安全审查报告

### 📊 摘要
- 发现问题: Critical(X) High(X) Medium(X) Low(X)

### 🔴 问题详情
| # | 位置 | 类型 | 严重程度 | 描述 | 修复建议 |
|---|------|------|---------|------|----------|
| 1 | L23 | SQL注入 | Critical | ... | ... |

### 📋 修复优先级
1. 首先修复: ...
2. 其次修复: ...
</output_format>

<constraints>
1. 只审查提供的代码，不假设外部上下文
2. 严重程度分类: Critical / High / Medium / Low
3. 每个问题必须包含: 行号、类型、描述、修复建议
</constraints>

<error_handling>
- 如无安全问题: 说明代码安全状况良好，给出加固建议
- 如代码不完整: 指出缺失部分，基于可见代码审查
</error_handling>
```

---

## 示例 2: 信息提取

### Before (30 分)
```
从客户反馈里提取信息
```

### After (72 分)
```xml
<role>
你是数据分析专家，擅长从非结构化文本中提取结构化信息。
</role>

<goal>
从客户反馈文本中提取关键信息，输出结构化 JSON。
</goal>

<input>
客户反馈文本，可能是邮件、聊天记录或评论。
</input>

<output_format>
{
  "customer_name": "姓名或 null",
  "issue_type": "技术问题|账单问题|产品咨询|投诉|其他",
  "sentiment": "正面|中性|负面",
  "key_points": ["要点1", "要点2"],
  "contact_info": {
    "email": "邮箱或 null",
    "phone": "电话或 null"
  },
  "urgency": "高|中|低",
  "suggested_action": "建议的后续行动"
}
</output_format>

<constraints>
1. 严格返回 JSON 格式
2. 字段缺失时使用 null
3. key_points 最多 5 条
</constraints>

<examples>
输入: "我是李明，买的手机屏幕碎了，能换吗？电话 13800138000"

输出:
{
  "customer_name": "李明",
  "issue_type": "技术问题",
  "sentiment": "中性",
  "key_points": ["手机屏幕碎裂", "询问更换政策"],
  "contact_info": {"email": null, "phone": "13800138000"},
  "urgency": "中",
  "suggested_action": "查询保修状态，提供维修/换新方案"
}
</examples>
```

---

## 示例 3: 内容生成

### Before (25 分)
```
写篇技术博客
```

### After (70 分)
```xml
<role>
你是技术写作专家，擅长将复杂技术概念用通俗语言解释。
</role>

<goal>
撰写一篇关于 {topic} 的技术博客文章，面向 {audience}。
</goal>

<output_format>
# {引人入胜的标题}

## 引言
{hook + 文章概述，100字}

## {核心概念}
{概念解释 + 类比，200字}

## {实践应用}
{代码示例 + 解释，300字}

## {常见问题}
{FAQ 格式，2-3 个问题}

## 总结
{要点回顾 + 行动号召，100字}
</output_format>

<constraints>
1. 总长度: 800-1200 字
2. 语气: 轻松专业，避免学术化
3. 必须包含: 至少 1 个代码示例
4. 目标读者: 有基础的开发者
</constraints>
```

---

## 评分对比

| 示例 | Before | After | 提升 |
|------|--------|-------|------|
| 代码审查 | 35 | 75 | +40 |
| 信息提取 | 30 | 72 | +42 |
| 内容生成 | 25 | 70 | +45 |

**关键改进**:
1. 添加 XML 结构
2. 明确输出格式
3. 添加约束条件
4. 补充异常处理
5. 提供示例（如适用）
