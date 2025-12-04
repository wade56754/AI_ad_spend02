# Agent Platform 迁移方案 v1.1

> **版本**: v1.1 (MCP-Safe + 影子模式)
> **状态**: Ready for Execution
> **创建日期**: 2025-12-04
> **更新日期**: 2025-12-04
> **目标**: 将 `agents/` 安全并入 `agent_platform/`，实现 MCP-First 架构

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-04 | 初版：基础迁移方案，6 Phase 结构 |
| v1.1 | 2025-12-04 | **重大升级**：新增 MCP 安全边界、影子模式、兼容层、生态迁移、调整时间估算 |

### v1.1 变更摘要

1. **新增 MCP 安全边界设计** (第 2 章)
   - 明确 MCP 模式下严禁 LLM 调用的原则
   - 引入 `mcp_safe` 标记机制
   - `ap_run_agent` 只允许调用 `mcp_safe=True` 的 Agent

2. **重构 Phase 0 为 Freeze & 影子模式** (第 3.1 节)
   - 引入 `AGENT_PLATFORM_LEGACY` 环境变量
   - 保留 `agents/` 兼容壳而非直接删除
   - 定义观察期和安全删除条件

3. **新增兼容层与生态迁移** (第 3.6 节)
   - `.claude/commands` 调用路径迁移
   - MCP 配置更新
   - SKILL 文档同步

4. **调整时间估算**
   - 从理想化的 8h 调整为现实的 1.5 天
   - 按 Phase 粒度拆分，支持分段执行

5. **增强验收标准**
   - 每个 Phase 增加 Checklist 风格验收条件
   - 新增最终验收 Checklist

---

## 1. 现状分析

### 1.1 当前目录结构

```
AI_ad_spend02/
├── agent_platform/           # 底层平台 (~800 行代码)
│   ├── core/                 # Agent 协议定义
│   │   ├── protocol.py       # AgentProtocol, AgentContext
│   │   ├── orchestrator.py   # OrchestratorBase
│   │   ├── registry.py       # Agent 注册表
│   │   ├── run.py            # AgentRun, RunStatus
│   │   └── exceptions.py
│   ├── llm/                  # LLM 客户端抽象
│   │   ├── factory.py        # get_llm_client(), is_mcp_mode()
│   │   ├── base.py           # LLMClient, LLMResponse
│   │   └── deeprouter_client.py
│   ├── mcp/                  # MCP 服务
│   │   └── server.py         # 6 个 MCP 工具
│   └── tools/                # 工具层
│       ├── fs_tool.py
│       └── validation.py
│
├── agents/                   # Agent 实现 (~2500 行代码)
│   ├── agent_core/           # 具体 Agent
│   │   ├── fe_agent.py       # 前端 Agent (需 LLM) ⚠️
│   │   ├── be_agent.py       # 后端 Agent (需 LLM) ⚠️
│   │   ├── test_agent.py     # 测试 Agent
│   │   ├── orchestrator_agent.py
│   │   ├── doc_agent.py
│   │   └── code_review_agent.py  # 纯逻辑 ✓
│   ├── skills/               # 技能层
│   │   ├── fe_dev_skill.py   # 需 LLM ⚠️
│   │   ├── be_dev_skill.py   # 需 LLM ⚠️
│   │   ├── sot_guard_skill.py  # 纯逻辑 ✓
│   │   └── ...
│   ├── tools/                # 工具层 (与 agent_platform/tools 重复)
│   ├── agents_config.py      # 统一配置
│   ├── cli.py                # CLI 入口
│   └── server.py             # HTTP 入口
│
├── .claude/
│   ├── commands/             # 自定义命令
│   │   ├── gen-backend-mcp.md
│   │   ├── gen-frontend-mcp.md
│   │   └── ...
│   └── mcp.json              # MCP 配置 (待创建)
```

### 1.2 问题清单

| # | 问题 | 影响 | 严重度 | v1.1 解决方案 |
|---|------|------|--------|---------------|
| 1 | AgentProtocol 定义重复 | 两处定义不一致 | 中 | Phase 2 合并 |
| 2 | 工具层重复 | 维护成本高 | 中 | Phase 4 合并 |
| 3 | LLM 客户端重复 | 行为不一致 | 中 | Phase 4 合并 |
| 4 | 跨模块依赖 | mcp/server.py 导入 agents/ | 高 | Phase 1 解耦 |
| 5 | MCP 模式下 LLM Agent 被阻断 | FEAgent/BEAgent 不可用 | 高 | mcp_safe 标记 |
| 6 | 配置分散 | SOT_FILES 在多处引用 | 中 | Phase 1 统一 |
| 7 | **[新增]** 无安全回退机制 | 迁移失败无法快速恢复 | 高 | 影子模式 + LEGACY |
| 8 | **[新增]** 生态未同步 | .claude/commands 路径失效 | 中 | Phase 5 迁移 |

### 1.3 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code (外部 LLM)                    │
│           所有代码生成/文档撰写/重构决策由此完成               │
└────────────────────────────┬────────────────────────────────┘
                             │ MCP Protocol (stdio)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ agent_platform/mcp/server.py                                │
│   ├── ap_run_agent ──────▶ 仅允许 mcp_safe=True Agent       │
│   └── 导入 agents/agents_config.py ←────┐ (待解耦)          │
└──────────────────────────┬──────────────│───────────────────┘
                           │              │
┌──────────────────────────▼──────────────│───────────────────┐
│ agents/ (迁移后变为影子模式兼容壳)       │                   │
│   ├── agents_config.py ─────────────────┘                   │
│   ├── agent_core/                                            │
│   │     ├── code_review_agent.py   ✓ mcp_safe=True          │
│   │     ├── fe_agent.py            ⚠️ mcp_safe=False         │
│   │     └── ...                                              │
│   └── skills/                                                │
│         └── fe_dev_skill.py ─ 调用 LLM ─▶ MCP 模式下阻断    │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. MCP 安全边界设计

