"""
任务列表模块单元测试

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.task_persistence.task_list import (
    TaskListManager,
    TaskItem,
)
from agents.skills.code_factory.task_persistence.reminder import ReminderInjector


class TestTaskItem:
    """任务项测试"""

    def test_create_task_item(self):
        """测试创建任务项"""
        task = TaskItem(
            id="task-001",
            content="实现用户认证",
            priority=1,
            phase_id=0,
        )

        assert task.id == "task-001"
        assert task.content == "实现用户认证"
        assert task.priority == 1
        assert task.status == "pending"

    def test_task_to_dict(self):
        """测试任务转字典"""
        task = TaskItem(
            id="task-001",
            content="实现用户认证",
            priority=1,
        )

        data = task.to_dict()
        assert data["id"] == "task-001"
        assert data["content"] == "实现用户认证"
        assert data["status"] == "pending"

    def test_task_from_dict(self):
        """测试从字典创建任务"""
        data = {
            "id": "task-001",
            "content": "实现用户认证",
            "priority": 1,
            "status": "in_progress",
            "phase_id": 2,
            "output_files": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "completed_at": None,
            "error_message": None,
            "retry_count": 0,
            "phase_name": None,
        }

        task = TaskItem.from_dict(data)
        assert task.id == "task-001"
        assert task.status == "in_progress"
        assert task.phase_id == 2


class TestTaskListManager:
    """任务列表管理器测试"""

    def test_init_session(self, temp_dir):
        """测试初始化会话"""
        manager = TaskListManager(temp_dir / "tasks.json")
        session_id = manager.init_session("实现登录功能")

        assert session_id is not None
        assert len(session_id) > 0
        assert manager.session_id == session_id

    def test_add_task(self, temp_dir):
        """测试添加任务"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        task = manager.add("编写登录 API", priority=1)

        assert task is not None
        assert task.content == "编写登录 API"
        assert task.priority == 1

    def test_update_task_status(self, temp_dir):
        """测试更新任务状态"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        task = manager.add("编写登录 API")
        manager.update_status(task.id, "in_progress")

        for t in manager.tasks:
            if t.id == task.id:
                assert t.status == "in_progress"
                break

    def test_complete_task(self, temp_dir):
        """测试完成任务"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        task = manager.add("编写登录 API")
        manager.complete_task(task.id)

        for t in manager.tasks:
            if t.id == task.id:
                assert t.status == "completed"
                assert t.completed_at is not None
                break

    def test_get_pending_tasks(self, temp_dir):
        """测试获取待处理任务"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        manager.add("任务 1")
        task2 = manager.add("任务 2")
        manager.add("任务 3")
        manager.complete_task(task2.id)

        pending = manager.get_pending()
        assert len(pending) == 2

    def test_persistence(self, temp_dir):
        """测试持久化"""
        task_file = temp_dir / "tasks.json"
        manager = TaskListManager(task_file)
        session_id = manager.init_session("实现登录功能")
        manager.add("任务 1")
        manager.add("任务 2")

        # 创建新管理器并加载
        manager2 = TaskListManager(task_file)

        assert len(manager2.tasks) == 2
        assert manager2.session_id == session_id

    def test_generate_reminder(self, temp_dir):
        """测试生成提醒"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        manager.add("高优先级任务", priority=10)
        manager.add("低优先级任务", priority=1)

        reminder = manager.generate_reminder()
        assert "高优先级任务" in reminder
        assert "低优先级任务" in reminder

    def test_get_progress(self, temp_dir):
        """测试获取进度"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")

        manager.add("任务 1")
        task2 = manager.add("任务 2")
        manager.complete_task(task2.id)

        progress = manager.get_progress()
        assert progress["total"] == 2
        assert progress["completed"] == 1
        assert progress["pending"] == 1


class TestReminderInjector:
    """任务提醒注入器测试"""

    def test_should_inject_interval(self, temp_dir):
        """测试注入间隔"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")
        manager.add("任务 1")

        injector = ReminderInjector(manager, inject_interval=3)

        assert not injector.should_inject()  # 1
        assert not injector.should_inject()  # 2
        assert injector.should_inject()      # 3
        assert not injector.should_inject()  # 4

    def test_inject_to_prompt(self, temp_dir):
        """测试注入到提示词"""
        manager = TaskListManager(temp_dir / "tasks.json")
        manager.init_session("实现登录功能")
        manager.add("实现功能 X", priority=1)

        injector = ReminderInjector(manager, inject_interval=1)
        injector.should_inject()  # 触发注入条件

        original_prompt = "请帮我写代码"
        injected = injector.inject_to_prompt(original_prompt)

        assert "task_reminder" in injected
        assert "请帮我写代码" in injected

    def test_no_inject_when_no_tasks(self, temp_dir):
        """测试无任务时不注入"""
        manager = TaskListManager(temp_dir / "tasks.json")

        injector = ReminderInjector(manager, inject_interval=1)
        injector.should_inject()

        original_prompt = "请帮我写代码"
        result = injector.inject_to_prompt(original_prompt)

        # 没有任务时不应该注入
        assert result == original_prompt

    def test_reset_counter(self, temp_dir):
        """测试重置计数"""
        manager = TaskListManager(temp_dir / "tasks.json")
        injector = ReminderInjector(manager, inject_interval=3)

        injector.should_inject()
        injector.should_inject()
        injector.reset()

        # 重置后从 0 开始
        assert not injector.should_inject()  # 1
