# AI 代码工厂重构方案

> **版本**: v1.0
> **日期**: 2025-12-17
> **状态**: Draft
> **作者**: wade

---

## 1. 执行摘要

### 1.1 重构目标

将现有的 AI 代码生成系统从"从零生成"模式重构为"搜索→选型→适配→组装"的**组装器模式**，并预留自学习能力的扩展接口。

### 1.2 核心理念

```
传统模式: 需求 → AI 凭空生成 → 高幻觉风险
组装器模式: 需求 → 搜索参考 → 适配改良 → 组装成品 → 低幻觉、高可靠
```

### 1.3 预期收益

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 代码接受率 | ~50% | >80% | +60% |
| 幻觉发生率 | ~30% | <5% | -83% |
| 开发效率 | 基准 | 3x | +200% |
| 代码可追溯性 | 无 | 100% | - |

---

## 2. 现状分析

### 2.1 现有架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    现有 Agent 系统                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   OrchestratorAgent (总控)                                      │
│       ├── BEAgent (后端生成)                                    │
│       │     └── be_dev_skill (prompt → LLM → 代码)             │
│       ├── FEAgent (前端生成)                                    │
│       │     └── fe_dev_skill (prompt → LLM → 代码)             │
│       ├── TestAgent (测试生成)                                  │
│       ├── DocAgent (文档生成)                                   │
│       └── CodeReviewAgent (代码审查)                            │
│                                                                 │
│   问题:                                                         │
│   • 从零生成，无参考代码                                         │
│   • 依赖大量 SoT 文档作为上下文                                  │
│   • 生成代码无法追溯来源                                         │
│   • 无学习能力，每次独立生成                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 现有问题

| 问题 | 影响 | 根因 |
|------|------|------|
| AI 幻觉 | 生成不存在的字段/状态/API | 无真实代码参考 |
| 代码风格不一致 | 需要大量人工修改 | 未学习项目规范 |
| 重复劳动 | 每次都从零生成相似功能 | 无代码复用机制 |
| 不可追溯 | 难以审查和维护 | 未标注代码来源 |
| 无法改进 | 相同错误反复出现 | 无学习反馈机制 |

### 2.3 现有资产（可复用）

- ✅ Agent 协议和基础架构 (`AgentProtocol`, `AgentContext`)
- ✅ LLM 客户端 (`llm_client.py` - 支持 Anthropic API / Claude Code)
- ✅ 文件操作工具 (`fs_tool.py`)
- ✅ SoT 守护 (`sot_guard_skill.py`)
- ✅ SuperClaude Skill 框架 (`.claude/skills/`)
- ✅ 58k 行 SoT 文档（可精简后作为约束）

---

## 3. 目标架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI 代码工厂 v2.0 - 组装器架构                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              SuperClaude Skill Layer (声明层)                  │ │
│  │                                                               │ │
│  │  ai-ad-code-factory/SKILL.md                                  │ │
│  │    ├── ai-ad-code-searcher      (搜索)                       │ │
│  │    ├── ai-ad-code-selector      (选型)                       │ │
│  │    ├── ai-ad-code-adapter       (适配)                       │ │
│  │    ├── ai-ad-code-assembler     (组装)                       │ │
│  │    └── ai-ad-code-verifier      (验证)                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Python Agent Layer (执行层)                       │ │
│  │                                                               │ │
│  │  CodeFactoryAgent                                             │ │
│  │    ├── CodeSearcherSkill        (代码搜索)                    │ │
│  │    ├── CodeSelectorSkill        (选型评估)                    │ │
│  │    ├── CodeAdapterSkill         (代码适配)                    │ │
│  │    ├── CodeAssemblerSkill       (代码组装)                    │ │
│  │    └── CodeVerifierSkill        (代码验证)                    │ │
│  │                                                               │ │
│  │  复用现有:                                                    │ │
│  │    ├── BEAgent / be_dev_skill   (后端生成能力)                │ │
│  │    ├── FEAgent / fe_dev_skill   (前端生成能力)                │ │
│  │    └── sot_guard_skill          (SoT 合规检查)                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Code Library (代码资料库)                         │ │
│  │                                                               │ │
│  │  code-library/                                                │ │
│  │    ├── inventory/               (本项目功能清单)              │ │
│  │    ├── references/              (GitHub 参考索引)             │ │
│  │    ├── snippets/                (代码片段库)                  │ │
│  │    ├── templates/               (适配模板)                    │ │
│  │    └── knowledge/               (学习知识库 - Phase 2)        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         组装器工作流程                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   输入: "添加日报批量导出 Excel 功能"                                │
│                                                                     │
│   Phase 1: SEARCH (搜索)                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  搜索优先级:                                                 │  │
│   │  1. 本项目代码 → 找到 batch_import 可参考                    │  │
│   │  2. 代码资料库 → 找到 fastapi-excel 参考实现                 │  │
│   │  3. GitHub → 补充搜索                                        │  │
│   │                                                             │  │
│   │  输出: 候选代码列表 (按相关度排序)                           │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│   Phase 2: SELECT (选型)                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  评估维度:                                                   │  │
│   │  • 技术栈匹配度 (FastAPI/Next.js 版本)                       │  │
│   │  • 功能覆盖度                                                │  │
│   │  • 适配成本                                                  │  │
│   │  • 代码质量                                                  │  │
│   │                                                             │  │
│   │  输出: 最佳参考 + 适配方案                                   │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│   Phase 3: ADAPT (适配)                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  适配层次:                                                   │  │
│   │  1. 技术栈适配 (Pydantic v2, SQLAlchemy 2.x)                │  │
│   │  2. 项目规范适配 (响应格式, 错误码, 命名)                    │  │
│   │  3. SoT 合规适配 (字段/状态/类型)                            │  │
│   │  4. 功能定制 (按需求调整)                                    │  │
│   │                                                             │  │
│   │  输出: 适配后的代码 (标注所有改动点)                         │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│   Phase 4: ASSEMBLE (组装)                                          │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  组装模式:                                                   │  │
│   │  • Backend: Schema → Service → Router                       │  │
│   │  • Frontend: Types → API → Hooks → Components → Page        │  │
│   │                                                             │  │
│   │  输出: 完整功能模块                                          │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│   Phase 5: VERIFY (验证)                                            │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │  检查项:                                                     │  │
│   │  • 类型检查 (mypy/tsc)                                      │  │
│   │  • SoT 合规检查                                              │  │
│   │  • 测试执行                                                  │  │
│   │                                                             │  │
│   │  失败 → 回到 ADAPT 修复 (最多 3 次)                          │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│   输出: 可用代码 + 参考来源 + 改动说明                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 实施阶段

