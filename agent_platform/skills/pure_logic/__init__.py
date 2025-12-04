"""
agent_platform.skills.pure_logic - MCP 安全的纯逻辑 Skill

Phase 3: 技能层迁移
- 此目录包含 mcp_safe=True 的 Skill（不调用 LLM）
- MCP 模式下这些 Skill 可以安全暴露

纯逻辑 Skill:
- db_test_skill: 生成数据库测试提示词
- backend_test_skill: 生成后端 pytest 测试提示词
- sot_guard_skill: SoT 规则校验（验证代码是否违反 SoT）

设计原则:
- 这些 Skill 只生成提示词或进行规则校验
- 不直接调用 LLM API
- 可在 MCP 模式下安全运行

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
- SoT Freeze v2.6
"""

from agent_platform.skills.registry import register_skill

# Import skill functions
from .db_test_skill import db_test_skill
from .backend_test_skill import backend_test_skill
from .sot_guard_skill import (
    validate_against_sot,
    guard_check,
    check_state_machine_compliance,
    check_ledger_compliance,
    check_error_code_compliance,
    check_data_schema_compliance,
    SotViolation,
    SotGuardResult,
    SotParser,
)

# Register skills
register_skill(
    name="db_test",
    func=db_test_skill,
    description="生成数据库测试提示词（给 Supabase MCP 使用）",
    version="1.0.0",
    tags=["db", "test", "pure_logic"],
    mcp_safe=True,
)

register_skill(
    name="backend_test",
    func=backend_test_skill,
    description="生成后端 pytest 测试执行提示词",
    version="1.2.0",
    tags=["backend", "test", "pytest", "pure_logic"],
    mcp_safe=True,
)

register_skill(
    name="sot_guard",
    func=validate_against_sot,
    description="SoT 规则校验（检测代码是否违反 SoT）",
    version="2.0.0",
    tags=["sot", "guard", "validation", "pure_logic"],
    mcp_safe=True,
)

__all__ = [
    # Skill functions
    "db_test_skill",
    "backend_test_skill",
    # SoT Guard exports
    "validate_against_sot",
    "guard_check",
    "check_state_machine_compliance",
    "check_ledger_compliance",
    "check_error_code_compliance",
    "check_data_schema_compliance",
    "SotViolation",
    "SotGuardResult",
    "SotParser",
]
