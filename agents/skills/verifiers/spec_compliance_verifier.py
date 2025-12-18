"""
Spec 合规验证器 (Spec Compliance Verifier)

验证代码是否符合项目 SoT (Source of Truth) 文档定义：
- 字段名 (DATA_SCHEMA.md)
- 状态值 (STATE_MACHINE.md)
- 错误码 (ERROR_CODES_SOT.md)
- 角色 (AUTH_SPEC.md)
- 业务规则 (BUSINESS_RULES.md)

借鉴项目:
- Guardrails AI: 输入/输出守卫概念
- CodeScene: Code Health 质量门禁

Code Sources:
- Guardrails AI: https://github.com/guardrails-ai/guardrails
"""

import ast
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

from .base import (
    BaseVerifier,
    VerifyResult,
    VerifyIssue,
    VerifyContext,
    IssueCategory,
    IssueSeverity,
    create_issue,
)

logger = logging.getLogger(__name__)


# ============================================================================
# SoT 定义 (来自项目文档)
# ============================================================================

# 日报 8 状态机 (STATE_MACHINE.md v2.6)
DAILY_REPORT_STATES = {
    "raw_submitted",
    "trend_pending",
    "trend_ok",
    "trend_flagged",
    "trend_resolved",
    "final_pending",
    "final_confirmed",
    "final_locked",
}

# 充值状态 (STATE_MACHINE.md v2.6 §9)
TOPUP_STATES = {
    "draft",
    "pending_review",
    "data_reviewed",
    "finance_approved",
    "paid",
    "completed",
    "rejected",
    "cancelled",
}

# 迁移状态 (STATE_MACHINE.md v2.6 §12)
TRANSFER_STATES = {
    "draft",
    "pending_approval",
    "approved",
    "completed",
    "rejected",
}

# 对账状态
RECONCILIATION_STATES = {
    "draft",
    "pending",
    "reviewed",
    "adjusting",
    "confirmed",
    "completed",
}

# 广告账户状态
AD_ACCOUNT_STATES = {
    "new",
    "testing",
    "active",
    "suspended",
    "dead",
    "archived",
}

# 所有有效状态
ALL_VALID_STATES = (
    DAILY_REPORT_STATES |
    TOPUP_STATES |
    TRANSFER_STATES |
    RECONCILIATION_STATES |
    AD_ACCOUNT_STATES
)

# 有效角色 (AUTH_SPEC.md v2.0)
VALID_ROLES = {
    "admin",
    "finance",
    "data_operator",
    "account_manager",
    "media_buyer",
}

# 旧角色映射 (用于自动修复)
OLD_ROLE_MAPPING = {
    "administrator": "admin",
    "operator": "data_operator",
    "manager": "account_manager",
    "buyer": "media_buyer",
    "accountant": "finance",
}

# 错误码前缀 (ERROR_CODES_SOT.md v2.1)
VALID_ERROR_PREFIXES = {
    "VAL",   # 验证错误
    "AUTH",  # 认证授权错误
    "BIZ",   # 业务逻辑错误
    "SYS",   # 系统错误
    "DB",    # 数据库错误
}

# 常用字段 (DATA_SCHEMA.md v5.2)
COMMON_FIELDS = {
    # 通用
    "id", "uuid", "created_at", "updated_at", "created_by", "updated_by",
    "status", "notes", "description",
    # 项目
    "project_id", "project_name", "client_name",
    # 广告账户
    "ad_account_id", "account_id", "account_name", "account_code",
    "balance", "daily_budget", "total_budget",
    # 日报
    "report_date", "spend", "real_spend", "conversions", "leads",
    "cost_per_lead", "cost_per_conversion", "cpa", "roi", "roas",
    # 充值/迁移
    "amount", "requested_amount", "actual_amount", "transfer_amount",
    # 供应商
    "supplier_id", "supplier_name",
    # 渠道
    "channel_id", "channel_name", "channel_code",
}


