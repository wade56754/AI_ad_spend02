# 知识库搜索

在项目知识库中搜索相关文档和代码。

## 使用方法

```
/kb-search <搜索关键词>
```

## 执行逻辑

请执行以下 Python 代码搜索知识库：

```python
from agents.skills.code_factory import create_knowledge_base

query = "$ARGUMENTS"

# 创建并构建知识库
kb = create_knowledge_base(".")
kb.build_index()

# 搜索
results = kb.search(query, top_k=5)

print(f"🔍 搜索: '{query}'")
print(f"📚 找到 {len(results)} 个相关结果")
print("=" * 50)

for i, r in enumerate(results, 1):
    path = r.chunk.metadata.get('path', '未知')
    print(f"\n[{i}] 相关度: {r.score:.2f}")
    print(f"📁 来源: {path}")
    print(f"📝 内容预览:")
    content = r.chunk.content[:300].replace('\n', '\n   ')
    print(f"   {content}...")
```

基于搜索结果，为用户提供相关建议或直接引用找到的代码。






