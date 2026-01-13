#!/usr/bin/env python3
"""
Pre-Commit Hook - 违规阻断

在 git commit 前自动运行，检查:
- 禁止的角色
- 禁止的状态
- 禁止的代码模式

违规将阻断提交！

版本: v7.0
"""

import re
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# 禁止清单
# =============================================================================

# 禁止的角色
FORBIDDEN_ROLES: Set[str] = {
    "supervisor",
    "data_operator", 
    "data_clerk",
    "manager",
    "trader",
    "super_admin",
    "accountant",
    "operator",
}

# 禁止的日报状态
FORBIDDEN_DAILY_REPORT_STATES: Set[str] = {
    "draft",
    "pending",
    "approved",
    "rejected",
}

# 禁止的代码模式
FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    # (正则表达式, 错误消息)
    (r"\.balance\s*[+-]=", "禁止直接修改 balance 字段，请使用 ledger"),
    (r"\.balance\s*=\s*", "禁止直接赋值 balance 字段，请使用 ledger"),
    (r"HTTPException\s*\(\s*\d+\s*,\s*['\"]", "禁止自定义错误消息，请使用 BusinessError"),
]

# 排除的文件/目录模式
EXCLUDED_PATTERNS: List[str] = [
    r"test_.*\.py$",           # 测试文件
    r".*_test\.py$",           # 测试文件
    r"conftest\.py$",          # pytest 配置
    r"migrations/.*\.py$",     # 数据库迁移
    r"__pycache__/",           # 缓存
    r"\.git/",                 # Git 目录
    r"node_modules/",          # Node 模块
    r"\.venv/",                # 虚拟环境
    r"venv/",                  # 虚拟环境
]


@dataclass
class Issue:
    """违规问题"""
    filepath: str
    line_number: int
    message: str
    code_snippet: str = ""
    
    def __str__(self) -> str:
        result = f"❌ {self.filepath}:{self.line_number}: {self.message}"
        if self.code_snippet:
            result += f"\n   → {self.code_snippet.strip()}"
        return result


class PreCommitHook:
    """
    Pre-Commit Hook
    
    检查暂存的文件是否违反 SoT 规则
    """
    
    def __init__(self):
        self.issues: List[Issue] = []
    
    def get_staged_files(self) -> List[str]:
        """获取暂存的文件列表"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True,
            )
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]
        except subprocess.CalledProcessError:
            return []
    
    def should_check_file(self, filepath: str) -> bool:
        """判断是否应该检查此文件"""
        # 只检查 Python 和 TypeScript 文件
        if not filepath.endswith((".py", ".ts", ".tsx")):
            return False
        
        # 排除特定文件/目录
        for pattern in EXCLUDED_PATTERNS:
            if re.search(pattern, filepath):
                return False
        
        return True
    
    def check_file(self, filepath: str) -> List[Issue]:
        """
        检查单个文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            发现的问题列表
        """
        issues = []
        
        try:
            path = Path(filepath)
            if not path.exists():
                return issues
            
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            for line_num, line in enumerate(lines, 1):
                # 跳过注释行
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                
                # 检查禁止的角色
                for role in FORBIDDEN_ROLES:
                    # 匹配 "role" 或 'role' 作为字符串值
                    patterns = [
                        rf'["\']?role["\']?\s*[:=]\s*["\']{role}["\']',
                        rf'role\s*==\s*["\']{role}["\']',
                        rf'["\']{role}["\']',  # 直接使用角色名
                    ]
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # 排除定义废弃角色列表的情况
                            if "FORBIDDEN" in line or "DEPRECATED" in line or "deprecated" in line.lower():
                                continue
                            issues.append(Issue(
                                filepath=filepath,
                                line_number=line_num,
                                message=f"使用了禁止的角色: {role}",
                                code_snippet=line,
                            ))
                            break
                
                # 检查禁止的日报状态
                for state in FORBIDDEN_DAILY_REPORT_STATES:
                    # 只检查日报相关的状态使用
                    patterns = [
                        rf'status\s*[:=]\s*["\']{state}["\']',
                        rf'DailyReport.*status.*["\']{state}["\']',
                    ]
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # 排除定义废弃状态列表的情况
                            if "FORBIDDEN" in line or "DEPRECATED" in line:
                                continue
                            issues.append(Issue(
                                filepath=filepath,
                                line_number=line_num,
                                message=f"使用了禁止的日报状态: {state}",
                                code_snippet=line,
                            ))
                            break
                
                # 检查禁止的代码模式
                for pattern, message in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line):
                        issues.append(Issue(
                            filepath=filepath,
                            line_number=line_num,
                            message=message,
                            code_snippet=line,
                        ))
            
        except Exception as e:
            logger.error(f"检查文件失败 {filepath}: {e}")
        
        return issues
    
    def run(self) -> Tuple[bool, List[Issue]]:
        """
        运行检查
        
        Returns:
            (是否通过, 问题列表)
        """
        staged_files = self.get_staged_files()
        all_issues = []
        
        for filepath in staged_files:
            if self.should_check_file(filepath):
                issues = self.check_file(filepath)
                all_issues.extend(issues)
        
        return len(all_issues) == 0, all_issues


def run_pre_commit() -> int:
    """
    运行 pre-commit hook
    
    Returns:
        退出码 (0=通过, 1=失败)
    """
    hook = PreCommitHook()
    passed, issues = hook.run()
    
    if passed:
        print("[PASS] SoT compliance check passed")
        return 0
    
    print("\n[BLOCKED] SoT violations found:\n")
    for issue in issues:
        print(f"[ERROR] {issue.filepath}:{issue.line_number}: {issue.message}")
        if issue.code_snippet:
            print(f"        -> {issue.code_snippet.strip()}")
    
    print("\nPlease fix the above issues before committing.")
    print("Hint: See .claude/rules.md for detailed rules.\n")
    
    return 1


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行入口"""
    sys.exit(run_pre_commit())


if __name__ == "__main__":
    main()
