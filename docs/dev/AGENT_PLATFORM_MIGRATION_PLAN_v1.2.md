# Agent Platform 迁移方案 v1.2 (终版)

> **版本**: v1.2 Final
> **状态**: Ready for Execution
> **创建日期**: 2025-12-04
> **目标**: 将 `agents/` 安全并入 `agent_platform/`，实现 MCP-First 架构

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2025-12-04 | 初版：基础迁移方案 |
| v1.1 | 2025-12-04 | 新增 MCP 安全边界、影子模式、生态迁移 |
| v1.2 | 2025-12-04 | **终版**：修复 mcp_safe 双写、循环依赖、增加健康检查、明确执行顺序 |

### v1.2 关键改进

| 问题 | v1.1 风险 | v1.2 修复 |
|------|----------|----------|
| mcp_safe 双写 | 类属性 + 注册表参数可能不一致 | **唯一真相在 AgentMeta**，类属性移除 |
| 影子模式循环依赖 | `agents/` 导入 `agent_platform.config` | **纯 os.environ 检查**，无跨模块依赖 |
| BASE_PATH 推断 | 假设固定目录层级 | **增加 fallback + 验证** |
| Phase 粒度过大 | 7 Phase 一口气执行风险高 | **第一轮只执行 Phase 0+1** |
| 缺少健康检查 | Phase 之间无验证 | **每个 Phase 末尾标准化健康检查** |

---

## 执行顺序建议

```
┌─────────────────────────────────────────────────────────────────┐
│                        执行节奏                                  │
├─────────────────────────────────────────────────────────────────┤
│  第一轮（必须）: Phase 0 + Phase 1                               │
│    - 建立安全回退机制                                            │
│    - 完成配置层迁移                                              │
│    - 验证 MCP server 可正常启动                                  │
│    - 预计时间: 3-4 小时                                          │
│                                                                  │
│  后续轮次（单独触发）:                                           │
│    - Phase 2: Agent 层迁移                                       │
│    - Phase 3: 技能层 + 工具层迁移                                │
│    - Phase 4: 生态迁移 + MCP 工具重构                            │
│    - Phase 5: 观察期 + 最终清理                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. MCP 安全边界设计

### 1.1 核心原则

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

### 1.2 运行模式对比

| 特性 | MCP 模式 | CLI 模式 |
|------|----------|----------|
| 触发条件 | `AGENT_PLATFORM_MODE=mcp` | 默认 / `AGENT_PLATFORM_MODE=cli` |
| LLM 调用 | **严禁** | 允许 |
| 可用 Agent | 仅 `mcp_safe=True` | 全部 |
| 主要用途 | Claude Code 工具扩展 | 独立调试/测试 |
| 入口 | `mcp/server.py` (stdio) | `cli.py` / `__main__.py` |

### 1.3 mcp_safe 唯一真相

**设计决策**: `mcp_safe` 的唯一真相在 `AgentMeta`（注册表），不在类属性。

```python
# agent_platform/agents/registry.py

@dataclass(frozen=True)
class AgentMeta:
    """Agent 元信息 - mcp_safe 的唯一真相"""
    key: str
    name: str
    description: str
    mcp_safe: bool  # ← 唯一真相在这里
    factory: Callable[..., AgentProtocol]


def register_agent(key: str, name: str, description: str = "", mcp_safe: bool = False):
    """
    装饰器：注册 Agent。

    mcp_safe 参数是判断 Agent 是否可在 MCP 模式运行的唯一依据。
    Agent 类本身不需要定义 mcp_safe 属性。
    """
    def decorator(cls):
        _AGENT_REGISTRY[key] = AgentMeta(
            key=key, name=name, description=description,
            mcp_safe=mcp_safe,  # ← 唯一真相
            factory=cls,
        )
        return cls
    return decorator


def is_agent_mcp_safe(agent_name: str) -> bool:
    """检查 Agent 是否 MCP 安全（从注册表读取）"""
    meta = get_agent_meta(agent_name)
    return meta.mcp_safe  # ← 从 AgentMeta 读取，不从类实例读取
