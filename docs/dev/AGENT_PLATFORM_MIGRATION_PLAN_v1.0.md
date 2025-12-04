# Agent Platform 迁移方案 v1.0

> **状态**: Draft - 待评估
> **创建日期**: 2025-12-04
> **目标**: 将 `agent_platform/` 和 `agents/` 合并为 MCP-First 架构

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
│   │   ├── fe_agent.py       # 前端 Agent (需 LLM)
│   │   ├── be_agent.py       # 后端 Agent (需 LLM)
│   │   ├── test_agent.py     # 测试 Agent
│   │   ├── orchestrator_agent.py
│   │   ├── doc_agent.py
│   │   └── code_review_agent.py  # 纯逻辑 ✓
│   ├── skills/               # 技能层
│   │   ├── fe_dev_skill.py   # 需 LLM
│   │   ├── be_dev_skill.py   # 需 LLM
│   │   ├── sot_guard_skill.py  # 纯逻辑 ✓
│   │   └── ...
│   ├── tools/                # 工具层 (与 agent_platform/tools 重复)
│   │   ├── fs_tool.py
│   │   ├── llm_client.py
│   │   ├── claude_code_adapter.py
│   │   └── supabase_tool.py
│   ├── agents_config.py      # 统一配置 (SOT_FILES, LLM_CONFIG)
│   ├── cli.py                # CLI 入口
│   └── server.py             # HTTP 入口
```

### 1.2 问题清单

| # | 问题 | 影响 | 严重度 |
|---|------|------|--------|
| 1 | AgentProtocol 定义重复 | `agent_platform/core/protocol.py` vs `agents/agents_config.py` | 中 |
| 2 | 工具层重复 | `agent_platform/tools/` vs `agents/tools/` | 中 |
| 3 | LLM 客户端重复 | `agent_platform/llm/` vs `agents/tools/llm_client.py` | 中 |
| 4 | 跨模块依赖 | `mcp/server.py` 导入 `agents/agents_config.py` | 高 |
| 5 | MCP 模式下 LLM Agent 无法使用 | FEAgent/BEAgent 在 MCP 模式被阻断 | 高 |
| 6 | 配置分散 | SOT_FILES 在 agents_config.py，但 MCP server 也需要 | 中 |

### 1.3 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code (外部)                        │
└────────────────────────────┬────────────────────────────────┘
                             │ MCP Protocol (stdio)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ agent_platform/mcp/server.py                                │
│   └── 导入 agents/agents_config.py ←────┐                   │
└──────────────────────────┬──────────────│───────────────────┘
                           │              │
┌──────────────────────────▼──────────────│───────────────────┐
│ agents/                                 │                    │
│   ├── agents_config.py ─────────────────┘                   │
│   │     └── SOT_FILES, LLM_CONFIG, create_agent()           │
│   ├── agent_core/                                            │
│   │     ├── fe_agent.py ──── 导入 ──▶ agent_platform/core/  │
│   │     └── ...                                              │
│   └── skills/                                                │
│         └── fe_dev_skill.py ─ 调用 ─▶ agent_platform/llm/   │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 目标架构

### 2.1 设计原则

1. **MCP-First**: Claude Code 是唯一 LLM，agent_platform 只提供工具
2. **单一模块**: 合并为一个 `agent_platform/` 模块
3. **纯逻辑 Agent**: Agent 不调用 LLM，只做规则检查/流程编排
4. **可选 CLI 模式**: 保留独立运行能力（用于调试/测试）

### 2.2 目标目录结构

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
│   │   ├── registry.py           # 统一注册表
│   │   ├── protocol.py           # AgentProtocol (统一定义)
│   │   │
│   │   ├── pure_logic/           # 纯逻辑 Agent (推荐)
│   │   │   ├── __init__.py
│   │   │   ├── code_review_agent.py   # SoT 规则检查
│   │   │   ├── sot_guard_agent.py     # 状态机/账本守护
│   │   │   ├── test_agent.py          # 测试编排
│   │   │   └── workflow_agent.py      # 流程编排
│   │   │
│   │   └── deprecated/           # 已废弃 (保留代码参考)
│   │       ├── fe_agent.py       # → 由 Claude 直接生成
│   │       └── be_agent.py       # → 由 Claude 直接生成
│   │
│   ├── skills/                   # 技能层 (从 agents/skills 迁移)
│   │   ├── __init__.py
│   │   ├── sot_guard_skill.py    # 纯规则检查
│   │   ├── review_skill.py
│   │   └── deprecated/           # 需 LLM 的技能 (废弃)
│   │       ├── fe_dev_skill.py
│   │       └── be_dev_skill.py
│   │
│   ├── config/                   # 配置层 (从 agents_config.py 拆分)
│   │   ├── __init__.py
│   │   ├── paths.py              # BASE_PATH, BACKEND_DIR, FRONTEND_DIR
│   │   ├── sot_files.py          # SOT_FILES 映射
│   │   └── constants.py          # 其他常量
│   │
│   ├── tools/                    # 通用工具 (合并)
│   │   ├── __init__.py
│   │   ├── fs_tool.py            # 文件操作
│   │   ├── validation.py         # 输入校验
│   │   └── supabase_tool.py      # Supabase 客户端
│   │
│   ├── llm/                      # LLM 层 (可选，用于 CLI 模式)
│   │   ├── __init__.py
│   │   ├── factory.py            # get_llm_client()
│   │   ├── base.py               # LLMClient 抽象
│   │   └── deeprouter_client.py
│   │
│   └── tests/                    # 测试
│       ├── __init__.py
│       ├── test_mcp_server.py
│       ├── test_agents.py
│       └── ...
│
├── agents/                       # [删除] 迁移后删除
│   └── ...
```