class SpecComplianceVerifier(BaseVerifier):
    """
    Spec 合规验证器

    验证代码是否符合项目 SoT 文档定义
    """

    @property
    def name(self) -> str:
        return "SpecComplianceVerifier"

    @property
    def category(self) -> IssueCategory:
        return IssueCategory.SOT_COMPLIANCE

    @property
    def priority(self) -> int:
        return 30

    def __init__(self, context: Optional[VerifyContext] = None):
        super().__init__(context)

        # 使用上下文中的定义，否则使用默认值
        if context:
            self.valid_states = context.valid_states or ALL_VALID_STATES
            self.valid_fields = context.valid_fields or COMMON_FIELDS
            self.valid_roles = context.valid_roles or VALID_ROLES
            self.valid_error_codes = context.valid_error_codes or set()
        else:
            self.valid_states = ALL_VALID_STATES
            self.valid_fields = COMMON_FIELDS
            self.valid_roles = VALID_ROLES
            self.valid_error_codes = set()

    def verify(
        self,
        file_path: str,
        content: str,
        **kwargs
    ) -> VerifyResult:
        """
        执行 Spec 合规验证

        检测:
        1. 无效的状态值
        2. 无效的角色名
        3. 无效的错误码
        4. 不规范的字段名
        5. 违反业务规则
        """
        issues: List[VerifyIssue] = []
        metrics: Dict[str, Any] = {
            "states_checked": 0,
            "roles_checked": 0,
            "error_codes_checked": 0,
            "fields_checked": 0,
            "violations_found": 0,
        }

        # 1. 检查状态值
        state_issues = self._check_states(file_path, content)
        issues.extend(state_issues)
        metrics["states_checked"] = len(self._extract_state_candidates(content))

        # 2. 检查角色
        role_issues = self._check_roles(file_path, content)
        issues.extend(role_issues)
        metrics["roles_checked"] = len(self._extract_role_candidates(content))

        # 3. 检查错误码
        error_code_issues = self._check_error_codes(file_path, content)
        issues.extend(error_code_issues)
        metrics["error_codes_checked"] = len(self._extract_error_codes(content))

        # 4. 检查响应格式
        response_issues = self._check_response_format(file_path, content)
        issues.extend(response_issues)

        # 5. 检查业务规则违反
        rule_issues = self._check_business_rules(file_path, content)
        issues.extend(rule_issues)

        metrics["violations_found"] = len(issues)

        passed = not any(i.severity == IssueSeverity.ERROR for i in issues)

        return VerifyResult(
            passed=passed,
            category=self.category,
            issues=issues,
            metrics=metrics,
            details=[
                f"States checked: {metrics['states_checked']}",
                f"Roles checked: {metrics['roles_checked']}",
                f"Violations found: {metrics['violations_found']}",
            ],
        )

    # ========================================================================
    # 状态检查
    # ========================================================================

    def _check_states(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查状态值是否有效"""
        issues = []
        candidates = self._extract_state_candidates(content)

        for state, line, evidence in candidates:
            if state not in self.valid_states:
                # 尝试找到相似的有效状态
                similar = self._find_similar(state, self.valid_states)
                suggestion = f"使用有效状态: {similar}" if similar else \
                    f"检查 STATE_MACHINE.md 获取有效状态列表"

                issues.append(create_issue(
                    file_path=file_path,
                    line=line,
                    category=IssueCategory.SOT_COMPLIANCE,
                    code="SOT-001",
                    message=f"无效的状态值: '{state}'",
                    suggestion=suggestion,
                    severity=IssueSeverity.ERROR,
                    evidence=evidence,
                    auto_fixable=similar is not None,
                ))

        return issues

    def _extract_state_candidates(
        self,
        content: str
    ) -> List[Tuple[str, int, str]]:
        """提取可能的状态值"""
        candidates = []

        # 模式 1: status = "xxx" 或 status: "xxx"
        pattern1 = r'status\s*[=:]\s*["\'](\w+)["\']'
        for match in re.finditer(pattern1, content, re.IGNORECASE):
            line = content[:match.start()].count('\n') + 1
            candidates.append((match.group(1), line, match.group(0)))

        # 模式 2: StatusEnum.XXX 或 Status.XXX
        pattern2 = r'(?:Status|State)(?:Enum)?\.(\w+)'
        for match in re.finditer(pattern2, content):
            line = content[:match.start()].count('\n') + 1
            state = match.group(1).lower()
            candidates.append((state, line, match.group(0)))

        # 模式 3: 状态关键词模式 xxx_pending, xxx_confirmed 等
        state_keywords = ['pending', 'confirmed', 'locked', 'flagged', 'resolved',
                          'approved', 'rejected', 'completed', 'cancelled', 'draft']
        pattern3 = rf'["\'](\w+_(?:{"|".join(state_keywords)}))["\']'
        for match in re.finditer(pattern3, content, re.IGNORECASE):
            line = content[:match.start()].count('\n') + 1
            candidates.append((match.group(1), line, match.group(0)))

        return candidates

    # ========================================================================
    # 角色检查
    # ========================================================================

    def _check_roles(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查角色是否有效"""
        issues = []
        candidates = self._extract_role_candidates(content)

        for role, line, evidence in candidates:
            if role not in self.valid_roles:
                # 检查是否是旧角色名
                if role in OLD_ROLE_MAPPING:
                    new_role = OLD_ROLE_MAPPING[role]
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SOT-002",
                        message=f"使用了旧角色名: '{role}'",
                        suggestion=f"替换为新角色名: '{new_role}'",
                        severity=IssueSeverity.ERROR,
                        evidence=evidence,
                        auto_fixable=True,
                    ))
                else:
                    similar = self._find_similar(role, self.valid_roles)
                    suggestion = f"使用有效角色: {similar}" if similar else \
                        f"有效角色: {', '.join(self.valid_roles)}"

                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SOT-003",
                        message=f"无效的角色: '{role}'",
                        suggestion=suggestion,
                        severity=IssueSeverity.ERROR,
                        evidence=evidence,
                    ))

        return issues

    def _extract_role_candidates(
        self,
        content: str
    ) -> List[Tuple[str, int, str]]:
        """提取可能的角色值"""
        candidates = []

        # 模式 1: role = "xxx" 或 role: "xxx"
        pattern1 = r'role\s*[=:]\s*["\'](\w+)["\']'
        for match in re.finditer(pattern1, content, re.IGNORECASE):
            line = content[:match.start()].count('\n') + 1
            candidates.append((match.group(1), line, match.group(0)))

        # 模式 2: require_role(["xxx", "yyy"])
        pattern2 = r'require_role\s*\(\s*\[([^\]]+)\]'
        for match in re.finditer(pattern2, content):
            line = content[:match.start()].count('\n') + 1
            roles_str = match.group(1)
            for role_match in re.finditer(r'["\'](\w+)["\']', roles_str):
                candidates.append((role_match.group(1), line, match.group(0)))

        # 模式 3: roles 列表
        pattern3 = r'roles\s*=\s*\[([^\]]+)\]'
        for match in re.finditer(pattern3, content):
            line = content[:match.start()].count('\n') + 1
            roles_str = match.group(1)
            for role_match in re.finditer(r'["\'](\w+)["\']', roles_str):
                candidates.append((role_match.group(1), line, match.group(0)))

        return candidates

    # ========================================================================
    # 错误码检查
    # ========================================================================

    def _check_error_codes(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查错误码是否符合规范"""
        issues = []
        codes = self._extract_error_codes(content)

        for code, line, evidence in codes:
            # 解析错误码格式: PREFIX-NNN
            parts = code.split('-')
            if len(parts) != 2:
                # 检查是否是下划线格式 (可自动修复)
                underscore_parts = code.split('_')
                if len(underscore_parts) == 2 and underscore_parts[1].isdigit():
                    # 下划线格式，可以自动修复为连字符格式
                    fixed_code = code.replace('_', '-')
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SOT-004",
                        message=f"错误码格式不正确: '{code}'",
                        suggestion=f"应使用连字符格式: '{fixed_code}'",
                        severity=IssueSeverity.WARNING,
                        evidence=evidence,
                        auto_fixable=True,
                    ))
                else:
                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SOT-004",
                        message=f"错误码格式不正确: '{code}'",
                        suggestion="错误码格式应为: PREFIX-NNN (如 VAL-001)",
                        severity=IssueSeverity.WARNING,
                        evidence=evidence,
                    ))
                continue

            prefix = parts[0]
            if prefix not in VALID_ERROR_PREFIXES:
                issues.append(create_issue(
                    file_path=file_path,
                    line=line,
                    category=IssueCategory.SOT_COMPLIANCE,
                    code="SOT-005",
                    message=f"无效的错误码前缀: '{prefix}'",
                    suggestion=f"有效前缀: {', '.join(VALID_ERROR_PREFIXES)}",
                    severity=IssueSeverity.ERROR,
                    evidence=evidence,
                ))

        return issues

    def _extract_error_codes(
        self,
        content: str
    ) -> List[Tuple[str, int, str]]:
        """提取错误码"""
        codes = []

        # 模式: code = "XXX-NNN" 或 code: "XXX-NNN"
        pattern = r'code\s*[=:]\s*["\']([A-Z]+[-_]\d+)["\']'
        for match in re.finditer(pattern, content):
            line = content[:match.start()].count('\n') + 1
            codes.append((match.group(1), line, match.group(0)))

        # 模式: ErrorCode.XXX_NNN
        pattern2 = r'(?:Error|Business|System)(?:Error)?Codes?\.(\w+)'
        for match in re.finditer(pattern2, content):
            line = content[:match.start()].count('\n') + 1
            # 转换为标准格式
            code = match.group(1).replace('_', '-')
            codes.append((code, line, match.group(0)))

        return codes

    # ========================================================================
    # 响应格式检查
    # ========================================================================

    def _check_response_format(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查 API 响应格式是否符合规范"""
        issues = []

        # 检查是否使用了标准响应函数
        if 'router' in content.lower() or '@app.' in content:
            # 检查是否直接返回 dict 而不是用 success_response
            direct_return = re.findall(r'return\s*\{[^}]+\}', content)
            for match in direct_return:
                if 'success' not in match and 'code' not in match:
                    line = content.find(match)
                    line = content[:line].count('\n') + 1 if line >= 0 else 1

                    issues.append(create_issue(
                        file_path=file_path,
                        line=line,
                        category=IssueCategory.SOT_COMPLIANCE,
                        code="SOT-006",
                        message="直接返回 dict，未使用标准响应格式",
                        suggestion="使用 success_response() 或 error_response()",
                        severity=IssueSeverity.WARNING,
                        evidence=match[:50],
                    ))

        return issues

    # ========================================================================
    # 业务规则检查
    # ========================================================================

    def _check_business_rules(
        self,
        file_path: str,
        content: str
    ) -> List[VerifyIssue]:
        """检查是否违反业务规则"""
        issues = []

        # 规则 1: 不能直接修改 balance
        if re.search(r'\.balance\s*[+\-*/]=', content) or \
           re.search(r'\.balance\s*=\s*(?!.*ledger)', content, re.IGNORECASE):
            line = content.find('.balance')
            line = content[:line].count('\n') + 1 if line >= 0 else 1

            issues.append(create_issue(
                file_path=file_path,
                line=line,
                category=IssueCategory.SOT_COMPLIANCE,
                code="SOT-007",
                message="直接修改 balance 字段",
                suggestion="通过 ledger_entries 记录修改余额",
                severity=IssueSeverity.ERROR,
            ))

        # 规则 2: 状态转换必须通过状态机
        # (简化检查，完整检查需要更复杂的逻辑)
        if re.search(r'\.status\s*=\s*["\']', content):
            # 检查是否在 Service 层
            if '/routers/' in file_path:
                line = content.find('.status =')
                line = content[:line].count('\n') + 1 if line >= 0 else 1

                issues.append(create_issue(
                    file_path=file_path,
                    line=line,
                    category=IssueCategory.SOT_COMPLIANCE,
                    code="SOT-008",
                    message="在 Router 层直接修改状态",
                    suggestion="状态转换应在 Service 层通过状态机方法进行",
                    severity=IssueSeverity.WARNING,
                ))

        return issues

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _find_similar(self, value: str, valid_set: Set[str]) -> Optional[str]:
        """查找相似的有效值"""
        value_lower = value.lower()

        # 精确匹配 (不区分大小写)
        for valid in valid_set:
            if valid.lower() == value_lower:
                return valid

        # 部分匹配
        for valid in valid_set:
            if value_lower in valid.lower() or valid.lower() in value_lower:
                return valid

        # Levenshtein 距离 (简化版)
        best_match = None
        best_score = 0
        for valid in valid_set:
            score = self._similarity_score(value_lower, valid.lower())
            if score > best_score and score > 0.6:
                best_score = score
                best_match = valid

        return best_match

    def _similarity_score(self, s1: str, s2: str) -> float:
        """计算相似度分数"""
        if not s1 or not s2:
            return 0

        # 简单的字符重叠比率
        common = set(s1) & set(s2)
        return len(common) / max(len(set(s1)), len(set(s2)))

    # ========================================================================
    # 自动修复
    # ========================================================================

    def auto_fix(
        self,
        content: str,
        issues: List[VerifyIssue]
    ) -> tuple[str, int]:
        """自动修复 SoT 合规问题"""
        fixed_count = 0

        for issue in issues:
            if not issue.auto_fixable:
                continue

            # 修复旧角色名 (SOT-002)
            if issue.code == "SOT-002":
                old_role = issue.evidence.split('"')[1] if '"' in issue.evidence else \
                    issue.evidence.split("'")[1]
                new_role = OLD_ROLE_MAPPING.get(old_role)
                if new_role:
                    content = content.replace(f'"{old_role}"', f'"{new_role}"')
                    content = content.replace(f"'{old_role}'", f"'{new_role}'")
                    fixed_count += 1
                    issue.fix_applied = True

            # 修复错误码格式 (SOT-004): 下划线改连字符
            elif issue.code == "SOT-004":
                # 从 evidence 中提取错误码
                # evidence 格式: code = "BIZ_001" 或 code: "BIZ_001"
                match = re.search(r'["\']([A-Z]+_\d+)["\']', issue.evidence)
                if match:
                    old_code = match.group(1)
                    new_code = old_code.replace('_', '-')
                    # 替换引号内的值
                    content = content.replace(f'"{old_code}"', f'"{new_code}"')
                    content = content.replace(f"'{old_code}'", f"'{new_code}'")
                    fixed_count += 1
                    issue.fix_applied = True

        return content, fixed_count


# ============================================================================
# 便捷函数
# ============================================================================

def verify_spec_compliance(
    file_path: str,
    content: str,
    context: Optional[VerifyContext] = None
) -> VerifyResult:
    """
    Spec 合规验证便捷函数

    Args:
        file_path: 文件路径
        content: 文件内容
        context: 验证上下文

    Returns:
        验证结果
    """
    verifier = SpecComplianceVerifier(context)
    return verifier.verify(file_path, content)
