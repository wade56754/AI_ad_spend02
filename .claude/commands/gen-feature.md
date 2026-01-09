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

### Step 4.5: 前端设计审查 (调用 frontend-design skill)

**如果功能涉及前端代码，必须执行设计审查**:

```python
# 前端设计审查清单
design_checklist = {
    "设计系统一致性": {
        "颜色": "使用 CSS 变量 (--primary, --destructive, --muted 等)",
        "间距": "使用 Tailwind 标准值 (space-4, gap-6, p-4 等)",
        "字体": "使用层级规范 (text-2xl/bold, text-lg/medium 等)",
        "圆角": "统一使用 rounded-md",
    },
    "组件复用": {
        "表格": "必须使用 DataTable 组件",
        "状态": "必须使用 StatusBadge 组件",
        "表单": "必须使用 Form + FormField 模式",
        "弹窗": "必须使用 Dialog/AlertDialog",
        "加载": "必须使用 Skeleton 或 DataStateManager",
    },
    "响应式设计": {
        "网格": "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
        "隐藏": "hidden md:block / md:hidden",
    },
    "可访问性": {
        "按钮": "图标按钮需要 aria-label",
        "表单": "输入框需要关联 label",
        "对比度": ">= 4.5:1",
    },
}

# 禁止模式
forbidden_patterns = [
    "style={{}}",           # 内联样式
    "bg-[#",                # 硬编码颜色
    "<table>",              # 手写表格
    "w-[\\d+px]",           # 魔法数字
    "fetch('/api",          # 直接 fetch (应使用 apiFetch)
]
```

**审查结果输出**:
```
🎨 设计审查结果:
  ✅ 设计系统一致性: 通过
  ✅ 组件复用性: DataTable, StatusBadge
  ⚠️ 响应式设计: 建议添加移动端适配
  ✅ 可访问性: 符合 WCAG 2.1 AA
```

### Step 5: 验证代码

```python
from agents.skills.code_factory import load_project_config

print("\n✅ Step 5: 验证代码")
print("=" * 50)

config = load_project_config(".")
# 检查生成的代码是否有违规
# violations = config.check_forbidden(generated_code)
```






