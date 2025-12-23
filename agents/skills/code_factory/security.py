"""
安全验证器 - Defense-in-Depth 安全模型

借鉴 Anthropic autonomous-coding 的安全设计:
- 白名单命令验证
- 文件系统隔离
- 敏感命令额外检查

结合我们的 SoT 合规验证:
- 状态机合规
- 错误码合规
- 角色权限合规

来源: Anthropic autonomous-coding/security.py
"""

import shlex
import re
from pathlib import Path
from typing import Set, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum


class SecurityLevel(Enum):
    """安全级别"""
    SAFE = "safe"           # 完全安全
    RESTRICTED = "restricted"  # 需要额外检查
    BLOCKED = "blocked"      # 禁止执行


# ============================================================
# 命令白名单 (借鉴 Anthropic)
# ============================================================

ALLOWED_COMMANDS: Set[str] = {
    # 文件检查
    "ls", "dir", "cat", "head", "tail", "wc", "grep", "find",
    "cp", "mv", "mkdir",

    # Python
    "python", "python3", "pip", "pytest", "mypy", "ruff",

    # Node.js
    "npm", "npx", "node",

    # 版本控制
    "git",

    # 进程管理 (受限)
    "ps", "lsof", "sleep",

    # 网络 (受限)
    "curl", "wget",
}

# 需要额外验证的敏感命令
RESTRICTED_COMMANDS: Set[str] = {
    "pkill", "kill",      # 只能终止开发进程
    "chmod",              # 只能 +x
    "rm",                 # 只能删除项目内文件
    "git push",           # 需要确认
}

# 绝对禁止的命令
BLOCKED_COMMANDS: Set[str] = {
    "rm -rf",
    "format",
    "mkfs",
    "dd",
    "shutdown",
    "reboot",
    "sudo",
    "su",
}

# 禁止的文件模式
BLOCKED_FILE_PATTERNS: Set[str] = {
    ".env",
    "*.pem",
    "*.key",
    "credentials.json",
    "secrets.yaml",
    "*.secret",
    "id_rsa",
    "id_ed25519",
}


@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    allowed: bool
    level: SecurityLevel
    command: str
    reason: str
    blocked_parts: List[str] = None

    def __post_init__(self):
        if self.blocked_parts is None:
            self.blocked_parts = []


