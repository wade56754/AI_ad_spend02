# AI 代码工厂 - 开源参考项目调研

> **版本**: v1.0
> **日期**: 2024-12-17
> **目的**: 为代码工厂各 Skill 找到可借鉴的开源项目

---

## 1. 调研概览

### 1.1 代码工厂 Skill 与参考项目映射

| Skill | 核心能力 | 推荐参考项目 | 优先级 |
|-------|---------|-------------|--------|
| **CodeSearcherSkill** | 代码搜索/检索 | code-graph-rag, code-rag | ⭐⭐⭐⭐⭐ |
| **CodeSelectorSkill** | 选型评估 | 自研 (规则引擎) | - |
| **CodeAdapterSkill** | 代码转换/适配 | astx, refactor, ast-transpiler | ⭐⭐⭐⭐ |
| **CodeAssemblerSkill** | 代码组装/生成 | Aider, Continue, Copier | ⭐⭐⭐⭐⭐ |
| **CodeVerifierSkill** | 代码验证 | CodeQL, mypy, SonarQube | ⭐⭐⭐⭐ |
| **整体架构** | Agent 编排 | MetaGPT, OpenHands, SWE-agent | ⭐⭐⭐⭐⭐ |

---

## 2. AI Agent 框架（整体架构参考）

### 2.1 MetaGPT ⭐⭐⭐⭐⭐

> **最推荐** - 多 Agent 协作的软件公司模拟

