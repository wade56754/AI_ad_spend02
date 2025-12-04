"""
agent_platform.skills.llm_dependent - LLM 依赖的 Skill

Phase 3: 技能层迁移
- 此目录包含 mcp_safe=False 的 Skill（调用 LLM）
- MCP 模式下这些 Skill 不会被暴露

LLM 依赖的 Skill:
- fe_dev_skill: 前端代码生成（调用 LLM）
- be_dev_skill: 后端代码生成（调用 LLM）

占位 Skill (NotImplementedError):
- doc_skill: 文档生成（尚未实现）
- review_skill: 代码审核（尚未实现）
- refactor_skill: 代码重构（尚未实现）

设计原则:
- 这些 Skill 的实现仍在 agents/skills/
- 此处只是注册到新 registry（mcp_safe=False）
- 保持与旧 agents/ 的兼容

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 3
"""

import logging
from typing import Dict, Any, Optional

from agent_platform.skills.registry import register_skill

logger = logging.getLogger(__name__)


# ============================================================
# FE Dev Skill (mcp_safe=False)
# ============================================================

def _fe_dev_skill_wrapper(**kwargs: Any) -> Dict[str, Any]:
    """fe_dev_skill 包装器（委托给 agents.skills.fe_dev_skill）"""
    try:
        from agents.skills.fe_dev_skill import fe_dev_skill
        return fe_dev_skill(**kwargs)
    except ImportError as e:
        return {
            "success": False,
            "data": None,
            "error": f"fe_dev_skill import failed: {e}",
        }


register_skill(
    name="fe_dev",
    func=_fe_dev_skill_wrapper,
    description="前端代码生成 Skill（调用 LLM）",
    version="1.0.0",
    tags=["fe", "frontend", "code_gen", "llm_dependent"],
    mcp_safe=False,
)


# ============================================================
# BE Dev Skill (mcp_safe=False)
# ============================================================

def _be_dev_skill_wrapper(**kwargs: Any) -> Dict[str, Any]:
    """be_dev_skill 包装器（委托给 agents.skills.be_dev_skill）"""
    try:
        from agents.skills.be_dev_skill import be_dev_skill
        return be_dev_skill(**kwargs)
    except ImportError as e:
        return {
            "success": False,
            "data": None,
            "error": f"be_dev_skill import failed: {e}",
        }


register_skill(
    name="be_dev",
    func=_be_dev_skill_wrapper,
    description="后端代码生成 Skill（调用 LLM）",
    version="1.0.0",
    tags=["be", "backend", "code_gen", "llm_dependent"],
    mcp_safe=False,
)


# ============================================================
# Placeholder Skills (NotImplementedError)
# 注册但标记为未实现
# ============================================================

def _doc_skill_placeholder(**kwargs: Any) -> Dict[str, Any]:
    """doc_skill 占位实现"""
    return {
        "success": False,
        "data": None,
        "error": "doc_skill 尚未实现",
    }


def _review_skill_placeholder(**kwargs: Any) -> Dict[str, Any]:
    """review_skill 占位实现"""
    return {
        "success": False,
        "data": None,
        "error": "review_skill 尚未实现",
    }


def _refactor_skill_placeholder(**kwargs: Any) -> Dict[str, Any]:
    """refactor_skill 占位实现"""
    return {
        "success": False,
        "data": None,
        "error": "refactor_skill 尚未实现",
    }


register_skill(
    name="doc",
    func=_doc_skill_placeholder,
    description="文档生成 Skill（尚未实现）",
    version="0.1.0",
    tags=["doc", "placeholder"],
    mcp_safe=False,
)

register_skill(
    name="review",
    func=_review_skill_placeholder,
    description="代码审核 Skill（尚未实现）",
    version="0.1.0",
    tags=["review", "placeholder"],
    mcp_safe=False,
)

register_skill(
    name="refactor",
    func=_refactor_skill_placeholder,
    description="代码重构 Skill（尚未实现）",
    version="0.1.0",
    tags=["refactor", "placeholder"],
    mcp_safe=False,
)


logger.info("LLM-dependent skills registered: fe_dev, be_dev (mcp_safe=False)")
logger.info("Placeholder skills registered: doc, review, refactor (mcp_safe=False)")
