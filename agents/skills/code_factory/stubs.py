"""
Stub implementations for deprecated modules.

These stubs exist to maintain backward compatibility with factory.py
while the actual functionality has been migrated to Claude Code native features.

Migration Status:
- CodeSearcher → Use Claude Code Grep/Glob tools
- CodeSelector → Use Claude Code understanding
- CodeAdapter → Rules inlined to Hook system
- CodeAssembler → Use Claude Code generation

Version: 6.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import warnings


def _deprecation_warning(name: str, replacement: str):
    """发出废弃警告"""
    warnings.warn(
        f"{name} is deprecated in v6.0. Use {replacement} instead.",
        DeprecationWarning,
        stacklevel=3,
    )


# =============================================================================
# CodeSearcher Stubs
# =============================================================================


@dataclass
class SearchCandidate:
    """搜索候选 (stub)"""

    file_path: str = ""
    score: float = 0.0
    reason: str = "Stub implementation"
    snippet: str = ""


@dataclass
class SearchResult:
    """搜索结果 (stub)"""

    candidates: List[SearchCandidate] = field(default_factory=list)
    search_time: float = 0.0
    source: str = "stub"


class CodeSearcher:
    """代码搜索器 (stub) - 使用 Claude Code Grep/Glob 替代"""

    def __init__(self, project_root: Path = None, sot_base_path: Path = None, **kwargs):
        _deprecation_warning("CodeSearcher", "Claude Code Grep/Glob tools")
        self.project_root = project_root or Path(".")

    def search(self, requirement: str, **kwargs) -> SearchResult:
        """搜索相关代码 (stub)"""
        return SearchResult(candidates=[], search_time=0.0, source="stub")


# =============================================================================
# CodeSelector Stubs
# =============================================================================


@dataclass
class AdaptationPlan:
    """适配计划 (stub)"""

    files_to_modify: List[str] = field(default_factory=list)
    new_files: List[str] = field(default_factory=list)
    adaptations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SelectionResult:
    """选择结果 (stub)"""

    selected_files: List[str] = field(default_factory=list)
    plan: AdaptationPlan = field(default_factory=AdaptationPlan)
    reasoning: str = "Stub implementation"


class CodeSelector:
    """代码选择器 (stub) - 使用 Claude Code 替代"""

    def __init__(self, project_root: Path = None, **kwargs):
        _deprecation_warning("CodeSelector", "Claude Code understanding")
        self.project_root = project_root or Path(".")

    def select(
        self, candidates: List[SearchCandidate], requirement: str, **kwargs
    ) -> SelectionResult:
        """选择相关代码 (stub)"""
        return SelectionResult(
            selected_files=[], plan=AdaptationPlan(), reasoning="Stub - use Claude Code"
        )


# =============================================================================
# CodeAdapter Stubs
# =============================================================================


@dataclass
class AdaptedFile:
    """适配后的文件 (stub)"""

    path: str = ""
    content: str = ""
    original_content: str = ""
    changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AdaptResult:
    """适配结果 (stub)"""

    files: List[AdaptedFile] = field(default_factory=list)
    success: bool = True
    message: str = "Stub implementation"


class CodeAdapter:
    """代码适配器 (stub) - 规则已内联到 Hook 系统"""

    def __init__(self, project_root: Path = None, **kwargs):
        _deprecation_warning("CodeAdapter", ".claude/hooks/lib/sot_validator.py")
        self.project_root = project_root or Path(".")

    def adapt(self, files: List[str], plan: AdaptationPlan, **kwargs) -> AdaptResult:
        """适配代码 (stub)"""
        return AdaptResult(
            files=[], success=True, message="Stub - rules inlined to Hook system"
        )


# =============================================================================
# CodeAssembler Stubs
# =============================================================================


@dataclass
class AssembleResult:
    """组装结果 (stub)"""

    output_files: List[str] = field(default_factory=list)
    success: bool = True
    message: str = "Stub implementation"


class CodeAssembler:
    """代码组装器 (stub) - 使用 Claude Code 生成替代"""

    def __init__(self, project_root: Path = None, **kwargs):
        _deprecation_warning("CodeAssembler", "Claude Code generation")
        self.project_root = project_root or Path(".")

    def assemble(self, adapted_files: List[AdaptedFile], **kwargs) -> AssembleResult:
        """组装代码 (stub)"""
        return AssembleResult(
            output_files=[], success=True, message="Stub - use Claude Code generation"
        )


# =============================================================================
# RepoMap Stubs
# =============================================================================


@dataclass
class RepoMap:
    """仓库地图 (stub)"""

    files: List[str] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)


class RepoMapGenerator:
    """仓库地图生成器 (stub) - 使用 Claude Code 文件浏览替代"""

    def __init__(self, project_root: Path = None, **kwargs):
        _deprecation_warning("RepoMapGenerator", "Claude Code file browsing")
        self.project_root = project_root or Path(".")

    def generate(self, **kwargs) -> RepoMap:
        """生成仓库地图 (stub)"""
        return RepoMap()


# =============================================================================
# Prompts Stubs
# =============================================================================


@dataclass
class InjectedContext:
    """注入的上下文 (stub)"""

    content: str = ""
    source: str = "stub"


class PromptInjector:
    """提示词注入器 (stub) - 使用 Claude Code 直接对话替代"""

    def __init__(self, **kwargs):
        _deprecation_warning("PromptInjector", "Claude Code direct conversation")

    def inject(self, **kwargs) -> InjectedContext:
        """注入上下文 (stub)"""
        return InjectedContext()


class PromptLoader:
    """提示词加载器 (stub)"""

    def __init__(self, **kwargs):
        _deprecation_warning("PromptLoader", "Claude Code direct conversation")

    def load(self, name: str, **kwargs) -> str:
        """加载提示词 (stub)"""
        return ""


# =============================================================================
# 便捷导出
# =============================================================================

__all__ = [
    # Searcher
    "CodeSearcher",
    "SearchCandidate",
    "SearchResult",
    # Selector
    "CodeSelector",
    "SelectionResult",
    "AdaptationPlan",
    # Adapter
    "CodeAdapter",
    "AdaptResult",
    "AdaptedFile",
    # Assembler
    "CodeAssembler",
    "AssembleResult",
    # RepoMap
    "RepoMap",
    "RepoMapGenerator",
    # Prompts
    "InjectedContext",
    "PromptInjector",
    "PromptLoader",
]