class SecurityValidator:
    """
    安全验证器

    三层防护:
    1. 命令白名单
    2. 文件系统隔离
    3. SoT 合规检查
    """

    def __init__(self, project_dir: Path, allowed_commands: Set[str] = None):
        self.project_dir = Path(project_dir).resolve()
        self.allowed_commands = allowed_commands or ALLOWED_COMMANDS

    def validate_command(self, command: str) -> SecurityCheckResult:
        """
        验证 Bash 命令是否安全

        使用 shlex 解析防止绕过
        """
        # 检查绝对禁止的命令
        for blocked in BLOCKED_COMMANDS:
            if blocked in command.lower():
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.BLOCKED,
                    command=command,
                    reason=f"命令 '{blocked}' 被禁止执行",
                    blocked_parts=[blocked],
                )

        # 解析命令
        try:
            parts = self._extract_commands(command)
        except ValueError as e:
            return SecurityCheckResult(
                allowed=False,
                level=SecurityLevel.BLOCKED,
                command=command,
                reason=f"命令解析失败: {e}",
            )

        # 检查每个命令部分
        blocked_parts = []
        for cmd in parts:
            if cmd not in self.allowed_commands:
                blocked_parts.append(cmd)

        if blocked_parts:
            return SecurityCheckResult(
                allowed=False,
                level=SecurityLevel.BLOCKED,
                command=command,
                reason=f"命令不在白名单中: {', '.join(blocked_parts)}",
                blocked_parts=blocked_parts,
            )

        # 检查受限命令的额外约束
        for restricted in RESTRICTED_COMMANDS:
            if restricted in command:
                result = self._check_restricted_command(command, restricted)
                if not result.allowed:
                    return result

        return SecurityCheckResult(
            allowed=True,
            level=SecurityLevel.SAFE,
            command=command,
            reason="命令验证通过",
        )

    def _extract_commands(self, command: str) -> List[str]:
        """
        提取命令中的所有命令名

        处理管道、链式命令等
        """
        commands = []

        # 使用 shlex 安全解析
        try:
            tokens = shlex.split(command)
        except ValueError:
            # 解析失败时保守处理
            raise ValueError("命令格式无效")

        # 分隔符
        separators = {"&&", "||", ";", "|"}
        shell_keywords = {"if", "then", "else", "fi", "for", "while", "do", "done", "case", "esac"}

        expect_command = True
        for token in tokens:
            if token in separators:
                expect_command = True
            elif token.startswith("-"):
                # 跳过参数
                continue
            elif token in shell_keywords:
                continue
            elif expect_command:
                # 提取命令名
                cmd_name = Path(token).name if "/" in token else token
                if cmd_name and not cmd_name.startswith("$"):
                    commands.append(cmd_name)
                expect_command = False

        return commands

    def _check_restricted_command(self, command: str, restricted: str) -> SecurityCheckResult:
        """检查受限命令的额外约束"""

        if restricted in ["pkill", "kill"]:
            # 只能终止开发进程
            allowed_targets = {"node", "npm", "vite", "next", "python", "uvicorn"}
            has_valid_target = any(target in command for target in allowed_targets)
            if not has_valid_target:
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.RESTRICTED,
                    command=command,
                    reason=f"{restricted} 只能用于开发进程: {', '.join(allowed_targets)}",
                )

        elif restricted == "chmod":
            # 只允许 +x
            if "+x" not in command and "755" not in command:
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.RESTRICTED,
                    command=command,
                    reason="chmod 只允许添加执行权限 (+x 或 755)",
                )

        elif restricted == "rm":
            # 检查是否在项目目录内
            if not self._is_in_project_dir(command):
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.RESTRICTED,
                    command=command,
                    reason="rm 只能删除项目目录内的文件",
                )

        elif restricted == "git push":
            # 需要额外确认
            return SecurityCheckResult(
                allowed=True,
                level=SecurityLevel.RESTRICTED,
                command=command,
                reason="git push 需要用户确认",
            )

        return SecurityCheckResult(
            allowed=True,
            level=SecurityLevel.SAFE,
            command=command,
            reason="受限命令检查通过",
        )

    def _is_in_project_dir(self, command: str) -> bool:
        """检查命令中的路径是否在项目目录内"""
        try:
            tokens = shlex.split(command)
            for token in tokens:
                if token.startswith("-"):
                    continue
                # 尝试解析为路径
                try:
                    path = Path(token).resolve()
                    if path.exists() and not str(path).startswith(str(self.project_dir)):
                        return False
                except Exception:
                    continue
        except ValueError:
            return False
        return True

    def validate_file_path(self, file_path: str) -> SecurityCheckResult:
        """验证文件路径是否安全"""
        path = Path(file_path)

        # 检查敏感文件模式
        for pattern in BLOCKED_FILE_PATTERNS:
            if path.match(pattern):
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.BLOCKED,
                    command=file_path,
                    reason=f"禁止操作敏感文件: {pattern}",
                )

        # 检查是否在项目目录内
        try:
            resolved = path.resolve()
            if not str(resolved).startswith(str(self.project_dir)):
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.BLOCKED,
                    command=file_path,
                    reason="文件路径必须在项目目录内",
                )
        except Exception as e:
            return SecurityCheckResult(
                allowed=False,
                level=SecurityLevel.BLOCKED,
                command=file_path,
                reason=f"路径解析失败: {e}",
            )

        return SecurityCheckResult(
            allowed=True,
            level=SecurityLevel.SAFE,
            command=file_path,
            reason="文件路径验证通过",
        )

    def validate_code_content(self, content: str) -> SecurityCheckResult:
        """验证代码内容是否包含危险模式"""
        dangerous_patterns = [
            (r"os\.system\s*\(", "禁止使用 os.system"),
            (r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "禁止使用 shell=True"),
            (r"eval\s*\(", "禁止使用 eval"),
            (r"exec\s*\(", "禁止使用 exec"),
            (r"__import__\s*\(", "禁止使用 __import__"),
            (r"rm\s+-rf\s+/", "禁止递归删除根目录"),
            (r"DROP\s+DATABASE", "禁止删除数据库"),
            (r"DELETE\s+FROM\s+\w+\s*;?\s*$", "禁止无条件删除"),
        ]

        for pattern, reason in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return SecurityCheckResult(
                    allowed=False,
                    level=SecurityLevel.BLOCKED,
                    command=pattern,
                    reason=reason,
                )

        return SecurityCheckResult(
            allowed=True,
            level=SecurityLevel.SAFE,
            command="code_content",
            reason="代码内容验证通过",
        )


