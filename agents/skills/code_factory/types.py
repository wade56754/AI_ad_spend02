"""
AI 代码工厂 - 核心数据类型

版本: v7.0
基准文档: MASTER.md v4.8

本文件定义代码工厂使用的核心数据类型，
替代原有的 stubs.py 占位实现。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum


# =============================================================================
# 阶段枚举
# =============================================================================

class PhaseType(str, Enum):
    """工厂阶段类型"""
    CLARIFY = "clarify"      # 需求澄清
    PLAN = "plan"            # 计划生成
    IMPLEMENT = "implement"  # TDD 实现
    REVIEW = "review"        # 两阶段审查
    CONFIRM = "confirm"      # 幻觉抑制确认


class ReviewStage(str, Enum):
    """审查阶段"""
    SPEC = "spec"        # 规格合规审查
    QUALITY = "quality"  # 代码质量审查


# =============================================================================
# 文件相关数据类型
# =============================================================================

@dataclass
class FileContent:
    """文件内容"""
    path: str
    content: str
    language: str = ""
    
    def __post_init__(self):
        """自动推断语言"""
        if not self.language:
            ext = Path(self.path).suffix.lower()
            lang_map = {
                ".py": "python",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".js": "javascript",
                ".jsx": "javascript",
                ".md": "markdown",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".json": "json",
            }
            self.language = lang_map.get(ext, "text")


@dataclass
class AdaptedFile:
    """适配后的文件
    
    用于验证器和流水线间传递文件内容
    """
    file_path: str
    content: str
    adaptations: List[Dict[str, Any]] = field(default_factory=list)
    source_attribution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "content": self.content,
            "adaptations": self.adaptations,
            "source_attribution": self.source_attribution,
        }


@dataclass
class GeneratedFile:
    """生成的文件"""
    path: str
    content: str
    action: str = "create"  # create, modify, delete
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "content": self.content,
            "action": self.action,
        }


# =============================================================================
# 任务相关数据类型
# =============================================================================

@dataclass
class TaskSpec:
    """任务规格"""
    id: str
    description: str
    category: str = "general"
    priority: int = 1
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "acceptance_criteria": self.acceptance_criteria,
        }


@dataclass
class ImplementationPlan:
    """实现计划"""
    tasks: List[TaskSpec] = field(default_factory=list)
    estimated_time: str = ""
    approach: str = ""
    risks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "estimated_time": self.estimated_time,
            "approach": self.approach,
            "risks": self.risks,
        }


# =============================================================================
# 审查相关数据类型
# =============================================================================

@dataclass
class ReviewIssue:
    """审查问题"""
    code: str
    line: int
    message: str
    severity: str  # error, warning, info
    category: str = ""  # spec_violation, quality_issue, etc.
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "suggestion": self.suggestion,
        }


@dataclass
class ReviewResult:
    """审查结果"""
    passed: bool
    stage: ReviewStage
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "stage": self.stage.value,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
        }


# =============================================================================
# 阶段结果数据类型
# =============================================================================

@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: PhaseType
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class PipelineResult:
    """流水线执行结果"""
    success: bool
    phases: List[PhaseResult] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "phases": [p.to_dict() for p in self.phases],
            "output_files": self.output_files,
            "error": self.error,
        }


# =============================================================================
# 上下文数据类型
# =============================================================================

@dataclass
class ExecutionContext:
    """执行上下文"""
    project_root: Path
    requirement: str
    workflow_type: str = "full_stack_development"
    sot_dir: Optional[Path] = None
    superpowers_dir: Optional[Path] = None
    
    def __post_init__(self):
        """初始化默认路径"""
        if self.sot_dir is None:
            self.sot_dir = self.project_root / "docs" / "sot"
        if self.superpowers_dir is None:
            self.superpowers_dir = self.project_root / ".superpowers" / "skills"


# =============================================================================
# 兼容层 - 原 stubs.py 的类型 (v7.0 迁移)
# =============================================================================

@dataclass
class RepoMap:
    """仓库地图 (stub)"""
    root: Path
    files: List[str] = field(default_factory=list)
    summary: str = ""


class RepoMapGenerator:
    """仓库地图生成器 (stub)"""
    
    def __init__(self, root: Optional[Path] = None):
        self.root = root or Path.cwd()
    
    def generate(self) -> RepoMap:
        """生成仓库地图"""
        return RepoMap(root=self.root)


@dataclass
class InjectedContext:
    """注入上下文 (stub)"""
    sot_content: str = ""
    skill_content: str = ""
    repo_map: Optional[RepoMap] = None


class PromptLoader:
    """提示词加载器 (stub)"""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir
    
    def load(self, name: str) -> str:
        """加载提示词"""
        return ""


class PromptInjector:
    """提示词注入器 (stub)"""
    
    def __init__(self, context: Optional[InjectedContext] = None):
        self.context = context
    
    def inject(self, prompt: str) -> str:
        """注入上下文到提示词"""
        return prompt


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    # 枚举
    "PhaseType",
    "ReviewStage",
    # 文件类型
    "FileContent",
    "AdaptedFile",
    "GeneratedFile",
    # 任务类型
    "TaskSpec",
    "ImplementationPlan",
    # 审查类型
    "ReviewIssue",
    "ReviewResult",
    # 结果类型
    "PhaseResult",
    "PipelineResult",
    # 上下文
    "ExecutionContext",
    # 兼容层 (原 stubs.py)
    "RepoMap",
    "RepoMapGenerator",
    "InjectedContext",
    "PromptLoader",
    "PromptInjector",
]
