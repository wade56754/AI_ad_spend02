"""
Anti-Hallucination Checker - AI 防幻觉检查器

基准文档: MASTER.md v4.4 §7 防止 AI 幻觉规则
版本: v1.0
创建日期: 2025-12-22

实现规则:
- AH-01: 禁止假设数据一致
- AH-02: 禁止自动做管理裁决（Phase 1）
- AH-03: 禁止引入 SoT 未定义的概念
- AH-04: 必须遵循 Phase 1 软性原则
- AH-05: 遇到歧义必须停止并询问
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

# 导入依赖
try:
    from agents.skills.code_factory.phase_config import PhaseConfig
    from agents.skills.code_factory.sot_loader import SotLoader
except ImportError:
    # 允许独立测试
    PhaseConfig = None  # type: ignore
    SotLoader = None  # type: ignore


@dataclass
class AHIssue:
    """AH 检查问题数据类"""
    rule_id: str  # AH-01, AH-02, etc.
    severity: str  # ERROR, WARNING, INFO
    message: str  # 问题描述
    line: int  # 问题所在行号
    suggestion: Optional[str] = None  # 修复建议


class AntiHallucinationChecker:
    """Anti-Hallucination 检查器

    实现 MASTER.md v4.4 §7 的 AH-01~AH-05 检查

    用法:
        >>> checker = AntiHallucinationChecker()
        >>> code = "user.balance -= 100"
        >>> issues = checker.check_ah01_no_assumption(code)
        >>> len(issues) > 0
        True
    """

    def __init__(
        self,
        phase_config: Optional["PhaseConfig"] = None,
        sot_loader: Optional["SotLoader"] = None
    ):
        """初始化检查器

        Args:
            phase_config: Phase 配置实例（可选）
            sot_loader: SoT 加载器实例（可选）
        """
        self.phase_config = phase_config
        self.sot_loader = sot_loader

    # ========== AH-01: 禁止假设数据一致 ==========

    def check_ah01_no_assumption(self, code: str) -> List[AHIssue]:
        """AH-01: 禁止假设数据一致

        检查项:
        1. 禁止假设 balance 一定存在 → 应通过 ledger_entries 记录
        2. 禁止假设 unit_price 一定有值 → 应检查 None
        3. 禁止假设外键关系一定存在 → 应 LEFT JOIN
        4. 禁止假设枚举值一定合法 → 应先验证

        Args:
            code: 待检查的代码字符串

        Returns:
            List[AHIssue]: 发现的问题列表
        """
        issues = []

        # 检查 1: 直接修改 balance
        if re.search(r'\.balance\s*[-+*/]=', code):
            issues.append(AHIssue(
                rule_id="AH-01-BALANCE",
                severity="ERROR",
                message="禁止直接修改 balance 字段",
                line=self._find_line(code, r'\.balance\s*[-+*/]='),
                suggestion=(
                    "应通过 ledger_entries 表记录流水，由触发器/视图自动计算 balance。"
                    "参考 DATA_SCHEMA.md v5.11 §3.4.4"
                )
            ))

        # 检查 2: 使用 unit_price 但未检查 None
        if re.search(r'\bunit_price\s*[*/]', code) and 'if unit_price' not in code and 'unit_price or' not in code:
            issues.append(AHIssue(
                rule_id="AH-01-NULLABLE",
                severity="WARNING",
                message="使用 unit_price 计算前应检查是否为 None",
                line=self._find_line(code, r'\bunit_price\s*[*/]'),
                suggestion="添加: if unit_price is not None: ..."
            ))

        # 检查 3: 使用 INNER JOIN 但可能存在空值
        if re.search(r'INNER\s+JOIN', code, re.IGNORECASE):
            # 检查是否有注释说明为何使用 INNER JOIN
            if '# INNER JOIN 原因:' not in code and '-- INNER JOIN 原因:' not in code:
                issues.append(AHIssue(
                    rule_id="AH-01-JOIN",
                    severity="WARNING",
                    message="使用 INNER JOIN 可能导致数据丢失",
                    line=self._find_line(code, r'INNER\s+JOIN', re.IGNORECASE),
                    suggestion=(
                        "考虑使用 LEFT JOIN 并处理 None 值。"
                        "如必须用 INNER JOIN，请添加注释说明原因。"
                    )
                ))

        # 检查 4: 枚举值未验证
        if re.search(r'\.status\s*=\s*["\'](\w+)["\']', code):
            match = re.search(r'\.status\s*=\s*["\'](\w+)["\']', code)
            if match and 'if' not in code[:match.start()]:
                status_value = match.group(1)
                issues.append(AHIssue(
                    rule_id="AH-01-ENUM",
                    severity="WARNING",
                    message=f"设置状态 '{status_value}' 前应验证其合法性",
                    line=self._find_line(code, r'\.status\s*='),
                    suggestion="从 STATE_MACHINE.md 确认状态值是否合法"
                ))

        return issues

    # ========== AH-02: 禁止自动做管理裁决 ==========

    def check_ah02_no_auto_decision(self, code: str) -> List[AHIssue]:
        """AH-02: 禁止自动做管理裁决（Phase 1 禁止）

        检查项:
        1. 禁止自动拒绝请求 (status = 'rejected')
        2. 禁止自动暂停账户 (status = 'suspended')
        3. 禁止自动扣款/罚款
        4. 禁止自动调整投手权限

        Args:
            code: 待检查的代码字符串

        Returns:
            List[AHIssue]: 发现的问题列表（仅 Phase 1）
        """
        if self.phase_config and self.phase_config.is_phase2_enabled():
            return []  # Phase 2 允许自动裁决

        issues = []

        # 检查 1: 自动拒绝
        if re.search(r'\.status\s*=\s*["\']rejected["\']', code):
            issues.append(AHIssue(
                rule_id="AH-02-REJECT",
                severity="ERROR",
                message="Phase 1 禁止自动拒绝请求",
                line=self._find_line(code, r'\.status\s*=\s*["\']rejected["\']'),
                suggestion=(
                    "应高亮显示异常并通知管理员人工处理。"
                    "如需自动拒绝，请在 Phase 2 启用后实现。"
                )
            ))

        # 检查 2: 自动暂停
        if re.search(r'\.status\s*=\s*["\']suspended["\']', code):
            issues.append(AHIssue(
                rule_id="AH-02-SUSPEND",
                severity="ERROR",
                message="Phase 1 禁止自动暂停账户",
                line=self._find_line(code, r'\.status\s*=\s*["\']suspended["\']'),
                suggestion="应发送通知，由管理员决定是否暂停"
            ))

        # 检查 3: 自动扣款/罚款
        if re.search(r'penalty|fine|deduct', code, re.IGNORECASE):
            if 'ledger' in code.lower():
                issues.append(AHIssue(
                    rule_id="AH-02-PENALTY",
                    severity="WARNING",
                    message="Phase 1 应避免自动罚款/扣款逻辑",
                    line=self._find_line(code, r'penalty|fine|deduct', re.IGNORECASE),
                    suggestion="记录违规但不自动处罚，由财务人工审核"
                ))

        return issues

    # ========== AH-03: 禁止引入 SoT 未定义的概念 ==========

    def check_ah03_no_undefined_concepts(self, code: str) -> List[AHIssue]:
        """AH-03: 禁止引入 SoT 未定义的概念

        检查项:
        1. 状态值必须在 STATE_MACHINE.md 中定义
        2. 角色必须在规定的 5 个技术角色中
        3. 错误码前缀必须在 ERROR_CODES_SOT.md 中定义
        4. 表名、字段名必须在 DATA_SCHEMA.md 中定义

        Args:
            code: 待检查的代码字符串

        Returns:
            List[AHIssue]: 发现的问题列表
        """
        issues = []

        if not self.sot_loader:
            return issues  # 无法检查

        # 检查 1: 状态值
        status_pattern = r'["\'](\w+)["\']'
        for match in re.finditer(status_pattern, code):
            status = match.group(1)
            # 跳过明显不是状态的值
            if len(status) < 3 or status.isupper():
                continue

            if not self.sot_loader.is_valid_status(status):
                issues.append(AHIssue(
                    rule_id="AH-03-STATUS",
                    severity="ERROR",
                    message=f"状态 '{status}' 未在 STATE_MACHINE.md 中定义",
                    line=self._find_line_number(code, match.start()),
                    suggestion=f"有效状态: {', '.join(sorted(self.sot_loader.get_all_daily_report_states()))}"
                ))

        # 检查 2: 角色
        role_pattern = r'role\s*=\s*["\'](\w+)["\']'
        for match in re.finditer(role_pattern, code, re.IGNORECASE):
            role = match.group(1)
            if not self.sot_loader.is_valid_role(role):
                issues.append(AHIssue(
                    rule_id="AH-03-ROLE",
                    severity="ERROR",
                    message=f"角色 '{role}' 不在 5 个技术角色中",
                    line=self._find_line_number(code, match.start()),
                    suggestion=f"有效角色: {', '.join(sorted(self.sot_loader.get_all_roles()))}"
                ))

        # 检查 3: 错误码前缀
        error_code_pattern = r'([A-Z]{2,5})-\d{3}'
        for match in re.finditer(error_code_pattern, code):
            prefix = match.group(1)
            if not self.sot_loader.is_valid_error_code_prefix(prefix):
                issues.append(AHIssue(
                    rule_id="AH-03-ERROR",
                    severity="ERROR",
                    message=f"错误码前缀 '{prefix}' 未在 ERROR_CODES_SOT.md 中定义",
                    line=self._find_line_number(code, match.start()),
                    suggestion=f"有效前缀: {', '.join(sorted(self.sot_loader.get_all_error_code_prefixes()))}"
                ))

        return issues

    # ========== AH-04: 必须遵循 Phase 1 软性原则 ==========

    def check_ah04_phase1_soft_constraints(self, code: str) -> List[AHIssue]:
        """AH-04: 必须遵循 Phase 1 软性原则

        检查项:
        1. 避免使用 raise 抛出业务异常（除非标注 Phase 2）
        2. 避免强制阻断流程
        3. 使用提示/高亮而非错误

        Args:
            code: 待检查的代码字符串

        Returns:
            List[AHIssue]: 发现的问题列表（仅 Phase 1）
        """
        if self.phase_config and self.phase_config.is_phase2_enabled():
            return []  # Phase 2 允许强制约束

        issues = []

        # 检查 1: 使用 raise 但未标注 Phase 2
        if 'raise' in code and 'BusinessError' in code:
            if 'Phase 2' not in code and '# Phase 2 only' not in code:
                issues.append(AHIssue(
                    rule_id="AH-04-RAISE",
                    severity="WARNING",
                    message="Phase 1 应避免抛出业务异常阻断流程",
                    line=self._find_line(code, r'raise.*BusinessError'),
                    suggestion=(
                        "考虑:\n"
                        "1. 记录警告日志并继续处理\n"
                        "2. 返回 warning 字段提示用户\n"
                        "3. 如确需阻断，添加注释: # Phase 2 only"
                    )
                ))

        # 检查 2: 使用 return error 而非 warning
        if re.search(r'return\s+.*error', code, re.IGNORECASE):
            if 'warning' not in code.lower():
                issues.append(AHIssue(
                    rule_id="AH-04-ERROR",
                    severity="INFO",
                    message="Phase 1 建议使用 warning 而非 error",
                    line=self._find_line(code, r'return\s+.*error', re.IGNORECASE),
                    suggestion="考虑返回 {\"warnings\": [...], \"data\": ...} 格式"
                ))

        return issues

    # ========== AH-05: 遇到歧义必须停止并询问 ==========

    def check_ah05_ambiguity_handling(self, code: str) -> List[AHIssue]:
        """AH-05: 遇到歧义必须停止并询问

        检查项:
        1. 检测代码注释中的"假设"、"推测"、"可能"等词
        2. 检测 TODO、FIXME 注释
        3. 检测硬编码的 magic number

        Args:
            code: 待检查的代码字符串

        Returns:
            List[AHIssue]: 发现的问题列表
        """
        issues = []

        # 检查 1: 假设/推测注释
        ambiguous_patterns = [
            (r'#.*假设', "假设"),
            (r'#.*推测', "推测"),
            (r'#.*可能', "可能"),
            (r'#.*不确定', "不确定"),
            (r'#.*待确认', "待确认")
        ]

        for pattern, keyword in ambiguous_patterns:
            if re.search(pattern, code):
                issues.append(AHIssue(
                    rule_id="AH-05-ASSUME",
                    severity="ERROR",
                    message=f"发现不确定性注释（'{keyword}'），应停止并询问用户",
                    line=self._find_line(code, pattern),
                    suggestion="删除代码，使用 AskUserQuestion 工具询问用户确认需求"
                ))

        # 检查 2: TODO/FIXME
        if re.search(r'#\s*(TODO|FIXME)', code, re.IGNORECASE):
            issues.append(AHIssue(
                rule_id="AH-05-TODO",
                severity="WARNING",
                message="代码包含 TODO/FIXME，表明逻辑不完整",
                line=self._find_line(code, r'#\s*(TODO|FIXME)', re.IGNORECASE),
                suggestion="完成逻辑或询问用户如何处理"
            ))

        # 检查 3: Magic number (数字 > 1 且不是常量)
        magic_number_pattern = r'(?<![A-Z_])\b([2-9]\d+)\b(?!\s*#)'
        for match in re.finditer(magic_number_pattern, code):
            number = match.group(1)
            issues.append(AHIssue(
                rule_id="AH-05-MAGIC",
                severity="INFO",
                message=f"发现 magic number '{number}'，应定义为常量并注释含义",
                line=self._find_line_number(code, match.start()),
                suggestion=f"定义: MAX_RETRIES = {number}  # 描述"
            ))

        return issues

    # ========== 综合检查 ==========

    def check_all(self, code: str) -> Dict[str, List[AHIssue]]:
        """运行所有 AH 检查

        Args:
            code: 待检查的代码字符串

        Returns:
            Dict[str, List[AHIssue]]: 按规则分组的问题字典
        """
        return {
            "AH-01": self.check_ah01_no_assumption(code),
            "AH-02": self.check_ah02_no_auto_decision(code),
            "AH-03": self.check_ah03_no_undefined_concepts(code),
            "AH-04": self.check_ah04_phase1_soft_constraints(code),
            "AH-05": self.check_ah05_ambiguity_handling(code)
        }

    def format_report(self, issues_by_rule: Dict[str, List[AHIssue]]) -> str:
        """格式化检查报告

        Args:
            issues_by_rule: check_all() 返回的问题字典

        Returns:
            str: 格式化的报告文本
        """
        total_errors = sum(
            len([i for i in issues if i.severity == "ERROR"])
            for issues in issues_by_rule.values()
        )
        total_warnings = sum(
            len([i for i in issues if i.severity == "WARNING"])
            for issues in issues_by_rule.values()
        )

        lines = [
            "=" * 60,
            "Anti-Hallucination Check Report",
            "=" * 60,
            f"Total: {total_errors} Errors, {total_warnings} Warnings",
            ""
        ]

        for rule_id, issues in issues_by_rule.items():
            if not issues:
                continue

            lines.append(f"\n[{rule_id}] - {len(issues)} issue(s)")
            lines.append("-" * 60)

            for issue in issues:
                lines.append(f"  Line {issue.line} [{issue.severity}]: {issue.message}")
                if issue.suggestion:
                    lines.append(f"    建议: {issue.suggestion}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    # ========== 辅助方法 ==========

    def _find_line(self, code: str, pattern: str, flags: int = 0) -> int:
        """查找匹配模式的行号

        Args:
            code: 代码字符串
            pattern: 正则表达式模式
            flags: 正则表达式标志

        Returns:
            int: 行号（从 1 开始），未找到返回 0
        """
        match = re.search(pattern, code, flags)
        if match:
            return self._find_line_number(code, match.start())
        return 0

    def _find_line_number(self, code: str, char_position: int) -> int:
        """根据字符位置查找行号

        Args:
            code: 代码字符串
            char_position: 字符位置

        Returns:
            int: 行号（从 1 开始）
        """
        return code[:char_position].count('\n') + 1
