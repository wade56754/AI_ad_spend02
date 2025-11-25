"""
前端 Agent
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..skills.fe_dev_skill import FEDevSkill
from ..tools.fs_tool import FSTool


class FEAgent:
    """前端开发 Agent"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化前端 Agent
        
        Args:
            base_path: 项目根路径
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.skill = FEDevSkill(base_path)
        self.fs_tool = FSTool(base_path)
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理前端开发请求
        
        Args:
            request: 请求内容，包含 action 和参数
            
        Returns:
            处理结果
        """
        action = request.get("action")
        
        if action == "create_component":
            return self.skill.create_component(
                request.get("component_name"),
                request.get("component_type", "tsx")
            )
        elif action == "update_component":
            return self.skill.update_component(
                request.get("component_name"),
                request.get("changes", {})
            )
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

