# AI 编程助手使用指南 v5.0

> **版本**: v5.0 | **最后更新**: 2025-12-30

## 目录

1. [快速开始](#快速开始)
2. [CLI 命令详解](#cli-命令详解)
3. [交互模式](#交互模式)
4. [项目配置](#项目配置)
5. [知识库管理](#知识库管理)
6. [需求澄清](#需求澄清)
7. [代码生成](#代码生成)
8. [代码审查](#代码审查)
9. [Python API](#python-api)
10. [常见问题](#常见问题)

---

## 快速开始

### 安装依赖

```bash
# 进入项目目录
cd your_project

# 安装 Python 依赖
pip install pyyaml

# (可选) 安装语义搜索依赖
pip install chromadb sentence-transformers
```

### 初始化配置

```bash
# 创建默认配置文件
python -m agents.skills.code_factory.cli init
```

这会在项目根目录创建 `.codefactory.yaml` 配置文件。

### 第一次使用

```bash
# 进入交互模式
python -m agents.skills.code_factory.cli chat

# 或者一次性生成
python -m agents.skills.code_factory.cli gen "添加用户登录功能"
```

---

## CLI 命令详解

### 命令总览

| 命令 | 说明 | 示例 |
|------|------|------|
| `chat` | 进入交互模式 | `codefactory chat` |
| `gen` | 一次性代码生成 | `codefactory gen "需求描述"` |
| `init` | 初始化配置文件 | `codefactory init` |
| `kb` | 知识库管理 | `codefactory kb build` |
| `clarify` | 需求澄清 | `codefactory clarify "需求描述"` |
| `review` | 代码审查 | `codefactory review file.py` |

### 通用选项

```bash
# 查看帮助
python -m agents.skills.code_factory.cli --help

# 查看版本
python -m agents.skills.code_factory.cli --version

# 详细输出
python -m agents.skills.code_factory.cli --verbose chat

# 指定项目目录
python -m agents.skills.code_factory.cli --project-dir /path/to/project chat
```

---

## 交互模式

### 进入交互模式

```bash
python -m agents.skills.code_factory.cli chat
```

### 交互命令

在交互模式下，可以使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/exit` 或 `/quit` | 退出交互模式 |
| `/clear` | 清空对话历史 |
| `/search <query>` | 搜索知识库 |
| `/history` | 显示对话历史 |

### 使用示例

```
🤖 > 添加日报导出功能

📝 正在处理...

❓ 需要澄清的问题:
  • 这个功能的具体范围是什么？请列出包含的功能点。

📋 理解的需求:
  摘要: 添加日报导出功能
  包含: 数据导出
  数据表: daily_reports

📚 相关文档:
  • docs/sot/STATE_MACHINE.md
  • backend/services/report_service.py

💬 收到需求: 添加日报导出功能

我将帮助你实现这个功能。首先，让我检查一下相关的代码和文档...
```

---

## 项目配置

### 配置文件位置

AI 助手会按以下顺序查找配置文件：

1. `.codefactory.yaml` (项目根目录)
2. `.codefactory.yml`
3. `.claude/codefactory.yaml`
4. `.claude/codefactory.yml`

### 配置文件结构

```yaml
# .codefactory.yaml
version: "1.0"

project:
  name: "AI 广告代投系统"
  description: "广告账户管理、日报审核、充值对账"
  tech_stack:
    backend: "FastAPI + SQLAlchemy 2.x + Pydantic v2"
    frontend: "Next.js 16 + TanStack Query v5 + shadcn/ui"
    database: "PostgreSQL (via Supabase)"
    auth: "Supabase Auth"

rules:
  # SoT 文档路径
  sot_docs:
    - docs/sot/MASTER.md
    - docs/sot/STATE_MACHINE.md
    - docs/sot/DATA_SCHEMA.md
    - docs/sot/API_SOT.md
    - docs/sot/ERROR_CODES_SOT.md
  
  # 代码风格配置
  code_style:
    python:
      formatter: "ruff"
      type_checker: "mypy"
      max_line_length: 88
    typescript:
      strict: true
  
  # 禁止模式 (自动检查)
  forbidden:
    - pattern: "os\\.system"
      reason: "使用 subprocess 代替"
    - pattern: "\\.balance\\s*="
      reason: "通过 ledger 修改余额"
    - pattern: "class Config:"
      reason: "使用 model_config = ConfigDict() (Pydantic v2)"
    - pattern: "\\.dict\\(\\)"
      reason: "使用 .model_dump() (Pydantic v2)"

# 自定义提示词
preprompts:
  system: |
    你是 AI 广告系统的编程助手。
    遵循 MASTER.md v4.6 的所有规范。
    处于 Phase 1 阶段，系统照亮而非问责。

# 搜索配置
search:
  include_dirs:
    - backend/
    - frontend/src/
  exclude_dirs:
    - node_modules/
    - __pycache__/
    - .git/

# 输出配置
output:
  dir: .agents/output
```

### 创建配置文件

```bash
# 创建默认配置
python -m agents.skills.code_factory.cli init

# 强制覆盖现有配置
python -m agents.skills.code_factory.cli init --force
```

---

## 知识库管理

知识库用于索引项目文档和代码，提供智能检索能力。

### 构建索引

```bash
# 构建知识库索引
python -m agents.skills.code_factory.cli kb build

# 强制重建索引
python -m agents.skills.code_factory.cli kb build --force
```

输出示例：
```
ℹ️  正在构建知识库索引...

索引统计:
  sot:
    文档数: 5
    块数: 42
  code:
    文档数: 128
    块数: 356

✅ 索引构建完成
```

### 搜索知识库

```bash
# 搜索文档
python -m agents.skills.code_factory.cli kb search "日报状态机"

# 指定返回数量
python -m agents.skills.code_factory.cli kb search "用户权限" --top-k 10
```

输出示例：
```
搜索: '日报状态机'
找到 5 个结果:

[1] 相关度: 0.85
    来源: docs/sot/STATE_MACHINE.md
    内容: ## 日报状态机 (Daily Report Status)...

[2] 相关度: 0.72
    来源: backend/models/daily_report.py
    内容: class ReportStatus(str, Enum):...
```

### 查看统计

```bash
python -m agents.skills.code_factory.cli kb stats
```

---

## 需求澄清

在代码生成前澄清需求，减少歧义和误解。

### 基本使用

```bash
# 自动澄清
python -m agents.skills.code_factory.cli clarify "添加批量导出功能"

# 交互式澄清 (会询问问题)
python -m agents.skills.code_factory.cli clarify "添加批量导出功能" --interactive
```

### 输出示例

```
📋 澄清结果:
  清晰度: needs_clarification

## 澄清后的需求

**摘要**: 添加批量导出功能
**目标用户**: pitcher

### 功能范围
包含:
  - 数据导出

### 涉及数据表: daily_reports

### API 端点:
  - GET /api/v1/daily_reports/export: 导出数据

❓ 未回答的问题:
  • [可选] 这个功能的具体范围是什么？请列出包含的功能点。
  • [可选] 如何判断这个功能已经完成？请列出验收标准。
```

---

## 代码生成

### 一次性生成

```bash
# 基本用法
python -m agents.skills.code_factory.cli gen "添加用户登录 API"

# 指定输出目录
python -m agents.skills.code_factory.cli gen "添加用户登录 API" --output ./generated

# 指定项目模板
python -m agents.skills.code_factory.cli gen "创建新项目" --template fullstack
```

### 项目模板

| 模板 | 说明 |
|------|------|
| `fastapi` | FastAPI 后端项目 |
| `nextjs` | Next.js 前端项目 |
| `fullstack` | 全栈项目 (FastAPI + Next.js) |

---

## 代码审查

检查代码是否符合项目规范。

### 基本使用

```bash
# 审查单个文件
python -m agents.skills.code_factory.cli review backend/services/report_service.py

# 审查多个文件
python -m agents.skills.code_factory.cli review backend/services/*.py

# 输出到文件
python -m agents.skills.code_factory.cli review backend/ --output review_report.md
```

### 输出示例

```
📝 审查文件: backend/services/report_service.py

## backend/services/report_service.py
  行数: 156
  发现问题:
    ❌ 使用了旧的 Pydantic v1 语法 (class Config)
    ❌ 使用了旧的 .dict() 方法，应使用 .model_dump()

## backend/services/user_service.py
  行数: 89
  ✅ 未发现明显问题
```

---

## Python API

### 基本使用

```python
from agents.skills.code_factory import (
    CodeFactory, 
    FactoryConfig,
    create_knowledge_base,
    clarify_requirement,
)
from pathlib import Path

# 创建代码工厂
config = FactoryConfig(project_dir=Path("./my_project"))
factory = CodeFactory(config)

# 运行代码生成
result = factory.run(requirement="添加日报导出功能")

if result["success"]:
    print(f"完成 {result['tasks_executed']} 个任务")
```

### 使用知识库

```python
from agents.skills.code_factory import create_knowledge_base

# 创建知识库
kb = create_knowledge_base(project_dir="./my_project")

# 构建索引
stats = kb.build_index()
print(f"索引了 {stats['sot']['total_documents']} 个 SoT 文档")

# 搜索
results = kb.search("日报状态机", top_k=5)
for r in results:
    print(f"[{r.score:.2f}] {r.chunk.metadata['path']}")

# 获取上下文
context = kb.get_context("如何实现日报导出")
print(context.to_prompt_context())
```

### 需求澄清

```python
from agents.skills.code_factory import clarify_requirement, auto_clarify

# 自动澄清
clarified = auto_clarify("添加批量导出功能")
print(clarified.summary)
print(clarified.scope_included)

# 完整澄清 (带问题)
result = clarify_requirement("添加批量导出功能")
if result.needs_interaction:
    for q in result.required_unanswered:
        print(f"问题: {q.question}")
```

### 使用 Preprompts

```python
from agents.skills.code_factory import create_preprompts, PrepromptType

# 创建 Preprompts 实例
preprompts = create_preprompts(project_dir="./my_project")

# 加载单个提示词
system_prompt = preprompts.get_system_prompt()
clarify_prompt = preprompts.get_clarify_prompt()

# 加载代码生成提示词 (含项目模板)
generate_prompt = preprompts.get_generate_prompt(template="fastapi")

# 加载完整集合
prompt_set = preprompts.load_all()
print(prompt_set.system)
```

### 使用工具

```python
from agents.skills.code_factory import Tool, ToolRegistry
from agents.skills.code_factory.tools.builtin import RunTestsTool, LintCodeTool

# 创建工具注册表
registry = ToolRegistry()

# 注册工具
registry.register(RunTestsTool(project_dir=Path("./my_project")))
registry.register(LintCodeTool(project_dir=Path("./my_project")))

# 执行工具
result = registry.execute("run_tests", path="tests/", verbose=True)
if result.success:
    print(result.output)
else:
    print(f"错误: {result.error}")
```

### 项目配置

```python
from agents.skills.code_factory import load_project_config

# 加载配置
config = load_project_config(project_dir="./my_project")

# 访问配置
print(config.name)
print(config.tech_stack.backend)

# 检查代码违规
violations = config.check_forbidden("""
class MyModel(BaseModel):
    class Config:
        orm_mode = True
""")

for v in violations:
    print(f"违规: {v['pattern']} - {v['reason']}")
```

---

## 常见问题

### Q: 如何自定义提示词？

A: 有两种方式：

**方式 1: 配置文件**
```yaml
# .codefactory.yaml
preprompts:
  system: |
    你是一个专门为本项目服务的 AI 助手...
```

**方式 2: 项目级覆盖**

在 `.claude/prompts/` 目录下创建同名文件覆盖内置模板：
```
.claude/prompts/
├── system.md      # 覆盖系统提示词
├── generate.md    # 覆盖生成提示词
└── review.md      # 覆盖审查提示词
```

### Q: 如何添加自定义禁止模式？

A: 在配置文件中添加：

```yaml
rules:
  forbidden:
    - pattern: "print\\("
      reason: "使用 logging 代替 print"
      severity: "warning"
```

### Q: 知识库支持哪些文件类型？

A: 目前支持：
- Markdown (`.md`)
- Python (`.py`)
- TypeScript (`.ts`, `.tsx`)
- JavaScript (`.js`, `.jsx`)
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)

### Q: 如何启用语义搜索？

A: 需要安装额外依赖并提供嵌入函数：

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embedding_fn(text):
    return model.encode(text).tolist()

kb = create_knowledge_base(
    project_dir="./my_project",
    embedding_fn=embedding_fn,
)
```

### Q: 如何查看详细日志？

A: 使用 `--verbose` 选项：

```bash
python -m agents.skills.code_factory.cli --verbose chat
```

---

## 更多资源

- [README.md](../README.md) - 架构设计和技术细节
- [.codefactory.yaml 示例](../config/project_config.py) - 完整配置示例
- [Preprompts 模板](../prompts/templates/) - 内置提示词模板

---

*文档版本: v1.0 | 生成时间: 2025-12-30*

