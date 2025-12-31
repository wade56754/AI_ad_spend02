# 加载提示词模板

加载项目的 Preprompts 提示词配置。

## 使用方法

```
/preprompt <类型>
```

类型可选：`system` | `clarify` | `generate` | `improve` | `review` | `all`

## 执行逻辑

请执行以下 Python 代码加载提示词：

```python
from agents.skills.code_factory import create_preprompts, PrepromptType

prompt_type = "$ARGUMENTS".strip().lower() or "system"

preprompts = create_preprompts(".")

print(f"📝 加载提示词: {prompt_type}")
print("=" * 50)

if prompt_type == "all":
    prompt_set = preprompts.load_all()
    print("\n可用的提示词模板:")
    print(f"  • system: {len(prompt_set.system)} 字符")
    print(f"  • clarify: {len(prompt_set.clarify)} 字符")
    print(f"  • generate: {len(prompt_set.generate)} 字符")
    print(f"  • improve: {len(prompt_set.improve)} 字符")
    print(f"  • review: {len(prompt_set.review)} 字符")
elif prompt_type == "system":
    print(preprompts.get_system_prompt())
elif prompt_type == "clarify":
    print(preprompts.get_clarify_prompt())
elif prompt_type == "generate":
    print(preprompts.get_generate_prompt())
elif prompt_type == "improve":
    print(preprompts.get_improve_prompt())
elif prompt_type == "review":
    print(preprompts.get_review_prompt())
else:
    print(f"❌ 未知类型: {prompt_type}")
    print("可用类型: system, clarify, generate, improve, review, all")
```

加载的提示词可以作为上下文增强后续的代码生成。


