"""
agent_core - Agent 核心实现

# Fix: P2-02 - 添加包级别导出

包含所有 Agent 类的实现：
- FEAgent: 前端代码生成
- BEAgent: 后端代码生成
- TestAgent: 测试用例生成
- DocAgent: 文档管理
- CodeReviewAgent: 代码审核
- OrchestratorAgent: 流程编排

基准对齐：
- Agent Layer Freeze v1.0
- SUBAGENT_PROTOCOL.md
"""

# Fix: P2-02 - 导出所有 Agent 类
from .fe_agent import FEAgent
from .be_agent import BEAgent
from .test_agent import TestAgent
from .doc_agent import DocAgent
from .code_review_agent import CodeReviewAgent
from .orchestrator_agent import OrchestratorAgent

__all__ = [
    "FEAgent",
    "BEAgent",
    "TestAgent",
    "DocAgent",
    "CodeReviewAgent",
    "OrchestratorAgent",
]