---

## 3. 迁移步骤

### Phase 0: 准备工作 (预计 0.5h)

| 步骤 | 操作 | 产出 |
|------|------|------|
| 0.1 | 创建 git 分支 `refactor/agent-platform-merge` | 隔离变更 |
| 0.2 | 运行现有测试，记录基线 | 测试报告 |
| 0.3 | 备份 agents/ 和 agent_platform/ | 可回滚 |

### Phase 1: 配置层迁移 (预计 1h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 1.1 | 创建 `agent_platform/config/` 目录 | 新建 |
| 1.2 | 从 `agents/agents_config.py` 提取 SOT_FILES → `config/sot_files.py` | 新建 |
| 1.3 | 从 `agents/agents_config.py` 提取路径常量 → `config/paths.py` | 新建 |
| 1.4 | 更新 `mcp/server.py` 的导入路径 | 修改 |
| 1.5 | 运行测试验证 | - |

**关键代码变更:**

```python
# agent_platform/config/sot_files.py (新建)
from pathlib import Path
from .paths import BASE_PATH

SOT_FILES = {
    "STATE_MACHINE": BASE_PATH / "docs/2.sot/STATE_MACHINE.md",
    "DATA_SCHEMA": BASE_PATH / "docs/2.sot/DATA_SCHEMA.md",
    # ... 其他 SoT 文件
}
```

```python
# agent_platform/mcp/server.py (修改)
- from agents.agents_config import SOT_FILES, create_agent
+ from agent_platform.config.sot_files import SOT_FILES
+ from agent_platform.agents.registry import create_agent
```

### Phase 2: Agent 层迁移 (预计 2h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 2.1 | 合并 AgentProtocol 定义到 `agents/protocol.py` | 新建 |
| 2.2 | 迁移 `CodeReviewAgent` → `agents/pure_logic/` | 移动 |
| 2.3 | 迁移 `TestAgent` → `agents/pure_logic/` (移除 LLM 依赖) | 移动+修改 |
| 2.4 | 创建 `agents/registry.py` 替代 `agents_config.py` 的注册功能 | 新建 |
| 2.5 | 将 `FEAgent`, `BEAgent` 移动到 `agents/deprecated/` | 移动 |
| 2.6 | 更新所有 import 路径 | 批量修改 |
| 2.7 | 运行测试验证 | - |

**注册表变更:**