### 4.1 阶段概览

```
┌─────────────────────────────────────────────────────────────────────┐
│  Phase 1         Phase 2         Phase 3         Phase 4           │
│  基础设施        核心能力         整合优化        学习能力(可选)     │
│  ─────────      ─────────       ─────────       ─────────          │
│                                                                     │
│  • 代码资料库    • 搜索 Skill    • 端到端测试    • 反馈收集         │
│  • 目录结构      • 选型 Skill    • SuperClaude   • 知识积累         │
│  • 本项目清单    • 适配 Skill      整合          • 自动优化         │
│  • 参考索引      • 组装 Skill    • 性能优化                         │
│                 • 验证 Skill                                        │
│                                                                     │
│  预计: 1 周      预计: 2 周       预计: 1 周      预计: 2 周         │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Phase 1: 基础设施建设

**目标**: 建立代码资料库和目录结构

#### 4.2.1 目录结构

```
AI_ad_spend02/
├── code-library/                      # 🆕 代码资料库
│   ├── inventory/                     # 本项目功能清单
│   │   ├── backend-features.yaml      # 后端功能清单
│   │   ├── frontend-features.yaml     # 前端功能清单
│   │   └── components.yaml            # 组件清单
│   │
│   ├── references/                    # 外部参考索引
│   │   ├── github-repos.yaml          # GitHub 仓库索引
│   │   ├── by-feature/                # 按功能分类
│   │   │   ├── excel-export.yaml
│   │   │   ├── pagination.yaml
│   │   │   ├── file-upload.yaml
│   │   │   └── ...
│   │   └── by-tech/                   # 按技术分类
│   │       ├── fastapi.yaml
│   │       ├── nextjs.yaml
│   │       └── shadcn.yaml
│   │
│   ├── snippets/                      # 代码片段库
│   │   ├── backend/
│   │   │   ├── excel-export/
│   │   │   ├── pagination/
│   │   │   └── ...
│   │   └── frontend/
│   │       ├── data-table/
│   │       ├── export-button/
│   │       └── ...
│   │
│   ├── templates/                     # 适配模板
│   │   ├── adaptation-checklist.md    # 适配检查清单
│   │   ├── pydantic-v2.yaml           # Pydantic v2 转换规则
│   │   ├── sqlalchemy-2.yaml          # SQLAlchemy 2 转换规则
│   │   └── project-standards.yaml     # 项目规范
│   │
│   └── knowledge/                     # 学习知识库 (Phase 4)
│       ├── patterns/                  # 成功模式
│       ├── anti-patterns/             # 失败案例
│       └── history/                   # 执行历史
│
├── agents/
│   ├── agent_core/
│   │   ├── code_factory_agent.py      # 🆕 代码工厂 Agent
│   │   └── ... (现有 agents)
│   │
│   ├── skills/
│   │   ├── code_searcher_skill.py     # 🆕 代码搜索
│   │   ├── code_selector_skill.py     # 🆕 选型评估
│   │   ├── code_adapter_skill.py      # 🆕 代码适配
│   │   ├── code_assembler_skill.py    # 🆕 代码组装
│   │   ├── code_verifier_skill.py     # 🆕 代码验证
│   │   └── ... (现有 skills)
│   │
│   └── tools/
│       ├── code_search_tool.py        # 🆕 代码搜索工具
│       └── ... (现有 tools)
│
└── .claude/
    └── skills/
        ├── ai-ad-code-factory/        # 🆕 SuperClaude Skill
        │   └── SKILL.md
        ├── ai-ad-code-searcher/
        │   └── SKILL.md
        ├── ai-ad-code-selector/
        │   └── SKILL.md
        ├── ai-ad-code-adapter/
        │   └── SKILL.md
        └── ai-ad-code-assembler/
            └── SKILL.md