### 2.1 核心原则

```
┌────────────────────────────────────────────────────────────────────┐
│                    MCP 安全边界 - 不可违反                          │
├────────────────────────────────────────────────────────────────────┤
│  1. MCP 模式下，Claude 是唯一的 LLM                                 │
│  2. agent_platform 在 MCP 模式下严禁任何 LLM 调用                   │
│  3. ap_run_agent 只允许调用 mcp_safe=True 的 Agent                 │
│  4. 任何尝试调用 LLM 的操作必须立即失败并返回明确错误                 │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 运行模式对比

| 特性 | MCP 模式 | CLI 模式 |
|------|----------|----------|
| 触发条件 | `AGENT_PLATFORM_MODE=mcp` | 默认 / `AGENT_PLATFORM_MODE=cli` |
| LLM 调用 | **严禁** | 允许 |
| 可用 Agent | 仅 `mcp_safe=True` | 全部 |
| 主要用途 | Claude Code 工具扩展 | 独立调试/测试 |
| 入口 | `mcp/server.py` (stdio) | `cli.py` / `__main__.py` |

### 2.3 mcp_safe 标记机制

每个 Agent 必须声明 `mcp_safe` 属性：

```python
# agent_platform/agents/protocol.py

class AgentProtocol(ABC):
    """Agent 协议基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 唯一标识"""
        ...

    @property
    def mcp_safe(self) -> bool:
        """
        是否可在 MCP 模式下安全运行。

        mcp_safe=True 的条件：
        1. 不调用任何 LLM 客户端
        2. 不依赖需要 LLM 的技能
        3. 所有操作都是纯逻辑/规则检查/流程编排

        默认 False，子类需显式声明 True。
        """
        return False

    @abstractmethod
    def handle_request(self, request: Dict[str, Any], context: Optional[AgentContext] = None) -> Dict[str, Any]:
        ...
```

### 2.4 Agent 分类

| Agent | mcp_safe | 原因 | 迁移去向 |
|-------|----------|------|----------|
| `CodeReviewAgent` | `True` | 纯 SoT 规则检查 | `pure_logic/` |
| `TestAgent` | `True` | 测试编排，不调 LLM | `pure_logic/` |
| `SoTGuardAgent` | `True` | 状态机/账本守护 | `pure_logic/` |
| `WorkflowAgent` | `True` | 流程编排 | `pure_logic/` |
| `FEAgent` | `False` | 依赖 fe_dev_skill (LLM) | `deprecated/` |
| `BEAgent` | `False` | 依赖 be_dev_skill (LLM) | `deprecated/` |
| `DocAgent` | `False` | 依赖 LLM 生成文档 | `deprecated/` |
| `OrchestratorAgent` | 条件 | 取决于调用链 | 需重构 |

### 2.5 ap_run_agent 安全检查

```python
# agent_platform/mcp/tools/agent_tools.py

