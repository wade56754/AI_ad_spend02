"""
流水线上下文

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 在各阶段之间传递数据
- 存储中间结果
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import PhaseResult


@dataclass
class SearchCandidate:
    """搜索候选"""
    id: str
    source: str
    path: str
    relevance_score: float
    snippet: str
    match_reason: str


@dataclass
class PipelineContext:
    """流水线上下文 - 各阶段共享"""

    # === 输入 ===
    requirement: str
    module_id: Optional[str] = None
    project_dir: Optional[Path] = None

    # === SoT 数据 ===
    sot_data: Any = None
    sot_versions: Dict[str, str] = field(default_factory=dict)

    # === 风险评估 ===
    risk_level: str = "low"
    risk_assessment: Any = None

    # === 代码地图 ===
    repo_map: Any = None

    # === 搜索结果 ===
    search_results: List[SearchCandidate] = field(default_factory=list)
    search_stats: Dict[str, int] = field(default_factory=dict)

    # === 选型结果 ===
    selected_candidates: List[SearchCandidate] = field(default_factory=list)
    selection_scores: Dict[str, float] = field(default_factory=dict)

    # === 适配结果 ===
    adapted_code: str = ""
    adapted_files: Dict[str, str] = field(default_factory=dict)
    adaptation_summary: str = ""

    # === 组装结果 ===
    assembled_code: str = ""
    assembled_files: Dict[str, str] = field(default_factory=dict)

    # === 验证结果 ===
    verification_passed: bool = False
    verification_errors: List[str] = field(default_factory=list)

    # === 追溯结果 ===
    trace_report: Any = None
    trace_rate: float = 0.0

    # === 输出 ===
    output_files: List[str] = field(default_factory=list)
    generated_code: Dict[str, str] = field(default_factory=dict)

    # === 阶段结果 ===
    phase_results: List[PhaseResult] = field(default_factory=list)

    # === 元数据 ===
    session_id: str = ""
    started_at: str = ""
    finished_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def add_phase_result(self, result: PhaseResult):
        """添加阶段结果"""
        self.phase_results.append(result)

    def get_phase_result(self, phase_id: int) -> Optional[PhaseResult]:
        """获取指定阶段的结果"""
        for result in self.phase_results:
            if result.phase_id == phase_id:
                return result
        return None

    def is_phase_success(self, phase_id: int) -> bool:
        """检查阶段是否成功"""
        result = self.get_phase_result(phase_id)
        return result is not None and result.success

    def get_total_duration_ms(self) -> int:
        """获取总耗时"""
        return sum(r.duration_ms for r in self.phase_results)

    def get_errors(self) -> List[str]:
        """获取所有错误"""
        errors = []
        for result in self.phase_results:
            errors.extend(result.errors)
        return errors

    def get_warnings(self) -> List[str]:
        """获取所有警告"""
        warnings = []
        for result in self.phase_results:
            warnings.extend(result.warnings)
        return warnings

    def to_summary(self) -> Dict[str, Any]:
        """生成摘要"""
        return {
            "requirement": self.requirement,
            "module_id": self.module_id,
            "session_id": self.session_id,
            "risk_level": self.risk_level,
            "trace_rate": f"{self.trace_rate:.0%}",
            "phases_completed": len(self.phase_results),
            "phases_success": len([r for r in self.phase_results if r.success]),
            "total_duration_ms": self.get_total_duration_ms(),
            "output_files": self.output_files,
            "errors": self.get_errors(),
            "warnings": self.get_warnings(),
        }

    def finish(self):
        """标记完成"""
        self.finished_at = datetime.now().isoformat()
