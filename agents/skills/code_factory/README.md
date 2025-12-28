# AI 代码工厂 v4.0

> **基准文档**: MASTER.md v4.6 | **最后更新**: 2025-12-27

## 概述

AI 代码工厂是一个基于"搜索优先、组装为主"理念的代码生成系统。它不是从零生成代码，而是通过搜索现有代码、选择最佳参考、适配到项目规范、组装成完整功能的流水线方式工作。

### 核心理念

```
搜索优先 → 减少幻觉
来源追溯 → 可信可查
SoT 驱动 → 规范一致
```

### 预期收益

| 指标 | 传统 AI | 代码工厂 | 提升 |
|------|---------|----------|------|
| 代码接受率 | ~50% | >80% | +60% |
| 幻觉发生率 | ~30% | <5% | -83% |
| 代码可追溯性 | 0% | 100% | - |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI 代码工厂 v4.0 (幻觉抑制版)                  │
│                 对齐 MASTER.md v4.6 + 6 阶段流水线                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                Session 1: INITIALIZER                      │ │
│  │  1. 解析需求 (PromptStructurer)                            │ │
│  │  2. 搜索参考代码 (CodeSearcher)                            │ │
│  │  3. 生成 task_list.json (N 个子任务)                       │ │
│  │  4. 初始化项目结构 + Git                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼ (3秒自动继续)                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                Session 2+: FACTORY AGENT                   │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │               6 阶段流水线 (每个任务)                  │ │ │
│  │  │                                                      │ │ │
│  │  │  SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM │ │
│  │  │                                                      │ │ │
│  │  │  ✅ 任务完成 → 更新 task_list.json → Git commit       │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    安全模型 (Defense-in-Depth)              │ │
│  │  Layer 1: 命令白名单 (security.py)                         │ │
│  │  Layer 2: 文件系统限制 (project_dir only)                  │ │
│  │  Layer 3: SoT 合规验证 (CodeVerifier)                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 目录结构

```
agents/skills/code_factory/
├── __init__.py         # 模块导出
├── factory.py          # 主编排器 (CodeFactory)
├── task_list.py        # 任务管理 (TaskList)
├── session.py          # 会话管理 (SessionManager)
├── security.py         # 安全验证 (SecurityValidator)
├── sot_loader.py       # SoT 动态加载器
├── searcher.py         # 代码搜索器 (Phase 1)
├── selector.py         # 代码选择器 (Phase 2)
├── adapter.py          # 代码适配器 (Phase 3)
├── assembler.py        # 代码组装器 (Phase 4)
├── verifier.py         # 代码验证器 (Phase 5)
└── phase_config.py     # 阶段配置
```

### 组件职责

| 组件 | 职责 | 来源 |
|------|------|------|
| `CodeFactory` | 主编排器，协调 6 阶段流水线 | Anthropic autonomous-coding |
| `TaskList` | 任务持久化，状态只能 pending→completed | Anthropic feature_list |
| `SessionManager` | 会话管理，支持中断恢复 | 自研 |
| `SecurityValidator` | 命令白名单 + 文件系统隔离 | Anthropic + 自研 |
| `SotLoader` | 从 SoT 文档动态加载白名单 | 自研 |
| `CodeSearcher` | 多源代码搜索 | code-graph-rag, Aider |
| `CodeSelector` | 候选评估与选型 | MetaGPT, Devika |
| `CodeAdapter` | 技术栈 + 规范适配 | astx, refactor |
| `CodeAssembler` | 多文件组装 | Aider, Copier |
| `CodeVerifier` | 类型检查 + SoT 合规 | mypy, ruff |

---

## 6 阶段流水线

### Phase 1: SEARCH (搜索)

**职责**: 从多个来源搜索与需求相关的参考代码

**搜索来源**:
1. 本项目代码 (最高优先级)
2. 代码资料库 (`code-library/`)
3. GitHub (可选，需配置)

**输出**: 候选代码列表 (按相关度排序)

```python
SearchResult:
  candidates: List[SearchCandidate]
  stats: SearchStats
```

### Phase 2: SELECT (选型)

**职责**: 评估候选代码，选择最佳参考

**评估维度**:
- 技术栈匹配度 (30%)
- 功能覆盖度 (30%)
- 适配成本 (25%)
- 代码质量 (15%)

**输出**: 最佳参考 + 适配方案

```python
SelectionResult:
  selected: SearchCandidate
  scores: EvaluationScores
  adaptation_plan: AdaptationPlan
```

### Phase 3: ADAPT (适配)

**职责**: 将参考代码适配到项目规范

**适配内容**:
1. 技术栈适配 (Pydantic v2, SQLAlchemy 2.x)
2. 项目规范适配 (响应格式, 错误码, 命名)
3. SoT 合规适配 (字段/状态/类型)
4. 功能定制 (按需求调整)

**输出**: 适配后的代码 (标注所有改动点)

```python
AdaptResult:
  adapted_files: List[AdaptedFile]
  summary: AdaptationSummary
```

### Phase 4: ASSEMBLE (组装)

**职责**: 将适配后的代码组装成完整功能模块

