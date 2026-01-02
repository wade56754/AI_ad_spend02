# 构建知识库

构建或重建项目知识库索引。

## 使用方法

```
/kb-build
```

## 执行逻辑

请执行以下 Python 代码构建知识库：

```python
from agents.skills.code_factory import create_knowledge_base

print("🔨 正在构建知识库索引...")
print("=" * 50)

# 创建知识库
kb = create_knowledge_base(".")

# 构建索引
stats = kb.build_index(force_rebuild=True)

print("\n✅ 索引构建完成！\n")
print("📊 索引统计:")

for source, stat in stats.items():
    print(f"\n  📂 {source}:")
    print(f"     文档数: {stat['total_documents']}")
    print(f"     块数: {stat['total_chunks']}")
    print(f"     字符数: {stat['total_chars']:,}")
```

索引构建完成后，可以使用 `/kb-search` 搜索内容。


