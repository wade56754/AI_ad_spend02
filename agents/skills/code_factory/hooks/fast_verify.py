"""
Fast Verifier - 快速验证器

提供 < 100ms 的快速 SoT 合规检查，用于:
- 实时编辑器检查
- Pre-commit hook
- CI/CD 流水线

版本: v7.0
"""

import re
import logging
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """问题严重程度"""
    ERROR = "error"      # 阻断
    WARNING = "warning"  # 警告
    INFO = "info"        # 信息


@dataclass
class VerifyIssue:
    """验证问题"""
    filepath: str
    line: int
    message: str
    severity: IssueSeverity = IssueSeverity.ERROR
    code: str = ""
    
    def __str__(self) -> str:
        icon = "❌" if self.severity == IssueSeverity.ERROR else "⚠️"
        return f"{icon} {self.filepath}:{self.line}: {self.message}"


@dataclass
class VerifyResult:
    """验证结果"""
    passed: bool
    issues: List[VerifyIssue]
    checked_files: int
    elapsed_ms: float = 0.0
    
    def has_errors(self) -> bool:
        """是否有错误级别问题"""
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)


class FastVerifier:
    """
    快速验证器
    
    使用正则表达式进行快速检查，目标 < 100ms
    """
    
    # 禁止的角色
    FORBIDDEN_ROLES: Set[str] = {
        "supervisor", "data_operator", "data_clerk",
        "manager", "trader", "super_admin",
    }
    
    # 禁止的日报状态
    FORBIDDEN_STATES: Set[str] = {
        "draft", "pending", "approved",
    }
    
    # 高风险模式 (阻断)
    HIGH_RISK_PATTERNS = [
        (r"\.balance\s*[+-]=", "禁止直接修改 balance"),
        (r"\.balance\s*=\s*[^=]", "禁止直接赋值 balance"),
    ]
    
    # 中风险模式 (警告)
    MEDIUM_RISK_PATTERNS = [
        (r"HTTPException\s*\(\s*\d+\s*,", "建议使用 BusinessError"),
        (r"print\s*\(", "建议使用 logger"),
    ]
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """预编译正则表达式"""
        self._role_pattern = re.compile(
            r'["\'](' + '|'.join(self.FORBIDDEN_ROLES) + r')["\']',
            re.IGNORECASE
        )
        self._state_pattern = re.compile(
            r'status\s*[:=]\s*["\'](' + '|'.join(self.FORBIDDEN_STATES) + r')["\']',
            re.IGNORECASE
        )
        self._high_risk = [
            (re.compile(p), m) for p, m in self.HIGH_RISK_PATTERNS
        ]
        self._medium_risk = [
            (re.compile(p), m) for p, m in self.MEDIUM_RISK_PATTERNS
        ]
    
    def verify_content(
        self,
        content: str,
        filepath: str = "<string>",
    ) -> List[VerifyIssue]:
        """
        验证代码内容
        
        Args:
            content: 代码内容
            filepath: 文件路径 (用于报告)
            
        Returns:
            问题列表
        """
        issues = []
        lines = content.split("\n")
        in_docstring = False
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 检测 docstring 边界
            if '"""' in stripped or "'''" in stripped:
                # 单行 docstring
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    continue  # 跳过单行 docstring
                # 多行 docstring 开始/结束
                in_docstring = not in_docstring
                continue
            
            # 跳过 docstring 内容
            if in_docstring:
                continue
            
            # 跳过注释
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            
            # 跳过定义禁止列表的行、角色映射定义
            skip_keywords = [
                "FORBIDDEN", "DEPRECATED", "deprecated",
                "已移除", "已废弃", "已合并",
                ">>> ",  # docstring 示例 (额外保险)
                "# 已", "# 废弃", "# 移除",
                "# PRD",  # PRD 注释
                "# v",  # 版本注释
                "迁移",  # 迁移相关
                "映射",  # 映射定义
                "MAPPING",
                "project_owner",  # 角色映射目标
                "显示为",
            ]
            if any(kw in line for kw in skip_keywords):
                continue
            
            # 检查禁止角色
            match = self._role_pattern.search(line)
            if match:
                role = match.group(1)
                issues.append(VerifyIssue(
                    filepath=filepath,
                    line=line_num,
                    message=f"使用了禁止的角色: {role}",
                    severity=IssueSeverity.ERROR,
                    code=stripped,
                ))
            
            # 检查禁止状态
            match = self._state_pattern.search(line)
            if match:
                state = match.group(1)
                issues.append(VerifyIssue(
                    filepath=filepath,
                    line=line_num,
                    message=f"使用了禁止的日报状态: {state}",
                    severity=IssueSeverity.ERROR,
                    code=stripped,
                ))
            
            # 检查高风险模式
            for pattern, message in self._high_risk:
                if pattern.search(line):
                    issues.append(VerifyIssue(
                        filepath=filepath,
                        line=line_num,
                        message=message,
                        severity=IssueSeverity.ERROR,
                        code=stripped,
                    ))
            
            # 检查中风险模式
            for pattern, message in self._medium_risk:
                if pattern.search(line):
                    issues.append(VerifyIssue(
                        filepath=filepath,
                        line=line_num,
                        message=message,
                        severity=IssueSeverity.WARNING,
                        code=stripped,
                    ))
        
        return issues
    
    def verify_file(self, filepath: Path) -> List[VerifyIssue]:
        """
        验证单个文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            问题列表
        """
        if not filepath.exists():
            return []
        
        # 只检查 Python 和 TypeScript
        if filepath.suffix not in (".py", ".ts", ".tsx"):
            return []
        
        # 排除迁移文件 (迁移中可能合法使用旧角色/状态)
        filepath_str = str(filepath).replace("\\", "/")
        if "alembic/versions" in filepath_str or "migrations" in filepath_str:
            return []
        
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            return self.verify_content(content, str(filepath))
        except Exception as e:
            logger.error(f"读取文件失败 {filepath}: {e}")
            return []
    
    def verify_files(self, filepaths: List[Path]) -> VerifyResult:
        """
        验证多个文件
        
        Args:
            filepaths: 文件路径列表
            
        Returns:
            验证结果
        """
        import time
        start_time = time.time()
        
        all_issues = []
        checked = 0
        
        for filepath in filepaths:
            issues = self.verify_file(filepath)
            all_issues.extend(issues)
            checked += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return VerifyResult(
            passed=not any(i.severity == IssueSeverity.ERROR for i in all_issues),
            issues=all_issues,
            checked_files=checked,
            elapsed_ms=elapsed_ms,
        )
    
    def verify_directory(
        self,
        directory: Path,
        recursive: bool = True,
    ) -> VerifyResult:
        """
        验证目录
        
        Args:
            directory: 目录路径
            recursive: 是否递归
            
        Returns:
            验证结果
        """
        if not directory.exists():
            return VerifyResult(passed=True, issues=[], checked_files=0)
        
        pattern = "**/*" if recursive else "*"
        files = [
            f for f in directory.glob(pattern)
            if f.is_file() and f.suffix in (".py", ".ts", ".tsx")
        ]
        
        return self.verify_files(files)