**组装顺序**:
- 后端: Schema → Service → Router
- 前端: Types → API → Hooks → Components → Page

**输出**: 完整功能模块 + 集成指南

```python
AssembleResult:
  module: AssembledModule
  repo_map: RepoMap
  integration_guide: IntegrationGuide
```

### Phase 5: VERIFY (验证)

**职责**: 验证代码质量并自动修复

**验证内容**:
1. 类型检查 (mypy/tsc)
2. Lint 检查 (ruff/eslint)
3. SoT 合规检查
4. 自动修复 (最多 3 次迭代)

**输出**: 验证报告 + 修复后代码

```python
VerifyResult:
  verified_files: List[VerifiedFile]
  report: VerificationReport
  remaining_issues: List[Issue]
```

### Phase 6: CONFIRM (幻觉抑制确认) [v4.0 新增]

**职责**: 幻觉抑制最终确认

**确认内容**:
1. 遍历生成的每个状态值 → 追溯到 STATE_MACHINE.md
2. 遍历生成的每个角色值 → 追溯到 6 角色白名单
3. 遍历生成的每个字段 → 追溯到 DATA_SCHEMA.md
4. 遍历调用的每个 API → 确认在项目中存在
5. 生成来源追溯报告

**规则**: 任何追溯失败 → BLOCKING，必须人工介入

---

## 角色定义 (MASTER.md v4.6)

### 业务角色 (6 个)

| 角色 | 说明 | 技术映射 |
|------|------|----------|
| `ceo` | 老板：资金安全、公司盈亏、最终决策 | admin |
| `project_owner` | 项目负责人：项目盈亏、日报审核 | (通过 is_project_owner 判断) |
| `finance` | 财务：资金出入准确、数据真实、对账 | finance |
| `pitcher` | 投手：CPL 达标、日报准确、执行投放 | media_buyer |
| `account_manager` | 户管：账户分配、账户状态监控 | account_manager |
| `admin` | 管理员：系统配置（不参与业务） | admin |

### 技术角色 (数据库 CHECK 约束)

```python
TECH_ROLES = frozenset([
    'admin',           # 系统管理员
    'finance',         # 财务
    'data_operator',   # 数据运营 (兼容旧代码)
    'account_manager', # 账户管理员
    'media_buyer'      # 广告投手
])
```

---

## 安全模型

### Defense-in-Depth 三层防护

```
Layer 1: 命令白名单
├── ALLOWED_COMMANDS: 允许的命令 (ls, git, python, npm...)
├── RESTRICTED_COMMANDS: 需额外验证 (rm, chmod, kill...)
└── BLOCKED_COMMANDS: 禁止执行 (rm -rf, sudo, format...)

Layer 2: 文件系统隔离
├── 只能操作 project_dir 内的文件
├── 禁止访问敏感文件 (.env, *.pem, secrets...)
└── 禁止符号链接逃逸

Layer 3: SoT 合规验证
├── 状态值必须在 STATE_MACHINE.md 白名单中
├── 角色值必须在 6 角色白名单中
├── 字段必须在 DATA_SCHEMA.md 中定义
└── 错误码必须在 ERROR_CODES_SOT.md 中定义
```

---

## 使用指南

### 基础用法

```python
from agents.skills.code_factory import CodeFactory, FactoryConfig
from pathlib import Path

# 创建配置
config = FactoryConfig(
    project_dir=Path("./my_project"),
    max_iterations=10,      # 最多执行 10 轮
    auto_continue=True,     # 自动继续
    enable_security=True,   # 启用安全检查
    enable_sot_check=True,  # 启用 SoT 合规检查
)

# 创建工厂实例
factory = CodeFactory(config)

# 运行 (首次会进入初始化会话)
result = factory.run(requirement="添加用户登录 API")

# 检查结果
if result["success"]:
    print(f"完成 {result['tasks_executed']} 个任务")
else:
    print(f"错误: {result['error']}")
```

### 快捷函数

```python
from agents.skills.code_factory import run_factory

result = run_factory(
    project_dir="./my_project",
    requirement="添加日报导出功能",
    max_iterations=5,
)
```

### 恢复执行

```python
# 中断后恢复 (自动从 task_list.json 读取进度)
result = factory.run()  # 无需 requirement
```

### 单独使用组件

```python
from agents.skills.code_factory import TaskList, SecurityValidator

# 任务列表管理
tasks = TaskList(Path("./my_project"))
next_task = tasks.get_next_task()
tasks.complete_task(next_task.id, output_files=["file.py"])

# 安全验证
validator = SecurityValidator(Path("./my_project"))
result = validator.validate_command("rm -rf /")
# result.allowed = False, result.reason = "命令 'rm -rf' 被禁止执行"
```

---

## 配置选项

### FactoryConfig

