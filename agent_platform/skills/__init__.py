"""
agent_platform.skills - Skill 子系统

Phase 3: 技能层迁移
- 提供 Skill 注册、发现、调用机制
- mcp_safe=True 的 Skill 可在 MCP 模式下安全运行
- 与 Agent 子系统设计对齐

设计原则:
- mcp_safe 是注册时的"唯一真相"
- 所有 Skill 通过 registry 注册
- MCP 模式下只暴露 mcp_safe=True 的 Skill

Skill 分类:
- MCP 安全 (mcp_safe=True): db_test, backend_test, sot_guard
- LLM 依赖 (mcp_safe=False): fe_dev, be_dev, doc, review, refactor

使用示例:
```python
from agent_platform.skills import (
    list_skills,
    list_mcp_safe_skills,
    invoke_skill,
    is_skill_mcp_safe,
)

# 列出所有 Skill
for meta in list_skills():
    print(f"{meta.name}: mcp_safe={meta.mcp_safe}")

# 列出 MCP 安全的 Skill
safe_skills = list_mcp_safe_skills()

# 调用 Skill
result = invoke_skill("sot_guard", changes={"file.py": "code..."})
```

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
- SoT Freeze v2.6
"""

# Re-export from registry
from agent_platform.skills.registry import (
    SkillMeta,
    SkillRegistry,
    get_registry,
    register_skill,
    list_skills,
    list_mcp_safe_skills,
    invoke_skill,
    is_skill_mcp_safe,
)

# Import skill modules to trigger registration
# Order: pure_logic first (mcp_safe=True), then llm_dependent (mcp_safe=False)
from . import pure_logic
from . import llm_dependent

# Re-export commonly used skill functions
from .pure_logic import (
    db_test_skill,
    backend_test_skill,
    validate_against_sot,
    guard_check,
    SotViolation,
    SotGuardResult,
    SotParser,
)

__all__ = [
    # Registry
    "SkillMeta",
    "SkillRegistry",
    "get_registry",
    "register_skill",
    "list_skills",
    "list_mcp_safe_skills",
    "invoke_skill",
    "is_skill_mcp_safe",
    # Pure logic skill functions
    "db_test_skill",
    "backend_test_skill",
    "validate_against_sot",
    "guard_check",
    "SotViolation",
    "SotGuardResult",
    "SotParser",
]