```

**为什么不在类属性定义？**
- 避免双写不一致：注册表写 `mcp_safe=True`，类返回 `False`
- 单一真相原则：判断逻辑只看注册表，不需要实例化 Agent
- 性能更好：`is_agent_mcp_safe()` 无需创建 Agent 实例

### 1.4 Agent 分类

| Agent | mcp_safe | 原因 | 迁移去向 |
|-------|----------|------|----------|
| `CodeReviewAgent` | `True` | 纯 SoT 规则检查 | `pure_logic/` |
| `TestAgent` | `True` | 测试编排，不调 LLM | `pure_logic/` |
| `SoTGuardAgent` | `True` | 状态机/账本守护 | `pure_logic/` |
| `FEAgent` | `False` | 依赖 fe_dev_skill (LLM) | `deprecated/` |
| `BEAgent` | `False` | 依赖 be_dev_skill (LLM) | `deprecated/` |
| `DocAgent` | `False` | 依赖 LLM 生成文档 | `deprecated/` |
| `OrchestratorAgent` | `False` | 可能调用 LLM Agent | `deprecated/` |

---

## 2. 目标架构

```
AI_ad_spend02/
├── agent_platform/               # 唯一的 Agent 平台模块
│   ├── __init__.py
│   ├── __main__.py               # CLI 入口
│   │
│   ├── mcp/                      # MCP 服务层 (主入口)
│   │   ├── __init__.py
│   │   ├── server.py             # MCP stdio 服务器
│   │   └── tools/                # MCP 工具定义 (Phase 4)
│   │       └── ...
│   │
│   ├── agents/                   # Agent 实现层 (Phase 2)
│   │   ├── __init__.py
│   │   ├── registry.py           # mcp_safe 唯一真相
│   │   ├── protocol.py           # AgentProtocol (无 mcp_safe 属性)
│   │   ├── pure_logic/           # mcp_safe=True Agent
│   │   └── deprecated/           # mcp_safe=False Agent
│   │
│   ├── config/                   # 配置层 (Phase 1)
│   │   ├── __init__.py
│   │   ├── paths.py              # BASE_PATH (带 fallback)
│   │   ├── sot_files.py          # SOT_FILES 映射
│   │   └── constants.py          # LEGACY_MODE 等
│   │
│   ├── skills/                   # 技能层 (Phase 3)
│   ├── tools/                    # 通用工具 (Phase 3)
│   ├── llm/                      # LLM 层 (仅 CLI 模式)
│   └── tests/
│
├── agents/                       # 影子模式兼容壳 (观察期后删除)
│   ├── __init__.py               # 纯 os.environ 检查，无跨模块导入
│   ├── cli.py                    # 转调壳
│   ├── agents_config.py          # 保留原文件 (LEGACY 模式使用)
│   └── _DEPRECATED.md
│
├── .claude/
│   ├── commands/                 # 更新后的自定义命令 (Phase 4)
│   └── mcp.json                  # ai-ad-agents MCP 配置
```

---

## 3. 迁移步骤

### Phase 0: Freeze & 影子模式准备

**目标**: 建立安全回退机制，确保迁移可随时中断和回滚。

**预计时间**: 1.5h

#### 0.1 创建迁移分支

```bash
git checkout -b refactor/agent-platform-merge-v1.2
```

#### 0.2 运行基线测试

```bash
# 记录当前测试状态
pytest agent_platform/tests/ -v --tb=short 2>&1 | tee baseline_agent_platform.txt
pytest agents/tests/ -v --tb=short 2>&1 | tee baseline_agents.txt

# 记录 MCP server 启动状态
python -c "from agent_platform.mcp.server import _registry; print('Tools:', len(_registry.tools))" 2>&1 | tee baseline_mcp.txt
```

#### 0.3 创建影子模式兼容壳

**关键设计**: 影子模式使用纯 `os.environ` 检查，**不导入 agent_platform**，避免循环依赖。

```python
# agents/__init__.py (修改为转调壳)

"""
[DEPRECATED] agents 模块 - 影子模式兼容壳

此模块已迁移至 agent_platform/。
设置 AGENT_PLATFORM_LEGACY=1 可临时回退旧逻辑。
"""

import os
import warnings

# 关键：使用纯 os.environ 检查，不导入 agent_platform
# 这避免了循环依赖问题
_LEGACY_MODE = os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"

if _LEGACY_MODE:
    # Legacy 模式：使用原有逻辑
    from .agents_config import (
        create_agent,
        list_agents,
        SOT_FILES,
        BASE_PATH,
        BACKEND_DIR,
        FRONTEND_DIR,
    )
else:
    # 新模式：转发到 agent_platform
    warnings.warn(
        "agents 模块已废弃，请改用 agent_platform。"
        "设置 AGENT_PLATFORM_LEGACY=1 可临时回退。",
        DeprecationWarning,
        stacklevel=2,
    )

    # 延迟导入，仅在实际使用时触发
    def __getattr__(name):
        if name == "create_agent":
            from agent_platform.agents.registry import create_agent
            return create_agent
        elif name == "list_agents":
            from agent_platform.agents.registry import list_agents
            return list_agents
        elif name == "SOT_FILES":
            from agent_platform.config.sot_files import SOT_FILES
            return SOT_FILES
        elif name in ("BASE_PATH", "BACKEND_DIR", "FRONTEND_DIR"):
            from agent_platform.config import paths
            return getattr(paths, name)
        raise AttributeError(f"module 'agents' has no attribute '{name}'")

    __all__ = ["create_agent", "list_agents", "SOT_FILES", "BASE_PATH", "BACKEND_DIR", "FRONTEND_DIR"]
