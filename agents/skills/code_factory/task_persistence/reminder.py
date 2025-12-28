"""
任务提醒注入器

版本: v4.2

功能:
- 在 LLM 交互中注入任务提醒
- 确保任务不被遗忘
"""

from typing import Optional, Callable
from .task_list import TaskListManager


class ReminderInjector:
    """任务提醒注入器"""

    def __init__(
        self,
        task_manager: TaskListManager,
        inject_interval: int = 5,  # 每 N 次交互注入一次
    ):
        """初始化

        Args:
            task_manager: 任务管理器
            inject_interval: 注入间隔
        """
        self.task_manager = task_manager
        self.inject_interval = inject_interval
        self._interaction_count = 0

    def should_inject(self) -> bool:
        """是否应该注入提醒"""
        self._interaction_count += 1
        return self._interaction_count % self.inject_interval == 0

    def get_reminder(self) -> Optional[str]:
        """获取提醒内容

        Returns:
            提醒字符串，如果没有待处理任务则返回 None
        """
        if not self.task_manager.can_resume():
            return None

        return self.task_manager.generate_reminder()

    def inject_to_prompt(self, prompt: str) -> str:
        """注入提醒到提示词

        Args:
            prompt: 原提示词

        Returns:
            注入后的提示词
        """
        if not self.should_inject():
            return prompt

        reminder = self.get_reminder()
        if not reminder:
            return prompt

        return f"""<task_reminder>
{reminder}
</task_reminder>

{prompt}"""

    def reset(self):
        """重置计数"""
        self._interaction_count = 0

    def create_hook(self) -> Callable[[str], str]:
        """创建钩子函数

        Returns:
            可用于提示词处理的钩子
        """
        def hook(prompt: str) -> str:
            return self.inject_to_prompt(prompt)
        return hook
