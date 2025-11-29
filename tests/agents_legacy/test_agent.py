from pathlib import Path
from typing import Dict, Any, Optional
import logging

from agents.tools.types import AgentResponse

logger = logging.getLogger(__name__)

class TestAgent:
    """
    Database Test Agent.

    Generates test prompts for Supabase MCP execution of db_invariants_test_v2.sql.

    IMPORTANT: This agent does NOT execute tests directly. It only generates
    prompts for manual or MCP-based execution. The 'executed' field in response
    will always be False to prevent callers (e.g., Orchestrator) from assuming
    tests passed when only prompt generation succeeded.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        初始化测试 Agent。

        Args:
            base_path: 项目根路径（可选，默认自动推断）
            project_id: Supabase 项目 ID（可选，用于执行实际测试）
        """
        self.base_path = (
            base_path
            if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )
        self.project_id = project_id

    def handle_request(self, request: Dict[str, Any]) -> AgentResponse:
        """
        处理测试请求（符合 AgentProtocol）。

        Args:
            request: 请求字典（当前版本不需要额外参数）

        Returns:
            {
                "success": bool,
                "data": {
                    "prompt": str,       # 给 Supabase MCP 使用的提示词
                    "executed": bool,    # 是否已执行测试（当前版本始终为 False）
                    "reason": str        # 未执行原因
                },
                "error": Optional[str]
            }
        """
        from agents.skills.db_test_skill import db_test_skill

        logger.info("Test Agent generating DB test prompt")

        # 调用 skill 生成测试 prompt
        result = db_test_skill()

        # Clarify that tests were NOT executed (only prompt was generated)
        # This prevents Orchestrator from misinterpreting success=True as "tests passed"
        if result["success"]:
            prompt_len = len(result["data"]["prompt"])
            logger.info(f"Test Agent completed: prompt generated ({prompt_len} chars)")
            return {
                "success": True,
                "data": {
                    "prompt": result["data"]["prompt"],
                    "executed": False,  # Always False until actual MCP integration
                    "reason": "Test prompt generated but not executed (requires Supabase MCP configuration and manual execution)",
                },
                "error": None,
            }
        else:
            logger.error(f"Test Agent failed: {result.get('error')}")

        return result

