"""
Guardrails 统计追踪器

版本: v4.2

功能:
- 追踪编辑成功/失败/恢复统计
- 计算成功率和恢复率
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class EditAttempt:
    """单次编辑尝试记录"""
    file_path: str
    success: bool
    attempts: int
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GuardrailsStats:
    """Guardrails 统计"""

    total: int = 0          # 总编辑次数
    first_success: int = 0  # 首次成功次数
    recovered: int = 0      # 恢复成功次数
    failed: int = 0         # 失败次数

    # 详细记录
    attempts: List[EditAttempt] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率 (首次成功 + 恢复成功)"""
        if self.total == 0:
            return 0.0
        return (self.first_success + self.recovered) / self.total * 100

    @property
    def recovery_rate(self) -> float:
        """恢复率 (恢复成功 / 首次失败)"""
        failed_first = self.total - self.first_success
        if failed_first == 0:
            return 0.0
        return self.recovered / failed_first * 100

    @property
    def failure_rate(self) -> float:
        """失败率"""
        if self.total == 0:
            return 0.0
        return self.failed / self.total * 100

    def record_success(self, file_path: str, first_try: bool = True):
        """记录成功"""
        self.total += 1
        if first_try:
            self.first_success += 1
        else:
            self.recovered += 1

        self.attempts.append(EditAttempt(
            file_path=file_path,
            success=True,
            attempts=1 if first_try else 2,
        ))

    def record_failure(self, file_path: str, attempts: int, errors: List[str]):
        """记录失败"""
        self.total += 1
        self.failed += 1

        self.attempts.append(EditAttempt(
            file_path=file_path,
            success=False,
            attempts=attempts,
            errors=errors,
        ))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total": self.total,
            "first_success": self.first_success,
            "recovered": self.recovered,
            "failed": self.failed,
            "success_rate": f"{self.success_rate:.1f}%",
            "recovery_rate": f"{self.recovery_rate:.1f}%",
            "failure_rate": f"{self.failure_rate:.1f}%",
        }

    def to_report(self) -> str:
        """生成报告"""
        lines = [
            "=" * 40,
            "Guardrails 统计报告",
            "=" * 40,
            f"总编辑次数: {self.total}",
            f"首次成功: {self.first_success}",
            f"恢复成功: {self.recovered}",
            f"失败: {self.failed}",
            "",
            f"成功率: {self.success_rate:.1f}%",
            f"恢复率: {self.recovery_rate:.1f}%",
            f"失败率: {self.failure_rate:.1f}%",
        ]

        if self.failed > 0:
            lines.extend([
                "",
                "失败详情:",
            ])
            for attempt in self.attempts:
                if not attempt.success:
                    lines.append(f"  - {attempt.file_path}: {attempt.errors[:2]}")

        return "\n".join(lines)

    def reset(self):
        """重置统计"""
        self.total = 0
        self.first_success = 0
        self.recovered = 0
        self.failed = 0
        self.attempts = []
