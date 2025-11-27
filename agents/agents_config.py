"""
agents_config.py

统一管理项目中的 Agent 注册与创建逻辑：
- 提供 agent 名称到实际实现类的映射
- 对外暴露 create_agent / list_agents，方便 CLI 等入口调用
"""

from __future__ import annotations
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol, TypedDict

# === 引入各个 Agent 实现 ===
from .agent_core.fe_agent import FEAgent
from .agent_core.be_agent import BEAgent
from .agent_core.test_agent import TestAgent
from .agent_core.orchestrator_agent import OrchestratorAgent


# === 通用 Agent 协议（方便类型检查，不强制继承） ===
class AgentProtocol(Protocol):
    """所有 Agent 建议至少实现 handle_request 或 run 之一"""

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        ...


# === Agent 元信息结构 ===
@dataclass(frozen=True)
class AgentMeta:
    key: str
    name: str
    description: str
    factory: Callable[..., AgentProtocol]


class AgentInfo(TypedDict):
    key: str
    name: str
    description: str


# === 项目路径与 SoT 文档配置 ===


def _default_base_path() -> Path:
    """
    推断项目根路径：
    agents/
      ├─ agents_config.py  ← 当前文件
      └─ agent_core/
    默认返回 agents/ 的上一级目录（项目根）
    """
    return Path(__file__).resolve().parent.parent


# 项目根路径（供外部导入使用）
BASE_PATH = _default_base_path()

# 前后端代码目录
BACKEND_DIR = BASE_PATH / "backend"
FRONTEND_DIR = BASE_PATH / "frontend"

# SoT 文档路径映射
SOT_FILES: Dict[str, Path] = {
    "MASTER": BASE_PATH / "docs/1.overview/MASTER.md",
    "PROJECT": BASE_PATH / "docs/1.overview/PROJECT.md",
    "ARCHITECTURE": BASE_PATH / "docs/1.overview/ARCHITECTURE.md",
    "PATTERNS": BASE_PATH / "docs/1.overview/PATTERNS.md",
    "TESTING": BASE_PATH / "docs/1.overview/TESTING.md",
    "API_SOT": BASE_PATH / "docs/2.sot/API_SOT.md",
    "DATA_SCHEMA": BASE_PATH / "docs/2.sot/DATA_SCHEMA.md",
    "STATE_MACHINE": BASE_PATH / "docs/2.sot/STATE_MACHINE.md",
    "BUSINESS_RULES": BASE_PATH / "docs/2.sot/BUSINESS_RULES.md",
    "ERROR_CODES": BASE_PATH / "docs/2.sot/ERROR_CODES_SOT.md",
    "LEDGER_SOT": BASE_PATH / "docs/2.sot/LEDGER_SOT.md",
    "DAILY_REPORT_SOT": BASE_PATH / "docs/2.sot/DAILY_REPORT_SOT.md",
    "RECONCILIATION_SOT": BASE_PATH / "docs/2.sot/RECONCILIATION_SOT.md",
    "TRANSFER_SOT": BASE_PATH / "docs/2.sot/TRANSFER_SOT.md",
    "AUTH_SPEC": BASE_PATH / "docs/2.sot/AUTH_SPEC.md",
    "RLS_POLICIES": BASE_PATH / "docs/2.sot/RLS_POLICIES.md",
    "FRONTEND_RULES": BASE_PATH / "docs/3.dev-guides/FRONTEND_SPEC.md",
    "UI_DESIGN_SYSTEM": BASE_PATH / "docs/3.dev-guides/UI_DESIGN_SYSTEM.md",
    "DB_TEST_CASES": BASE_PATH / "tests/db_invariants_test_cases.md",
    "DB_INVARIANTS_SQL": BASE_PATH / "tests/db_invariants_test_v2.sql",
}


def read_optional(path: Path) -> str:
    """
    读取文件内容，如果文件不存在则返回空字符串。

    Args:
        path: 文件路径

    Returns:
        文件内容，或空字符串（文件不存在时）
    """
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError, OSError):
        pass
    return ""


# === LLM 配置常量 ===

LLM_CONFIG: Dict[str, Any] = {
    "model": "claude-3-5-sonnet-latest",
    "max_tokens": 8000,
    "temperature": 0,
}


# === 日志配置 ===