| 属性 | 值 |
|------|-----|
| **GitHub** | [geekan/MetaGPT](https://github.com/geekan/MetaGPT) |
| **Stars** | 45k+ |
| **License** | MIT |
| **语言** | Python |

**核心架构**:
```
┌─────────────────────────────────────────────────────────────┐
│                      MetaGPT 架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户需求                                                    │
│      ↓                                                      │
│  ┌─────────────┐                                           │
│  │ Product Mgr │ → PRD (产品需求文档)                       │
│  └─────────────┘                                           │
│      ↓                                                      │
│  ┌─────────────┐                                           │
│  │  Architect  │ → 系统设计 + API 设计                      │
│  └─────────────┘                                           │
│      ↓                                                      │
│  ┌─────────────┐                                           │
│  │  Engineer   │ → 代码实现                                 │
│  └─────────────┘                                           │
│      ↓                                                      │
│  ┌─────────────┐                                           │
│  │ QA Engineer │ → 测试用例 + 验证                          │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**可借鉴点**:
- ✅ 多角色 Agent 协作模式
- ✅ 标准化 SOP (Standard Operating Procedure)
- ✅ 消息传递机制
- ✅ 角色定义和职责划分

**代码工厂借鉴方式**:
```python
# MetaGPT 的角色定义模式
class Role(BaseModel):
    name: str
    profile: str
    goal: str
    constraints: str
    actions: List[Action]

# 可借鉴到 CodeFactoryAgent
class CodeSearcher(Role):
    name = "CodeSearcher"
    profile = "代码搜索专家"
    goal = "找到最相关的参考代码"
    constraints = "优先本项目代码，其次代码资料库"
```

---

### 2.2 OpenHands (OpenDevin) ⭐⭐⭐⭐⭐

> 自主软件开发 Agent 平台

| 属性 | 值 |
|------|-----|
| **GitHub** | [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) |
| **Stars** | 38k+ |
| **License** | MIT |
| **语言** | Python |

**核心能力**:
- 执行 Shell 命令
- 读写文件
- 浏览网页
- 与开发环境交互

**可借鉴点**:
- ✅ Agent-Computer Interface (ACI) 设计
- ✅ 沙箱执行环境
- ✅ 事件驱动架构
- ✅ 工具调用机制

---

### 2.3 SWE-agent ⭐⭐⭐⭐

> Princeton 大学开发的 GitHub Issue 自动修复 Agent

| 属性 | 值 |
|------|-----|
| **GitHub** | [princeton-nlp/SWE-agent](https://github.com/princeton-nlp/SWE-agent) |
| **Stars** | 13k+ |
| **License** | MIT |
| **语言** | Python |

**核心特点**:
- 专为软件工程任务设计的 ACI
- SWE-bench 基准测试领先
- 支持多种 LLM 后端

**可借鉴点**:
- ✅ 文件编辑接口设计
- ✅ 代码搜索策略
- ✅ 错误修复循环

---

### 2.4 Devika ⭐⭐⭐⭐

> AI 软件工程师，Devin 的开源替代

| 属性 | 值 |
|------|-----|
| **GitHub** | [stitionai/devika](https://github.com/stitionai/devika) |
| **Stars** | 18k+ |
| **License** | MIT |
| **语言** | Python |

**架构组件**:
```
┌─────────────────────────────────────────────────────────────┐
│                      Devika 架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                       │
│  │   User Interface │  Web Chat 界面                        │
│  └─────────────────┘                                       │
│           ↓                                                 │
│  ┌─────────────────┐                                       │
│  │   Agent Core    │  规划、推理、执行协调                   │
│  └─────────────────┘                                       │
│           ↓                                                 │
│  ┌─────────────────────────────────────┐                   │
│  │  Planning & Reasoning Engine        │                   │
│  │  • 任务分解                          │                   │
│  │  • 决策制定                          │                   │
│  └─────────────────────────────────────┘                   │
│           ↓                                                 │
│  ┌─────────────────────────────────────┐                   │
│  │  Research Module                    │                   │
│  │  • 关键词提取                        │                   │
│  │  • Web 搜索                          │                   │
│  └─────────────────────────────────────┘                   │
│           ↓                                                 │
│  ┌─────────────────────────────────────┐                   │
│  │  Code Generation                    │                   │
│  │  • 多语言支持                        │                   │
│  │  • 代码写入                          │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**可借鉴点**:
- ✅ 任务分解逻辑
- ✅ 研究模块 (关键词提取)
- ✅ Agent 状态追踪和可视化
- ✅ 多 LLM 支持 (Claude, GPT-4, Gemini, Ollama)

---

### 2.5 Goose (Block) ⭐⭐⭐⭐

> Block 公司的开源 AI Agent

| 属性 | 值 |
|------|-----|
| **GitHub** | [block/goose](https://github.com/block/goose) |
| **Stars** | 10k+ |
| **License** | Apache-2.0 |
| **语言** | Python |

**特点**:
- 安装、执行、编辑、测试一体化
- 可扩展架构
- 支持任意 LLM

---

## 3. 代码搜索/检索（CodeSearcherSkill 参考）

### 3.1 code-graph-rag ⭐⭐⭐⭐⭐

> **最推荐** - 基于知识图谱的代码 RAG

| 属性 | 值 |
|------|-----|
| **GitHub** | [vitali87/code-graph-rag](https://github.com/vitali87/code-graph-rag) |
| **License** | MIT |
| **语言** | Python |

**核心特性**:
```
┌─────────────────────────────────────────────────────────────┐
│                 code-graph-rag 架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  代码库                                                      │
│      ↓                                                      │
│  ┌─────────────────┐                                       │
│  │  Tree-sitter    │  AST 解析 (多语言支持)                  │
│  └─────────────────┘                                       │
│      ↓                                                      │
│  ┌─────────────────┐                                       │
│  │ Knowledge Graph │  代码关系图谱                           │
│  │  • 函数调用关系  │                                       │
│  │  • 类继承关系    │                                       │
│  │  • 模块依赖关系  │                                       │
│  └─────────────────┘                                       │
│      ↓                                                      │
│  ┌─────────────────┐                                       │
│  │  UniXcoder      │  语义向量化                            │
│  │  Embeddings     │  意图搜索 (非精确匹配)                  │
│  └─────────────────┘                                       │
│      ↓                                                      │
│  自然语言查询 → 相关代码片段                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**可借鉴点**:
- ✅ Tree-sitter AST 解析 (支持 Python, TypeScript, JavaScript 等)
- ✅ UniXcoder 语义搜索 (按功能描述搜索，非精确匹配)
- ✅ 知识图谱存储代码关系
- ✅ 自然语言查询接口

**代码工厂集成方式**:
```python
# 借鉴 code-graph-rag 的语义搜索
class CodeSearcherSkill:
    def search_by_intent(self, description: str):
        """
        按意图搜索 (如 "error handling functions")
        而非按名称搜索
        """
        # 使用 UniXcoder 将描述转为向量
        query_embedding = self.encoder.encode(description)
        # 在代码向量库中搜索
        return self.vector_db.search(query_embedding)
```

---

### 3.2 code-rag ⭐⭐⭐⭐

> 语义代码搜索工具

| 属性 | 值 |
|------|-----|
| **GitHub** | [rawveg/code-rag](https://github.com/rawveg/code-rag) |
| **License** | MIT |
| **语言** | Python |

**特点**:
- 自然语言问答
- RAG 架构
- 支持大型代码库

---

### 3.3 mcp-codebase-rag ⭐⭐⭐

> MCP 协议的代码 RAG 服务

| 属性 | 值 |
|------|-----|
| **GitHub** | [allentcm/mcp-codebase-rag](https://github.com/allentcm/mcp-codebase-rag) |
| **License** | MIT |
| **语言** | Python |

**特点**:
- Voyage embedding 模型
- 向量相似度搜索
- 文件列表和内容检索

---

### 3.4 技术方案总结

**代码搜索最佳实践**:

| 技术 | 用途 | 推荐工具 |
|------|------|---------|
| **AST 解析** | 理解代码结构 | Tree-sitter |
| **向量化** | 语义搜索 | UniXcoder, Voyage, OpenAI |
| **向量数据库** | 存储和检索 | Chroma, Pinecone, FAISS |
| **分块策略** | 代码切分 | 按函数/类边界 (非任意切分) |
| **混合搜索** | 精确+语义 | BM25 + Vector |

---

## 4. 代码转换/适配（CodeAdapterSkill 参考）

### 4.1 astx ⭐⭐⭐⭐⭐

> **最推荐** - 强大的结构化搜索替换

| 属性 | 值 |
|------|-----|
| **GitHub** | [codemodsquad/astx](https://github.com/codemodsquad/astx) |
| **License** | MIT |
| **语言** | TypeScript |

**核心能力**:
- 结构化搜索和替换
- 支持 JavaScript/TypeScript
- 通配符匹配
- VSCode 扩展

**代码示例**:
```javascript
// 搜索模式 (带通配符)
const pattern = `console.log($message)`;

// 替换模式
const replacement = `logger.info($message)`;

// astx 自动处理 AST 转换
```

**代码工厂借鉴方式**:
```python
# 借鉴 astx 的模式匹配思路
class CodeAdapterSkill:
    # 预定义的适配规则
    ADAPTATION_RULES = {
        # Pydantic v1 → v2
        "pydantic_v2": {
            "pattern": "class Config:",
            "replacement": "model_config = ConfigDict(",
        },
        # SQLAlchemy 1 → 2
        "sqlalchemy_2": {
            "pattern": "session.query($Model)",
            "replacement": "session.execute(select($Model))",
        },
    }
```

---

### 4.2 refactor (Python) ⭐⭐⭐⭐

> AST 重构工具包

| 属性 | 值 |
|------|-----|
| **GitHub** | [isidentical/refactor](https://github.com/isidentical/refactor) |
| **License** | MIT |
| **语言** | Python |

**特点**:
- 基于 Python AST
- 契约式转换 (assert-based)
- 多种转换动作

**代码示例**:
```python
from refactor import Rule, Replace

class RenamePrintToLog(Rule):
    """将 print 替换为 logger.info"""

    def match(self, node):
        assert isinstance(node, ast.Call)
        assert isinstance(node.func, ast.Name)
        assert node.func.id == "print"
        return Replace(node, self.make_log_call(node))
```

---

### 4.3 ast-transpiler ⭐⭐⭐

> 跨语言 AST 转译器

| 属性 | 值 |
|------|-----|
| **GitHub** | [carlosmiei/ast-transpiler](https://github.com/carlosmiei/ast-transpiler) |
| **License** | MIT |
| **语言** | TypeScript |

**特点**:
- TypeScript → Python/PHP/C#
- 利用 TypeScript 类型检查器
- 非 1:1 转换，支持尽可能多的特性

---

### 4.4 ts-morph ⭐⭐⭐⭐

> TypeScript AST 操作库

| 属性 | 值 |
|------|-----|
| **GitHub** | [dsherret/ts-morph](https://github.com/dsherret/ts-morph) |
| **License** | MIT |
| **语言** | TypeScript |

**特点**:
- 简化 TypeScript AST 操作
- 强类型 API
- 代码重构辅助

---

## 5. 代码组装/生成（CodeAssemblerSkill 参考）

### 5.1 Aider ⭐⭐⭐⭐⭐

> **最推荐** - AI 配对编程工具

| 属性 | 值 |
|------|-----|
| **GitHub** | [paul-gauthier/aider](https://github.com/paul-gauthier/aider) |
| **Stars** | 22k+ |
| **License** | Apache-2.0 |
| **语言** | Python |

**核心特性**:
```
┌─────────────────────────────────────────────────────────────┐
│                      Aider 架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  特性:                                                       │
│  • 多文件同时编辑                                            │
│  • 自动 Git 提交                                             │
│  • 多 LLM 支持 (GPT-4, Claude)                              │
│  • 代码地图 (repo map) - 理解项目结构                        │
│  • 编辑格式化 (diff, whole, etc.)                           │
│                                                             │
│  工作流:                                                     │
│  1. 分析项目结构 → 生成 repo map                             │
│  2. 用户请求 → 识别需要修改的文件                            │
│  3. LLM 生成 diff → 应用更改                                │
│  4. 自动 Git commit                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**可借鉴点**:
- ✅ Repo Map 技术 (项目结构概览)
- ✅ 多文件协同编辑
- ✅ Diff 格式输出
- ✅ 自动 Git 集成
- ✅ 上下文管理策略

**代码工厂借鉴方式**:
```python
# 借鉴 Aider 的 repo map 概念
class CodeAssemblerSkill:
    def get_repo_map(self):
        """
        生成项目结构概览，帮助 LLM 理解项目
        """
        return {
            "backend": {
                "routers": ["daily_reports.py", "topups.py"],
                "services": ["daily_report_service.py"],
                "models": ["daily_report.py"],
            },
            "frontend": {
                "pages": ["daily-reports/page.tsx"],
                "components": ["DataTable.tsx"],
            }
        }
```

---

### 5.2 Continue ⭐⭐⭐⭐⭐

> 开源 AI 代码助手

| 属性 | 值 |
|------|-----|
| **GitHub** | [continuedev/continue](https://github.com/continuedev/continue) |
| **Stars** | 20k+ |
| **License** | Apache-2.0 |
| **语言** | TypeScript |

**核心能力**:
- Chat (对话式编程)
- Edit Mode (内联编辑)
- Autocomplete (自动补全)
- Agents (自主任务执行)

**可借鉴点**:
- ✅ IDE 集成架构
- ✅ 多 LLM Provider 支持 (20+)
- ✅ Context Provider 系统
- ✅ 工具调用机制

---

### 5.3 Copier ⭐⭐⭐⭐

> 项目模板和代码生成

| 属性 | 值 |
|------|-----|
| **GitHub** | [copier-org/copier](https://github.com/copier-org/copier) |
| **Stars** | 2k+ |
| **License** | MIT |
| **语言** | Python |

**特点**:
- 模板渲染
- 支持模板更新/迁移
- YAML 配置

**代码工厂借鉴方式**:
```yaml
# 借鉴 Copier 的模板机制
# templates/backend-service.yaml.jinja
class {{ service_name }}Service:
    """{{ description }}"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: {{ schema_name }}Create) -> {{ model_name }}:
        """创建 {{ entity_name }}"""
        pass
```

---

### 5.4 Cookiecutter ⭐⭐⭐

> 项目脚手架工具

| 属性 | 值 |
|------|-----|
| **GitHub** | [cookiecutter/cookiecutter](https://github.com/cookiecutter/cookiecutter) |
| **Stars** | 22k+ |
| **License** | BSD-3 |
| **语言** | Python |

**特点**:
- 业界标准
- 4000+ 模板
- JSON 配置

---

## 6. 代码验证（CodeVerifierSkill 参考）

### 6.1 静态分析工具列表 ⭐⭐⭐⭐⭐

| 属性 | 值 |
|------|-----|
| **GitHub** | [analysis-tools-dev/static-analysis](https://github.com/analysis-tools-dev/static-analysis) |
| **Stars** | 13k+ |

**收录工具**:
- **Python**: mypy, pyright, ruff, pylint
- **TypeScript**: tsc, eslint
- **通用**: SonarQube, CodeQL

---

### 6.2 Mypy ⭐⭐⭐⭐⭐

> Python 静态类型检查器

| 属性 | 值 |
|------|-----|
| **GitHub** | [python/mypy](https://github.com/python/mypy) |
| **Stars** | 18k+ |
| **License** | MIT |

**代码工厂集成**:
```python
class CodeVerifierSkill:
    def verify_types(self, file_path: str) -> dict:
        """运行 mypy 类型检查"""
        result = subprocess.run(
            ["mypy", file_path, "--json-report", "-"],
            capture_output=True
        )
        return self._parse_mypy_output(result)
```

---

### 6.3 CodeQL ⭐⭐⭐⭐

> GitHub 安全代码分析

| 属性 | 值 |
|------|-----|
| **GitHub** | [github/codeql](https://github.com/github/codeql) |
| **License** | MIT |

**特点**:
- 安全漏洞检测
- AI 辅助修复建议
- SARIF 格式输出

---

### 6.4 Ruff ⭐⭐⭐⭐⭐

> 超快 Python Linter

| 属性 | 值 |
|------|-----|
| **GitHub** | [astral-sh/ruff](https://github.com/astral-sh/ruff) |
| **Stars** | 32k+ |
| **License** | MIT |
| **语言** | Rust |

**特点**:
- 比 flake8 快 10-100 倍
- 替代多个工具 (isort, pyupgrade, etc.)
- 自动修复

---

## 7. 推荐整合方案

### 7.1 架构参考

```
┌─────────────────────────────────────────────────────────────────────┐
│                    代码工厂整合架构                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  整体架构参考: MetaGPT (多角色协作) + OpenHands (ACI 设计)          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CodeSearcherSkill                                          │   │
│  │  参考: code-graph-rag (语义搜索) + Tree-sitter (AST 解析)   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CodeSelectorSkill                                          │   │
│  │  自研: 基于规则的评分引擎                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CodeAdapterSkill                                           │   │
│  │  参考: astx (模式匹配) + refactor (Python AST)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CodeAssemblerSkill                                         │   │
│  │  参考: Aider (repo map + diff) + Copier (模板)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CodeVerifierSkill                                          │   │
│  │  参考: mypy + ruff + 自研 SoT 检查                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 优先级排序

| 优先级 | 借鉴项目 | 借鉴内容 | 工作量 |
|--------|---------|---------|--------|
| **P0** | MetaGPT | 多 Agent 协作架构 | 中 |
| **P0** | Aider | Repo Map + Diff 格式 | 低 |
| **P1** | code-graph-rag | 语义代码搜索 | 高 |
| **P1** | astx | 代码转换模式 | 中 |
| **P2** | Continue | 多 LLM Provider | 低 |
| **P2** | Copier | 模板系统 | 低 |

### 7.3 快速启动建议

**第一阶段 (快速验证)**:
1. 借鉴 Aider 的 repo map 概念，实现项目结构索引
2. 使用简单的关键词搜索 (grep/glob)
3. 借鉴 astx 的模式匹配，实现基础适配规则
4. 集成 mypy + ruff 进行验证

**第二阶段 (能力增强)**:
1. 引入 Tree-sitter 进行 AST 解析
2. 引入 UniXcoder 进行语义搜索
3. 借鉴 MetaGPT 的多角色协作

---

## 8. 参考链接汇总

### AI Agent 框架
- [MetaGPT](https://github.com/geekan/MetaGPT) - 多 Agent 软件公司
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) - 自主开发 Agent
- [SWE-agent](https://github.com/princeton-nlp/SWE-agent) - GitHub Issue 修复
- [Devika](https://github.com/stitionai/devika) - AI 软件工程师
- [Goose](https://github.com/block/goose) - Block 的 AI Agent

### 代码搜索
- [code-graph-rag](https://github.com/vitali87/code-graph-rag) - 知识图谱 RAG
- [code-rag](https://github.com/rawveg/code-rag) - 语义代码搜索

### 代码转换
- [astx](https://github.com/codemodsquad/astx) - JS/TS 结构化替换
- [refactor](https://github.com/isidentical/refactor) - Python AST 重构
- [ts-morph](https://github.com/dsherret/ts-morph) - TypeScript AST

### 代码生成
- [Aider](https://github.com/paul-gauthier/aider) - AI 配对编程
- [Continue](https://github.com/continuedev/continue) - 开源代码助手
- [Copier](https://github.com/copier-org/copier) - 项目模板

### 代码验证
- [static-analysis](https://github.com/analysis-tools-dev/static-analysis) - 工具列表
- [mypy](https://github.com/python/mypy) - Python 类型检查
- [ruff](https://github.com/astral-sh/ruff) - Python Linter

---

**文档结束**
