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
from typing import Any, Callable, Dict, List, Optional, Protocol
from typing_extensions import TypedDict  # Fix: Python 3.11 兼容

# === Agent 导入采用延迟加载 ===
# 避免循环导入：agent_core 模块可能导入本模块的 SOT_FILES 等常量
# 实际导入在各 factory 函数中完成


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
PROJECT_ROOT = BASE_PATH  # Alias for compatibility with sot_guard_skill.py

# 前后端代码目录
BACKEND_DIR = BASE_PATH / "backend"
FRONTEND_DIR = BASE_PATH / "frontend"

# SoT 文档路径映射 (对齐 SoT Freeze v2.6 + Dev-Guides Freeze vFinal)
SOT_FILES: Dict[str, Path] = {
    # Layer 1: Overview
    "MASTER": BASE_PATH / "docs/1.overview/MASTER.md",
    "PROJECT": BASE_PATH / "docs/1.overview/PROJECT.md",
    "ARCHITECTURE": BASE_PATH / "docs/1.overview/ARCHITECTURE.md",
    "PATTERNS": BASE_PATH / "docs/1.overview/PATTERNS.md",
    "TESTING": BASE_PATH / "docs/1.overview/TESTING.md",
    "DOMAIN": BASE_PATH / "docs/1.overview/DOMAIN.md",
    "DEPLOYMENT": BASE_PATH / "docs/1.overview/DEPLOYMENT.md",
    # Layer 2: SoT (v2.6 Freeze)
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
    "RLS_POLICIES": BASE_PATH / "docs/2.sot/RLS_POLICIES_SOT.md",
    "TOPUP_SOT": BASE_PATH / "docs/2.sot/TOPUP_SOT.md",
    # Layer 3: Dev-Guides (vFinal Freeze)
    "FRONTEND_RULES": BASE_PATH / "docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md",
    "UI_DESIGN_SYSTEM": BASE_PATH / "docs/3.dev-guides/UI_DESIGN_SYSTEM.md",
    "UI_FLOW_SPEC": BASE_PATH / "docs/3.dev-guides/UI_FLOW_SPEC.md",
    "API_DEV_FLOW": BASE_PATH / "docs/3.dev-guides/API_DEVELOPMENT_FLOW.md",
    "DDD_ARCHITECTURE": BASE_PATH / "docs/3.dev-guides/DDD_API_ARCHITECTURE.md",
    "TESTING_STRATEGY": BASE_PATH / "docs/3.dev-guides/TESTING_STRATEGY.md",
    "AGENT_WORKFLOW": BASE_PATH / "docs/3.dev-guides/AGENT_WORKFLOW_GUIDE.md",
    # Test artifacts (可选)
    "DB_TEST_CASES": BASE_PATH / "tests/db_invariants_test_cases.md",
    "DB_INVARIANTS_SQL": BASE_PATH / "tests/db_invariants_test_v2.sql",
}

# Frontend restructure pipeline 默认目标文件列表
# 对应 OrchestratorAgent._run_frontend_restructure() 中的 frontend_files
# 可通过 request["frontend_files"] 覆盖
FRONTEND_RESTRUCTURE_FILES: List[str] = [
    "src/lib/api/apiFetch.ts",
    "src/lib/api/apiTypes.ts",
    "src/lib/api/apiErrors.ts",
    "src/lib/api/queryKeys.ts",
    "src/lib/auth/authStore.ts",
    "src/modules/daily-reports/types/dailyReport.types.ts",
    "src/modules/daily-reports/services/dailyReportsApi.ts",
    "src/modules/daily-reports/hooks/useDailyReports.ts",
    "src/modules/topups/types/topup.types.ts",
    "src/modules/topups/services/topupsApi.ts",
    "src/modules/ledger/types/ledger.types.ts",
    "src/modules/reconciliation/types/reconciliation.types.ts",
]


logger = logging.getLogger(__name__)

# Critical SoT files that should trigger warnings when missing
# Fix: P2-03 - 添加 AUTH_SPEC 到关键 SoT 文件列表
CRITICAL_SOT_FILES = {
    "STATE_MACHINE", "DATA_SCHEMA", "BUSINESS_RULES",
    "API_SOT", "ERROR_CODES", "LEDGER_SOT", "AUTH_SPEC",
}

# Track which missing files have been warned about (avoid duplicate warnings)
_warned_missing_files: set = set()


def read_optional(path: Path, warn_if_critical: bool = True) -> str:
    """
    读取文件内容，如果文件不存在则返回空字符串。

    P2 增强：对关键 SoT 文件缺失发出警告（每个文件只警告一次）。

    Args:
        path: 文件路径
        warn_if_critical: 是否在关键文件缺失时发出警告（默认 True）

    Returns:
        文件内容，或空字符串（文件不存在时）
    """
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
        else:
            # P2-10: Add warning for missing critical SoT files
            if warn_if_critical:
                _warn_if_critical_missing(path)
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        logger.warning(f"Error reading file {path}: {e}")
    return ""


