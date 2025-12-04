"""
agent_platform.agents.pure_logic - MCP 安全的纯逻辑 Agent

Phase 2: Agent 层迁移
- 此目录包含所有 mcp_safe=True 的 Agent
- 这些 Agent 不调用 LLM，只执行文件操作、测试、验证等逻辑

已迁移的 Agent:
- test_agent: 测试提示词生成（db/backend）
- code_review_agent: 代码审核（SoT 一致性检查）
- doc_agent: 文档生成与审核

设计原则:
- 每个 Agent 在模块加载时自动注册到 registry
- mcp_safe=True 作为注册参数显式声明
- 保持与 agents/ 旧实现的接口兼容

基准对齐:
- AGENT_PLATFORM_MIGRATION_PLAN_v1.2.md Phase 2
"""

# 导入各 Agent 以触发注册
from .test_agent import TestAgentPure
from .code_review_agent import CodeReviewAgentPure
from .doc_agent import DocAgentPure

__all__ = [
    "TestAgentPure",
    "CodeReviewAgentPure",
    "DocAgentPure",
]
