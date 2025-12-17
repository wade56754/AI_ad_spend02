"""
sot_loader.py - 统一 SoT 文档加载器

对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0 Section 9.2:
- Layer 6: SoT 文档层 (Single Source of Truth)
- 提供统一的 SoT 文档加载接口
- 支持按 Skill 声明的依赖自动加载
- 缓存机制避免重复读取

SoT 裁判链优先级:
STATE_MACHINE.md → DATA_SCHEMA.md → BUSINESS_RULES.md
→ API_SOT.md → ERROR_CODES_SOT.md → AUTH_SPEC.md → LEDGER_SOT.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class SoTCategory(str, Enum):
    """SoT 文档分类"""
    # 核心 SoT (必须加载)
    STATE_MACHINE = "STATE_MACHINE"
    DATA_SCHEMA = "DATA_SCHEMA"
    BUSINESS_RULES = "BUSINESS_RULES"
    API_SOT = "API_SOT"
    ERROR_CODES = "ERROR_CODES"

    # 扩展 SoT (按需加载)
    AUTH_SPEC = "AUTH_SPEC"
    LEDGER_SOT = "LEDGER_SOT"
    TOPUP_SOT = "TOPUP_SOT"
    DAILY_REPORT_SOT = "DAILY_REPORT_SOT"
    RECONCILIATION_SOT = "RECONCILIATION_SOT"
    TRANSFER_SOT = "TRANSFER_SOT"
    RLS_POLICIES = "RLS_POLICIES"

    # 概览文档 (参考)
    MASTER = "MASTER"
    PROJECT = "PROJECT"
    ARCHITECTURE = "ARCHITECTURE"

    # 开发指南 (参考)
    FRONTEND_RULES = "FRONTEND_RULES"
    UI_DESIGN_SYSTEM = "UI_DESIGN_SYSTEM"
    TESTING_STRATEGY = "TESTING_STRATEGY"


@dataclass
class SoTDependency:
    """SoT 依赖声明"""
    required: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)


@dataclass
class SoTSnapshot:
    """SoT 文档快照"""
    documents: Dict[str, str] = field(default_factory=dict)
    missing_required: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    loaded_from_cache: bool = False

    def get(self, key: str, default: str = "") -> str:
        """获取文档内容"""
        return self.documents.get(key, default)

    def has_all_required(self) -> bool:
        """检查是否加载了所有必需文档"""
        return len(self.missing_required) == 0

    def to_context_block(self) -> str:
        """转换为 Prompt 上下文块"""
        blocks = []
        for key, content in self.documents.items():
            if content:
                blocks.append(f"<DOC name=\"{key}\">\n{content}\n</DOC>")
        return "\n\n".join(blocks)


class SoTLoader:
    """
    统一 SoT 文档加载器

    使用示例:
        loader = SoTLoader(base_path)

        # 按 Skill 依赖加载
        snapshot = loader.load_for_skill("be-gen")

        # 手动指定加载
        snapshot = loader.load(
            required=["STATE_MACHINE", "DATA_SCHEMA"],
            optional=["LEDGER_SOT"]
        )

        # 获取 Prompt 上下文
        context = snapshot.to_context_block()
    """

    # SoT 文件路径映射 (相对于 BASE_PATH)
    SOT_PATHS: Dict[str, str] = {
        # Layer 2: SoT (v2.6 Freeze)
        "STATE_MACHINE": "docs/2.sot/STATE_MACHINE.md",
        "DATA_SCHEMA": "docs/2.sot/DATA_SCHEMA.md",
        "BUSINESS_RULES": "docs/2.sot/BUSINESS_RULES.md",
        "API_SOT": "docs/2.sot/API_SOT.md",
        "ERROR_CODES": "docs/2.sot/ERROR_CODES_SOT.md",
        "AUTH_SPEC": "docs/2.sot/AUTH_SPEC.md",
        "LEDGER_SOT": "docs/2.sot/LEDGER_SOT.md",
        "TOPUP_SOT": "docs/2.sot/TOPUP_SOT.md",
        "DAILY_REPORT_SOT": "docs/2.sot/DAILY_REPORT_SOT.md",
        "RECONCILIATION_SOT": "docs/2.sot/RECONCILIATION_SOT.md",
        "TRANSFER_SOT": "docs/2.sot/TRANSFER_SOT.md",
        "RLS_POLICIES": "docs/2.sot/RLS_POLICIES_SOT.md",

        # Layer 1: Overview
        "MASTER": "docs/1.overview/MASTER.md",
        "PROJECT": "docs/1.overview/PROJECT.md",
        "ARCHITECTURE": "docs/1.overview/ARCHITECTURE.md",
        "PATTERNS": "docs/1.overview/PATTERNS.md",
        "TESTING": "docs/1.overview/TESTING.md",
        "DOMAIN": "docs/1.overview/DOMAIN.md",
        "DEPLOYMENT": "docs/1.overview/DEPLOYMENT.md",

        # Layer 3: Dev-Guides
        "FRONTEND_RULES": "docs/3.dev-guides/FRONTEND_DEVELOPMENT_RULES.md",
        "UI_DESIGN_SYSTEM": "docs/3.dev-guides/UI_DESIGN_SYSTEM.md",
        "UI_FLOW_SPEC": "docs/3.dev-guides/UI_FLOW_SPEC.md",
        "API_DEV_FLOW": "docs/3.dev-guides/API_DEVELOPMENT_FLOW.md",
        "DDD_ARCHITECTURE": "docs/3.dev-guides/DDD_API_ARCHITECTURE.md",
        "TESTING_STRATEGY": "docs/3.dev-guides/TESTING_STRATEGY.md",
        "AGENT_WORKFLOW": "docs/3.dev-guides/AGENT_WORKFLOW_GUIDE.md",
    }

    # Skill 依赖预设 (对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0)
    SKILL_DEPENDENCIES: Dict[str, SoTDependency] = {
        "be-gen": SoTDependency(
            required=["DATA_SCHEMA", "STATE_MACHINE", "API_SOT", "BUSINESS_RULES", "ERROR_CODES"],
            optional=["LEDGER_SOT", "AUTH_SPEC", "MASTER"]
        ),
        "test-gen": SoTDependency(
            required=["STATE_MACHINE", "DATA_SCHEMA", "BUSINESS_RULES", "ERROR_CODES"],
            optional=["LEDGER_SOT", "API_SOT", "TESTING_STRATEGY"]
        ),
        "fe-gen": SoTDependency(
            required=["API_SOT", "STATE_MACHINE"],
            optional=["FRONTEND_RULES", "UI_DESIGN_SYSTEM", "UI_FLOW_SPEC", "DATA_SCHEMA"]
        ),
        "sot-check": SoTDependency(
            required=["STATE_MACHINE", "DATA_SCHEMA", "API_SOT", "ERROR_CODES", "LEDGER_SOT", "AUTH_SPEC"],
            optional=["BUSINESS_RULES", "MASTER"]
        ),
        "doc-gen": SoTDependency(
            required=["MASTER", "PROJECT"],
            optional=["ARCHITECTURE", "PATTERNS"]
        ),
    }

    # 关键 SoT 文件列表 (缺失时发出警告)
    CRITICAL_SOT: Set[str] = {
        "STATE_MACHINE", "DATA_SCHEMA", "BUSINESS_RULES",
        "API_SOT", "ERROR_CODES", "LEDGER_SOT", "AUTH_SPEC"
    }

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化 SoT Loader

        Args:
            base_path: 项目根路径 (默认自动检测)
        """
        self.base_path = base_path or self._detect_base_path()
        self._cache: Dict[str, str] = {}
        self._warned_missing: Set[str] = set()

    @staticmethod
    def _detect_base_path() -> Path:
        """自动检测项目根路径"""
        # 从当前文件向上查找 CLAUDE.md 所在目录
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "CLAUDE.md").exists():
                return parent
        # 回退到默认路径
        return Path(__file__).resolve().parent.parent.parent

    def _read_file(self, key: str) -> str:
        """
        读取单个 SoT 文件

        Args:
            key: SoT 文件键名 (如 "STATE_MACHINE")

        Returns:
            文件内容，或空字符串（文件不存在时）
        """
        # 检查缓存
        if key in self._cache:
            return self._cache[key]

        rel_path = self.SOT_PATHS.get(key)
        if not rel_path:
            logger.warning(f"[SoT Loader] Unknown SoT key: {key}")
            return ""

        full_path = self.base_path / rel_path

        try:
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                self._cache[key] = content
                logger.debug(f"[SoT Loader] Loaded {key}: {len(content)} chars")
                return content
            else:
                # 关键 SoT 文件缺失警告 (每个文件只警告一次)
                if key in self.CRITICAL_SOT and key not in self._warned_missing:
                    self._warned_missing.add(key)
                    logger.warning(
                        f"[SoT Warning] Critical SoT file missing: {rel_path}. "
                        "Agent operations may use default values."
                    )
                return ""
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.error(f"[SoT Loader] Error reading {full_path}: {e}")
            return ""

    def load(
        self,
        required: Optional[List[str]] = None,
        optional: Optional[List[str]] = None,
    ) -> SoTSnapshot:
        """
        加载指定的 SoT 文档

        Args:
            required: 必需的 SoT 键名列表
            optional: 可选的 SoT 键名列表

        Returns:
            SoTSnapshot 包含加载的文档和缺失信息
        """
        required = required or []
        optional = optional or []

        snapshot = SoTSnapshot()

        # 加载必需文档
        for key in required:
            content = self._read_file(key)
            if content:
                snapshot.documents[key] = content
            else:
                snapshot.missing_required.append(key)

        # 加载可选文档
        for key in optional:
            content = self._read_file(key)
            if content:
                snapshot.documents[key] = content
            else:
                snapshot.missing_optional.append(key)

        # 记录加载结果
        loaded_count = len(snapshot.documents)
        total_count = len(required) + len(optional)
        logger.info(
            f"[SoT Loader] Loaded {loaded_count}/{total_count} documents "
            f"(missing required: {len(snapshot.missing_required)})"
        )

        return snapshot

    def load_for_skill(self, skill_name: str) -> SoTSnapshot:
        """
        按 Skill 依赖加载 SoT 文档

        Args:
            skill_name: Skill 名称 (如 "be-gen", "test-gen")

        Returns:
            SoTSnapshot 包含 Skill 所需的所有文档
        """
        dep = self.SKILL_DEPENDENCIES.get(skill_name)
        if not dep:
            logger.warning(f"[SoT Loader] Unknown skill: {skill_name}, loading core SoT")
            dep = SoTDependency(
                required=["STATE_MACHINE", "DATA_SCHEMA", "ERROR_CODES"],
                optional=[]
            )

        logger.info(f"[SoT Loader] Loading SoT for skill: {skill_name}")
        return self.load(required=dep.required, optional=dep.optional)

    def load_all_core(self) -> SoTSnapshot:
        """
        加载所有核心 SoT 文档

        Returns:
            包含所有核心 SoT 的快照
        """
        return self.load(
            required=list(self.CRITICAL_SOT),
            optional=["MASTER", "PROJECT"]
        )

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        logger.debug("[SoT Loader] Cache cleared")

    def get_arbitration_chain(self) -> List[str]:
        """
        获取 SoT 裁判链顺序

        根据 CLAUDE.md 定义的优先级:
        STATE_MACHINE → DATA_SCHEMA → BUSINESS_RULES → API_SOT → ERROR_CODES → AUTH_SPEC → LEDGER_SOT
        """
        return [
            "STATE_MACHINE",
            "DATA_SCHEMA",
            "BUSINESS_RULES",
            "API_SOT",
            "ERROR_CODES",
            "AUTH_SPEC",
            "LEDGER_SOT",
        ]