def _warn_if_critical_missing(path: Path) -> None:
    """
    Check if a missing file is a critical SoT file and warn if so.

    Only warns once per file path to avoid log spam.
    """
    global _warned_missing_files

    # Check if this is a critical SoT file
    for sot_key, sot_path in SOT_FILES.items():
        if sot_path == path and sot_key in CRITICAL_SOT_FILES:
            if str(path) not in _warned_missing_files:
                _warned_missing_files.add(str(path))
                logger.warning(
                    f"[SoT Warning] Critical SoT file missing: {path.name} "
                    f"(key: {sot_key}). Agent operations may use default values "
                    "which could be outdated. Ensure SoT documents exist."
                )
            break


# === LLM 配置常量 ===

LLM_CONFIG: Dict[str, Any] = {
    "model": "claude-3-5-sonnet-latest",
    "max_tokens": 8000,
    "temperature": 0,
}


# === Claude Code CLI 配置 ===

def get_llm_backend() -> str:
    """
    检测当前使用的 LLM 后端。

    Returns:
        "anthropic_api" - 使用 Anthropic API（需要 ANTHROPIC_API_KEY）
        "claude_code" - 使用 Claude Code CLI（支持 Claude Max 订阅）
    """
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic_api"
    return "claude_code"


def check_llm_available() -> Dict[str, Any]:
    """
    检查 LLM 服务是否可用。

    Returns:
        {
            "available": bool,
            "backend": str,  # "anthropic_api" 或 "claude_code"
            "message": str,
            "details": Any
        }
    """
    import os
    backend = get_llm_backend()

    if backend == "anthropic_api":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            return {
                "available": True,
                "backend": "anthropic_api",
                "message": "Anthropic API 可用",
                "details": {"key_prefix": api_key[:10] + "..."},
            }
        return {
            "available": False,
            "backend": "anthropic_api",
            "message": "ANTHROPIC_API_KEY 未设置",
            "details": None,
        }

    # Claude Code CLI 检测
    from .tools.claude_code_adapter import check_claude_code_available
    result = check_claude_code_available()

    return {
        "available": result["available"],
        "backend": "claude_code",
        "message": "Claude Code CLI 可用" if result["available"] else result["error"],
        "details": {
            "path": result.get("path"),
            "version": result.get("version"),
        },
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
# 注意：使用延迟导入避免循环依赖


def _fe_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> "AgentProtocol":
    """前端 Agent 工厂"""
    from .agent_core.fe_agent import FEAgent
    return FEAgent(base_path=base_path or _default_base_path())


def _be_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> "AgentProtocol":
    """后端 Agent 工厂"""
    from .agent_core.be_agent import BEAgent
    return BEAgent(base_path=base_path or _default_base_path())


def _test_agent_factory(
    base_path: Optional[Path] = None,
    supabase_project_id: Optional[str] = None,
    **_: Any,
) -> "AgentProtocol":
    """
    测试 Agent 工厂

    supabase_project_id:
        - 传入后会注入给 TestAgent(project_id=...)
        - 不传则只解析/生成 SQL & 用例，不真正执行
    """
    from .agent_core.test_agent import TestAgent
    # Phase 3.0A: TestAgent only accepts base_path, not project_id
    return TestAgent(
        base_path=base_path or _default_base_path(),
    )


def _orchestrator_agent_factory(
    base_path: Optional[Path] = None,
    supabase_project_id: Optional[str] = None,
    **_: Any,
) -> "AgentProtocol":
    """Orchestrator Agent 工厂"""
    from .agent_core.orchestrator_agent import OrchestratorAgent
    return OrchestratorAgent(
        base_path=base_path or _default_base_path(),
        supabase_project_id=supabase_project_id,
    )


def _doc_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> "AgentProtocol":
    """文档 Agent 工厂"""
    from .agent_core.doc_agent import DocAgent
    return DocAgent(base_path=base_path or _default_base_path())


def _code_review_agent_factory(
    base_path: Optional[Path] = None,
    **_: Any,
) -> "AgentProtocol":
    """代码审核 Agent 工厂"""
    from .agent_core.code_review_agent import CodeReviewAgent
    return CodeReviewAgent(base_path=base_path or _default_base_path())


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
    "doc": AgentMeta(
        key="doc",
        name="DocAgent",
        description="文档 Agent：负责生成/审核/同步项目文档。",
        factory=_doc_agent_factory,
    ),
    "review": AgentMeta(
        key="review",
        name="CodeReviewAgent",
        description="代码审核 Agent：负责 SoT 一致性检查和代码质量审核。",
        factory=_code_review_agent_factory,
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
    "PROJECT_ROOT",  # Alias for BASE_PATH
    "BACKEND_DIR",
    "FRONTEND_DIR",
    # SoT 文档配置
    "SOT_FILES",
    "CRITICAL_SOT_FILES",
    # LLM 配置
    "LLM_CONFIG",
    "get_llm_backend",
    "check_llm_available",
    # 工具函数
    "read_optional",
    "setup_logging",
    # 类型定义
    "AgentProtocol",
    "AgentInfo",
    # Pipeline 配置
    "FRONTEND_RESTRUCTURE_FILES",
]