```

#### 4.2.2 本项目功能清单模板

```yaml
# code-library/inventory/backend-features.yaml

version: "1.0"
updated: "2024-12-17"

features:
  auth:
    - name: "JWT 认证"
      files:
        - backend/core/security.py
        - backend/routers/auth.py
      status: completed
      reusable: true
      tags: [auth, jwt, security]

    - name: "角色权限 RBAC"
      files:
        - backend/core/dependencies.py
      status: completed
      reusable: true
      tags: [auth, rbac, permission]

  daily_reports:
    - name: "日报 CRUD"
      files:
        - backend/routers/daily_reports.py
        - backend/services/daily_report_service.py
        - backend/schemas/daily_report.py
      status: completed
      reusable: true
      tags: [crud, daily-report]

    - name: "8状态机流转"
      files:
        - backend/services/daily_report_service.py
        - backend/models/enums.py
      status: completed
      reusable: false  # 业务特定
      tags: [state-machine, workflow]

    - name: "批量导入"
      files:
        - backend/routers/daily_reports.py
      status: completed
      reusable: true
      tags: [import, batch, excel]
      description: "可作为导出功能的参考"

    - name: "批量导出 Excel"
      files: []
      status: TODO
      tags: [export, batch, excel]

  ledger:
    - name: "双账本系统"
      files:
        - backend/services/ledger_service.py
        - backend/models/finance/ledger.py
      status: completed
      reusable: false  # 业务特定
      tags: [ledger, finance]
```

#### 4.2.3 GitHub 参考索引模板

```yaml
# code-library/references/by-feature/excel-export.yaml

feature: "Excel 导出"
updated: "2024-12-17"

references:
  - id: "excel-001"
    name: "fastapi-excel-response"
    github: "https://github.com/example/fastapi-excel"
    stars: 2500
    license: "MIT"
    tech_stack:
      - FastAPI >= 0.100
      - openpyxl >= 3.0
      - Python >= 3.10
    compatibility:
      fastapi_version: "compatible"
      pydantic_version: "v2"  # 或 v1 需适配
    code_path: "/src/excel_export.py"
    quality_score: 4.5

    features:
      - 基础 Excel 生成
      - 自定义列名
      - 日期格式化
      - 流式响应

    limitations:
      - 不支持图表
      - 大数据量需要分批

    adaptation_notes: |
      1. Pydantic 已是 v2，无需适配
      2. 需要替换响应格式为项目标准
      3. 需要添加权限检查

  - id: "excel-002"
    name: "openpyxl-examples"
    github: "https://github.com/example/openpyxl-examples"
    stars: 1800
    license: "Apache-2.0"
    # ...
```

#### 4.2.4 Phase 1 任务清单

| 任务 | 描述 | 产出 | 优先级 |
|------|------|------|--------|
| P1-01 | 创建目录结构 | `code-library/` 目录 | P0 |
| P1-02 | 扫描后端功能 | `backend-features.yaml` | P0 |
| P1-03 | 扫描前端功能 | `frontend-features.yaml` | P0 |
| P1-04 | 收集 FastAPI 参考 | `fastapi.yaml` | P1 |
| P1-05 | 收集 Next.js 参考 | `nextjs.yaml` | P1 |
| P1-06 | 收集 shadcn 参考 | `shadcn.yaml` | P1 |
| P1-07 | 编写适配检查清单 | `adaptation-checklist.md` | P1 |
| P1-08 | 编写技术栈转换规则 | `pydantic-v2.yaml` 等 | P2 |

---

### 4.3 Phase 2: 核心 Skill 开发

**目标**: 实现组装器的 5 个核心 Skill

#### 4.3.1 CodeSearcherSkill

```python
# agents/skills/code_searcher_skill.py

