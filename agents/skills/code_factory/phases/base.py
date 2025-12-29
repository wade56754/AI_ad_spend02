"""
阶段基类

基准文档: MASTER.md v4.6
版本: v4.2
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import time


@dataclass
class PhaseResult:
    """阶段执行结果"""

    phase_id: int
    phase_name: str
    success: bool
    duration_ms: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class PhaseBase(ABC):
    """阶段基类"""

    def __init__(self, phase_id: int, phase_name: str):
        """初始化

        Args:
            phase_id: 阶段 ID (0-9)
            phase_name: 阶段名称
        """
        self.phase_id = phase_id
        self.phase_name = phase_name

    @abstractmethod
    def execute(self, context: "PipelineContext") -> PhaseResult:
        """执行阶段逻辑

        Args:
            context: 流水线上下文

        Returns:
            PhaseResult
        """
        pass

    def run(self, context: "PipelineContext") -> PhaseResult:
        """运行阶段 (带计时)

        Args:
            context: 流水线上下文

        Returns:
            PhaseResult
        """
        start = time.time()

        try:
            result = self.execute(context)
            result.duration_ms = int((time.time() - start) * 1000)
            return result
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return self._failure([str(e)], duration_ms=duration_ms)

    def _success(self, duration_ms: int = 0, **data) -> PhaseResult:
        """创建成功结果"""
        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.phase_name,
            success=True,
            duration_ms=duration_ms,
            data=data,
        )

    def _failure(self, errors: List[str], duration_ms: int = 0, **data) -> PhaseResult:
        """创建失败结果"""
        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.phase_name,
            success=False,
            duration_ms=duration_ms,
            errors=errors,
            data=data,
        )

    def _warning(self, warnings: List[str], duration_ms: int = 0, **data) -> PhaseResult:
        """创建带警告的成功结果"""
        return PhaseResult(
            phase_id=self.phase_id,
            phase_name=self.phase_name,
            success=True,
            duration_ms=duration_ms,
            warnings=warnings,
            data=data,
        )