def quick_verify(
    target: str,
    strict: bool = False,
) -> VerifyResult:
    """
    快速验证
    
    Args:
        target: 文件或目录路径
        strict: 是否严格模式 (警告也算失败)
        
    Returns:
        验证结果
    """
    verifier = FastVerifier()
    path = Path(target)
    
    if path.is_file():
        issues = verifier.verify_file(path)
        result = VerifyResult(
            passed=not any(i.severity == IssueSeverity.ERROR for i in issues),
            issues=issues,
            checked_files=1,
        )
    elif path.is_dir():
        result = verifier.verify_directory(path)
    else:
        return VerifyResult(passed=True, issues=[], checked_files=0)
    
    if strict:
        result.passed = len(result.issues) == 0
    
    return result


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agents.skills.code_factory.hooks.fast_verify <file_or_dir>")
        print("Options: --strict  Warnings count as failures")
        sys.exit(1)
    
    target = sys.argv[1]
    strict = "--strict" in sys.argv
    
    result = quick_verify(target, strict)
    
    if result.passed:
        print(f"[PASS] Verified {result.checked_files} files in {result.elapsed_ms:.1f}ms")
        sys.exit(0)
    
    print(f"\n[FAIL] Verified {result.checked_files} files in {result.elapsed_ms:.1f}ms\n")
    for issue in result.issues:
        severity = "ERROR" if issue.severity == IssueSeverity.ERROR else "WARN"
        print(f"[{severity}] {issue.filepath}:{issue.line}: {issue.message}")
    
    sys.exit(1)


if __name__ == "__main__":
    main()