def setup_logging(level: int = logging.INFO) -> None:
    """
    配置 agents 模块的日志系统。

    Args:
        level: 日志级别（默认 INFO）
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# === 各 Agent 的工厂函数 ===


def _fe_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> FEAgent:
    """前端 Agent 工厂"""
    return FEAgent(base_path=base_path or _default_base_path())


def _be_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> BEAgent:
    """后端 Agent 工厂"""
    return BEAgent(base_path=base_path or _default_base_path())


def _test_agent_factory(
    base_path: Optional[Path] = None,
    supabase_project_id: Optional[str] = None,
    **_: Any,
) -> TestAgent:
    """
    测试 Agent 工厂

    supabase_project_id:
        - 传入后会注入给 TestAgent(project_id=...)
        - 不传则只解析/生成 SQL & 用例，不真正执行
    """
    return TestAgent(
        base_path=base_path or _default_base_path(),
        project_id=supabase_project_id,
    )


def _orchestrator_agent_factory(
    base_path: Optional[Path] = None,
    supabase_project_id: Optional[str] = None,
    **_: Any,
) -> OrchestratorAgent:
    """Orchestrator Agent 工厂"""
    return OrchestratorAgent(
        base_path=base_path or _default_base_path(),
        supabase_project_id=supabase_project_id,
    )


# === 注册中心 ===

_AGENT_REGISTRY: Dict[str, AgentMeta] = {
    "fe": AgentMeta(
        key="fe",
        name="FrontendAgent",
        description="前端开发 Agent：负责 TSX 组件/页面的生成与重构。",
        factory=_fe_agent_factory,
    ),
    "be": AgentMeta(
        key="be",
        name="BackendAgent",
        description="后端开发 Agent：负责 FastAPI Router/Service 等后端代码生成与重构。",
        factory=_be_agent_factory,
    ),
    "test": AgentMeta(
        key="test",
        name="TestAgent",
        description="测试 Agent：负责数据库不变量测试脚本与用例的生成与执行。",
        factory=_test_agent_factory,
    ),
    "orch": AgentMeta(
        key="orch",
        name="OrchestratorAgent",
        description="总控 Orchestrator Agent：协调前端/后端/测试三个 Agent 组成流水线。",
        factory=_orchestrator_agent_factory,
    ),
}


# === 对外暴露的工具函数 ===


def list_agents() -> Dict[str, AgentInfo]:
    """
    列出当前可用的 Agent 信息，给 CLI 或上层调用展示使用。

    Returns:
        {
          "fe":   {"key": "fe",   "name": "FrontendAgent",     "description": "..."},
          "be":   {"key": "be",   "name": "BackendAgent",      "description": "..."},
          "test": {"key": "test", "name": "TestAgent",         "description": "..."},
          "orch": {"key": "orch", "name": "OrchestratorAgent", "description": "..."},
        }
    """
    return {
        key: AgentInfo(
            key=meta.key,
            name=meta.name,
            description=meta.description,
        )
        for key, meta in _AGENT_REGISTRY.items()
    }


def create_agent(
    name: str,
    base_path: Optional[Path] = None,
    **kwargs: Any,
) -> AgentProtocol:
    """
    Create an agent instance by name.

    Available agents:
        - "fe" or "FEAgent": Frontend code generation (TSX/React)
        - "be" or "BEAgent": Backend code generation (FastAPI/Service)
        - "test" or "TestAgent": DB test prompt generation
        - "orch" or "OrchestratorAgent": Multi-agent workflow coordinator

    Args:
        name: Agent key (case-insensitive), e.g., "fe", "be", "test", "orch"
        base_path: Project root directory (defaults to auto-detected path)
        **kwargs: Agent-specific parameters:
                  - supabase_project_id: For TestAgent and OrchestratorAgent

    Returns:
        Agent instance conforming to AgentProtocol (has handle_request method)

    Raises:
        KeyError: If agent name is not recognized
    """
    key = name.strip().lower()
    if key not in _AGENT_REGISTRY:
        available = ", ".join(sorted(_AGENT_REGISTRY.keys()))
        raise KeyError(f"Unknown agent '{name}'. Available: {available}")

    meta = _AGENT_REGISTRY[key]
    return meta.factory(base_path=base_path, **kwargs)


# === 对外暴露的接口 ===

__all__ = [
    # Agent 管理函数
    "create_agent",
    "list_agents",
    # 项目路径
    "BASE_PATH",
    "BACKEND_DIR",
    "FRONTEND_DIR",
    # SoT 文档配置
    "SOT_FILES",
    # LLM 配置
    "LLM_CONFIG",
    # 工具函数
    "read_optional",
    "setup_logging",
    # 类型定义
    "AgentProtocol",
    "AgentInfo",
]
