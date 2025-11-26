from typing import List, Dict, Any
from skills.be_dev_skill import be_dev_skill


class BEAgent:
    """后端开发 Agent：对接后端 Skill，负责改 FastAPI/Service 代码。"""

    def run(self, task: str, target_files: List[str]) -> Dict[str, Any]:
        """
        :param task: 中文任务描述，如“实现充值申请列表 API，支持状态筛选和分页”
        :param target_files: 需要改动的后端相对路径列表
        """
        return be_dev_skill(task, target_files)

