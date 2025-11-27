"""
前端 Agent
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Callable
from pathlib import Path

from ..skills.fe_dev_skill import FEDevSkill
from ..tools.fs_tool import FSTool


class FEAgent:
    """前端开发 Agent"""

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """
        初始化前端 Agent

        Args:
            base_path: 项目根路径，默认为当前文件向上三级目录
        """
        self.base_path: Path = (
            base_path if base_path is not None
            else Path(__file__).resolve().parent.parent.parent
        )

        # 统一使用 self.base_path，避免 None 传入 skill 内部
        self.skill = FEDevSkill(self.base_path)
        self.fs_tool = FSTool(self.base_path)

        # action → 处理函数映射，后续扩展更方便
        self._action_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "create_component": self._handle_create_component,
            "update_component": self._handle_update_component,
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理前端开发请求

        Args:
            request: 请求内容，至少包含 "action"，其余参数随 action 变化

        Returns:
            统一结构：
            {
                "success": bool,
                "data"?: Any,
                "error"?: str
            }
        """
        action = request.get("action")
        if not action or not isinstance(action, str):
            return {
                "success": False,
                "error": "Missing or invalid 'action' in request",
            }

        handler = self._action_handlers.get(action)
        if handler is None:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
            }

        try:
            return handler(request)
        except Exception as exc:  # 保底兜一层
            return {
                "success": False,
                "error": f"FEAgent action '{action}' failed: {exc}",
            }

    # -------------------- 内部具体处理函数 --------------------

    def _handle_create_component(self, request: Dict[str, Any]) -> Dict[str, Any]:
        component_name = request.get("component_name")
        if not component_name:
            return {
                "success": False,
                "error": "Missing 'component_name' for action 'create_component'",
            }

        component_type = request.get("component_type", "tsx")

        result = self.skill.create_component(
            component_name=component_name,
            component_type=component_type,
        )

        # 约定 skill 返回中成功与否也统一为 success/data/error
        return result

    def _handle_update_component(self, request: Dict[str, Any]) -> Dict[str, Any]:
        component_name = request.get("component_name")
        if not component_name:
            return {
                "success": False,
                "error": "Missing 'component_name' for action 'update_component'",
            }

        changes = request.get("changes") or {}
        if not isinstance(changes, dict):
            return {
                "success": False,
                "error": "'changes' must be a dict",
            }

        result = self.skill.update_component(
            component_name=component_name,
            changes=changes,
        )
        return result