```

```python
# agents/cli.py (修改为转调壳)

"""
[DEPRECATED] agents CLI - 影子模式兼容壳

请改用: python -m agent_platform
"""

import os
import sys
import warnings

_LEGACY_MODE = os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"

if _LEGACY_MODE:
    # Legacy 模式：使用原有 CLI
    # 将原 cli.py 重命名为 cli_legacy.py
    from .cli_legacy import main
else:
    warnings.warn(
        "agents.cli 已废弃，请改用 python -m agent_platform",
        DeprecationWarning,
    )
    from agent_platform.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
```

#### 0.4 重命名原 CLI 文件

```bash
# 将原 cli.py 重命名，保留 Legacy 模式使用
cp agents/cli.py agents/cli_legacy.py
```

#### 0.5 创建废弃说明

```markdown
# agents/_DEPRECATED.md

## 废弃声明

`agents/` 目录已迁移至 `agent_platform/`。

### 紧急回退

```bash
export AGENT_PLATFORM_LEGACY=1
python -m agents.cli ...
```

### 删除条件 (观察期 7 天后)

- [ ] 连续 7 天无 LEGACY 回退
- [ ] 无 `from agents` 直接导入
- [ ] CI/CD 持续绿色
```

#### Phase 0 健康检查

```bash
# 1. 验证影子模式转调
python -c "import agents; print('Shadow mode OK')" 2>&1

# 2. 验证 Legacy 模式
AGENT_PLATFORM_LEGACY=1 python -c "from agents import BASE_PATH; print('Legacy OK:', BASE_PATH)"

# 3. 验证无循环依赖
python -c "import agents; import agent_platform; print('No circular import')"
```

#### Phase 0 验收 Checklist

- [ ] 迁移分支已创建
- [ ] 基线测试报告已生成
- [ ] `agents/__init__.py` 改为转调壳（纯 os.environ 检查）
- [ ] `agents/cli.py` 改为转调壳
- [ ] `agents/cli_legacy.py` 已创建（原 CLI 备份）
- [ ] `agents/_DEPRECATED.md` 已创建
- [ ] **健康检查**: 影子模式转调成功
- [ ] **健康检查**: Legacy 模式可用
- [ ] **健康检查**: 无循环依赖

#### Phase 0 回滚

```bash
git checkout master -- agents/__init__.py agents/cli.py
rm -f agents/cli_legacy.py agents/_DEPRECATED.md
```

---

### Phase 1: 配置层迁移

**目标**: 将配置从 `agents/agents_config.py` 迁移到 `agent_platform/config/`。

**预计时间**: 2h

#### 1.1 创建配置目录

```bash
mkdir -p agent_platform/config
touch agent_platform/config/__init__.py
```

#### 1.2 创建 paths.py（带 fallback 和验证）

```python
# agent_platform/config/paths.py

import os
from pathlib import Path