def run_agent(agent_name: str, payload: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    运行 Agent 的 MCP 工具。

    MCP 安全检查：
    - 如果 is_mcp_mode() == True，只允许 mcp_safe=True 的 Agent
    - 否则返回 error_kind: "MCP_SAFETY_VIOLATION"
    """
    from agent_platform.llm.factory import is_mcp_mode
    from agent_platform.agents.registry import create_agent, get_agent_meta

    # 检查 Agent 是否存在
    try:
        meta = get_agent_meta(agent_name)
    except KeyError:
        return {
            "success": False,
            "error": f"Unknown agent: {agent_name}",
            "error_kind": "AGENT_NOT_FOUND",
        }

    # MCP 安全检查
    if is_mcp_mode():
        agent = create_agent(agent_name)
        if not getattr(agent, "mcp_safe", False):
            return {
                "success": False,
                "error": (
                    f"Agent '{agent_name}' is not MCP-safe (mcp_safe=False). "
                    f"In MCP mode, only pure-logic agents can be invoked. "
                    f"Claude should perform LLM-dependent tasks directly."
                ),
                "error_kind": "MCP_SAFETY_VIOLATION",
                "mcp_safe_agents": list_mcp_safe_agents(),
            }

    # 执行 Agent
    try:
        agent = create_agent(agent_name)
        result = agent.handle_request(payload, context or {})
        return {"success": True, "agent_name": agent_name, "agent_result": result}
    except Exception as e:
        return {"success": False, "error": str(e), "error_kind": "AGENT_EXECUTION_ERROR"}


def list_mcp_safe_agents() -> List[str]:
    """列出所有 mcp_safe=True 的 Agent"""
    from agent_platform.agents.registry import list_agents, create_agent

    safe_agents = []
    for key in list_agents():
        try:
            agent = create_agent(key)
            if getattr(agent, "mcp_safe", False):
                safe_agents.append(key)
        except Exception:
            pass
    return safe_agents
```

---

## 3. 迁移步骤

### 3.0 目标架构

```
AI_ad_spend02/
├── agent_platform/               # 唯一的 Agent 平台模块
│   ├── __init__.py
│   ├── __main__.py               # CLI 入口
│   │
│   ├── mcp/                      # MCP 服务层 (主入口)
│   │   ├── __init__.py
│   │   ├── server.py             # MCP stdio 服务器
│   │   └── tools/                # MCP 工具定义
│   │       ├── __init__.py
│   │       ├── sot_tools.py      # ap_read_sot, ap_list_sot
│   │       ├── file_tools.py     # ap_read_file, ap_write_file
│   │       ├── test_tools.py     # ap_run_pytest
│   │       └── agent_tools.py    # ap_list_agents, ap_run_agent
│   │
│   ├── agents/                   # Agent 实现层
│   │   ├── __init__.py
│   │   ├── registry.py           # 统一注册表 + mcp_safe 检查
│   │   ├── protocol.py           # AgentProtocol (含 mcp_safe)
│   │   │
│   │   ├── pure_logic/           # mcp_safe=True Agent
│   │   │   ├── __init__.py
│   │   │   ├── code_review_agent.py
│   │   │   ├── sot_guard_agent.py
│   │   │   ├── test_agent.py
│   │   │   └── workflow_agent.py
│   │   │
│   │   └── deprecated/           # mcp_safe=False (保留参考)
│   │       ├── __init__.py
│   │       ├── fe_agent.py
│   │       ├── be_agent.py
│   │       └── doc_agent.py
│   │
│   ├── skills/                   # 技能层
│   │   ├── __init__.py
│   │   ├── sot_guard_skill.py    # 纯规则
│   │   ├── review_skill.py
│   │   └── deprecated/           # 需 LLM
│   │       ├── fe_dev_skill.py
│   │       └── be_dev_skill.py
│   │
│   ├── config/                   # 配置层
│   │   ├── __init__.py
│   │   ├── paths.py              # BASE_PATH, BACKEND_DIR, FRONTEND_DIR
│   │   ├── sot_files.py          # SOT_FILES 映射
│   │   └── constants.py
│   │
│   ├── tools/                    # 通用工具
│   │   ├── __init__.py
│   │   ├── fs_tool.py
│   │   ├── validation.py
│   │   └── supabase_tool.py
│   │
│   ├── llm/                      # LLM 层 (仅 CLI 模式)
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── base.py
│   │   └── deeprouter_client.py
│   │
│   └── tests/
│       └── ...
│
├── agents/                       # 影子模式兼容壳 (观察期后删除)
│   ├── __init__.py               # 转调 agent_platform
│   ├── cli.py                    # 转调 agent_platform.__main__
│   └── _DEPRECATED.md            # 废弃说明
│
├── .claude/
│   ├── commands/                 # 更新后的自定义命令
│   │   ├── gen-backend-mcp.md    # 使用 agent_platform
│   │   └── ...
│   └── mcp.json                  # ai-ad-agents MCP 配置
```

---

### Phase 0: Freeze & 影子模式准备 (预计 2h)

**目标**: 建立安全回退机制，确保迁移可随时中断和回滚。

#### 0.1 创建迁移分支

```bash
git checkout -b refactor/agent-platform-merge-v1.1
```

#### 0.2 运行基线测试

```bash
# 记录当前测试状态
pytest agent_platform/tests/ -v --tb=short > baseline_agent_platform.txt
pytest agents/tests/ -v --tb=short > baseline_agents.txt
```

#### 0.3 引入 AGENT_PLATFORM_LEGACY 环境变量

在 `agent_platform/config/constants.py` 中定义：

```python
# agent_platform/config/constants.py

import os

# 兼容模式环境变量
# 设置 AGENT_PLATFORM_LEGACY=1 时，使用旧的 agents/ 模块
LEGACY_MODE = os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"

def is_legacy_mode() -> bool:
    """检查是否启用兼容模式（使用旧 agents/ 模块）"""
    return LEGACY_MODE
```

#### 0.4 创建影子模式兼容壳

```python
# agents/__init__.py (修改为转调壳)

"""
[DEPRECATED] agents 模块 - 影子模式兼容壳

此模块已迁移至 agent_platform/agents/。
当前文件仅作为兼容层，所有调用转发至新模块。

迁移状态: 观察期
观察期结束条件:
  1. 连续 7 天无 AGENT_PLATFORM_LEGACY 回退
  2. 所有 .claude/commands 已更新
  3. CI/CD 全部通过

删除前检查清单:
  - [ ] grep -r "from agents" --include="*.py" 无结果
  - [ ] grep -r "import agents" --include="*.py" 无结果
  - [ ] .claude/commands 中无 agents.cli 引用
"""

import warnings
from agent_platform.config.constants import is_legacy_mode

if not is_legacy_mode():
    warnings.warn(
        "agents 模块已废弃，请改用 agent_platform。"
        "设置 AGENT_PLATFORM_LEGACY=1 可临时回退旧逻辑。",
        DeprecationWarning,
        stacklevel=2,
    )

    # 转发所有导出到 agent_platform
    from agent_platform.agents.registry import create_agent, list_agents
    from agent_platform.config.sot_files import SOT_FILES
    from agent_platform.config.paths import BASE_PATH, BACKEND_DIR, FRONTEND_DIR

    __all__ = [
        "create_agent",
        "list_agents",
        "SOT_FILES",
        "BASE_PATH",
        "BACKEND_DIR",
        "FRONTEND_DIR",
    ]
else:
    # Legacy 模式：保留原有逻辑
    from .agents_config import *
```

```python
# agents/cli.py (修改为转调壳)

"""
[DEPRECATED] agents CLI - 影子模式兼容壳

请改用: python -m agent_platform
"""

import sys
import warnings
from agent_platform.config.constants import is_legacy_mode

if not is_legacy_mode():
    warnings.warn(
        "agents.cli 已废弃，请改用 python -m agent_platform",
        DeprecationWarning,
    )

    # 转调新入口
    from agent_platform.__main__ import main

    if __name__ == "__main__":
        sys.exit(main())
else:
    # Legacy 模式：保留原有逻辑
    from .cli_legacy import main  # 重命名原 cli.py 为 cli_legacy.py

    if __name__ == "__main__":
        sys.exit(main())
```

#### 0.5 创建废弃说明文件

```markdown
# agents/_DEPRECATED.md

## 废弃声明

`agents/` 目录已迁移至 `agent_platform/agents/`。

### 迁移状态

- **当前状态**: 影子模式（兼容壳）
- **观察期**: 2025-12-04 ~ 2025-12-11 (7 天)
- **计划删除**: 观察期结束且满足删除条件后

### 紧急回退

如遇问题，可设置环境变量临时回退：

```bash
export AGENT_PLATFORM_LEGACY=1
python -m agents.cli ...
```

### 删除条件

1. [ ] 连续 7 天无 AGENT_PLATFORM_LEGACY 回退使用记录
2. [ ] 所有 `.claude/commands` 已更新为新路径
3. [ ] CI/CD 流水线全部通过
4. [ ] 无外部依赖此目录

### 路径映射

| 旧路径 | 新路径 |
|--------|--------|
| `agents/agents_config.py` | `agent_platform/config/` |
| `agents/agent_core/` | `agent_platform/agents/pure_logic/` |
| `agents/skills/` | `agent_platform/skills/` |
| `agents/tools/` | `agent_platform/tools/` |
| `agents/cli.py` | `agent_platform/__main__.py` |
```

#### Phase 0 验收 Checklist

- [ ] 迁移分支已创建
- [ ] 基线测试报告已生成
- [ ] `AGENT_PLATFORM_LEGACY` 环境变量已实现
- [ ] `agents/__init__.py` 已改为转调壳
- [ ] `agents/cli.py` 已改为转调壳
- [ ] `agents/_DEPRECATED.md` 已创建
- [ ] 设置 `AGENT_PLATFORM_LEGACY=1` 后，旧逻辑可正常运行
- [ ] 不设置时，显示 DeprecationWarning 并转调新模块

#### Phase 0 风险 & 回滚

| 风险 | 概率 | 缓解措施 | 回滚方式 |
|------|------|----------|----------|
| 转调壳导入错误 | 中 | 先测试单个文件 | `git checkout master -- agents/` |
| Legacy 模式判断逻辑错误 | 低 | 环境变量测试 | 修复 `is_legacy_mode()` |

---

### Phase 1: 配置层迁移 (预计 2h)

**目标**: 将 `agents/agents_config.py` 中的配置拆分到 `agent_platform/config/`。

#### 1.1 创建配置目录结构

```bash
mkdir -p agent_platform/config
touch agent_platform/config/__init__.py
```

#### 1.2 迁移路径常量

```python
# agent_platform/config/paths.py

from pathlib import Path

def _get_base_path() -> Path:
    """推断项目根路径"""
    # config/ -> agent_platform/ -> 项目根
    return Path(__file__).resolve().parent.parent.parent

BASE_PATH = _get_base_path()
PROJECT_ROOT = BASE_PATH  # 别名

BACKEND_DIR = BASE_PATH / "backend"
FRONTEND_DIR = BASE_PATH / "frontend"
DOCS_DIR = BASE_PATH / "docs"
```

#### 1.3 迁移 SOT_FILES

```python
# agent_platform/config/sot_files.py

from pathlib import Path
from typing import Dict
from .paths import BASE_PATH

SOT_FILES: Dict[str, Path] = {
    # Layer 1: Overview
    "MASTER": BASE_PATH / "docs/1.overview/MASTER.md",
    "PROJECT": BASE_PATH / "docs/1.overview/PROJECT.md",

    # Layer 2: SoT (v2.6 Freeze)
    "API_SOT": BASE_PATH / "docs/2.sot/API_SOT.md",
    "DATA_SCHEMA": BASE_PATH / "docs/2.sot/DATA_SCHEMA.md",
    "STATE_MACHINE": BASE_PATH / "docs/2.sot/STATE_MACHINE.md",
    "BUSINESS_RULES": BASE_PATH / "docs/2.sot/BUSINESS_RULES.md",
    "ERROR_CODES": BASE_PATH / "docs/2.sot/ERROR_CODES_SOT.md",
    "LEDGER_SOT": BASE_PATH / "docs/2.sot/LEDGER_SOT.md",
    "AUTH_SPEC": BASE_PATH / "docs/2.sot/AUTH_SPEC.md",
    # ... 其他 SoT 文件

    # Layer 3: Dev-Guides
    "FRONTEND_RULES": BASE_PATH / "docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md",
    "API_DEV_FLOW": BASE_PATH / "docs/3.dev-guides/API_DEVELOPMENT_FLOW.md",
    # ... 其他 Dev-Guides
}

CRITICAL_SOT_FILES = {
    "STATE_MACHINE", "DATA_SCHEMA", "BUSINESS_RULES",
    "API_SOT", "ERROR_CODES", "LEDGER_SOT", "AUTH_SPEC",
}
```

#### 1.4 更新 MCP server.py 导入

```python
# agent_platform/mcp/server.py (修改)

# 旧导入
- from agents.agents_config import SOT_FILES, create_agent, list_agents

# 新导入
+ from agent_platform.config.sot_files import SOT_FILES
+ from agent_platform.agents.registry import create_agent, list_agents
```

#### 1.5 运行验证测试

```bash
# 验证配置导入
python -c "from agent_platform.config.sot_files import SOT_FILES; print(len(SOT_FILES))"

# 验证 MCP server 启动
python -c "from agent_platform.mcp.server import _registry; print(_registry.list_tools())"
```

#### Phase 1 验收 Checklist

- [ ] `agent_platform/config/` 目录已创建
- [ ] `paths.py` 包含 BASE_PATH, BACKEND_DIR, FRONTEND_DIR
- [ ] `sot_files.py` 包含完整 SOT_FILES 映射
- [ ] `mcp/server.py` 导入路径已更新
- [ ] MCP server 可正常启动
- [ ] 转调壳 `agents/__init__.py` 可正确导入新配置

#### Phase 1 风险 & 回滚

| 风险 | 概率 | 缓解措施 | 回滚方式 |
|------|------|----------|----------|
| 路径推断错误 | 中 | 打印验证 BASE_PATH | 修复 `_get_base_path()` |
| MCP server 导入失败 | 中 | 逐个测试导入 | `git checkout -- agent_platform/mcp/server.py` |

---

### Phase 2: Agent 层迁移 (预计 3h)

**目标**: 迁移 Agent 实现，建立 `mcp_safe` 标记机制。

#### 2.1 创建统一 AgentProtocol

```python
# agent_platform/agents/protocol.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AgentContext(BaseModel):
    """Agent 执行上下文"""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_run_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentProtocol(ABC):
    """
    Agent 协议基类。

    所有 Agent 必须实现此协议。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 唯一标识符"""
        ...

    @property
    def description(self) -> str:
        """Agent 描述"""
        return ""

    @property
    def version(self) -> str:
        """Agent 版本"""
        return "1.0.0"

    @property
    def mcp_safe(self) -> bool:
        """
        是否可在 MCP 模式下安全运行。

        mcp_safe=True 的条件：
        1. 不调用任何 LLM 客户端
        2. 不依赖需要 LLM 的技能
        3. 所有操作都是纯逻辑/规则检查/流程编排

        默认 False，子类需显式声明 True。
        """
        return False

    @abstractmethod
    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """处理请求"""
        ...
```

#### 2.2 创建注册表

```python
# agent_platform/agents/registry.py

from typing import Dict, Callable, List, Any, Optional
from dataclasses import dataclass
import logging

from .protocol import AgentProtocol

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AgentMeta:
    """Agent 元信息"""
    key: str
    name: str
    description: str
    mcp_safe: bool
    factory: Callable[..., AgentProtocol]


_AGENT_REGISTRY: Dict[str, AgentMeta] = {}


def register_agent(
    key: str,
    name: str,
    description: str = "",
    mcp_safe: bool = False,
):
    """
    装饰器：注册 Agent。

    Args:
        key: Agent 唯一键（小写）
        name: Agent 显示名称
        description: Agent 描述
        mcp_safe: 是否可在 MCP 模式下运行
    """
    def decorator(cls):
        _AGENT_REGISTRY[key] = AgentMeta(
            key=key,
            name=name,
            description=description,
            mcp_safe=mcp_safe,
            factory=cls,
        )
        logger.debug(f"Registered agent: {key} (mcp_safe={mcp_safe})")
        return cls
    return decorator


def create_agent(name: str, **kwargs) -> AgentProtocol:
    """创建 Agent 实例"""
    key = name.strip().lower()
    if key not in _AGENT_REGISTRY:
        available = ", ".join(sorted(_AGENT_REGISTRY.keys()))
        raise KeyError(f"Unknown agent '{name}'. Available: {available}")
    return _AGENT_REGISTRY[key].factory(**kwargs)


def get_agent_meta(name: str) -> AgentMeta:
    """获取 Agent 元信息"""
    key = name.strip().lower()
    if key not in _AGENT_REGISTRY:
        raise KeyError(f"Unknown agent: {name}")
    return _AGENT_REGISTRY[key]


def list_agents() -> Dict[str, Dict[str, Any]]:
    """列出所有 Agent"""
    return {
        key: {
            "key": meta.key,
            "name": meta.name,
            "description": meta.description,
            "mcp_safe": meta.mcp_safe,
        }
        for key, meta in _AGENT_REGISTRY.items()
    }


def list_mcp_safe_agents() -> List[str]:
    """列出所有 mcp_safe=True 的 Agent"""
    return [key for key, meta in _AGENT_REGISTRY.items() if meta.mcp_safe]
```

#### 2.3 迁移 pure_logic Agent

```python
# agent_platform/agents/pure_logic/code_review_agent.py

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from ..protocol import AgentProtocol, AgentContext
from ..registry import register_agent
from agent_platform.skills.sot_guard_skill import validate_against_sot

logger = logging.getLogger(__name__)


@register_agent(
    key="review",
    name="CodeReviewAgent",
    description="基于 SoT 规则的代码审核 Agent",
    mcp_safe=True,  # 纯逻辑，不调用 LLM
)
class CodeReviewAgent(AgentProtocol):
    """代码审核 Agent - MCP 安全"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()

    @property
    def name(self) -> str:
        return "review"

    @property
    def mcp_safe(self) -> bool:
        return True  # 纯规则检查，不调用 LLM

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        action = request.get("action", "review")
        changes = request.get("changes", {})

        if not changes:
            return {
                "success": True,
                "passed": True,
                "violations": [],
                "warnings": [],
                "notes": ["没有需要审核的代码变更"],
            }

        # 调用纯逻辑技能
        sot_result = validate_against_sot(changes)

        return {
            "success": True,
            "passed": sot_result["passed"],
            "violations": sot_result["violations"],
            "warnings": sot_result["warnings"],
            "notes": [
                f"审核文件数: {len(changes)}",
                f"SoT 检查: {'PASS' if sot_result['passed'] else 'FAIL'}",
            ],
        }
```

#### 2.4 迁移 deprecated Agent

```python
# agent_platform/agents/deprecated/fe_agent.py

"""
[DEPRECATED] FEAgent - 前端开发 Agent

此 Agent 依赖 LLM，在 MCP 模式下不可用。
在 MCP 模式下，前端代码生成应由 Claude 直接完成。

保留此文件仅供参考和 CLI 模式使用。
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..protocol import AgentProtocol, AgentContext
from ..registry import register_agent

@register_agent(
    key="fe",
    name="FEAgent",
    description="[DEPRECATED] 前端开发 Agent - 需要 LLM，MCP 模式下不可用",
    mcp_safe=False,  # 依赖 LLM，MCP 不安全
)
class FEAgent(AgentProtocol):
    """前端开发 Agent - MCP 不安全"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()

    @property
    def name(self) -> str:
        return "fe"

    @property
    def mcp_safe(self) -> bool:
        return False  # 需要 LLM

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        from agent_platform.llm.factory import is_mcp_mode

        if is_mcp_mode():
            return {
                "success": False,
                "error": (
                    "FEAgent 在 MCP 模式下不可用（需要 LLM）。"
                    "请让 Claude 直接生成前端代码。"
                ),
                "error_kind": "MCP_MODE_BLOCKED",
            }

        # CLI 模式：调用原有 LLM 逻辑
        from agent_platform.skills.deprecated.fe_dev_skill import fe_dev_skill
        # ... 原有实现
```

#### Phase 2 验收 Checklist

- [ ] `agent_platform/agents/protocol.py` 包含 `mcp_safe` 属性
- [ ] `agent_platform/agents/registry.py` 实现 `list_mcp_safe_agents()`
- [ ] `CodeReviewAgent` 迁移到 `pure_logic/`，`mcp_safe=True`
- [ ] `TestAgent` 迁移到 `pure_logic/`，`mcp_safe=True`
- [ ] `FEAgent`, `BEAgent` 迁移到 `deprecated/`，`mcp_safe=False`
- [ ] 所有 Agent 的 `mcp_safe` 属性正确声明
- [ ] `ap_run_agent` 在 MCP 模式下正确拒绝 `mcp_safe=False` Agent

#### Phase 2 风险 & 回滚

| 风险 | 概率 | 缓解措施 | 回滚方式 |
|------|------|----------|----------|
| Agent 导入循环依赖 | 中 | 延迟导入 | 调整导入顺序 |
| mcp_safe 判断逻辑错误 | 低 | 单元测试 | 修复 `is_mcp_mode()` |

---

### Phase 3: 技能层迁移 (预计 1.5h)

**目标**: 迁移技能层，分离纯逻辑技能和需 LLM 的技能。

#### 3.1 迁移纯逻辑技能

```bash
# 创建目录
mkdir -p agent_platform/skills
mkdir -p agent_platform/skills/deprecated

# 复制纯逻辑技能
cp agents/skills/sot_guard_skill.py agent_platform/skills/
cp agents/skills/review_skill.py agent_platform/skills/

# 复制需 LLM 的技能到 deprecated
cp agents/skills/fe_dev_skill.py agent_platform/skills/deprecated/
cp agents/skills/be_dev_skill.py agent_platform/skills/deprecated/
```

#### 3.2 更新技能导入路径

```python
# agent_platform/skills/__init__.py

from .sot_guard_skill import validate_against_sot
from .review_skill import review_code

__all__ = [
    "validate_against_sot",
    "review_code",
]
```

#### Phase 3 验收 Checklist

- [ ] `sot_guard_skill.py` 迁移到 `agent_platform/skills/`
- [ ] `review_skill.py` 迁移到 `agent_platform/skills/`
- [ ] `fe_dev_skill.py`, `be_dev_skill.py` 迁移到 `deprecated/`
- [ ] Agent 的技能导入路径已更新
- [ ] 技能功能测试通过

---

### Phase 4: 工具层合并 (预计 1.5h)

**目标**: 合并两处工具层，消除重复代码。

#### 4.1 比较并合并 fs_tool.py

```bash
# 比较两个版本
diff agents/tools/fs_tool.py agent_platform/tools/fs_tool.py

# 保留更完整的版本到 agent_platform/tools/
```

#### 4.2 迁移其他工具

```bash
cp agents/tools/supabase_tool.py agent_platform/tools/
cp agents/tools/validation.py agent_platform/tools/  # 如果更完整
```

#### 4.3 迁移 claude_code_adapter

```bash
# 移到 llm/ 目录（仅 CLI 模式使用）
cp agents/tools/claude_code_adapter.py agent_platform/llm/
```

#### Phase 4 验收 Checklist

- [ ] `fs_tool.py` 已合并（保留更完整版本）
- [ ] `supabase_tool.py` 迁移完成
- [ ] `validation.py` 迁移完成
- [ ] `claude_code_adapter.py` 移到 `llm/`
- [ ] 所有工具导入路径已更新
- [ ] 工具功能测试通过

---

### Phase 5: 兼容层与生态迁移 (预计 2h)

**目标**: 更新 `.claude/commands` 和其他生态文件，确保与新架构对齐。

#### 5.1 更新 .claude/commands

```markdown
# .claude/commands/gen-backend-mcp.md (更新)

# 旧路径
- python -m agents.cli ...

# 新路径
+ python -m agent_platform ...
```

需要更新的文件清单：

| 文件 | 需要更新的内容 |
|------|----------------|
| `gen-backend-mcp.md` | CLI 调用路径 |
| `gen-frontend-mcp.md` | CLI 调用路径 |
| `doc-agent.md` | Agent 引用路径 |
| `mcp-orch.md` | MCP 工具说明 |

#### 5.2 创建/更新 .claude/mcp.json

```json
{
  "mcpServers": {
    "ai-ad-agents": {
      "command": "python",
      "args": ["-m", "agent_platform.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "AGENT_PLATFORM_MODE": "mcp",
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

#### 5.3 更新 CLAUDE.md

```markdown
# CLAUDE.md (更新)

## Agent 平台

### MCP 模式 (推荐)

通过 ai-ad-agents MCP 服务使用 Agent 平台：

- `ap_list_agents`: 列出可用 Agent
- `ap_run_agent`: 运行 Agent（仅 mcp_safe=True）
- `ap_read_sot`: 读取 SoT 文档
- `ap_run_pytest`: 运行测试

### CLI 模式 (调试用)

```bash
python -m agent_platform --help
python -m agent_platform run <agent_name> --task "..."
```

### 注意事项

- MCP 模式下只能使用 `mcp_safe=True` 的 Agent
- 代码生成任务应由 Claude 直接完成，而非调用 Agent
```

#### 5.4 更新 SKILL 文档

检查并更新所有 SKILL 文档中对 Agent 的引用。

#### Phase 5 验收 Checklist

- [ ] `gen-backend-mcp.md` 已更新
- [ ] `gen-frontend-mcp.md` 已更新
- [ ] `doc-agent.md` 已更新
- [ ] `.claude/mcp.json` 已创建/更新
- [ ] `CLAUDE.md` 已更新
- [ ] 所有 SKILL 文档已检查
- [ ] Claude Code 中 ai-ad-agents MCP 可正常使用

---

### Phase 6: MCP 工具重构 (预计 2h)

**目标**: 将 MCP 工具模块化，增强 mcp_safe 检查。

#### 6.1 拆分 MCP 工具

```bash
mkdir -p agent_platform/mcp/tools
touch agent_platform/mcp/tools/__init__.py
```

#### 6.2 创建工具模块

```python
# agent_platform/mcp/tools/agent_tools.py

from typing import Dict, Any, List, Optional

def run_agent(
    agent_name: str,
    payload: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    运行 Agent 的 MCP 工具。

    MCP 安全检查：仅允许 mcp_safe=True 的 Agent。
    """
    from agent_platform.llm.factory import is_mcp_mode
    from agent_platform.agents.registry import (
        create_agent,
        get_agent_meta,
        list_mcp_safe_agents,
    )

    # 检查 Agent 是否存在
    try:
        meta = get_agent_meta(agent_name)
    except KeyError:
        return {
            "success": False,
            "error": f"Unknown agent: {agent_name}",
            "error_kind": "AGENT_NOT_FOUND",
        }

    # MCP 安全检查
    if is_mcp_mode() and not meta.mcp_safe:
        return {
            "success": False,
            "error": (
                f"Agent '{agent_name}' is not MCP-safe (mcp_safe=False). "
                f"In MCP mode, only pure-logic agents can be invoked. "
                f"Claude should perform LLM-dependent tasks directly."
            ),
            "error_kind": "MCP_SAFETY_VIOLATION",
            "mcp_safe_agents": list_mcp_safe_agents(),
        }

    # 执行 Agent
    try:
        agent = create_agent(agent_name)
        result = agent.handle_request(payload, context or {})
        return {
            "success": True,
            "agent_name": agent_name,
            "agent_result": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_kind": "AGENT_EXECUTION_ERROR",
        }
```

#### 6.3 更新 server.py 使用模块化工具

```python
# agent_platform/mcp/server.py (修改)

from .tools.sot_tools import read_sot_file, list_sot_files
from .tools.file_tools import read_file, write_file
from .tools.test_tools import run_pytest
from .tools.agent_tools import run_agent, list_agents

# 注册工具时使用模块化函数
@_registry.register(name="ap_run_agent", ...)
def ap_run_agent(agent_name: str, payload: Dict, context: Optional[Dict] = None):
    return run_agent(agent_name, payload, context)
```

#### Phase 6 验收 Checklist

- [ ] `mcp/tools/` 目录已创建
- [ ] `sot_tools.py` 已创建
- [ ] `file_tools.py` 已创建
- [ ] `test_tools.py` 已创建
- [ ] `agent_tools.py` 已创建（含 mcp_safe 检查）
- [ ] `server.py` 已更新使用模块化工具
- [ ] MCP 服务可正常启动
- [ ] `ap_run_agent` 正确拒绝 `mcp_safe=False` Agent

---

### Phase 7: 观察期与最终清理 (预计 1h + 7 天观察期)

**目标**: 确认迁移稳定后，删除 `agents/` 目录。

#### 7.1 进入观察期

观察期开始条件：
- Phase 0-6 全部完成
- 所有测试通过
- CI/CD 流水线绿色

观察期时长：**7 天**

#### 7.2 观察期监控

```bash
# 监控 AGENT_PLATFORM_LEGACY 使用情况
grep -r "AGENT_PLATFORM_LEGACY" --include="*.log" .

# 监控 agents/ 直接导入
grep -r "from agents" --include="*.py" . | grep -v "agent_platform"
grep -r "import agents" --include="*.py" . | grep -v "agent_platform"
```

#### 7.3 删除条件

观察期结束后，满足以下全部条件方可删除 `agents/`：

- [ ] 连续 7 天无 `AGENT_PLATFORM_LEGACY=1` 使用记录
- [ ] 无代码直接导入 `agents/` 模块
- [ ] 所有 `.claude/commands` 已使用新路径
- [ ] CI/CD 流水线持续绿色
- [ ] 无外部依赖报告

#### 7.4 最终删除

```bash
# 确认无遗留依赖
grep -r "from agents" --include="*.py" .
grep -r "import agents" --include="*.py" .

# 删除 agents/ 目录
rm -rf agents/

# 更新 .gitignore（可选）
echo "# agents/ 已迁移至 agent_platform/" >> .gitignore

# 提交
git add -A
git commit -m "chore: Remove deprecated agents/ directory after migration"
```

#### Phase 7 验收 Checklist

- [ ] 观察期 7 天已完成
- [ ] 无 LEGACY 模式使用记录
- [ ] 无 agents/ 直接导入
- [ ] 所有生态文件已更新
- [ ] CI/CD 持续绿色
- [ ] `agents/` 目录已删除
- [ ] PR 已合并到 master

---

## 4. 风险评估与回滚策略

### 4.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 | 回滚方式 |
|------|------|------|----------|----------|
| Import 路径遗漏 | 高 | 中 | 每 Phase 测试 | `git checkout` |
| MCP 服务无法启动 | 中 | 高 | 备份原 server.py | `AGENT_PLATFORM_LEGACY=1` |
| mcp_safe 判断错误 | 中 | 高 | 单元测试 | 修复 `is_mcp_mode()` |
| 影子模式转调失败 | 中 | 中 | 分步测试 | `AGENT_PLATFORM_LEGACY=1` |
| CI/CD 流程中断 | 低 | 中 | 检查 CI 配置 | 修复路径 |
| 生态文件遗漏 | 中 | 低 | Checklist 检查 | 逐个修复 |

### 4.2 回滚策略

#### 紧急回滚 (任意 Phase)

```bash
# 方式 1: 设置 LEGACY 环境变量（立即生效）
export AGENT_PLATFORM_LEGACY=1

# 方式 2: Git 回滚（完全回退）
git checkout master -- agents/
git checkout master -- agent_platform/
git checkout master -- .claude/
```

#### 分 Phase 回滚

| Phase | 回滚命令 |
|-------|----------|
| 0 | `git checkout master -- agents/__init__.py agents/cli.py` |
| 1 | `git checkout master -- agent_platform/config/ agent_platform/mcp/server.py` |
| 2 | `git checkout master -- agent_platform/agents/` |
| 3 | `git checkout master -- agent_platform/skills/` |
| 4 | `git checkout master -- agent_platform/tools/` |
| 5 | `git checkout master -- .claude/` |
| 6 | `git checkout master -- agent_platform/mcp/tools/` |

---

## 5. 时间估算

| Phase | 描述 | 预计时间 | 可并行 |
|-------|------|----------|--------|
| 0 | Freeze & 影子模式 | 2h | - |
| 1 | 配置层迁移 | 2h | - |
| 2 | Agent 层迁移 | 3h | - |
| 3 | 技能层迁移 | 1.5h | - |
| 4 | 工具层合并 | 1.5h | - |
| 5 | 兼容层与生态迁移 | 2h | - |
| 6 | MCP 工具重构 | 2h | - |
| 7 | 观察期 | 7 天 | 可做其他工作 |
| **总计** | | **14h + 7 天观察期** | |

**现实估算**: 1.5 工作日 + 1 周观察期

---

## 6. 最终验收 Checklist

### 功能验收

- [ ] MCP 服务可正常启动：`python -m agent_platform.mcp.server`
- [ ] 工具列表正确：`{"method": "tools/list"}` 返回 6+ 工具
- [ ] SoT 读取正常：`ap_read_sot("STATE_MACHINE")` 返回内容
- [ ] mcp_safe Agent 可运行：`ap_run_agent("review", {...})`
- [ ] 非 mcp_safe Agent 被拒绝：`ap_run_agent("fe", {...})` 返回 MCP_SAFETY_VIOLATION
- [ ] pytest 运行正常：`ap_run_pytest(["tests/"])`
- [ ] CLI 模式可用：`python -m agent_platform run review --task "..."`

### 安全验收

- [ ] MCP 模式下无法调用 LLM
- [ ] `mcp_safe=False` Agent 在 MCP 模式下被拒绝
- [ ] `AGENT_PLATFORM_LEGACY=1` 可正常回退

### 生态验收

- [ ] `.claude/commands/gen-backend-mcp.md` 使用新路径
- [ ] `.claude/commands/gen-frontend-mcp.md` 使用新路径
- [ ] `.claude/mcp.json` 配置正确
- [ ] `CLAUDE.md` 已更新
- [ ] 所有 SKILL 文档已检查

### 代码质量验收

- [ ] 无 `from agents` 直接导入（除影子模式）
- [ ] 所有测试通过
- [ ] CI/CD 流水线绿色
- [ ] 代码已 review

### 文档验收

- [ ] `agents/_DEPRECATED.md` 存在
- [ ] `agent_platform/README.md` 已创建
- [ ] 迁移方案文档已更新为 v1.1

---

## 附录

### A. 环境变量参考

| 变量 | 值 | 说明 |
|------|-----|------|
| `AGENT_PLATFORM_MODE` | `mcp` / `cli` | 运行模式 |
| `AGENT_PLATFORM_LEGACY` | `1` / `0` | 是否使用旧 agents/ 模块 |
| `AGENT_PLATFORM_REPO_ROOT` | 路径 | 覆盖仓库根路径 |

### B. MCP 工具列表

| 工具 | 说明 | mcp_safe 检查 |
|------|------|---------------|
| `ap_list_agents` | 列出可用 Agent | 返回 mcp_safe 属性 |
| `ap_run_agent` | 运行 Agent | 检查 mcp_safe=True |
| `ap_read_sot_file` | 读取 SoT 文档 | - |
| `ap_list_sot_files` | 列出 SoT 文件 | - |
| `ap_read_file` | 读取文件 | - |
| `ap_write_file` | 写入文件 | - |
| `ap_run_pytest` | 运行测试 | - |

### C. 文件映射表

| 原路径 | 新路径 | 操作 |
|--------|--------|------|
| `agents/agents_config.py` | `agent_platform/config/*.py` | 拆分 |
| `agents/agent_core/code_review_agent.py` | `agent_platform/agents/pure_logic/` | 移动 |
| `agents/agent_core/fe_agent.py` | `agent_platform/agents/deprecated/` | 移动 |
| `agents/skills/sot_guard_skill.py` | `agent_platform/skills/` | 移动 |
| `agents/skills/fe_dev_skill.py` | `agent_platform/skills/deprecated/` | 移动 |
| `agents/tools/*.py` | `agent_platform/tools/` | 合并 |
| `agents/cli.py` | `agent_platform/__main__.py` | 合并 |
| `agents/__init__.py` | 影子模式兼容壳 | 修改 |
| `agents/server.py` | 删除 | - |

---

**文档版本**: v1.1
**状态**: Ready for Execution
**负责人**: Agent Platform 迁移总架构师
**下一步**: 按 Phase 顺序执行迁移
