from typing import Dict, Any
from skills.db_test_skill import db_test_skill


class TestAgent:
    """
    测试 Agent：
    目前只负责生成一条“Supabase MCP + Claude”可用的测试提示词，
    用于执行 db_invariants_test_v2.sql。
    """

    def build_prompt(self) -> Dict[str, Any]:
        return db_test_skill()

