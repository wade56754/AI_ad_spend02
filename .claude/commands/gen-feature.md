# 生成功能代码

完整的功能开发流程：澄清需求 → 搜索参考 → 获取规范 → 生成代码。

## 使用方法

```
/gen-feature <功能描述>
```

## 执行逻辑

请按以下步骤执行完整的功能开发流程：

### Step 1: 需求澄清

```python
from agents.skills.code_factory import clarify_requirement, auto_clarify

requirement = "$ARGUMENTS"

print("📋 Step 1: 需求澄清")
print("=" * 50)

clarified = auto_clarify(requirement)
print(clarified.to_prompt_context())

result = clarify_requirement(requirement)
if result.unanswered_questions:
    print("\n❓ 建议确认的问题:")
    for q in result.unanswered_questions[:3]:
        print(f"  • {q.question}")
```

### Step 2: 搜索参考代码

```python
from agents.skills.code_factory import create_knowledge_base

print("\n🔍 Step 2: 搜索参考代码")
print("=" * 50)

kb = create_knowledge_base(".")
kb.build_index()

# 搜索代码
code_results = kb.search_code(requirement, top_k=3)
print(f"\n找到 {len(code_results)} 个相关代码参考:")
for r in code_results:
    print(f"  📁 {r.chunk.metadata.get('path')}")
```

### Step 3: 获取 SoT 规范

```python
print("\n📖 Step 3: 获取 SoT 规范")
print("=" * 50)

sot_results = kb.search_sot(requirement, top_k=3)
print(f"\n找到 {len(sot_results)} 个相关规范:")
for r in sot_results:
    print(f"  📄 {r.chunk.metadata.get('path')}")
```

### Step 4: 生成代码

基于以上信息，请生成符合以下要求的代码：

1. **遵循澄清后的需求范围**
2. **参考搜索到的现有代码模式**
3. **符合 SoT 规范**（状态值、角色、错误码等）
4. **技术栈**：
   - 后端：FastAPI + SQLAlchemy 2.x + Pydantic v2
   - 前端：Next.js 16 + TanStack Query v5 + shadcn/ui
5. **添加 SoT 来源标注**：`# SoT: {DOC}#{SECTION}`

### Step 5: 验证代码

```python
from agents.skills.code_factory import load_project_config

print("\n✅ Step 5: 验证代码")
print("=" * 50)

config = load_project_config(".")
# 检查生成的代码是否有违规
# violations = config.check_forbidden(generated_code)
```


