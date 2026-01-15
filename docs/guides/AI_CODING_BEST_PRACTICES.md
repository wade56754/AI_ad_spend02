# AI 代码编辑生成最佳实践

> **版本**: v1.0
> **更新日期**: 2026-01-12
> **基准**: MASTER.md v4.9, wshobson/agents 对比分析
> **核心原则**: 搜索优先 + SoT 驱动 + 防幻觉验证 + 渐进式披露

---

## 概述

本文档基于 [wshobson/agents](https://github.com/wshobson/agents) 项目与本项目 AI 代码工厂的对比分析，提炼出适用于本项目的 AI 辅助代码编辑生成最佳实践。

### 对比项目简介

| 项目 | 核心特点 | Stars |
|------|---------|-------|
| **wshobson/agents** | 67 插件 + 99 代理 + 107 技能 + 渐进式披露 | 25.1k |
| **本项目 AI 代码工厂** | 6 阶段流水线 + SoT 驱动 + 防幻觉验证器 | - |

---

## 第一章：架构对比与融合

### 1.1 架构设计对比

| 维度 | wshobson/agents | 本项目 | 融合建议 |
|------|-----------------|--------|----------|
| **核心理念** | 插件化 + 多代理协作 | 流水线 + SoT 驱动 | 插件化架构 + SoT 约束 |
| **代理数量** | 99 个专业代理 | 6 阶段 + 验证器 | 按领域拆分，控制粒度 |
| **技能系统** | 107 个渐进式披露技能 | 16 个代码块 | 扩展代码块为技能系统 |
| **Token 优化** | 三层披露 | 代码块优先查询 | 采用渐进式披露 |

### 1.2 代码生成策略对比

| 策略 | wshobson/agents | 本项目 | 最佳实践 |
|------|-----------------|--------|----------|
| **代码来源** | 插件命令 + Agent 生成 | 搜索优先 + 组装为主 | **搜索优先** |
| **幻觉控制** | Agent 自律 | CONFIRM 阶段 + SoT 验证 | **SoT 验证** |
| **来源追溯** | 无明确机制 | `# SoT: DOC#SECTION` | **必须标注** |
| **变更管理** | 无 | OpenSpec 流程 | **必须审批** |

### 1.3 验证机制对比

| 验证项 | wshobson/agents | 本项目 | 最佳实践 |
|--------|-----------------|--------|----------|
| **类型检查** | 依赖 IDE | mypy/tsc 自动验证 | **强制门禁** |
| **规范检查** | Agent 自律 | SoT 合规验证器 | **自动化** |
| **状态/角色** | 无白名单 | 白名单强制校验 | **零容忍** |
| **回归测试** | 无 | 五连拍/七连拍 | **必须通过** |

---

## 第二章：六大最佳实践

### BP-01: 渐进式技能披露架构

借鉴 wshobson/agents 的三层披露机制：

```
Layer 1: 技能元数据 (始终加载, ~50 tokens)
├── 名称 (name)
├── 激活条件 (triggers)
└── 关键词 (keywords)

Layer 2: 核心指令 (激活时加载, ~200 tokens)
├── 代码模板 (templates)
├── 约束规则 (constraints)
└── 示例片段 (examples)

Layer 3: 完整资源 (按需加载, ~500+ tokens)
├── 详细文档 (docs)
├── 边缘案例 (edge_cases)
└── 完整示例 (full_examples)
```

**实现示例**:

```python
# agents/skills/base.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Skill:
    """渐进式披露技能基类"""
    
    # Layer 1: 元数据 (始终加载)
    id: str
    name: str
    triggers: List[str]
    keywords: List[str]
    
    # Layer 2: 指令 (激活时加载)
    _instructions: Optional[str] = None
    
    # Layer 3: 资源 (按需加载)
    _resources: Optional[str] = None
    
    def get_instructions(self) -> str:
        """激活时加载核心指令"""
        if self._instructions is None:
            self._instructions = self._load_instructions()
        return self._instructions
    
    def get_resources(self) -> str:
        """按需加载完整资源"""
        if self._resources is None:
            self._resources = self._load_resources()
        return self._resources
```

---

### BP-02: SoT 驱动的代码生成 (核心优势)

本项目的核心竞争力，必须强化：

```python
# 生成任何代码前，必须执行以下步骤：

# Step 1: 查询 SoT 裁判链
SOT_PRECEDENCE = [
    "MASTER.md v4.9",       # 最高权威
    "STATE_MACHINE.md v2.9", # 状态规范
    "DATA_SCHEMA.md v5.11",  # 数据模型
    "BUSINESS_RULES.md v5.2", # 业务规则
    "API_SOT.md v9.7",      # 接口规范
    "ERROR_CODES_SOT.md v2.2", # 错误码
    "AUTH_SPEC.md v2.2",    # 认证授权
]

# Step 2: 提取白名单
DAILY_REPORT_STATES = {
    "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
    "trend_resolved", "final_pending", "final_confirmed", "final_locked"
}

VALID_ROLES = {
    "ceo", "project_owner", "finance", 
    "pitcher", "account_manager", "admin"
}

# Step 3: 生成代码时强制约束
def validate_state(state: str) -> bool:
    return state in DAILY_REPORT_STATES

# Step 4: 验证阶段二次校验
# (由 spec_compliance_verifier.py 执行)

# Step 5: 标注来源
# SoT: STATE_MACHINE.md#daily_report
class ReportStatus(str, Enum):
    RAW_SUBMITTED = "raw_submitted"
    # ...
```

---

### BP-03: 六阶段流水线

本项目的成熟架构，融合插件化优势：

```
┌─────────────────────────────────────────────────────────────────┐
│                    六阶段代码生成流水线                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1       Phase 2       Phase 3       Phase 4       Phase 5       Phase 6
│  SEARCH        SELECT        ADAPT         ASSEMBLE      VERIFY        CONFIRM
│    │             │             │              │             │             │
│    ▼             ▼             ▼              ▼             ▼             ▼
│  ┌────┐       ┌────┐       ┌────┐        ┌────┐        ┌────┐        ┌────┐
│  │搜索│  ───► │选型│  ───► │适配│  ───►  │组装│  ───►  │验证│  ───►  │确认│
│  │参考│       │评估│       │规范│        │模块│        │合规│        │追溯│
│  └────┘       └────┘       └────┘        └────┘        └────┘        └────┘
│                                                                         │
│                        ▲                    ▲                           │
│                        │                    │                           │
│                   ┌────────────────────────────────┐                    │
│                   │        技能插件系统              │                    │
│                   │  ┌──────┐ ┌──────┐ ┌──────┐   │                    │
│                   │  │领域  │ │语言  │ │代码块│   │                    │
│                   │  │技能  │ │技能  │ │  库  │   │                    │
│                   │  └──────┘ └──────┘ └──────┘   │                    │
│                   └────────────────────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**各阶段职责**:

| 阶段 | 职责 | 输出 |
|------|------|------|
| SEARCH | 从多源搜索参考代码 | 候选代码列表 |
| SELECT | 评估候选，选择最佳参考 | 最佳参考 + 适配方案 |
| ADAPT | 适配到项目规范 | 适配后代码 |
| ASSEMBLE | 组装成完整模块 | 完整功能模块 |
| VERIFY | 类型检查 + SoT 合规 | 验证报告 |
| CONFIRM | 幻觉抑制确认 | 来源追溯报告 |

---

### BP-04: 代码块优先 + 组装模式

本项目的核心优势，扩展代码块系统：

```
用户需求 
    │
    ▼
┌───────────────────────────────────┐
│  Step 1: 代码块注册表查询          │
│  (16+ 现有代码块)                  │
└───────────────────────────────────┘
    │
    ├── 命中 ──────────────────┐
    │                          ▼
    │                    ┌──────────┐
    │                    │直接使用   │
    │                    │代码块    │
    │                    └──────────┘
    │
    └── 未命中 ─────────────────┐
                                ▼
                    ┌───────────────────────┐
                    │  Step 2: 进入搜索流程   │
                    └───────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐        ┌──────────────┐
            │本项目代码搜索 │        │代码库搜索    │
            └──────────────┘        └──────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    ┌───────────────────────┐
                    │  Step 3: AI 生成       │
                    │  (无参考时)            │
                    └───────────────────────┘
```

**现有代码块索引 (16 个)**:

| 类别 | ID | 名称 | 用途 |
|------|-----|------|------|
| 前端 | CB-FE-001 | DataTable | 表格、分页、排序 |
| 前端 | CB-FE-002 | StatusBadge | 状态徽章 |
| 前端 | CB-FE-003 | DataState | 加载、空状态 |
| 前端 | CB-FE-004 | ActionButtons | 操作按钮 |
| 前端 | CB-FE-005 | GlobalFilters | 全局筛选 |
| 前端 | CB-FE-006 | PageHeader | 页面标题 |
| 前端 | CB-FE-007 | ApprovalTimeline | 审批时间线 |
| 前端 | CB-FE-008 | FormDialog | 表单弹窗 |
| 后端 | CB-BE-001 | Pagination | 分页 |
| 后端 | CB-BE-002 | ResponseEnvelope | 响应封装 |
| 后端 | CB-BE-003 | ErrorCodes | 错误码 |
| 后端 | CB-BE-004 | PermissionFilter | 权限过滤 |
| 后端 | CB-BE-005 | StateMachine | 状态机 |
| 后端 | CB-BE-006 | AuditLog | 审计日志 |
| 后端 | CB-BE-007 | LedgerEntry | 账本条目 |
| 后端 | CB-BE-008 | KPICalculator | KPI 计算 |

---

### BP-05: 防幻觉双重门禁

融合 wshobson/agents 的模型策略与本项目的 SoT 验证：

```python
# agents/skills/verifiers/hallucination_guard.py

class HallucinationGuard:
    """防幻觉双重门禁"""
    
    def __init__(self, sot_loader: SotLoader):
        self.sot_loader = sot_loader
    
    def verify(self, generated_code: str) -> VerifyResult:
        """执行双重门禁验证"""
        issues = []
        
        # Gate 1: SoT 白名单验证
        states = self._extract_states(generated_code)
        for state in states:
            if state not in self.sot_loader.get_valid_states():
                issues.append(HallucinationIssue(
                    type="INVALID_STATE",
                    value=state,
                    message=f"状态 '{state}' 不在 STATE_MACHINE.md 白名单中",
                    severity="BLOCKING"
                ))
        
        roles = self._extract_roles(generated_code)
        for role in roles:
            if role not in self.sot_loader.get_valid_roles():
                issues.append(HallucinationIssue(
                    type="INVALID_ROLE",
                    value=role,
                    message=f"角色 '{role}' 不在 6 角色白名单中",
                    severity="BLOCKING"
                ))
        
        # Gate 2: 来源追溯检查
        blocks = self._extract_code_blocks(generated_code)
        for block in blocks:
            if not self._has_source_annotation(block):
                issues.append(SourceTrackingIssue(
                    type="MISSING_SOURCE",
                    block=block[:50],
                    message="缺少 SoT 来源标注 (# SoT: DOC#SECTION)",
                    severity="WARNING"
                ))
        
        return VerifyResult(
            success=not any(i.severity == "BLOCKING" for i in issues),
            issues=issues
        )
```

**防幻觉规则 (AH-01 ~ AH-05)**:

| ID | 规则 | 触发条件 | 处理方式 |
|----|------|---------|---------|
| AH-01 | 禁止假设数据一致 | 数据缺失 | 标记"待确认"，禁止自动填充 |
| AH-02 | 禁止自动做管理裁决 | 需要裁决 | 改为"待人工确认" |
| AH-03 | 禁止引入 SoT 未定义概念 | SoT 未覆盖 | **立即停止** → 询问用户 |
| AH-04 | 遵循 Phase 1 软性原则 | 需要阻断 | 仅提示+高亮+记录，不阻断 |
| AH-05 | 遇到歧义必须停止 | 需求歧义 | **停止** → 列出歧义点 → 询问 |

---

### BP-06: 变更管理流程 (OpenSpec)

本项目的成熟流程，必须遵守：

```
需求到达
    │
    ▼
┌─────────────────────────────────────────┐
│  是否需要 Proposal?                      │
├─────────────────────────────────────────┤
│  ✅ 需要 Proposal:                       │
│     - 新增功能/能力                       │
│     - 破坏性变更 (API, Schema)            │
│     - 架构变更                            │
│     - 性能优化 (影响行为)                  │
│     - 安全模式变更                        │
│                                          │
│  ❌ 不需要 Proposal:                      │
│     - Bug 修复 (恢复预期行为)              │
│     - 格式化/注释/typo                    │
│     - 依赖更新 (非破坏性)                  │
│     - 配置变更                            │
│     - 现有行为的测试                       │
└─────────────────────────────────────────┘
    │
    ├── 需要 Proposal ──────────────────────┐
    │                                       ▼
    │                          ┌───────────────────────┐
    │                          │  OpenSpec 流程         │
    │                          │                       │
    │                          │  openspec/changes/    │
    │                          │  └── <change-id>/     │
    │                          │      ├── proposal.md  │
    │                          │      ├── tasks.md     │
    │                          │      ├── design.md    │
    │                          │      └── specs/       │
    │                          └───────────────────────┘
    │                                       │
    │                                       ▼
    │                          ┌───────────────────────┐
    │                          │  openspec validate    │
    │                          │  --strict             │
    │                          └───────────────────────┘
    │                                       │
    │                                       ▼
    │                          ┌───────────────────────┐
    │                          │  人工审批              │
    │                          └───────────────────────┘
    │
    └── 不需要 Proposal ────────────────────┐
                                            ▼
                               ┌───────────────────────┐
                               │  直接编码              │
                               └───────────────────────┘
```

---

## 第三章：代码来源标注规范

### 3.1 标准格式

```python
# SoT: {DOC}#{SECTION}
```

### 3.2 标注示例

```python
# SoT: STATE_MACHINE.md#daily_report
class ReportStatus(str, Enum):
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    # ...

# SoT: DATA_SCHEMA.md#daily_reports.amount
amount: Decimal = Field(..., description="消耗金额")

# SoT: BUSINESS_RULES.md#BR-RPT-001
def validate_report_date(self, date: date) -> bool:
    """日报日期不能是未来"""
    return date <= datetime.now().date()

# SoT: ERROR_CODES_SOT.md#RPT-001
raise BusinessError(code="RPT-001", message="日报日期不能是未来")

# SoT: API_SOT.md#POST /daily-reports
@router.post("/daily-reports")
async def create_daily_report(...):
    ...
```

### 3.3 必须标注的场景

| 场景 | 必须标注 |
|------|---------|
| 状态定义 (Enum) | ✅ |
| 角色检查 | ✅ |
| 业务规则实现 | ✅ |
| 错误码使用 | ✅ |
| API 端点定义 | ✅ |
| 数据字段定义 | ✅ |

---

## 第四章：技能系统扩展计划

### 4.1 目标结构

```
agents/skills/
├── code_blocks/           # 现有代码块 (16个)
│   ├── frontend/
│   │   ├── CB-FE-001-DataTable.yaml
│   │   ├── CB-FE-002-StatusBadge.yaml
│   │   └── ...
│   └── backend/
│       ├── CB-BE-001-Pagination.yaml
│       ├── CB-BE-002-ResponseEnvelope.yaml
│       └── ...
│
├── domain_skills/         # 新增：领域技能
│   ├── daily_report/
│   │   ├── skill.yaml     # Layer 1: 元数据
│   │   ├── instructions.md # Layer 2: 指令
│   │   └── resources/     # Layer 3: 资源
│   ├── topup/
│   │   ├── skill.yaml
│   │   ├── instructions.md
│   │   └── resources/
│   └── ledger/
│       ├── skill.yaml
│       ├── instructions.md
│       └── resources/
│
└── language_skills/       # 新增：语言技能
    ├── python/
    │   ├── pydantic_v2.yaml
    │   ├── sqlalchemy_2x.yaml
    │   └── fastapi.yaml
    └── typescript/
        ├── react_hooks.yaml
        ├── tanstack_query.yaml
        └── shadcn_ui.yaml
```

### 4.2 技能定义格式

```yaml
# agents/skills/domain_skills/daily_report/skill.yaml
id: daily-report
name: 日报管理技能
version: "1.0"

# Layer 1: 元数据 (始终加载)
triggers:
  - "日报"
  - "daily report"
  - "投手日报"
  - "趋势检测"
keywords:
  - "raw_submitted"
  - "trend_pending"
  - "final_locked"
  - "粉数"
  - "消耗"

# Layer 2: 指令路径 (激活时加载)
instructions: "./instructions.md"

# Layer 3: 资源路径 (按需加载)
resources:
  - "./resources/state_machine.md"
  - "./resources/api_examples.md"
  - "./resources/edge_cases.md"

# SoT 引用
sot_references:
  - "STATE_MACHINE.md#daily_report"
  - "DATA_SCHEMA.md#daily_reports"
  - "API_SOT.md#daily-reports"
```

---

## 第五章：验证清单

### 5.1 生成前检查

- [ ] 确认任务复杂度等级 (L1-L4)
- [ ] 确认涉及的 SoT 文档
- [ ] 确认 Phase 1 约束适用
- [ ] 查询代码块注册表

### 5.2 生成后检查

- [ ] 所有状态值在 STATE_MACHINE.md 白名单中
- [ ] 所有角色值在 6 角色白名单中
- [ ] 所有错误码在 ERROR_CODES_SOT.md 中定义
- [ ] 关键代码块有 `# SoT: DOC#SECTION` 标注
- [ ] 交互组件首行有 `'use client'`
- [ ] 使用 `DataTable` 而非 `<table>`
- [ ] 使用 `apiGet/apiPost` 而非 `fetch`
- [ ] 类型检查通过 (mypy/tsc)
- [ ] Lint 检查通过 (ruff/eslint)

### 5.3 提交前检查

- [ ] 回归测试通过 (`python run_tests.py --type regression`)
- [ ] 五连拍测试通过
- [ ] 无硬编码敏感信息
- [ ] Commit 消息格式正确

---

## 相关文档

- [AI_CODE_FACTORY_BEST_PRACTICES.md](./AI_CODE_FACTORY_BEST_PRACTICES.md) - 代码工厂最佳实践
- [AI_PROGRAMMING_BEST_PRACTICES_v3.1.md](./AI_PROGRAMMING_BEST_PRACTICES_v3.1.md) - AI 编程规范
- [AGENTS.md](../../AGENTS.md) - Agent 主规则
- [.cursorrules](../../.cursorrules) - Cursor 规则
- [openspec/AGENTS.md](../../openspec/AGENTS.md) - OpenSpec 流程

---

## 变更历史

### v1.0 (2026-01-12)

- 初始版本
- 基于 wshobson/agents 对比分析
- 提炼六大最佳实践 (BP-01 ~ BP-06)
- 定义渐进式技能披露架构
- 定义代码来源标注规范
- 定义技能系统扩展计划