# === 便捷函数 ===

_default_loader: Optional[SoTLoader] = None


def get_sot_loader(base_path: Optional[Path] = None) -> SoTLoader:
    """
    获取全局 SoT Loader 实例 (单例模式)

    Args:
        base_path: 项目根路径 (仅首次调用时生效)

    Returns:
        SoTLoader 实例
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = SoTLoader(base_path)
    return _default_loader


def load_sot_for_skill(skill_name: str, base_path: Optional[Path] = None) -> SoTSnapshot:
    """
    便捷函数: 按 Skill 加载 SoT

    Args:
        skill_name: Skill 名称
        base_path: 项目根路径

    Returns:
        SoTSnapshot
    """
    loader = get_sot_loader(base_path)
    return loader.load_for_skill(skill_name)


def load_sot(
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
    base_path: Optional[Path] = None,
) -> SoTSnapshot:
    """
    便捷函数: 加载指定 SoT

    Args:
        required: 必需的 SoT 列表
        optional: 可选的 SoT 列表
        base_path: 项目根路径

    Returns:
        SoTSnapshot
    """
    loader = get_sot_loader(base_path)
    return loader.load(required=required, optional=optional)


__all__ = [
    "SoTLoader",
    "SoTSnapshot",
    "SoTDependency",
    "SoTCategory",
    "get_sot_loader",
    "load_sot_for_skill",
    "load_sot",
]
