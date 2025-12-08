"""
Skills 模块：定义各种开发技能

# Fix: P1-04 - 正确导出 sot_guard_skill 相关函数
# Fix: P0-01 - 导出所有 skill 模块（含占位实现）
"""

from .fe_dev_skill import fe_dev_skill
from .be_dev_skill import be_dev_skill
from .db_test_skill import db_test_skill
# Fix: P1-04 - 导出 sot_guard_skill 公开函数
from .sot_guard_skill import (
    validate_against_sot,
    guard_check,
    SotParser,
    SotViolation,
    SotGuardResult,
)
# Fix: P0-01 - 导出占位 skill（明确标注未实现状态）
# 这些 skill 当前为占位实现，调用时会抛出 NotImplementedError
# 文档生成由 DocAgent 直接实现，代码审核由 CodeReviewAgent + sot_guard_skill 实现
from .doc_skill import doc_skill
from .review_skill import review_skill
from .refactor_skill import refactor_skill

__all__ = [
    # 开发技能（已实现）
    'fe_dev_skill',
    'be_dev_skill',
    'db_test_skill',
    # SoT 守门员（已实现）
    'validate_against_sot',
    'guard_check',
    'SotParser',
    'SotViolation',
    'SotGuardResult',
    # 占位技能（未实现，调用会抛 NotImplementedError）
    # - doc_skill: 文档生成由 DocAgent 直接实现
    # - review_skill: 代码审核由 CodeReviewAgent + sot_guard_skill 实现
    # - refactor_skill: 重构功能预留
    'doc_skill',
    'review_skill',
    'refactor_skill',
]