"""
代码搜索 Skill

职责: 从多个来源搜索与需求相关的参考代码
优先级: 本项目 > 代码资料库 > GitHub
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import yaml

@dataclass
class SearchCandidate:
    """搜索候选结果"""
    id: str
    source: str  # local_project | code_library | github
    path: str
    relevance_score: float  # 0-100
    snippet: str
    match_reason: str
    tech_stack_match: float
    adaptation_hint: Optional[str] = None

class CodeSearcherSkill:
    """代码搜索 Skill"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.code_library = base_path / "code-library"
        self.inventory = self._load_inventory()
        self.references = self._load_references()

    def search(
        self,
        requirement: str,
        sources: dict = None,
        max_candidates: int = 5,
    ) -> List[SearchCandidate]:
        """
        搜索参考代码

        Args:
            requirement: 需求描述
            sources: 搜索来源配置
            max_candidates: 最大候选数

        Returns:
            按相关度排序的候选列表
        """
        sources = sources or {
            "local_project": True,
            "code_library": True,
            "github": True,
        }

        candidates = []

        # 1. 搜索本项目
        if sources.get("local_project"):
            candidates.extend(self._search_local_project(requirement))

        # 2. 搜索代码资料库
        if sources.get("code_library"):
            candidates.extend(self._search_code_library(requirement))

        # 3. 搜索 GitHub (可选，需要网络)
        if sources.get("github"):
            candidates.extend(self._search_github(requirement))

        # 按相关度排序
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)

        return candidates[:max_candidates]

    def _search_local_project(self, requirement: str) -> List[SearchCandidate]:
        """搜索本项目代码"""
        candidates = []
        keywords = self._extract_keywords(requirement)

        # 从 inventory 中搜索
        for feature in self.inventory.get("features", {}).values():
            for item in feature:
                if self._matches_keywords(item, keywords):
                    candidates.append(SearchCandidate(
                        id=f"local-{item['name']}",
                        source="local_project",
                        path=item["files"][0] if item["files"] else "",
                        relevance_score=self._calculate_relevance(item, keywords),
                        snippet=self._get_code_snippet(item["files"]),
                        match_reason=f"本项目已有类似功能: {item['name']}",
                        tech_stack_match=100,  # 本项目代码 100% 匹配
                        adaptation_hint=item.get("description"),
                    ))

        return candidates

    def _search_code_library(self, requirement: str) -> List[SearchCandidate]:
        """搜索代码资料库"""
        candidates = []
        keywords = self._extract_keywords(requirement)

        # 搜索 references
        for ref in self.references:
            if self._matches_keywords(ref, keywords):
                candidates.append(SearchCandidate(
                    id=ref["id"],
                    source="code_library",
                    path=ref.get("code_path", ""),
                    relevance_score=self._calculate_relevance(ref, keywords),
                    snippet="",  # 需要时再加载
                    match_reason=f"代码资料库参考: {ref['name']}",
                    tech_stack_match=ref.get("compatibility", {}).get("score", 80),
                    adaptation_hint=ref.get("adaptation_notes"),
                ))

        return candidates

    def _search_github(self, requirement: str) -> List[SearchCandidate]:
        """搜索 GitHub (简化实现)"""
        # TODO: 实现 GitHub Code Search API
        return []

    def _extract_keywords(self, requirement: str) -> List[str]:
        """从需求中提取关键词"""
        # 简单实现，可以用更复杂的 NLP
        keywords = []
        keyword_map = {
            "导出": ["export", "download"],
            "excel": ["excel", "xlsx", "spreadsheet"],
            "导入": ["import", "upload"],
            "分页": ["pagination", "page"],
            "表格": ["table", "grid", "list"],
            "表单": ["form", "input"],
            "上传": ["upload", "file"],
            "图表": ["chart", "graph"],
        }

        for cn, en_list in keyword_map.items():
            if cn in requirement.lower():
                keywords.extend(en_list)
                keywords.append(cn)

        return keywords

    def _matches_keywords(self, item: dict, keywords: List[str]) -> bool:
        """检查是否匹配关键词"""
        item_text = str(item).lower()
        return any(kw.lower() in item_text for kw in keywords)

    def _calculate_relevance(self, item: dict, keywords: List[str]) -> float:
        """计算相关度分数"""
        item_text = str(item).lower()
        matched = sum(1 for kw in keywords if kw.lower() in item_text)
        return min(100, matched * 20 + 40)  # 基础分 40，每匹配一个 +20

    def _get_code_snippet(self, files: List[str], max_lines: int = 50) -> str:
        """获取代码片段"""
        if not files:
            return ""

        file_path = self.base_path / files[0]
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")[:max_lines]
            return "\n".join(lines)

        return ""

    def _load_inventory(self) -> dict:
        """加载本项目功能清单"""
        inventory_file = self.code_library / "inventory" / "backend-features.yaml"
        if inventory_file.exists():
            return yaml.safe_load(inventory_file.read_text(encoding="utf-8"))
        return {}

    def _load_references(self) -> List[dict]:
        """加载参考索引"""
        references = []
        refs_dir = self.code_library / "references" / "by-feature"
        if refs_dir.exists():
            for ref_file in refs_dir.glob("*.yaml"):
                data = yaml.safe_load(ref_file.read_text(encoding="utf-8"))
                references.extend(data.get("references", []))
        return references
```

#### 4.3.2 CodeSelectorSkill

```python
# agents/skills/code_selector_skill.py

