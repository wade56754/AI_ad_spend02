"""
测试 Agent - 专门执行数据库不变量测试
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from pathlib import Path

from ..skills.db_test_skill import DBTestSkill
from ..tools.supabase_tool import SupabaseTool


class TestAgent:
    """测试 Agent - 执行数据库不变量测试"""

    def __init__(
        self,
        base_path: Optional[Path] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """
        初始化测试 Agent

        Args:
            base_path: 项目根路径，默认为当前文件向上三级目录
            project_id: Supabase 项目 ID（可选，未提供则仅解析脚本不执行）
        """
        self.base_path: Path = (
            base_path if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

        self.skill = DBTestSkill(self.base_path)
        self.project_id = project_id

        # SupabaseTool 延迟使用，避免 project_id 为空时白建连接
        self._supabase_tool: Optional[SupabaseTool] = None
        if project_id:
            self._supabase_tool = SupabaseTool(project_id)

    def execute_db_invariants_test(self) -> Dict[str, Any]:
        """
        执行数据库不变量测试（当前版本：解析并准备测试脚本与用例）

        Returns:
            {
                "success": bool,
                "message": str,
                "script_path"?: str,
                "test_cases_count"?: int,
                "test_cases"?: List[dict],
                "warning"?: str,
            }
        """
        test_script_path = self.skill.get_test_script_path()

        if not test_script_path.exists():
            return {
                "success": False,
                "error": f"Test script not found: {test_script_path}",
            }

        # 读取 SQL（后续可以直接送给 Supabase MCP 执行）
        test_sql = test_script_path.read_text(encoding="utf-8")

        # 解析测试用例（比如每个 invariants 的描述/检查语句）
        test_cases: List[Dict[str, Any]] = self.skill.parse_test_cases()

        result: Dict[str, Any] = {
            "success": True,
            "message": "DB invariants test prepared",
            "script_path": str(test_script_path),
            "test_sql": test_sql,
            "test_cases_count": len(test_cases),
            "test_cases": test_cases,
        }

        # 这里先不直接执行 SQL，只做准备工作
        # 如果你后面要接 Supabase MCP，可以在这里补上执行逻辑：
        #
        # if self._supabase_tool is None:
        #     result["warning"] = "Supabase project_id not configured; SQL not executed."
        # else:
        #     exec_result = self._supabase_tool.execute_sql(test_sql, self.project_id)
        #     result["execution_result"] = exec_result

        if self._supabase_tool is None:
            result["warning"] = (
                "Supabase project_id not configured; "
                "only prepared SQL and test cases, did not execute."
            )

        return result

    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """
        生成测试报告（纯文本）

        Args:
            test_results: execute_db_invariants_test 或实际执行结果的聚合

        Returns:
            可直接保存为 .md / .txt 的测试报告
        """
        lines: List[str] = []
        lines.append("DB Invariants Test Report")
        lines.append("=" * 32)
        lines.append("")

        script_path = test_results.get("script_path")
        if script_path:
            lines.append(f"Script Path : {script_path}")

        cases_count = test_results.get("test_cases_count", 0)
        lines.append(f"Test Cases  : {cases_count}")

        warning = test_results.get("warning")
        if warning:
            lines.append(f"Warning     : {warning}")

        lines.append("")

        test_cases = test_results.get("test_cases") or []
        if test_cases:
            lines.append("Case Details:")
            for idx, case in enumerate(test_cases, start=1):
                desc = case.get("description") or case.get("name") or f"Case {idx}"
                status = case.get("status", "UNKNOWN")
                lines.append(f"  {idx}. [{status}] {desc}")
        else:
            lines.append("No detailed test cases found.")

        lines.append("")
        return "\n".join(lines)