```python
# agent_platform/agents/registry.py (新建)
from typing import Dict, Callable
from .protocol import AgentProtocol

_AGENT_REGISTRY: Dict[str, Callable[[], AgentProtocol]] = {}

def register_agent(key: str):
    """装饰器：注册 Agent"""
    def decorator(cls):
        _AGENT_REGISTRY[key] = cls
        return cls
    return decorator

def create_agent(name: str) -> AgentProtocol:
    """创建 Agent 实例"""
    if name not in _AGENT_REGISTRY:
        raise KeyError(f"Unknown agent: {name}")
    return _AGENT_REGISTRY[name]()

def list_agents() -> Dict[str, str]:
    """列出所有可用 Agent"""
    return {k: v.__doc__ or "" for k, v in _AGENT_REGISTRY.items()}
```

### Phase 3: 技能层迁移 (预计 1h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 3.1 | 迁移 `sot_guard_skill.py` → `skills/` | 移动 |
| 3.2 | 迁移 `review_skill.py` → `skills/` | 移动 |
| 3.3 | 将需 LLM 的技能移动到 `skills/deprecated/` | 移动 |
| 3.4 | 更新 Agent 的技能导入路径 | 批量修改 |
| 3.5 | 运行测试验证 | - |

### Phase 4: 工具层合并 (预计 1h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 4.1 | 比较两处 `fs_tool.py`，保留更完整版本 | 比较+合并 |
| 4.2 | 迁移 `supabase_tool.py` → `tools/` | 移动 |
| 4.3 | 迁移 `claude_code_adapter.py` → `llm/` (仅 CLI 模式使用) | 移动 |
| 4.4 | 删除 `agents/tools/` 目录 | 删除 |
| 4.5 | 运行测试验证 | - |

### Phase 5: MCP 工具重构 (预计 1.5h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 5.1 | 将 `mcp/server.py` 中的工具拆分到 `mcp/tools/` | 拆分 |
| 5.2 | 创建 `sot_tools.py` (ap_read_sot, ap_list_sot) | 新建 |
| 5.3 | 创建 `file_tools.py` (ap_read_file, ap_write_file) | 新建 |
| 5.4 | 创建 `test_tools.py` (ap_run_pytest) | 新建 |
| 5.5 | 创建 `agent_tools.py` (ap_list_agents, ap_run_agent) | 新建 |
| 5.6 | 更新 `server.py` 使用模块化工具 | 修改 |
| 5.7 | 运行 MCP 测试验证 | - |

### Phase 6: 清理与文档 (预计 1h)

| 步骤 | 操作 | 影响文件 |
|------|------|----------|
| 6.1 | 删除原 `agents/` 目录 | 删除 |
| 6.2 | 更新 `.claude/mcp.json` 配置 | 修改 |
| 6.3 | 更新 CLAUDE.md 中的 Agent 说明 | 修改 |
| 6.4 | 创建 `agent_platform/README.md` | 新建 |
| 6.5 | 全量测试 + 手动验证 MCP 功能 | - |
| 6.6 | 合并 PR | - |

---

## 4. 风险评估

### 4.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Import 路径遗漏导致运行时错误 | 高 | 中 | 每个 Phase 后运行完整测试 |
| MCP 服务无法启动 | 中 | 高 | 保留原 server.py 备份，可快速回滚 |
| 现有 CI/CD 流程中断 | 低 | 中 | 提前检查 CI 配置中的路径引用 |
| 第三方依赖路径问题 | 低 | 低 | 检查 pyproject.toml / setup.py |

### 4.2 回滚策略

```bash
# 如果迁移失败，执行回滚
git checkout master -- agents/
git checkout master -- agent_platform/
git checkout master -- .claude/mcp.json
```

---

## 5. 测试计划

### 5.1 每 Phase 测试

```bash
# Phase 1-4: 单元测试
pytest agent_platform/tests/ -v

# Phase 5: MCP 集成测试
python -m agent_platform.mcp.server  # 手动测试 stdio
```

### 5.2 最终验收测试

