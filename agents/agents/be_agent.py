"""
后端 Agent
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..skills.be_dev_skill import BEDevSkill
from ..tools.fs_tool import FSTool


class BEAgent:
    """后端开发 Agent"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化后端 Agent
        
        Args:
            base_path: 项目根路径
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.skill = BEDevSkill(base_path)
        self.fs_tool = FSTool(base_path)
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理后端开发请求
        
        Args:
            request: 请求内容，包含 action 和参数
            
        Returns:
            处理结果
        """
        action = request.get("action")
        
        if action == "create_api_route":
            return self.skill.create_api_route(
                request.get("route_name"),
                request.get("method", "GET")
            )
        elif action == "create_service":
            return self.skill.create_service(
                request.get("service_name")
            )
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

