# 需求澄清

分析并澄清用户需求，识别模糊点，输出结构化需求。

## 使用方法

```
/clarify <需求描述>
```

## 执行逻辑

请执行以下 Python 代码来澄清需求：

```python
from agents.skills.code_factory import clarify_requirement, auto_clarify

requirement = "$ARGUMENTS"

# 自动澄清
clarified = auto_clarify(requirement)

print("📋 澄清后的需求")
print("=" * 50)
print(clarified.to_prompt_context())

# 完整分析
result = clarify_requirement(requirement)

if result.unanswered_questions:
    print("\n❓ 建议澄清的问题:")
    for q in result.unanswered_questions[:5]:
        importance = "🔴 必需" if q.importance == "required" else "🟡 可选"
        print(f"  {importance} {q.question}")
        if q.options:
            for opt in q.options:
                print(f"      - {opt}")
```

基于澄清结果，提供更精确的实现建议。


