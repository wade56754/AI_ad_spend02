from typing import List, Dict, Any
from skills.fe_dev_skill import fe_dev_skill


class FEAgent:
    """前端开发 Agent：对接前端 Skill，负责改 TSX/TS 文件。"""

    def run(self, task: str, target_files: List[str]) -> Dict[str, Any]:
        """
        :param task: 中文任务描述，如“重构项目列表页，增加状态筛选和分页”
        :param target_files: 需要改动的前端相对路径列表
        """
        return fe_dev_skill(task, target_files)