```python
@dataclass
class FactoryConfig:
    # 项目路径 (必填)
    project_dir: Path

    # 搜索配置
    search_sources: Dict[str, bool] = {
        "local_project": True,   # 搜索本项目
        "code_library": True,    # 搜索代码资料库
        "github": False,         # 搜索 GitHub (需网络)
    }

    # 执行配置
    max_iterations: Optional[int] = None  # 最大迭代次数 (None=无限)
    auto_continue: bool = True            # 自动继续下一个任务
    auto_fix_iterations: int = 3          # 自动修复次数

    # 安全配置
    enable_security: bool = True          # 启用安全验证
    enable_sot_check: bool = True         # 启用 SoT 合规检查

    # 输出配置
    output_mode: str = "files"            # files | diff | preview
    verbose: bool = True                  # 详细输出
```

---

## AI 防幻觉原则

### BLOCKING 级别规则

| 原则 | 标题 | 规则 |
|------|------|------|
| AH-01 | 禁止假设数据一致 | 遇到数据缺失，标记"待确认"，禁止自动填充 |
| AH-02 | 禁止自动做管理裁决 | 禁止生成自动拒绝/暂停/终止/冻结代码 |
| AH-03 | 禁止引入 SoT 未定义概念 | 发现缺失 → 立即停止 → 询问用户 |
| AH-04 | 必须遵循 Phase 1 软性原则 | 仅提示+高亮+记录，不阻断 |
| AH-05 | 遇到歧义必须停止并询问 | 停止 → 列出歧义点 → 询问用户 |

### SoT 裁判链优先级

```
MASTER.md v4.6
    ↓
DATA_SCHEMA.md v5.2
    ↓
STATE_MACHINE.md v2.6
    ↓
BUSINESS_RULES.md v3.2
    ↓
API_SOT.md v9.0
    ↓
ERROR_CODES_SOT.md v2.1
```

---

## 代码来源标注规范

### 标准格式

```python
# SoT: {DOC}#{SECTION}
```

### 示例

```python
# SoT: STATE_MACHINE.md#daily_report
class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"

# SoT: DATA_SCHEMA.md#daily_reports.amount
amount: Decimal = Field(..., description="消耗金额")

# SoT: BUSINESS_RULES.md#BR-RPT-001
def validate_report_date(self, date: date) -> bool:
    ...

# SoT: ERROR_CODES_SOT.md#RPT-001
raise BusinessError(code="RPT-001", message="日报日期不能是未来")

# SoT: API_SOT.md#POST /daily-reports
@router.post("/daily-reports")
async def create_daily_report(...):
    ...
```

---

## 代码块优先原则

### 查询流程

```
用户需求 → 提取关键词 → 查询代码块注册表 → 匹配成功?
                                              │
                                         是 → 使用代码块
                                         否 → 进入搜索流程
```

### 代码块索引 (16 个)

**前端代码块 (8 个)**:
- CB-FE-001: DataTable (表格, 分页, 排序)
- CB-FE-002: StatusBadge (状态徽章)
- CB-FE-003: DataState (加载, 空状态)
- CB-FE-004: ActionButtons (操作按钮)
- CB-FE-005: GlobalFilters (全局筛选)
- CB-FE-006: PageHeader (页面标题)
- CB-FE-007: ApprovalTimeline (审批时间线)
- CB-FE-008: FormDialog (表单弹窗)

**后端代码块 (8 个)**:
- CB-BE-001: Pagination (分页)
- CB-BE-002: ResponseEnvelope (响应封装)
- CB-BE-003: ErrorCodes (错误码)
- CB-BE-004: PermissionFilter (权限过滤)
- CB-BE-005: StateMachine (状态机)
- CB-BE-006: AuditLog (审计日志)
- CB-BE-007: LedgerEntry (账本条目)
- CB-BE-008: KPICalculator (KPI 计算)

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v4.0 | 2025-12-27 | 对齐 MASTER.md v4.6，6 角色，Phase 6 CONFIRM |
| v3.4 | 2025-12-24 | 代码块优先原则 |
| v3.3 | 2025-12-24 | 集成防幻觉规则 |
| v3.2 | 2025-12-22 | 代码来源标注规范 |
| v3.1 | 2025-12-22 | Phase 6 CONFIRM |
| v3.0 | 2025-12-18 | 集成 Anthropic autonomous-coding |
| v2.0 | 2025-12-17 | 5 阶段流水线架构 |
| v1.0 | - | 初始版本 (从零生成) |

---

## 参考项目

| 项目 | License | 借鉴内容 |
|------|---------|----------|
| [Anthropic autonomous-coding](https://github.com/anthropics/claude-quickstarts) | Internal | 双 Agent 模式, task_list 持久化, 安全模型 |
| [MetaGPT](https://github.com/geekan/MetaGPT) | MIT | 多角色协作, 标准化 SOP |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | MIT | ACI 设计, 事件驱动 |
| [SWE-agent](https://github.com/princeton-nlp/SWE-agent) | MIT | 文件编辑接口, 错误修复循环 |
| [Aider](https://github.com/paul-gauthier/aider) | Apache 2.0 | Repo Map, 多文件编辑 |
| [code-graph-rag](https://github.com/microsoft/code-graph-rag) | MIT | 语义搜索架构 |

---

*文档版本: v1.0 | 生成时间: 2025-12-27*