| 测试项 | 命令 | 预期结果 |
|--------|------|----------|
| MCP 服务启动 | `python -m agent_platform.mcp.server` | 无错误，等待 stdin |
| 工具列表 | `{"method": "tools/list"}` | 返回 6+ 工具 |
| SoT 读取 | `ap_read_sot("STATE_MACHINE")` | 返回文档内容 |
| Agent 运行 | `ap_run_agent("review", {...})` | CodeReviewAgent 正常执行 |
| pytest 运行 | `ap_run_pytest(["tests/"])` | 返回测试结果 |

---

## 6. 时间估算

| Phase | 描述 | 预计时间 |
|-------|------|----------|
| 0 | 准备工作 | 0.5h |
| 1 | 配置层迁移 | 1h |
| 2 | Agent 层迁移 | 2h |
| 3 | 技能层迁移 | 1h |
| 4 | 工具层合并 | 1h |
| 5 | MCP 工具重构 | 1.5h |
| 6 | 清理与文档 | 1h |
| **总计** | | **8h** |

---

## 7. 决策点 (需要确认)

### Q1: 是否保留 CLI 模式？

| 选项 | 描述 | 工作量 |
|------|------|--------|
| A | 完全删除 LLM 层，只保留 MCP 模式 | -1h |
| B | 保留 LLM 层，支持独立 CLI 运行 | 0 (当前方案) |

**建议**: 选 B，保留灵活性用于调试

### Q2: FEAgent/BEAgent 处理方式？

| 选项 | 描述 | 工作量 |
|------|------|--------|
| A | 移动到 deprecated/，保留代码参考 | 0 (当前方案) |
| B | 完全删除 | -0.5h |
| C | 重构为纯模板生成器（无 LLM） | +2h |

**建议**: 选 A，保留代码供参考

### Q3: 迁移策略？

| 选项 | 描述 | 风险 |
|------|------|------|
| A | 一次性迁移 (当前方案) | 中，但可快速完成 |
| B | 渐进式迁移（先兼容两套，再逐步切换） | 低，但时间更长 |

**建议**: 选 A，代码量不大，一次性迁移更干净

---

## 8. 附录

### A. 文件映射表

| 原路径 | 新路径 | 操作 |
|--------|--------|------|
| `agents/agents_config.py` | `agent_platform/config/*.py` | 拆分 |
| `agents/agent_core/code_review_agent.py` | `agent_platform/agents/pure_logic/code_review_agent.py` | 移动 |
| `agents/agent_core/fe_agent.py` | `agent_platform/agents/deprecated/fe_agent.py` | 移动 |
| `agents/agent_core/be_agent.py` | `agent_platform/agents/deprecated/be_agent.py` | 移动 |
| `agents/skills/sot_guard_skill.py` | `agent_platform/skills/sot_guard_skill.py` | 移动 |
| `agents/skills/fe_dev_skill.py` | `agent_platform/skills/deprecated/fe_dev_skill.py` | 移动 |
| `agents/tools/fs_tool.py` | `agent_platform/tools/fs_tool.py` | 合并 |
| `agents/tools/supabase_tool.py` | `agent_platform/tools/supabase_tool.py` | 移动 |
| `agents/cli.py` | `agent_platform/__main__.py` | 合并 |
| `agents/server.py` | 删除 (HTTP 入口不再需要) | 删除 |

### B. Import 路径变更

```python
# 旧 → 新

# 配置
- from agents.agents_config import SOT_FILES, create_agent
+ from agent_platform.config.sot_files import SOT_FILES
+ from agent_platform.agents.registry import create_agent

# Agent
- from agents.agent_core.code_review_agent import CodeReviewAgent
+ from agent_platform.agents.pure_logic.code_review_agent import CodeReviewAgent

# 技能
- from agents.skills.sot_guard_skill import validate_against_sot
+ from agent_platform.skills.sot_guard_skill import validate_against_sot

# 工具
- from agents.tools.fs_tool import read_file, write_file
+ from agent_platform.tools.fs_tool import read_file, write_file

# LLM
- from agents.tools.llm_client import get_llm_client
+ from agent_platform.llm.factory import get_llm_client
```

---

**文档版本**: v1.0
**状态**: Draft - 待评估
**下一步**: 请评估后确认 Q1/Q2/Q3 决策点