"""
选型评估 Skill

职责: 评估候选代码，选择最佳参考方案
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .code_searcher_skill import SearchCandidate

@dataclass
class SelectionResult:
    """选型结果"""
    selected: SearchCandidate
    scores: Dict[str, float]
    adaptation_plan: Dict[str, Any]
    alternatives: List[Dict[str, Any]]

class CodeSelectorSkill:
    """选型评估 Skill"""

    # 评估权重
    WEIGHTS = {
        "tech_stack_match": 0.30,
        "feature_coverage": 0.30,
        "adaptation_cost": 0.25,
        "code_quality": 0.15,
    }

    def select(
        self,
        candidates: List[SearchCandidate],
        requirement: str,
        historical_success: Dict[str, float] = None,
    ) -> SelectionResult:
        """
        选择最佳参考代码

        Args:
            candidates: 候选代码列表
            requirement: 原始需求
            historical_success: 历史成功率 (用于学习优化)

        Returns:
            选型结果
        """
        if not candidates:
            raise ValueError("没有候选代码可选择")

        scored_candidates = []

        for candidate in candidates:
            scores = self._evaluate(candidate, requirement)

            # 应用历史成功率加成
            if historical_success and candidate.id in historical_success:
                scores["historical_bonus"] = historical_success[candidate.id] * 10

            total = self._calculate_total_score(scores)
            scored_candidates.append((candidate, scores, total))

        # 按总分排序
        scored_candidates.sort(key=lambda x: x[2], reverse=True)

        best = scored_candidates[0]

        return SelectionResult(
            selected=best[0],
            scores=best[1],
            adaptation_plan=self._create_adaptation_plan(best[0], requirement),
            alternatives=[
                {
                    "candidate_id": c[0].id,
                    "total_score": c[2],
                    "reason_not_selected": self._explain_not_selected(c, best),
                }
                for c in scored_candidates[1:3]  # 返回前 2 个备选
            ],
        )

    def _evaluate(self, candidate: SearchCandidate, requirement: str) -> Dict[str, float]:
        """评估单个候选"""
        return {
            "tech_stack_match": candidate.tech_stack_match,
            "feature_coverage": self._assess_feature_coverage(candidate, requirement),
            "adaptation_cost": self._assess_adaptation_cost(candidate),
            "code_quality": self._assess_code_quality(candidate),
        }

    def _calculate_total_score(self, scores: Dict[str, float]) -> float:
        """计算加权总分"""
        total = 0
        for key, weight in self.WEIGHTS.items():
            total += scores.get(key, 0) * weight
        total += scores.get("historical_bonus", 0)  # 历史加成
        return total

    def _assess_feature_coverage(self, candidate: SearchCandidate, requirement: str) -> float:
        """评估功能覆盖度"""
        # 简化实现
        return candidate.relevance_score

    def _assess_adaptation_cost(self, candidate: SearchCandidate) -> float:
        """评估适配成本 (越高越好，表示成本越低)"""
        if candidate.source == "local_project":
            return 95  # 本项目代码适配成本最低
        elif candidate.source == "code_library":
            return 80  # 已验证的参考
        else:
            return 60  # GitHub 需要更多验证

    def _assess_code_quality(self, candidate: SearchCandidate) -> float:
        """评估代码质量"""
        if candidate.source == "local_project":
            return 85  # 本项目代码已经过审查
        return 75  # 默认

    def _create_adaptation_plan(
        self,
        candidate: SearchCandidate,
        requirement: str,
    ) -> Dict[str, Any]:
        """创建适配方案"""
        return {
            "base_code": candidate.path,
            "source": candidate.source,
            "modifications_needed": [
                {
                    "type": "技术栈适配",
                    "description": "检查 Pydantic/SQLAlchemy 版本",
                    "effort": "low" if candidate.tech_stack_match > 90 else "medium",
                },
                {
                    "type": "项目规范适配",
                    "description": "使用项目标准响应格式和错误码",
                    "effort": "low",
                },
                {
                    "type": "SoT 合规适配",
                    "description": "检查字段/状态/类型定义",
                    "effort": "medium",
                },
            ],
            "estimated_adaptation_rate": f"{100 - (100 - candidate.tech_stack_match) * 0.5:.0f}%",
            "adaptation_hint": candidate.adaptation_hint,
        }

    def _explain_not_selected(self, candidate_tuple, best_tuple) -> str:
        """解释为什么没被选中"""
        candidate, scores, total = candidate_tuple
        best_candidate, best_scores, best_total = best_tuple

        if total < best_total - 10:
            return "综合评分较低"

        # 找出最大差距的维度
        max_diff_key = max(
            self.WEIGHTS.keys(),
            key=lambda k: best_scores.get(k, 0) - scores.get(k, 0)
        )

        return f"{max_diff_key} 评分较低"
```

#### 4.3.3 CodeAdapterSkill

```python
# agents/skills/code_adapter_skill.py

"""
代码适配 Skill

职责: 基于参考代码进行适配改良
核心原则: 保留参考代码结构，只做必要修改
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from ..agents_config import SOT_FILES, read_optional
from ..tools.llm_client import get_llm_client, extract_response_text

@dataclass
class Adaptation:
    """单个适配改动"""
    line: int
    type: str  # 技术栈适配 | 项目规范 | SoT合规 | 功能定制
    original: str
    adapted: str
    reason: str

@dataclass
class AdaptedCode:
    """适配后的代码"""
    file_path: str
    content: str
    adaptations: List[Adaptation]
    source_attribution: Dict[str, Any]

