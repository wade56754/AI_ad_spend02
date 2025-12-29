"""
来源追溯器

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 追溯代码中的状态值、角色值、字段到 SoT 文档
- 计算追溯率
- 生成追溯报告
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional
from enum import Enum
import re


class TraceCategory(Enum):
    """追溯类别"""
    ROLE = "role"
    STATE = "state"
    ERROR_CODE = "error_code"
    FIELD = "field"
    API = "api"


class TraceStatus(Enum):
    """追溯状态"""
    FOUND = "found"         # 在 SoT 中找到
    NOT_FOUND = "not_found" # 在 SoT 中未找到
    DEPRECATED = "deprecated"  # 已废弃


@dataclass
class TraceItem:
    """追溯项"""

    value: str
    category: TraceCategory
    status: TraceStatus
    source: Optional[str] = None  # SoT 来源 (如 "MASTER.md#roles")
    line: Optional[int] = None
    file: Optional[str] = None
    suggestion: Optional[str] = None  # 如果未找到，建议的值

    def is_valid(self) -> bool:
        return self.status == TraceStatus.FOUND

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "category": self.category.value,
            "status": self.status.value,
            "source": self.source,
            "line": self.line,
            "file": self.file,
            "suggestion": self.suggestion,
        }


@dataclass
class TraceResult:
    """追溯结果"""

    items: List[TraceItem] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def found(self) -> int:
        return len([i for i in self.items if i.status == TraceStatus.FOUND])

    @property
    def not_found(self) -> int:
        return len([i for i in self.items if i.status == TraceStatus.NOT_FOUND])

    @property
    def deprecated(self) -> int:
        return len([i for i in self.items if i.status == TraceStatus.DEPRECATED])

    @property
    def trace_rate(self) -> float:
        """追溯率"""
        if self.total == 0:
            return 1.0
        return self.found / self.total

    @property
    def is_complete(self) -> bool:
        """是否完全追溯"""
        return self.trace_rate == 1.0

    def get_by_category(self, category: TraceCategory) -> List[TraceItem]:
        """按类别获取"""
        return [i for i in self.items if i.category == category]

    def get_failures(self) -> List[TraceItem]:
        """获取失败项"""
        return [i for i in self.items if i.status != TraceStatus.FOUND]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "found": self.found,
            "not_found": self.not_found,
            "deprecated": self.deprecated,
            "trace_rate": f"{self.trace_rate:.0%}",
            "items": [i.to_dict() for i in self.items],
        }

    def to_report(self) -> str:
        """生成追溯报告"""
        lines = [
            "=" * 40,
            "来源追溯报告",
            "=" * 40,
            f"总计: {self.total}",
            f"已追溯: {self.found}",
            f"未找到: {self.not_found}",
            f"已废弃: {self.deprecated}",
            f"追溯率: {self.trace_rate:.0%}",
            "",
        ]

        # 按类别统计
        for cat in TraceCategory:
            items = self.get_by_category(cat)
            if items:
                lines.append(f"[{cat.value}]")
                for item in items:
                    status_icon = "✅" if item.is_valid() else "❌"
                    lines.append(f"  {status_icon} {item.value}")
                    if item.source:
                        lines.append(f"     来源: {item.source}")
                    if item.suggestion:
                        lines.append(f"     建议: {item.suggestion}")

        # 失败项汇总
        failures = self.get_failures()
        if failures:
            lines.extend(["", "需要修复:"])
            for item in failures:
                lines.append(f"  - {item.value} ({item.category.value})")

        return "\n".join(lines)


class SourceTracer:
    """来源追溯器"""

    def __init__(self, sot_data):
        """初始化

        Args:
            sot_data: LoadedSotData 实例
        """
        self.sot_data = sot_data

    def trace_code(self, code: str, file_path: Optional[str] = None) -> TraceResult:
        """追溯代码中的值

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            TraceResult
        """
        result = TraceResult()

        # 1. 追溯角色
        result.items.extend(self._trace_roles(code, file_path))

        # 2. 追溯状态
        result.items.extend(self._trace_states(code, file_path))

        # 3. 追溯错误码
        result.items.extend(self._trace_error_codes(code, file_path))

        return result

    def _trace_roles(self, code: str, file_path: Optional[str]) -> List[TraceItem]:
        """追溯角色"""
        items = []

        # 匹配角色引用: role="admin", role='pitcher', UserRole.ADMIN
        patterns = [
            r'role\s*[=:]\s*["\'](\w+)["\']',
            r'UserRole\.(\w+)',
            r'user\.role\s*==\s*["\'](\w+)["\']',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                role = match.group(1).lower()
                item = self._check_role(role, file_path)
                items.append(item)

        return items

    def _check_role(self, role: str, file_path: Optional[str]) -> TraceItem:
        """检查角色"""
        # 检查是否在角色白名单中
        if role in self.sot_data.roles:
            return TraceItem(
                value=role,
                category=TraceCategory.ROLE,
                status=TraceStatus.FOUND,
                source="MASTER.md#roles",
                file=file_path,
            )

        # 检查是否是废弃角色
        if role in self.sot_data.legacy_mapping:
            new_role = self.sot_data.legacy_mapping[role]
            return TraceItem(
                value=role,
                category=TraceCategory.ROLE,
                status=TraceStatus.DEPRECATED,
                suggestion=f"使用 '{new_role}' 替代",
                file=file_path,
            )

        # 未找到
        return TraceItem(
            value=role,
            category=TraceCategory.ROLE,
            status=TraceStatus.NOT_FOUND,
            file=file_path,
        )

    def _trace_states(self, code: str, file_path: Optional[str]) -> List[TraceItem]:
        """追溯状态"""
        items = []

        # 匹配状态引用
        patterns = [
            r'status\s*[=:]\s*["\'](\w+)["\']',
            r'DailyReportStatus\.(\w+)',
            r'TopupRequestStatus\.(\w+)',
            r'state\s*==\s*["\'](\w+)["\']',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                state = match.group(1).lower()
                item = self._check_state(state, file_path)
                items.append(item)

        return items

    def _check_state(self, state: str, file_path: Optional[str]) -> TraceItem:
        """检查状态"""
        # 检查所有状态集合
        for table, states in self.sot_data.states.items():
            if state in states:
                return TraceItem(
                    value=state,
                    category=TraceCategory.STATE,
                    status=TraceStatus.FOUND,
                    source=f"STATE_MACHINE.md#{table}",
                    file=file_path,
                )

        return TraceItem(
            value=state,
            category=TraceCategory.STATE,
            status=TraceStatus.NOT_FOUND,
            file=file_path,
        )

    def _trace_error_codes(self, code: str, file_path: Optional[str]) -> List[TraceItem]:
        """追溯错误码"""
        items = []

        # 匹配错误码: "VAL-001", "AUTH-002"
        pattern = r'["\']([A-Z]+)-(\d{3})["\']'

        for match in re.finditer(pattern, code):
            prefix = match.group(1)
            full_code = f"{prefix}-{match.group(2)}"

            if prefix in self.sot_data.error_codes:
                items.append(TraceItem(
                    value=full_code,
                    category=TraceCategory.ERROR_CODE,
                    status=TraceStatus.FOUND,
                    source="ERROR_CODES_SOT.md",
                    file=file_path,
                ))
            else:
                items.append(TraceItem(
                    value=full_code,
                    category=TraceCategory.ERROR_CODE,
                    status=TraceStatus.NOT_FOUND,
                    file=file_path,
                ))

        return items

    def verify_trace_rate(self, code: str, threshold: float = 1.0) -> bool:
        """验证追溯率

        Args:
            code: 代码内容
            threshold: 阈值 (0.0-1.0)

        Returns:
            是否达到阈值
        """
        result = self.trace_code(code)
        return result.trace_rate >= threshold
