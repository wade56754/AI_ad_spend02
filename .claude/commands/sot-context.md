# 获取 SoT 上下文

从知识库获取 SoT (Source of Truth) 文档相关内容。

## 使用方法

```
/sot-context <主题>
```

## 执行逻辑

请执行以下 Python 代码获取 SoT 上下文：

```python
from agents.skills.code_factory import create_knowledge_base
from agents.skills.code_factory.rag import KnowledgeSource

topic = "$ARGUMENTS"

# 创建知识库
kb = create_knowledge_base(".")
kb.build_index()

print(f"📖 获取 SoT 上下文: '{topic}'")
print("=" * 50)

# 只搜索 SoT 文档
results = kb.search(topic, sources=[KnowledgeSource.SOT], top_k=5)

if not results:
    print("\n⚠️ 未找到相关 SoT 文档")
else:
    print(f"\n找到 {len(results)} 个相关内容:\n")
    
    for i, r in enumerate(results, 1):
        path = r.chunk.metadata.get('path', '未知')
        print(f"### [{i}] {path}")
        print(f"相关度: {r.score:.2f}\n")
        print("```")
        print(r.chunk.content[:500])
        if len(r.chunk.content) > 500:
            print("...")
        print("```\n")
```

基于 SoT 上下文，确保后续生成的代码符合项目规范。






