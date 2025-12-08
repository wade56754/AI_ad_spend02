"""
Supabase MCP tool wrapper.

# Fix: P1-02 - 改进 SupabaseTool 提示，提供清晰的"未配置"状态
# Fix: P1-06 - 统一返回结构为 SkillResult，与 Agent 层协议对齐

当前状态：占位实现，需要配置 Supabase MCP 才能使用。
配置方式：
1. 安装 Supabase MCP server
2. 在 Claude Code 中配置 MCP 连接
3. 使用 mcp__supabase__execute_sql 等工具
"""

from typing import Optional, Any, List, Dict
import logging

from .types import SkillResult

logger = logging.getLogger(__name__)


# Fix: P1-02 - 自定义异常类，提供更清晰的错误信息
class SupabaseNotConfiguredError(Exception):
    """Supabase MCP 未配置异常"""

    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(
            f"Supabase MCP 未配置，无法执行 '{operation}'。\n"
            f"请先配置 Supabase MCP server:\n"
            f"  1. 确保已安装 Supabase MCP\n"
            f"  2. 在 Claude Code 中配置 MCP 连接\n"
            f"  3. 设置 project_id 参数"
        )


class SupabaseTool:
    """
    Supabase MCP tool wrapper.

    # Fix: P1-02 - 改进错误提示和状态检查

    当前为占位实现，调用任何方法都会返回友好的错误提示。
    真正的实现需要集成 Supabase MCP server。
    """

    # Fix: P1-02 - 类级别标记，表示是否已配置
    _mcp_configured: bool = False

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Supabase tool.

        Args:
            project_id: Supabase project ID（可选，用于执行实际操作）
        """
        self.project_id = project_id
        # Fix: P1-02 - 初始化时记录配置状态
        if project_id:
            logger.info(f"SupabaseTool initialized with project_id: {project_id[:8]}...")
        else:
            logger.debug("SupabaseTool initialized without project_id (placeholder mode)")

    @classmethod
    def is_configured(cls) -> bool:
        """
        检查 Supabase MCP 是否已配置。

        # Fix: P1-02 - 提供配置状态检查

        Returns:
            True: MCP 已配置可用
            False: MCP 未配置
        """
        return cls._mcp_configured

    @classmethod
    def set_configured(cls, configured: bool = True) -> None:
        """
        设置 MCP 配置状态（用于测试或运行时配置）。

        # Fix: P1-02 - 允许运行时更新配置状态
        """
        cls._mcp_configured = configured
        logger.info(f"SupabaseTool MCP configured: {configured}")

    def _require_project_id(self, project_id: Optional[str]) -> str:
        """Resolve project_id and fail loudly when missing."""
        pid = project_id or self.project_id
        if not pid:
            logger.error("Supabase project_id is not configured")
            raise RuntimeError(
                "Supabase project_id 未配置。\n"
                "请通过以下方式设置:\n"
                "  - 初始化时: SupabaseTool(project_id='xxx')\n"
                "  - 调用时: tool.execute_sql(query, project_id='xxx')"
            )
        return pid

    def _check_mcp_or_raise(self, operation: str) -> None:
        """
        检查 MCP 是否配置，未配置时抛出友好异常。

        # Fix: P1-02 - 统一的 MCP 检查
        """
        if not self._mcp_configured:
            raise SupabaseNotConfiguredError(operation)

    def execute_sql(self, query: str, project_id: Optional[str] = None) -> SkillResult:
        """
        Execute SQL query.

        # Fix: P1-02 - 返回结构化结果而非直接抛异常
        # Fix: P1-06 - 返回类型改为 SkillResult

        Args:
            query: SQL query to execute
            project_id: Optional project ID override

        Returns:
            SkillResult: 统一返回结构
                - success: bool
                - data: 查询结果或 None
                - error: 错误信息或 None
                - raw: 调试信息（包含 query_preview, hint 等）
        """
        pid = self._require_project_id(project_id)

        # Fix: P1-02 - MCP 未配置时返回结构化错误
        # Fix: P1-06 - 使用 SkillResult 结构
        if not self._mcp_configured:
            logger.warning(f"execute_sql called but MCP not configured (project: {pid[:8]}...)")
            return SkillResult(
                success=False,
                data=None,
                error="Supabase MCP 未配置。请先配置 Supabase MCP server，然后调用 SupabaseTool.set_configured(True)",
                raw=f"query_preview: {query[:100]}{'...' if len(query) > 100 else ''}",
            )

        # TODO: 实际集成 Supabase MCP (mcp__supabase__execute_sql)
        raise NotImplementedError("Supabase MCP integration pending")

    def apply_migration(
        self, name: str, query: str, project_id: Optional[str] = None
    ) -> SkillResult:
        """
        Apply database migration.

        # Fix: P1-02 - 返回结构化结果
        # Fix: P1-06 - 返回类型改为 SkillResult
        """
        pid = self._require_project_id(project_id)

        if not self._mcp_configured:
            logger.warning(f"apply_migration called but MCP not configured")
            return SkillResult(
                success=False,
                data=None,
                error="Supabase MCP 未配置。请先配置 Supabase MCP server",
                raw=f"migration_name: {name}",
            )

        # TODO: 实际集成 Supabase MCP
        raise NotImplementedError("Supabase MCP integration pending")

    def list_tables(
        self, project_id: Optional[str] = None, schemas: Optional[List[str]] = None
    ) -> SkillResult:
        """
        List database tables.

        # Fix: P1-02 - 返回结构化结果
        # Fix: P1-06 - 返回类型改为 SkillResult
        """
        pid = self._require_project_id(project_id)

        if not self._mcp_configured:
            logger.warning(f"list_tables called but MCP not configured")
            return SkillResult(
                success=False,
                data=None,
                error="Supabase MCP 未配置。请先配置 Supabase MCP server",
                raw=f"schemas_requested: {schemas or ['public']}",
            )

        # TODO: 实际集成 Supabase MCP
        raise NotImplementedError("Supabase MCP integration pending")

    def get_status(self) -> Dict[str, Any]:
        """
        获取 SupabaseTool 状态。

        # Fix: P1-02 - 新增状态检查方法

        Returns:
            {
                "configured": bool,
                "project_id": Optional[str],
                "message": str
            }
        """
        return {
            "configured": self._mcp_configured,
            "project_id": self.project_id[:8] + "..." if self.project_id else None,
            "message": (
                "Supabase MCP 已配置，可正常使用"
                if self._mcp_configured
                else "Supabase MCP 未配置，请先完成 MCP server 配置"
            ),
        }
