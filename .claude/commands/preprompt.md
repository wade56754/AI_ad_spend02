# 加载提示词模板

加载项目的 Preprompts 提示词配置（来源: `.codefactory.yaml`）。

## 使用方法

```
/preprompt <类型>
```

类型可选：`system` | `clarify` | `generate` | `improve` | `review` | `all`

## 执行逻辑

请执行以下 Python 代码加载提示词：

```python
from agents.skills.code_factory.config import load_project_config

prompt_type = "$ARGUMENTS".strip().lower() or "all"

config = load_project_config(".")
preprompts = config.preprompts

print(f"📝 加载提示词: {prompt_type}")
print("=" * 50)

prompts = {
    "system": preprompts.system or "(未配置)",
    "clarify": preprompts.clarify or "(未配置)",
    "generate": preprompts.generate or "(未配置)",
    "improve": preprompts.improve or "(未配置)",
    "review": preprompts.review or "(未配置)",
}

if prompt_type == "all":
    print("\n可用的提示词模板:")
    for name, content in prompts.items():
        char_count = len(content) if content != "(未配置)" else 0
        status = "✅" if char_count > 0 else "⚠️"
        print(f"  {status} {name}: {char_count} 字符")
    print("\n提示: 在 .codefactory.yaml 的 preprompts 节点配置自定义提示词")
elif prompt_type in prompts:
    print(f"\n### {prompt_type.upper()} 提示词\n")
    print(prompts[prompt_type])
else:
    print(f"❌ 未知类型: {prompt_type}")
    print("可用类型: system, clarify, generate, improve, review, all")
```

## 配置示例

在 `.codefactory.yaml` 中添加：

```yaml
preprompts:
  system: |
    你是 AI 广告系统的编程助手。
    严格遵循 MASTER.md v4.8 的所有规范。
  clarify: |
    请澄清需求中的模糊点...
  generate: |
    按照 SoT 规范生成代码...
```

加载的提示词可以作为上下文增强后续的代码生成。






