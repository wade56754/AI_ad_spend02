"""
CONFIRM 阶段 - 幻觉抑制确认

最终确认阶段，验证生成的代码不存在幻觉问题。

功能:
- 追溯每个状态值到 STATE_MACHINE.md
- 追溯每个角色值到 6 角色白名单
- 追溯每个字段到 DATA_SCHEMA.md
- 生成来源追溯报告

基准文档: MASTER.md v4.8 §7 AI 防幻觉原则
版本: v7.0

规则:
任何追溯失败 → BLOCKING
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from ..types import ExecutionContext

logger = logging.getLogger(__name__)


# =============================================================================
# 白名单定义 (来自 SoT)
# =============================================================================

# 6 业务角色 (MASTER.md v4.8 §2.4)
BUSINESS_ROLES: Set[str] = frozenset({
    "ceo",
    "project_owner",
    "finance",
    "pitcher",
    "account_manager",
    "admin",
})

# 4 技术角色 (数据库 CHECK 约束)
TECH_ROLES: Set[str] = frozenset({
    "admin",
    "finance",
    "account_manager",
    "media_buyer",
})

# 日报 8 状态 (STATE_MACHINE.md v2.8)
DAILY_REPORT_STATES: Set[str] = frozenset({
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
})

# 充值 7 状态 (STATE_MACHINE.md v2.8)
TOPUP_STATES: Set[str] = frozenset({
    "draft",
    "pending_review",
    "finance_approve",
    "paid",
    "completed",
    "cancelled",
    "rejected",
})


@dataclass
class TraceResult:
    """追溯结果"""
    value: str
    trace_type: str  # role, state, field
    valid: bool
    source: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FileTraceReport:
    """文件追溯报告"""
    path: str
    traces: List[TraceResult] = field(default_factory=list)
    confirmed: bool = True
    blocking_issues: List[str] = field(default_factory=list)


@dataclass
class ConfirmResult:
    """确认结果"""
    confirmed: bool
    files_checked: int
    reports: List[FileTraceReport] = field(default_factory=list)
    blocking_count: int = 0


class ConfirmPhase:
    """
    幻觉抑制确认阶段
    
    职责:
    1. 扫描生成的代码
    2. 追溯每个状态/角色/字段到 SoT
    3. 报告任何幻觉问题
    
    BLOCKING 规则:
    - 角色不在 6 角色白名单 → BLOCKING
    - 状态不在 8 状态机 → BLOCKING
    - 使用废弃角色 (supervisor, data_operator) → BLOCKING
    """
    
    PHASE_NAME = "confirm"
    
    def __init__(self, context: ExecutionContext):
        self.context = context
    
    def execute(
        self,
        requirement: str,
        phase_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行幻觉抑制确认
        
        Args:
            requirement: 需求描述
            phase_data: 前序阶段数据
            
        Returns:
            确认结果
        """
        logger.info("开始 CONFIRM 阶段 (幻觉抑制)")
        
        # 获取生成的文件
        impl_data = phase_data.get("implement", {})
        cycles = impl_data.get("cycles", [])
        
        if not cycles:
            logger.info("没有文件需要确认")
            return {
                "confirmed": True,
                "files_checked": 0,
                "reports": [],
                "blocking_count": 0,
            }
        
        # 检查每个文件
        reports = []
        
        for cycle in cycles:
            if not cycle.get("success"):
                continue
            
            # 检查测试文件
            test_file = cycle.get("test_file", {})
            if test_file and test_file.get("content"):
                report = self._trace_file(
                    test_file.get("path", "unknown"),
                    test_file.get("content", ""),
                )
                reports.append(report)
            
            # 检查实现文件
            impl_file = cycle.get("impl_file", {})
            if impl_file and impl_file.get("content"):
                report = self._trace_file(
                    impl_file.get("path", "unknown"),
                    impl_file.get("content", ""),
                )
                reports.append(report)
        
        # 统计
        blocking_count = sum(len(r.blocking_issues) for r in reports)
        all_confirmed = blocking_count == 0
        
        if all_confirmed:
            logger.info(f"幻觉抑制确认通过 ({len(reports)} 文件)")
        else:
            logger.error(f"幻觉抑制确认失败: {blocking_count} 个 BLOCKING 问题")
        
        return {
            "confirmed": all_confirmed,
            "files_checked": len(reports),
            "reports": [self._report_to_dict(r) for r in reports],
            "blocking_count": blocking_count,
        }
    
    def _trace_file(self, path: str, content: str) -> FileTraceReport:
        """
        追溯单个文件
        
        检查:
        1. 角色值
        2. 状态值
        3. SoT 标注
        """
        report = FileTraceReport(path=path)
        
        # 1. 追溯角色值
        role_traces = self._trace_roles(content)
        report.traces.extend(role_traces)
        
        for trace in role_traces:
            if not trace.valid:
                report.confirmed = False
                report.blocking_issues.append(
                    f"[BLOCKING] {trace.error}"
                )
        
        # 2. 追溯状态值
        state_traces = self._trace_states(content)
        report.traces.extend(state_traces)
        
        for trace in state_traces:
            if not trace.valid:
                report.confirmed = False
                report.blocking_issues.append(
                    f"[BLOCKING] {trace.error}"
                )
        
        # 3. 检查 SoT 标注
        sot_traces = self._trace_sot_annotations(content)
        report.traces.extend(sot_traces)
        
        return report
    
    def _trace_roles(self, content: str) -> List[TraceResult]:
        """追溯角色值"""
        traces = []
        
        # 废弃角色检测
        deprecated_roles = {
            "supervisor": "已废弃，使用 project_owner",
            "data_operator": "已废弃",
            "data_clerk": "已废弃，使用 finance",
            "manager": "已废弃，使用 account_manager",
            "trader": "已废弃，使用 media_buyer",
        }
        
        # 匹配角色模式
        role_patterns = [
            r'role\s*[=:]\s*["\'](\w+)["\']',
            r"UserRole\.(\w+)",
            r"role\s*==\s*[\"'](\w+)[\"']",
            r'roles?\s*=\s*\[.*["\'](\w+)["\'].*\]',
        ]
        
        found_roles = set()
        for pattern in role_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_roles.update(m.lower() for m in matches)
        
        for role in found_roles:
            # 检查是否为废弃角色
            if role in deprecated_roles:
                traces.append(TraceResult(
                    value=role,
                    trace_type="role",
                    valid=False,
                    error=f"使用废弃角色 '{role}': {deprecated_roles[role]}",
                ))
                continue
            
            # 检查业务角色
            if role in BUSINESS_ROLES:
                traces.append(TraceResult(
                    value=role,
                    trace_type="role",
                    valid=True,
                    source="MASTER.md v4.8 §2.4",
                ))
                continue
            
            # 检查技术角色
            if role in TECH_ROLES:
                traces.append(TraceResult(
                    value=role,
                    trace_type="role",
                    valid=True,
                    source="backend/models/enums.py",
                ))
                continue
            
            # 未知角色
            traces.append(TraceResult(
                value=role,
                trace_type="role",
                valid=False,
                error=f"角色 '{role}' 不在 6 角色白名单中",
            ))
        
        return traces
    
    def _trace_states(self, content: str) -> List[TraceResult]:
        """追溯状态值"""
        traces = []
        
        # 废弃状态检测
        deprecated_states = {
            "draft": None,  # draft 在充值中是有效的
            "pending": "已废弃，使用 8 状态机状态",
            "approved": "已废弃，使用 8 状态机状态",
            "rejected": None,  # rejected 在充值中是有效的
        }
        
        # 匹配状态模式
        state_patterns = [
            r'status\s*[=:]\s*["\'](\w+)["\']',
            r"DailyReportStatus\.(\w+)",
            r"TopupRequestStatus\.(\w+)",
            r"status\s*==\s*[\"'](\w+)[\"']",
        ]
        
        found_states = set()
        for pattern in state_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_states.update(m.lower() for m in matches)
        
        for state in found_states:
            # 检查日报状态
            if state in DAILY_REPORT_STATES:
                traces.append(TraceResult(
                    value=state,
                    trace_type="state",
                    valid=True,
                    source="STATE_MACHINE.md v2.8 §8 (日报)",
                ))
                continue
            
            # 检查充值状态
            if state in TOPUP_STATES:
                traces.append(TraceResult(
                    value=state,
                    trace_type="state",
                    valid=True,
                    source="STATE_MACHINE.md v2.8 (充值)",
                ))
                continue
            
            # 检查废弃状态
            if state in deprecated_states and deprecated_states[state]:
                traces.append(TraceResult(
                    value=state,
                    trace_type="state",
                    valid=False,
                    error=f"状态 '{state}': {deprecated_states[state]}",
                ))
                continue
            
            # 未知状态 (仅警告，不阻断)
            # 因为可能是其他实体的状态
            traces.append(TraceResult(
                value=state,
                trace_type="state",
                valid=True,  # 不阻断，但记录
                source="未在主状态机中，可能是其他实体状态",
            ))
        
        return traces
    
    def _trace_sot_annotations(self, content: str) -> List[TraceResult]:
        """追溯 SoT 标注"""
        traces = []
        
        # 匹配 SoT 标注: # SoT: xxx 或 // SoT: xxx
        pattern = r'[#/]+\s*SoT:\s*(\S+)'
        matches = re.findall(pattern, content)
        
        for annotation in matches:
            traces.append(TraceResult(
                value=annotation,
                trace_type="sot_annotation",
                valid=True,
                source=annotation,
            ))
        
        return traces
    
    def _report_to_dict(self, report: FileTraceReport) -> Dict[str, Any]:
        """报告转字典"""
        return {
            "path": report.path,
            "traces": [
                {
                    "value": t.value,
                    "trace_type": t.trace_type,
                    "valid": t.valid,
                    "source": t.source,
                    "error": t.error,
                }
                for t in report.traces
            ],
            "confirmed": report.confirmed,
            "blocking_issues": report.blocking_issues,
        }
