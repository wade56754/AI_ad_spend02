# 在 Claude CLI 中使用 AI 编程助手

> Claude Code 环境下的使用指南

## 概述

AI 编程助手已集成到项目中，可以在 Claude CLI (Claude Code) 环境下直接使用其能力来辅助编程。

---

## 方式一：直接调用 Python 模块

在 Claude CLI 中，可以直接让 Claude 执行 Python 代码来使用 AI 助手功能。

### 1. 需求澄清

让 Claude 帮你澄清需求：

```
请使用项目中的 clarify_requirement 函数分析这个需求："添加日报批量导出功能"
```

Claude 会执行：
```python
from agents.skills.code_factory import clarify_requirement

result = clarify_requirement("添加日报批量导出功能")
print(result.clarified_requirement.to_prompt_context())
```

### 2. 搜索知识库

让 Claude 搜索相关代码和文档：

```
请使用知识库搜索"日报状态机"相关的内容
```

Claude 会执行：
```python
from agents.skills.code_factory import create_knowledge_base

kb = create_knowledge_base(".")
kb.build_index()
results = kb.search("日报状态机", top_k=5)

for r in results:
    print(f"[{r.score:.2f}] {r.chunk.metadata.get('path')}")
    print(f"  {r.chunk.content[:200]}...")
```

### 3. 代码审查

让 Claude 审查代码：

```
请使用代码审查功能检查 backend/services/report_service.py
```

Claude 会执行：
```python
from agents.skills.code_factory import load_project_config

config = load_project_config(".")
code = open("backend/services/report_service.py").read()
violations = config.check_forbidden(code)

for v in violations:
    print(f"❌ {v['pattern']}: {v['reason']}")
```

---

## 方式二：使用 Preprompts 增强 Claude

将 Preprompts 作为上下文提供给 Claude，增强其编码能力。

### 获取系统提示词

```
请加载项目的系统提示词配置
```

```python
from agents.skills.code_factory import create_preprompts

preprompts = create_preprompts(".")
print(preprompts.get_system_prompt())
```

### 获取代码生成提示词

```
请加载 FastAPI 项目的代码生成模板
```

```python
from agents.skills.code_factory import create_preprompts, ProjectTemplate

preprompts = create_preprompts(".")
print(preprompts.get_generate_prompt(template=ProjectTemplate.FASTAPI))
```

---

## 方式三：集成到 Claude Code 工作流

### 推荐工作流

1. **开始新任务时** - 先澄清需求
```
我要实现 XXX 功能，请先用 clarify_requirement 分析需求
```

2. **查找参考代码** - 搜索知识库
```
请在知识库中搜索类似的实现
```

3. **生成代码时** - 加载相关上下文
```
请加载相关的 SoT 文档作为参考，然后生成代码
```

4. **代码完成后** - 审查检查
```
请检查生成的代码是否符合项目规范
```

---

## 常用命令模板

### 模板 1：完整的功能开发流程

```
我需要实现"XXX功能"，请按以下步骤：

1. 先用 clarify_requirement 分析需求
2. 在知识库中搜索相关代码
3. 加载相关 SoT 文档
4. 生成符合项目规范的代码
5. 检查代码是否有违规
```

### 模板 2：快速搜索

```
请在项目知识库中搜索"关键词"，列出最相关的 5 个结果
```

### 模板 3：代码审查

```
请使用项目的代码审查功能检查以下文件：
- backend/services/xxx_service.py
- frontend/src/features/xxx/hooks.ts

检查是否有 Pydantic v1 语法、错误的状态值等问题
```

### 模板 4：获取 SoT 上下文

```
我要实现日报相关功能，请从知识库获取：
1. STATE_MACHINE.md 中日报状态机的定义
2. DATA_SCHEMA.md 中 daily_reports 表的字段
3. API_SOT.md 中日报相关的 API 端点
```

---

## 快捷代码片段

### 片段 1：初始化知识库

```python
from agents.skills.code_factory import create_knowledge_base
kb = create_knowledge_base(".")
kb.build_index()
```

### 片段 2：搜索并获取上下文

```python
from agents.skills.code_factory import create_knowledge_base
kb = create_knowledge_base(".")
kb.build_index()
context = kb.get_context("你的查询")
print(context.to_prompt_context())
```

### 片段 3：需求澄清

```python
from agents.skills.code_factory import auto_clarify
clarified = auto_clarify("你的需求描述")
print(clarified.to_prompt_context())
```

### 片段 4：加载项目配置

```python
from agents.skills.code_factory import load_project_config
config = load_project_config(".")
print(f"项目: {config.name}")
print(f"技术栈: {config.tech_stack.backend}")
```

### 片段 5：检查代码违规

```python
from agents.skills.code_factory import load_project_config
config = load_project_config(".")
violations = config.check_forbidden(code_content)
for v in violations:
    print(f"❌ {v['reason']}")
```

---

## 实际使用示例

### 示例 1：实现新功能

**用户输入：**
```
我需要添加一个日报批量审批功能，请帮我分析需求并生成代码
```

**Claude 执行的步骤：**

1. 澄清需求：
```python
from agents.skills.code_factory import clarify_requirement
result = clarify_requirement("日报批量审批功能")
# 输出澄清后的需求
```

2. 搜索相关代码：
```python
from agents.skills.code_factory import create_knowledge_base
kb = create_knowledge_base(".")
kb.build_index()
results = kb.search("日报审批")
# 找到相关的现有实现
```

3. 获取 SoT 上下文：
```python
context = kb.get_sot_context("日报状态转换")
# 获取状态机定义
```

4. 生成代码（基于搜索到的参考和 SoT 规范）

5. 验证代码：
```python
from agents.skills.code_factory import load_project_config
config = load_project_config(".")
violations = config.check_forbidden(generated_code)
```

### 示例 2：代码审查

**用户输入：**
```
请审查 backend/routers/daily_report_router.py 是否符合项目规范
```

**Claude 执行：**
```python
from agents.skills.code_factory import load_project_config
from pathlib import Path

# 读取代码
code = Path("backend/routers/daily_report_router.py").read_text()

# 加载配置并检查
config = load_project_config(".")
violations = config.check_forbidden(code)

if violations:
    print("发现以下问题：")
    for v in violations:
        print(f"  ❌ {v['pattern']}: {v['reason']}")
else:
    print("✅ 代码符合项目规范")
```

---

## 注意事项

1. **首次使用前**需要构建知识库索引（只需一次）
2. **搜索结果**基于关键词匹配，可能需要尝试不同关键词
3. **代码审查**只检查预定义的禁止模式，不是完整的 lint
4. **Preprompts**可以通过 `.codefactory.yaml` 自定义

---

## 相关文档

- [完整使用指南](USER_GUIDE.md)
- [快速入门](QUICK_START.md)
- [架构设计](../README.md)


