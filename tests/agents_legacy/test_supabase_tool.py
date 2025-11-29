"""
Supabase MCP tool wrapper (placeholder).
"""

from typing import Optional, Any, List, Dict
import logging

logger = logging.getLogger(__name__)


class SupabaseTool:
    """Supabase MCP tool wrapper; real integration is not yet implemented."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Supabase tool.

        Args:
            project_id: Supabase project ID
        """
        self.project_id = project_id

    def _require_project_id(self, project_id: Optional[str]) -> str:
        """Resolve project_id and fail loudly when missing."""
        pid = project_id or self.project_id
        if not pid:
            logger.error("Supabase project_id is not configured")
            raise RuntimeError("Supabase project_id is required but missing")
        return pid

    def execute_sql(self, query: str, project_id: Optional[str] = None) -> Any:
        """Execute SQL query (placeholder implementation)."""
        _ = self._require_project_id(project_id)
        # TODO: integrate Supabase MCP (mcp_supabase_execute_sql)
        raise NotImplementedError("Supabase MCP integration is required")

    def apply_migration(self, name: str, query: str, project_id: Optional[str] = None) -> bool:
        """Apply database migration (placeholder implementation)."""
        _ = self._require_project_id(project_id)
        # TODO: integrate Supabase MCP
        raise NotImplementedError("Supabase MCP integration is required")

    def list_tables(self, project_id: Optional[str] = None, schemas: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List database tables (placeholder implementation)."""
        _ = self._require_project_id(project_id)
        # TODO: integrate Supabase MCP
        raise NotImplementedError("Supabase MCP integration is required")