# ============================================================
# SoT 合规验证 (我们的特色)
# ============================================================

class SoTComplianceChecker:
    """SoT 合规检查器"""

    # 日报 8 状态机 (STATE_MACHINE.md v2.6)
    VALID_DAILY_REPORT_STATES = {
        "raw_submitted",
        "trend_pending",
        "trend_ok",
        "trend_flagged",
        "trend_resolved",
        "final_pending",
        "final_confirmed",
        "final_locked",
    }

    # 已废弃状态
    DEPRECATED_STATES = {
        "draft", "pending_review", "approved", "rejected",
        "pending", "confirmed", "locked",
    }

    # 合法角色 (仅 5 个)
    VALID_ROLES = {
        "admin",
        "finance",
        "data_operator",
        "account_manager",
        "media_buyer",
    }

    # 已废弃角色
    DEPRECATED_ROLES = {
        "super_admin": "admin",
        "accountant": "finance",
        "operator": "data_operator",
    }

    # 错误码前缀
    VALID_ERROR_PREFIXES = {"VAL", "AUTH", "BIZ", "DB", "INT", "SYS"}

    def check_states(self, content: str) -> List[str]:
        """检查代码中的状态是否合规"""
        issues = []

        for state in self.DEPRECATED_STATES:
            pattern = rf'["\']?{state}["\']?\s*[=:]'
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"使用已废弃状态 '{state}'，请使用 8 状态机中的状态")

        return issues

    def check_roles(self, content: str) -> List[str]:
        """检查代码中的角色是否合规"""
        issues = []

        for old_role, new_role in self.DEPRECATED_ROLES.items():
            if f'"{old_role}"' in content or f"'{old_role}'" in content:
                issues.append(f"使用已废弃角色 '{old_role}'，请使用 '{new_role}'")

        return issues

    def check_error_codes(self, content: str) -> List[str]:
        """检查错误码是否合规"""
        issues = []

        # 查找所有错误码模式
        error_pattern = r'["\']([A-Z]{2,4})-(\d{3})["\']'
        matches = re.findall(error_pattern, content)

        for prefix, code in matches:
            if prefix not in self.VALID_ERROR_PREFIXES:
                issues.append(f"使用未知错误码前缀 '{prefix}'，合法前缀: {self.VALID_ERROR_PREFIXES}")

        return issues

    def check_balance_modification(self, content: str) -> List[str]:
        """检查是否直接修改 balance"""
        issues = []

        patterns = [
            r'\.balance\s*[+-]=',
            r'\.balance\s*=\s*[^=]',
            r'UPDATE.*SET.*balance\s*=',
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("禁止直接修改 balance，请通过 ledger_entries 记录")
                break

        return issues

    def check_all(self, content: str) -> List[str]:
        """执行所有 SoT 合规检查"""
        issues = []
        issues.extend(self.check_states(content))
        issues.extend(self.check_roles(content))
        issues.extend(self.check_error_codes(content))
        issues.extend(self.check_balance_modification(content))
        return issues


def create_security_hook(project_dir: Path) -> callable:
    """
    创建安全钩子函数

    用于 Claude SDK 的 bash 命令拦截
    """
    validator = SecurityValidator(project_dir)

    def security_hook(command: str) -> Tuple[bool, str]:
        result = validator.validate_command(command)
        return result.allowed, result.reason

    return security_hook