def _get_base_path() -> Path:
    """
    推断项目根路径（带 fallback 和验证）。

    优先级：
    1. AGENT_PLATFORM_REPO_ROOT 环境变量
    2. 从文件位置推断：config/ -> agent_platform/ -> 项目根
    3. 当前工作目录（fallback）

    验证：检查 backend/, frontend/, docs/ 是否存在。
    """
    # 优先级 1: 环境变量
    env_root = os.environ.get("AGENT_PLATFORM_REPO_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if _validate_base_path(path):
            return path

    # 优先级 2: 从文件位置推断
    # paths.py -> config/ -> agent_platform/ -> 项目根
    inferred = Path(__file__).resolve().parent.parent.parent
    if _validate_base_path(inferred):
        return inferred

    # 优先级 3: 当前工作目录
    cwd = Path.cwd()
    if _validate_base_path(cwd):
        return cwd

    # 无法找到有效路径，使用推断值并警告
    import warnings
    warnings.warn(
        f"无法验证 BASE_PATH，使用推断值: {inferred}。"
        f"如有问题，请设置 AGENT_PLATFORM_REPO_ROOT 环境变量。"
    )
    return inferred


def _validate_base_path(path: Path) -> bool:
    """验证路径是否为有效的项目根目录"""
    required_dirs = ["backend", "docs"]
    return all((path / d).is_dir() for d in required_dirs)


BASE_PATH = _get_base_path()
PROJECT_ROOT = BASE_PATH  # 别名

BACKEND_DIR = BASE_PATH / "backend"
FRONTEND_DIR = BASE_PATH / "frontend"
DOCS_DIR = BASE_PATH / "docs"
```

#### 1.3 创建 sot_files.py

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
    "DAILY_REPORT_SOT": BASE_PATH / "docs/2.sot/DAILY_REPORT_SOT.md",
    "RECONCILIATION_SOT": BASE_PATH / "docs/2.sot/RECONCILIATION_SOT.md",
    "TRANSFER_SOT": BASE_PATH / "docs/2.sot/TRANSFER_SOT.md",
    "RLS_POLICIES": BASE_PATH / "docs/2.sot/RLS_POLICIES_SOT.md",
    "TOPUP_SOT": BASE_PATH / "docs/2.sot/TOPUP_SOT.md",

    # Layer 3: Dev-Guides
    "FRONTEND_RULES": BASE_PATH / "docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md",
    "UI_DESIGN_SYSTEM": BASE_PATH / "docs/3.dev-guides/UI_DESIGN_SYSTEM.md",
    "API_DEV_FLOW": BASE_PATH / "docs/3.dev-guides/API_DEVELOPMENT_FLOW.md",
}

CRITICAL_SOT_FILES = {
    "STATE_MACHINE", "DATA_SCHEMA", "BUSINESS_RULES",
    "API_SOT", "ERROR_CODES", "LEDGER_SOT", "AUTH_SPEC",
}
```

#### 1.4 创建 constants.py

```python
# agent_platform/config/constants.py

import os

# 注意：此文件不应被 agents/__init__.py 导入
# 影子模式使用纯 os.environ 检查

def is_legacy_mode() -> bool:
    """检查是否启用 Legacy 模式（用于 agent_platform 内部）"""
    return os.environ.get("AGENT_PLATFORM_LEGACY", "0") == "1"

def is_mcp_mode() -> bool:
    """检查是否 MCP 模式（从 llm/factory.py 迁移）"""
    return os.environ.get("AGENT_PLATFORM_MODE", "cli").strip().lower() == "mcp"
```

#### 1.5 创建 config/__init__.py

```python
# agent_platform/config/__init__.py

from .paths import BASE_PATH, PROJECT_ROOT, BACKEND_DIR, FRONTEND_DIR, DOCS_DIR
from .sot_files import SOT_FILES, CRITICAL_SOT_FILES
from .constants import is_legacy_mode, is_mcp_mode

__all__ = [
    "BASE_PATH", "PROJECT_ROOT", "BACKEND_DIR", "FRONTEND_DIR", "DOCS_DIR",
    "SOT_FILES", "CRITICAL_SOT_FILES",
    "is_legacy_mode", "is_mcp_mode",
]
```

#### 1.6 更新 MCP server.py 导入

```python
# agent_platform/mcp/server.py (修改)

# 旧导入（需要删除或注释）
# from agents.agents_config import SOT_FILES, create_agent, list_agents

# 新导入
from agent_platform.config.sot_files import SOT_FILES

# 注意：create_agent, list_agents 暂时保留原导入
# 等 Phase 2 完成后再修改
```

#### Phase 1 健康检查

```bash
# 1. 验证配置导入
python -c "from agent_platform.config import BASE_PATH, SOT_FILES; print('Config OK:', BASE_PATH, len(SOT_FILES))"

# 2. 验证 BASE_PATH 正确
python -c "from agent_platform.config.paths import BASE_PATH; assert (BASE_PATH / 'backend').exists(), 'backend not found'"

# 3. 验证 MCP server 启动
python -c "from agent_platform.mcp.server import _registry; print('MCP OK:', len(_registry.tools), 'tools')"

# 4. 运行原有测试（确保未破坏）
pytest agent_platform/tests/ -v --tb=short
```

#### Phase 1 验收 Checklist

- [ ] `agent_platform/config/` 目录已创建
- [ ] `paths.py` 包含 BASE_PATH（带 fallback 和验证）
- [ ] `sot_files.py` 包含完整 SOT_FILES 映射
- [ ] `constants.py` 包含 `is_legacy_mode()`, `is_mcp_mode()`
- [ ] `mcp/server.py` 的 SOT_FILES 导入已更新
- [ ] **健康检查**: 配置导入成功
- [ ] **健康检查**: BASE_PATH 正确指向项目根
- [ ] **健康检查**: MCP server 可启动
- [ ] **健康检查**: 原有测试通过

#### Phase 1 回滚

```bash
rm -rf agent_platform/config/
git checkout master -- agent_platform/mcp/server.py
```

---

### 第一轮完成检查点

**完成 Phase 0 + Phase 1 后，进行整体验证：**

```bash
# 1. 验证影子模式
python -c "import agents; print('Shadow OK')"

# 2. 验证 Legacy 模式
AGENT_PLATFORM_LEGACY=1 python -c "from agents import SOT_FILES; print('Legacy OK:', len(SOT_FILES))"

# 3. 验证新配置
python -c "from agent_platform.config import SOT_FILES; print('New config OK:', len(SOT_FILES))"

# 4. 验证 MCP server
python -c "from agent_platform.mcp.server import handle_mcp_request; print('MCP OK')"

# 5. 运行全量测试
pytest agent_platform/tests/ agents/tests/ -v --tb=short
```

**如果全部通过，第一轮迁移完成。后续 Phase 需要单独触发。**

---

### Phase 2: Agent 层迁移

**目标**: 迁移 Agent 实现，建立 `mcp_safe` 注册机制。

**预计时间**: 3h

**触发条件**: Phase 0+1 完成且健康检查通过

#### 2.1 创建 Agent 目录结构

```bash
mkdir -p agent_platform/agents/pure_logic
mkdir -p agent_platform/agents/deprecated
touch agent_platform/agents/__init__.py
touch agent_platform/agents/pure_logic/__init__.py
touch agent_platform/agents/deprecated/__init__.py
```

#### 2.2 创建 protocol.py（无 mcp_safe 属性）

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

    注意：mcp_safe 不在此定义，唯一真相在 AgentMeta (registry.py)。
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

    @abstractmethod
    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """处理请求"""
        ...
```

#### 2.3 创建 registry.py（mcp_safe 唯一真相）

```python
# agent_platform/agents/registry.py

from typing import Dict, Callable, List, Any
from dataclasses import dataclass
import logging

from .protocol import AgentProtocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentMeta:
    """Agent 元信息 - mcp_safe 的唯一真相"""
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

    mcp_safe 参数是判断 Agent 是否可在 MCP 模式运行的唯一依据。
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


def is_agent_mcp_safe(name: str) -> bool:
    """检查 Agent 是否 MCP 安全（从注册表读取）"""
    return get_agent_meta(name).mcp_safe


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

#### 2.4 迁移 pure_logic Agent

详见 v1.1 文档 2.3 节，将 `CodeReviewAgent` 等迁移到 `pure_logic/`。

关键修改：使用 `@register_agent(..., mcp_safe=True)` 装饰器，不定义类属性。

#### Phase 2 健康检查

```bash
# 1. 验证注册表
python -c "from agent_platform.agents.registry import list_agents; print(list_agents())"

# 2. 验证 mcp_safe 检查
python -c "from agent_platform.agents.registry import is_agent_mcp_safe; print('review mcp_safe:', is_agent_mcp_safe('review'))"

# 3. 验证 Agent 创建
python -c "from agent_platform.agents.registry import create_agent; a = create_agent('review'); print('Agent OK:', a.name)"

# 4. 运行测试
pytest agent_platform/tests/ -v --tb=short
```

#### Phase 2 验收 Checklist

- [ ] `agent_platform/agents/` 目录结构已创建
- [ ] `protocol.py` 定义 AgentProtocol（无 mcp_safe 属性）
- [ ] `registry.py` 实现 mcp_safe 唯一真相
- [ ] `pure_logic/` 包含 mcp_safe=True 的 Agent
- [ ] `deprecated/` 包含 mcp_safe=False 的 Agent
- [ ] **健康检查**: 注册表正常
- [ ] **健康检查**: mcp_safe 检查正确
- [ ] **健康检查**: Agent 可创建

---

### Phase 3: 技能层 + 工具层迁移

**目标**: 合并技能和工具层，消除重复。

**预计时间**: 2h

详见 v1.1 文档 Phase 3-4，主要操作：

1. 迁移纯逻辑技能到 `agent_platform/skills/`
2. 迁移需 LLM 的技能到 `agent_platform/skills/deprecated/`
3. 合并 `fs_tool.py`, `validation.py` 等到 `agent_platform/tools/`

#### Phase 3 健康检查

```bash
# 1. 验证技能导入
python -c "from agent_platform.skills import validate_against_sot; print('Skills OK')"

# 2. 验证工具导入
python -c "from agent_platform.tools import fs_tool; print('Tools OK')"

# 3. 运行测试
pytest agent_platform/tests/ -v --tb=short
```

---

### Phase 4: 生态迁移 + MCP 工具重构

**目标**: 更新 `.claude/commands`，重构 MCP 工具模块化。

**预计时间**: 3h

详见 v1.1 文档 Phase 5-6，主要操作：

1. 更新 `gen-backend-mcp.md` 等自定义命令
2. 创建/更新 `.claude/mcp.json`
3. 拆分 MCP 工具到 `mcp/tools/` 目录
4. 增强 `ap_run_agent` 的 mcp_safe 检查

#### Phase 4 健康检查

```bash
# 1. 验证 MCP server 启动
python -m agent_platform.mcp.server &
sleep 2
echo '{"method": "tools/list", "id": 1}' | nc localhost 8080
kill %1

# 2. 检查 .claude/commands 路径
grep -r "agents.cli" .claude/commands/ && echo "WARNING: 旧路径残留" || echo "Commands OK"

# 3. 运行 MCP 测试
pytest agent_platform/tests/test_mcp_server.py -v
```

---

### Phase 5: 观察期 + 最终清理

**目标**: 确认迁移稳定后，删除 `agents/` 目录。

**观察期时间窗口**: 2025-12-05 ~ 2025-12-12 (7 天)

#### 5.1 观察期设计

##### 观察重点

| 监控项 | 检查方式 | 预期结果 | 问题级别 |
|--------|----------|----------|----------|
| MCP Server 稳定响应 | `ap_health_check` | success: true | P0 |
| ap_run_agent(test/review/doc) | 手动调用 | success: true, mcp_safe: true | P0 |
| ap_run_skill(sot_guard/db_test/backend_test) | 手动调用 | success: true | P0 |
| ap_run_tests | pytest 执行 | return_code: 0 | P1 |
| ap_validate_code | 代码验证 | passed: true | P1 |
| Legacy 模式使用 | 日志/环境变量 | 无 AGENT_PLATFORM_LEGACY=1 | P1 |
| 旧路径导入 | grep 检查 | 无 `from agents import` | P2 |

##### 观察期内禁止的动作

```
┌────────────────────────────────────────────────────────────────┐
│                   观察期禁止动作（P0 规则）                       │
├────────────────────────────────────────────────────────────────┤
│  ❌ 修改 MCP Server 核心逻辑 (agent_platform/mcp/server.py)      │
│  ❌ 修改 Agent/Skill Registry 核心 (agent_platform/core/*)       │
│  ❌ 新增 LLM 依赖 Agent 或 Skill                                │
│  ❌ 删除 agents/ 目录中的任何文件                                │
│  ❌ 修改 mcp_safe 标记或 enum 白名单                             │
└────────────────────────────────────────────────────────────────┘
```

##### 观察期内允许的动作

```
┌────────────────────────────────────────────────────────────────┐
│                   观察期允许动作                                 │
├────────────────────────────────────────────────────────────────┤
│  ✅ 修复纯 bug（不改变接口签名）                                 │
│  ✅ 完善测试用例 (agent_platform/tests/*)                       │
│  ✅ 完善文档（MIGRATION_LOG.md, 注释等）                        │
│  ✅ 记录健康检查结果                                            │
│  ✅ 更新 .claude/commands/ 中的提示词（不改变工具调用方式）       │
└────────────────────────────────────────────────────────────────┘
```

#### 5.2 最终清理计划

##### 计划删除的目录/文件

**agents/agent_core/** (6 文件)
| 文件 | 状态 | 新位置 | 说明 |
|------|------|--------|------|
| `__init__.py` | 待删除 | - | Agent 注册已迁移至 agent_platform |
| `fe_agent.py` | 待删除 | `agent_platform/agents/llm_dependent/` | LLM 依赖 Agent |
| `be_agent.py` | 待删除 | `agent_platform/agents/llm_dependent/` | LLM 依赖 Agent |
| `test_agent.py` | 待删除 | `agent_platform/agents/pure_logic/test_agent.py` | 已迁移 |
| `code_review_agent.py` | 待删除 | `agent_platform/agents/pure_logic/code_review_agent.py` | 已迁移 |
| `doc_agent.py` | 待删除 | `agent_platform/agents/pure_logic/doc_agent.py` | 已迁移 |
| `orchestrator_agent.py` | 待删除 | `agent_platform/agents/llm_dependent/` | LLM 依赖 Agent |

**agents/skills/** (8 文件)
| 文件 | 状态 | 新位置 | 说明 |
|------|------|--------|------|
| `__init__.py` | 待删除 | - | Skill 注册已迁移 |
| `db_test_skill.py` | 待删除 | `agent_platform/skills/pure_logic/` | 已迁移 |
| `backend_test_skill.py` | 待删除 | `agent_platform/skills/pure_logic/` | 已迁移 |
| `sot_guard_skill.py` | 待删除 | `agent_platform/skills/pure_logic/` | 已迁移 |
| `fe_dev_skill.py` | 待删除 | `agent_platform/skills/llm_dependent/` | LLM 依赖 |
| `be_dev_skill.py` | 待删除 | `agent_platform/skills/llm_dependent/` | LLM 依赖 |
| `doc_skill.py` | 待删除 | - | 占位未实现 |
| `review_skill.py` | 待删除 | - | 占位未实现 |
| `refactor_skill.py` | 待删除 | - | 占位未实现 |

**agents/tools/** (6 文件)
| 文件 | 状态 | 新位置 | 说明 |
|------|------|--------|------|
| `__init__.py` | 待删除 | - | 工具注册已迁移 |
| `fs_tool.py` | 待删除 | `agent_platform/tools/` | 已迁移 |
| `validation.py` | 待删除 | `agent_platform/tools/` | 已迁移 |
| `types.py` | 待删除 | `agent_platform/tools/types.py` | 已迁移，仅 re-export |
| `llm_client.py` | 待删除 | `agent_platform/llm/` | LLM 客户端 |
| `claude_code_adapter.py` | 待删除 | `agent_platform/tools/` | 已迁移 |
| `supabase_tool.py` | 待删除 | `agent_platform/tools/` | 已迁移 |

**agents/tests/** (8 文件)
| 文件 | 状态 | 说明 |
|------|------|------|
| `__init__.py` | 待删除 | 测试包 |
| `conftest.py` | 待删除 | pytest 配置 |
| `test_*.py` | 待删除 | 所有测试已迁移至 agent_platform/tests/ |

**agents/ 根目录** (7 文件)
| 文件 | 状态 | 说明 |
|------|------|------|
| `__init__.py` | 待删除 | 影子模式转调壳 |
| `cli.py` | 待删除 | CLI 转调壳 |
| `cli_legacy.py` | 待删除 | Legacy CLI 备份 |
| `agents_config.py` | 待删除 | 旧配置（已迁移至 agent_platform/config/） |
| `server.py` | 待删除 | HTTP 服务器（已废弃） |
| `plugin.py` | 待删除 | 插件系统（未使用） |
| `_DEPRECATED.md` | 待删除 | 废弃说明 |

**总计**: 约 40 个文件待删除

##### 需要更新的 .claude/commands/ 文件

扫描结果：**无需更新**

| 文件 | 状态 | 说明 |
|------|------|------|
| `doc-agent.md` | ✅ 已使用 MCP | 使用 ai-ad-doc-* Skill |
| `mcp-orch.md` | ✅ 已使用 MCP | 使用 ap_* MCP 工具 |
| `gen-backend-mcp.md` | ✅ 已使用 MCP | 使用 ap_* MCP 工具 |
| `gen-frontend-mcp.md` | ✅ 已使用 MCP | 使用 ap_* MCP 工具 |

所有 .claude/commands/ 文件已在 Phase 4 完成迁移，无旧 `agents/cli` 或 `from agents import` 引用。

##### 删除前置条件

```
┌────────────────────────────────────────────────────────────────┐
│            删除 agents/ 目录的前置条件（全部满足才可执行）        │
├────────────────────────────────────────────────────────────────┤
│  1. 观察期内无 P0/P1 级 bug                                     │
│  2. agent_platform/tests/ 全量测试通过                          │
│  3. MIGRATION_LOG.md 中记录至少 3 次健康检查结果                 │
│  4. 无 AGENT_PLATFORM_LEGACY=1 环境变量使用记录                  │
│  5. grep -r "from agents import" 无匹配（除 agents/ 自身）       │
│  6. .claude/commands/ 全部使用新 MCP 工具                        │
│  7. CI/CD pipeline 持续绿色                                     │
└────────────────────────────────────────────────────────────────┘
```

#### 5.3 观察期结束 Checklist

##### 功能验收

- [ ] **全量 pytest 通过**: `pytest agent_platform/tests/ -v --tb=short` 返回 0
- [ ] **ap_list_agents 正常**: 返回 `["test", "review", "doc"]` (MCP-safe)
- [ ] **ap_run_agent(test) 正常**: success=True, executed=False
- [ ] **ap_run_agent(review) 正常**: success=True, passed=True (空 changes)
- [ ] **ap_run_agent(doc) 正常**: success=True
- [ ] **ap_list_skills 正常**: 返回 `["db_test", "backend_test", "sot_guard"]`
- [ ] **ap_run_skill(sot_guard) 正常**: success=True, passed=True
- [ ] **ap_run_tests 正常**: 可执行 pytest
- [ ] **ap_health_check 正常**: success=True

##### 安全验收

- [ ] **mcp_safe 强制过滤**: ap_run_agent("fe") 返回 MCP_UNSAFE_AGENT
- [ ] **mcp_safe 强制过滤**: ap_run_skill("fe_dev") 返回 MCP_UNSAFE_SKILL
- [ ] **无循环依赖**: `python -c "import agents; import agent_platform"` 无错误

##### 生态验收

- [ ] **.claude/commands/ 全部使用新接口**: grep 检查无旧路径
- [ ] **无 Legacy 模式使用**: 日志中无 AGENT_PLATFORM_LEGACY=1

##### 删除验收（执行删除后）

- [ ] **agents/ 目录已删除**: `ls agents/` 返回 "No such file or directory"
- [ ] **项目仍可构建**: MCP Server 可启动
- [ ] **全量测试仍通过**: `pytest agent_platform/tests/` 通过

#### 5.4 删除操作命令

```bash
# 观察期结束后，确认所有 Checklist 已完成，执行以下命令：

# 1. 最终验证
pytest agent_platform/tests/ -v --tb=short

# 2. 检查无旧导入
grep -r "from agents import" --include="*.py" . | grep -v "^./agents/"

# 3. 备份并删除
git rm -r agents/

# 4. 提交
git commit -m "refactor(agents): Phase 5 完成 - 删除 agents/ 旧实现

观察期: 2025-12-05 ~ 2025-12-12
- 无 P0/P1 级 bug
- 全量测试通过
- 无 Legacy 模式使用
- .claude/commands/ 全部使用新 MCP 工具

删除内容:
- agents/agent_core/ (6 文件)
- agents/skills/ (9 文件)
- agents/tools/ (7 文件)
- agents/tests/ (8 文件)
- agents/ 根目录 (7 文件)
总计: 约 40 文件

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. 验证删除后项目正常
pytest agent_platform/tests/ -v --tb=short
python -c "from agent_platform.mcp.server import _registry; print('MCP OK:', len(_registry.tools))"
```

---

## 4. 风险评估与回滚

### 4.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 循环依赖 | 中 | 高 | 影子模式用纯 os.environ |
| mcp_safe 不一致 | 低 | 高 | 唯一真相在 AgentMeta |
| BASE_PATH 错误 | 中 | 中 | fallback + 验证 |
| MCP server 无法启动 | 中 | 高 | 每 Phase 健康检查 |

### 4.2 紧急回滚

```bash
# 方式 1: Legacy 模式（立即生效）
export AGENT_PLATFORM_LEGACY=1

# 方式 2: Git 回滚
git checkout master -- agents/ agent_platform/ .claude/
```

---

## 5. 时间估算

| Phase | 描述 | 预计时间 | 备注 |
|-------|------|----------|------|
| 0 | Freeze & 影子模式 | 1.5h | **第一轮** |
| 1 | 配置层迁移 | 2h | **第一轮** |
| 2 | Agent 层迁移 | 3h | 后续触发 |
| 3 | 技能层 + 工具层 | 2h | 后续触发 |
| 4 | 生态迁移 + MCP 重构 | 3h | 后续触发 |
| 5 | 观察期 + 清理 | 7 天 | 观察期 |
| **总计** | | **11.5h + 7 天** | |

---

## 6. 最终验收 Checklist

### 功能验收

- [ ] MCP 服务可启动：`python -m agent_platform.mcp.server`
- [ ] SoT 读取正常：`ap_read_sot("STATE_MACHINE")`
- [ ] mcp_safe Agent 可运行：`ap_run_agent("review", {...})`
- [ ] 非 mcp_safe Agent 被拒绝：返回 `MCP_SAFETY_VIOLATION`

### 安全验收

- [ ] mcp_safe 唯一真相在 AgentMeta
- [ ] 影子模式无循环依赖
- [ ] Legacy 模式可正常回退

### 生态验收

- [ ] `.claude/commands` 使用新路径
- [ ] `.claude/mcp.json` 配置正确
- [ ] `CLAUDE.md` 已更新

---

## 附录

### A. 环境变量

| 变量 | 值 | 说明 |
|------|-----|------|
| `AGENT_PLATFORM_MODE` | `mcp` / `cli` | 运行模式 |
| `AGENT_PLATFORM_LEGACY` | `1` / `0` | Legacy 模式回退 |
| `AGENT_PLATFORM_REPO_ROOT` | 路径 | 覆盖 BASE_PATH |

### B. 健康检查命令汇总

```bash
# Phase 0
python -c "import agents; print('Shadow OK')"
AGENT_PLATFORM_LEGACY=1 python -c "from agents import BASE_PATH; print('Legacy OK')"

# Phase 1
python -c "from agent_platform.config import SOT_FILES; print('Config OK:', len(SOT_FILES))"
python -c "from agent_platform.mcp.server import _registry; print('MCP OK:', len(_registry.tools))"

# Phase 2
python -c "from agent_platform.agents.registry import list_mcp_safe_agents; print(list_mcp_safe_agents())"

# 全量测试
pytest agent_platform/tests/ agents/tests/ -v --tb=short
```

---

**文档版本**: v1.2 Final
**状态**: Ready for Execution
**执行建议**: 第一轮只执行 Phase 0 + Phase 1，验证通过后再触发后续 Phase