class CodeAdapterSkill:
    """代码适配 Skill"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.adaptation_rules = self._load_adaptation_rules()

    def adapt(
        self,
        reference: "SearchCandidate",
        requirement: str,
        adaptation_plan: Dict[str, Any],
        adaptation_rules: Dict[str, Any] = None,
    ) -> List[AdaptedCode]:
        """
        适配参考代码

        Args:
            reference: 选中的参考代码
            requirement: 原始需求
            adaptation_plan: 适配方案
            adaptation_rules: 自定义适配规则 (用于学习优化)

        Returns:
            适配后的代码列表
        """
        rules = adaptation_rules or self.adaptation_rules

        # 读取参考代码
        reference_code = self._read_reference_code(reference)

        # 分层适配
        adapted = reference_code
        all_adaptations = []

        # Layer 1: 技术栈适配
        adapted, adaptations = self._adapt_tech_stack(adapted, rules)
        all_adaptations.extend(adaptations)

        # Layer 2: 项目规范适配
        adapted, adaptations = self._adapt_project_standards(adapted, rules)
        all_adaptations.extend(adaptations)

        # Layer 3: SoT 合规适配
        adapted, adaptations = self._adapt_sot_compliance(adapted)
        all_adaptations.extend(adaptations)

        # Layer 4: 功能定制 (使用 LLM)
        adapted, adaptations = self._adapt_for_requirement(
            adapted, requirement, reference
        )
        all_adaptations.extend(adaptations)

        # 添加来源标注
        adapted = self._add_source_attribution(adapted, reference)

        return [AdaptedCode(
            file_path=self._determine_target_path(reference, requirement),
            content=adapted,
            adaptations=all_adaptations,
            source_attribution={
                "reference": reference.path,
                "source": reference.source,
                "adaptation_rate": self._calculate_adaptation_rate(
                    reference_code, adapted
                ),
            },
        )]

    def _adapt_tech_stack(
        self,
        code: str,
        rules: Dict[str, Any],
    ) -> tuple[str, List[Adaptation]]:
        """技术栈适配"""
        adaptations = []

        # Pydantic v1 → v2 转换
        pydantic_rules = rules.get("pydantic_v2", {})
        for pattern, replacement in pydantic_rules.get("replacements", {}).items():
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                adaptations.append(Adaptation(
                    line=0,  # 简化，实际应计算行号
                    type="技术栈适配",
                    original=pattern,
                    adapted=replacement,
                    reason="Pydantic v2 语法",
                ))

        # SQLAlchemy 转换
        # ...

        return code, adaptations

    def _adapt_project_standards(
        self,
        code: str,
        rules: Dict[str, Any],
    ) -> tuple[str, List[Adaptation]]:
        """项目规范适配"""
        adaptations = []

        # 添加项目标准导入
        project_imports = rules.get("project_standards", {}).get("imports", [])
        if project_imports:
            import_block = "\n".join(project_imports)
            if import_block not in code:
                code = import_block + "\n\n" + code
                adaptations.append(Adaptation(
                    line=1,
                    type="项目规范",
                    original="",
                    adapted=import_block,
                    reason="添加项目标准导入",
                ))

        return code, adaptations

    def _adapt_sot_compliance(self, code: str) -> tuple[str, List[Adaptation]]:
        """SoT 合规适配"""
        adaptations = []

        # 加载 SoT 文档
        state_machine = read_optional(SOT_FILES.get("STATE_MACHINE", Path()))
        data_schema = read_optional(SOT_FILES.get("DATA_SCHEMA", Path()))
        error_codes = read_optional(SOT_FILES.get("ERROR_CODES", Path()))

        # 检查并替换状态值
        # 检查并替换字段名
        # 检查并替换错误码
        # ...

        return code, adaptations

    def _adapt_for_requirement(
        self,
        code: str,
        requirement: str,
        reference: "SearchCandidate",
    ) -> tuple[str, List[Adaptation]]:
        """使用 LLM 进行功能定制"""

        prompt = f"""
你是代码适配器。基于以下参考代码，根据需求进行定制。

## 参考代码
```python
{code}
```

## 需求
{requirement}

## 适配指南
{reference.adaptation_hint or "无特别说明"}

## 规则
1. 保留参考代码的整体结构
2. 只做满足需求的必要修改
3. 用注释标注所有改动点: # [ADAPTED] 原因: xxx
4. 不要发明新的状态/字段/错误码

## 输出格式
只输出适配后的完整代码，包含改动标注注释。
"""

        client = get_llm_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        adapted_code = extract_response_text(response)

        # 解析适配标注
        adaptations = self._parse_adaptation_comments(adapted_code)

        return adapted_code, adaptations

    def _add_source_attribution(self, code: str, reference: "SearchCandidate") -> str:
        """添加来源标注"""
        attribution = f'''"""
