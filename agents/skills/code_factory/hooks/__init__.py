"""
Hook 模块

提供 Claude Code 增强层的核心 Hook:
- pre_commit: 提交前验证 (违规阻断)
- rules_generator: .claude/rules.md 生成
- fast_verify: 快速验证器

版本: v7.0
"""

from .rules_generator import RulesGenerator, generate_rules
from .pre_commit import PreCommitHook, run_pre_commit
from .fast_verify import FastVerifier, quick_verify

__all__ = [
    # Rules 生成
    "RulesGenerator",
    "generate_rules",
    # Pre-commit
    "PreCommitHook",
    "run_pre_commit",
    # 快速验证
    "FastVerifier",
    "quick_verify",
]