[ADAPTED FROM] {reference.source}: {reference.path}
[ADAPTATION] 基于参考代码适配，非从零生成
"""

'''
        return attribution + code

    def _parse_adaptation_comments(self, code: str) -> List[Adaptation]:
        """解析代码中的适配标注注释"""
        adaptations = []
        pattern = r'#\s*\[ADAPTED\]\s*(.+)'

        for i, line in enumerate(code.split('\n'), 1):
            match = re.search(pattern, line)
            if match:
                adaptations.append(Adaptation(
                    line=i,
                    type="功能定制",
                    original="",
                    adapted=line.strip(),
                    reason=match.group(1),
                ))

        return adaptations

    def _calculate_adaptation_rate(self, original: str, adapted: str) -> str:
        """计算适配率 (保留了多少原代码)"""
        original_lines = set(original.strip().split('\n'))
        adapted_lines = set(adapted.strip().split('\n'))

        if not original_lines:
            return "0%"

        preserved = len(original_lines & adapted_lines)
        rate = preserved / len(original_lines) * 100

        return f"{rate:.0f}%"

    def _determine_target_path(
        self,
        reference: "SearchCandidate",
        requirement: str,
    ) -> str:
        """确定目标文件路径"""
        # 简化实现，实际应更智能
        if "export" in requirement.lower():
            return "backend/services/export_service.py"
        return "backend/services/new_service.py"

    def _read_reference_code(self, reference: "SearchCandidate") -> str:
        """读取参考代码"""
        if reference.snippet:
            return reference.snippet

        if reference.source == "local_project":
            file_path = self.base_path / reference.path
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")

        return ""

    def _load_adaptation_rules(self) -> Dict[str, Any]:
        """加载适配规则"""
        rules_file = self.base_path / "code-library/templates/adaptation-rules.yaml"
        if rules_file.exists():
            import yaml
            return yaml.safe_load(rules_file.read_text(encoding="utf-8"))

        # 默认规则
        return {
            "pydantic_v2": {
                "replacements": {
                    r"class Config:": "model_config = ConfigDict(",
                    r"@validator\(": "@field_validator(",
                }
            },
            "project_standards": {
                "imports": [
                    "from backend.core.response import StandardResponse",
                    "from backend.core.error_codes import ErrorCode",
                ]
            }
        }
```

#### 4.3.4 Phase 2 任务清单

| 任务 | 描述 | 产出 | 优先级 |
|------|------|------|--------|
| P2-01 | 实现 CodeSearcherSkill | `code_searcher_skill.py` | P0 |
| P2-02 | 实现 CodeSelectorSkill | `code_selector_skill.py` | P0 |
| P2-03 | 实现 CodeAdapterSkill | `code_adapter_skill.py` | P0 |
| P2-04 | 实现 CodeAssemblerSkill | `code_assembler_skill.py` | P0 |
| P2-05 | 实现 CodeVerifierSkill | `code_verifier_skill.py` | P0 |
| P2-06 | 实现 CodeFactoryAgent | `code_factory_agent.py` | P0 |
| P2-07 | 单元测试 | `tests/agents/test_code_factory.py` | P1 |
| P2-08 | 集成测试 | 端到端测试用例 | P1 |

---

### 4.4 Phase 3: SuperClaude 整合

**目标**: 创建 SuperClaude Skill 定义，与 Cursor 集成

#### 4.4.1 主 Skill 定义

```markdown
<!-- .claude/skills/ai-ad-code-factory/SKILL.md -->

---
name: ai-ad-code-factory
version: "2.0"
status: ready_for_production
layer: skill
owner: wade
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
---

<skill>
<name>ai-ad-code-factory</name>
<version>2.0</version>
<domain>AI_AD_SYSTEM / 代码组装工厂</domain>
<profile>Code-Assembler / Search-First / Low-Hallucination</profile>

<mission>
  作为代码组装器，通过"搜索→选型→适配→组装"的流程生成代码。

  核心原则：
  - 🔍 搜索优先: 先找现有代码，不从零写
  - 🔧 适配改良: 基于参考代码修改，而非凭空生成
  - 🧩 组装集成: 将多个片段组装成完整功能
  - ✅ 标注来源: 所有代码都标注参考来源
</mission>

<sub_skills>
  - ai-ad-code-searcher
  - ai-ad-code-selector
  - ai-ad-code-adapter
  - ai-ad-code-assembler
  - ai-ad-code-verifier
</sub_skills>

<input_contract>
  必填:
  {
    requirement: string  // 需求描述
  }

  可选:
  {
    scope: "backend" | "frontend" | "fullstack",
    search_sources: {
      local_project: boolean,
      code_library: boolean,
      github: boolean
    },
    auto_fix_iterations: number
  }
</input_contract>

<forbidden_actions>
  <forbidden id="CF-001">
    <action>在没有搜索的情况下直接生成代码</action>
    <correct_action>必须先执行 SEARCH Phase</correct_action>
  </forbidden>

  <forbidden id="CF-002">
    <action>不标注代码来源</action>
    <correct_action>所有代码必须标注来源</correct_action>
  </forbidden>

  <forbidden id="CF-003">
    <action>发明新的字段/状态/错误码</action>
    <correct_action>仅使用 SoT 中已定义的</correct_action>
  </forbidden>
</forbidden_actions>

<workflow>
  Phase 1: SEARCH
    - 搜索本项目代码
    - 搜索代码资料库
    - 搜索 GitHub (可选)

  Phase 2: SELECT
    - 评估技术栈匹配度
    - 评估功能覆盖度
    - 评估适配成本
    - 输出最佳选择

  Phase 3: ADAPT
    - 技术栈适配
    - 项目规范适配
    - SoT 合规适配
    - 功能定制

  Phase 4: ASSEMBLE
    - 组装后端模块
    - 组装前端模块
    - 处理依赖关系

  Phase 5: VERIFY
    - 类型检查
    - SoT 合规检查
    - 测试执行
</workflow>

<usage>
  示例 1: 添加导出功能
  「
  使用 ai-ad-code-factory，
  requirement = "添加日报批量导出 Excel 功能，支持按日期和状态筛选"
  」

  示例 2: 添加前端组件
  「
  使用 ai-ad-code-factory，
  requirement = "添加一个数据导出按钮组件"，
  scope = "frontend"
  」
</usage>

</skill>
```

#### 4.4.2 Phase 3 任务清单

| 任务 | 描述 | 产出 | 优先级 |
|------|------|------|--------|
| P3-01 | 编写主 Skill 定义 | `ai-ad-code-factory/SKILL.md` | P0 |
| P3-02 | 编写子 Skill 定义 | 5 个子 Skill 文件 | P1 |
| P3-03 | 添加到权限配置 | 更新 `settings.local.json` | P1 |
| P3-04 | 端到端测试 | 完整流程测试 | P0 |
| P3-05 | 文档更新 | 使用说明 | P2 |

---

### 4.5 Phase 4: 学习能力 (可选)

**目标**: 添加自学习能力，持续改进

#### 4.5.1 学习组件

| 组件 | 职责 | 优先级 |
|------|------|--------|
| FeedbackCollector | 收集用户反馈 | P2 |
| LearningEngine | 分析反馈，更新知识 | P2 |
| KnowledgeBase | 存储学习结果 | P2 |

#### 4.5.2 Phase 4 任务清单 (延后)

| 任务 | 描述 | 产出 | 优先级 |
|------|------|------|--------|
| P4-01 | 实现反馈收集器 | `feedback_collector.py` | P2 |
| P4-02 | 实现学习引擎 | `learning_engine.py` | P2 |
| P4-03 | 实现知识库 | `knowledge_base.py` | P2 |
| P4-04 | Git 追踪集成 | 自动检测代码修改 | P3 |

---

## 5. 关键接口定义

### 5.1 CodeFactoryAgent 接口

```python
class CodeFactoryAgent(AgentProtocol):
    """代码工厂 Agent"""

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """
        处理代码生成请求

        Request:
        {
            "requirement": str,           # 必填: 需求描述
            "scope": str,                 # 可选: backend|frontend|fullstack
            "search_sources": {           # 可选: 搜索来源
                "local_project": bool,
                "code_library": bool,
                "github": bool
            },
            "auto_fix_iterations": int,   # 可选: 自动修复次数
        }

        Response:
        {
            "success": bool,
            "data": {
                "files": [                # 生成的文件
                    {
                        "path": str,
                        "content": str,
                        "action": "create"|"modify",
                        "source_refs": [str]
                    }
                ],
                "search_results": [...],  # 搜索结果
                "selection": {...},       # 选型结果
                "adaptations": [...],     # 适配记录
                "verification": {...},    # 验证结果
            },
            "error": Optional[str]
        }
        """
        pass
```

### 5.2 Skill 接口

```python
# 搜索结果
@dataclass
class SearchCandidate:
    id: str
    source: str
    path: str
    relevance_score: float
    snippet: str
    match_reason: str
    tech_stack_match: float
    adaptation_hint: Optional[str]

# 选型结果
@dataclass
class SelectionResult:
    selected: SearchCandidate
    scores: Dict[str, float]
    adaptation_plan: Dict[str, Any]
    alternatives: List[Dict[str, Any]]

# 适配结果
@dataclass
class AdaptedCode:
    file_path: str
    content: str
    adaptations: List[Adaptation]
    source_attribution: Dict[str, Any]
```

---

## 6. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 搜索不到相关参考 | 中 | 中 | 回退到现有生成模式 |
| 适配后代码质量差 | 低 | 高 | 多轮验证 + 人工审查 |
| 代码资料库维护成本 | 中 | 中 | 半自动化更新 |
| 学习系统复杂度高 | 高 | 低 | Phase 4 可选实施 |

---

## 7. 里程碑

| 里程碑 | 内容 | 预计时间 |
|--------|------|---------|
| M1 | Phase 1 完成 - 基础设施就绪 | Week 1 |
| M2 | Phase 2 完成 - 核心 Skill 可用 | Week 3 |
| M3 | Phase 3 完成 - SuperClaude 集成 | Week 4 |
| M4 | Phase 4 完成 - 学习能力 (可选) | Week 6 |

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| 组装器模式 | 通过搜索、选型、适配、组装生成代码的模式 |
| 代码资料库 | 存储参考代码、模板、知识的目录结构 |
| 适配 | 将参考代码修改为符合项目规范的过程 |
| SoT | Source of Truth，单一真相来源 |

### 8.2 参考文档

- `.claude/PROJECT_RULES.md` - 项目规则总纲
- `docs/1.overview/MASTER.md` - 系统宪法
- `docs/2.sot/` - SoT 文档集

---

**文档结束**
