"""
任务列表管理器 - 借鉴 Anthropic feature_list.json 模式

核心设计:
- task_list.json 作为唯一真相源
- 任务只能 pending → completed，禁止删除或修改
- 支持优先级排序
- 支持会话间持久化

来源: Anthropic autonomous-coding
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskCategory(Enum):
    """任务类别"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    API = "api"
    TEST = "test"
    DOCS = "docs"
    CONFIG = "config"


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Task:
    """单个任务定义"""
    id: str
    description: str
    category: str
    priority: int = 3
    status: str = "pending"

    # 代码工厂 5 阶段追踪
    search_completed: bool = False
    select_completed: bool = False
    adapt_completed: bool = False
    assemble_completed: bool = False
    verify_completed: bool = False

    # 验收标准
    acceptance_criteria: List[str] = field(default_factory=list)

    # 参考来源
    source_refs: List[str] = field(default_factory=list)

    # 输出文件
    output_files: List[str] = field(default_factory=list)

    # 时间戳
    created_at: str = ""
    completed_at: str = ""

    # 失败信息
    error_message: str = ""
    retry_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(**data)

    def is_ready(self) -> bool:
        """检查任务是否可以开始"""
        return self.status == TaskStatus.PENDING.value

    def is_completed(self) -> bool:
        """检查任务是否完成"""
        return self.status == TaskStatus.COMPLETED.value

    def mark_phase_complete(self, phase: str) -> None:
        """标记某个阶段完成"""
        phase_map = {
            "search": "search_completed",
            "select": "select_completed",
            "adapt": "adapt_completed",
            "assemble": "assemble_completed",
            "verify": "verify_completed",
        }
        if phase in phase_map:
            setattr(self, phase_map[phase], True)

    def get_current_phase(self) -> str:
        """获取当前阶段"""
        if not self.search_completed:
            return "search"
        if not self.select_completed:
            return "select"
        if not self.adapt_completed:
            return "adapt"
        if not self.assemble_completed:
            return "assemble"
        if not self.verify_completed:
            return "verify"
        return "done"


class TaskList:
    """
    任务列表管理器

    核心原则 (借鉴 Anthropic):
    - 任务只能 pending → completed
    - 禁止删除任务
    - 禁止修改任务描述
    - 任务列表是唯一真相源
    """

    TASK_LIST_FILE = "task_list.json"

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.task_file = self.project_dir / self.TASK_LIST_FILE
        self.tasks: List[Task] = []
        self._load()

    def _load(self) -> None:
        """加载任务列表"""
        if self.task_file.exists():
            try:
                with open(self.task_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Failed to load task list: {e}")
                self.tasks = []

    def _save(self) -> None:
        """保存任务列表"""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "3.0",
            "updated_at": datetime.now().isoformat(),
            "total_tasks": len(self.tasks),
            "completed_tasks": self.count_completed(),
            "tasks": [t.to_dict() for t in self.tasks],
        }
        with open(self.task_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_task(self, task: Task) -> None:
        """添加任务 (仅在初始化阶段使用)"""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task {task.id} already exists")
        self.tasks.append(task)
        self._save()

    def add_tasks(self, tasks: List[Task]) -> None:
        """批量添加任务"""
        for task in tasks:
            if not any(t.id == task.id for t in self.tasks):
                self.tasks.append(task)
        self._save()

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_next_task(self) -> Optional[Task]:
        """获取下一个待执行任务 (按优先级排序)"""
        pending = [t for t in self.tasks if t.status == TaskStatus.PENDING.value]
        if not pending:
            return None
        return sorted(pending, key=lambda t: t.priority)[0]

    def get_in_progress_task(self) -> Optional[Task]:
        """获取正在执行的任务"""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS.value:
                return task
        return None

    def start_task(self, task_id: str) -> bool:
        """开始任务"""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.PENDING.value:
            task.status = TaskStatus.IN_PROGRESS.value
            self._save()
            return True
        return False

    def complete_task(self, task_id: str, output_files: List[str] = None) -> bool:
        """
        完成任务

        重要: 任务只能从 in_progress → completed
        """
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.IN_PROGRESS.value:
            task.status = TaskStatus.COMPLETED.value
            task.completed_at = datetime.now().isoformat()
            if output_files:
                task.output_files = output_files
            self._save()
            return True
        return False

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.FAILED.value
            task.error_message = error
            task.retry_count += 1
            self._save()
            return True
        return False

    def retry_task(self, task_id: str) -> bool:
        """重试失败的任务"""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.FAILED.value and task.retry_count < 3:
            task.status = TaskStatus.PENDING.value
            self._save()
            return True
        return False

    def update_phase(self, task_id: str, phase: str) -> bool:
        """更新任务阶段进度"""
        task = self.get_task(task_id)
        if task:
            task.mark_phase_complete(phase)
            self._save()
            return True
        return False

    def count_completed(self) -> int:
        """统计已完成任务数"""
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED.value)

    def count_pending(self) -> int:
        """统计待执行任务数"""
        return sum(1 for t in self.tasks if t.status == TaskStatus.PENDING.value)

    def get_progress(self) -> Dict[str, Any]:
        """获取整体进度"""
        total = len(self.tasks)
        completed = self.count_completed()
        pending = self.count_pending()
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS.value)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED.value)

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "failed": failed,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
        }

    def get_summary(self) -> str:
        """获取进度摘要"""
        progress = self.get_progress()
        return (
            f"任务进度: {progress['completed']}/{progress['total']} "
            f"({progress['progress_pct']}%) | "
            f"进行中: {progress['in_progress']} | "
            f"失败: {progress['failed']}"
        )

    def exists(self) -> bool:
        """检查任务列表是否存在"""
        return self.task_file.exists()

    def is_all_completed(self) -> bool:
        """检查是否全部完成"""
        return all(t.status == TaskStatus.COMPLETED.value for t in self.tasks)


def generate_api_tasks(requirement: str, scope: str = "backend") -> List[Task]:
    """
    根据需求生成 API 开发任务列表

    这是一个示例生成器，实际使用时会由 AI 生成更详细的任务
    """
    tasks = []
    base_id = requirement.replace(" ", "_").lower()[:20]

    if scope in ["backend", "fullstack"]:
        # Schema 任务
        tasks.append(Task(
            id=f"{base_id}_schema",
            description=f"创建 {requirement} 的 Pydantic Schema",
            category="backend",
            priority=1,
            acceptance_criteria=[
                "Schema 使用 Pydantic v2 语法",
                "包含 model_config = ConfigDict(from_attributes=True)",
                "字段类型与 DATA_SCHEMA.md 一致",
            ],
        ))

        # Service 任务
        tasks.append(Task(
            id=f"{base_id}_service",
            description=f"实现 {requirement} 的 Service 层",
            category="backend",
            priority=2,
            acceptance_criteria=[
                "使用 success_response() 包装响应",
                "错误使用 BusinessError + ERROR_CODES_SOT",
                "状态转换符合 STATE_MACHINE.md",
            ],
        ))

        # Router 任务
        tasks.append(Task(
            id=f"{base_id}_router",
            description=f"实现 {requirement} 的 Router 层",
            category="backend",
            priority=3,
            acceptance_criteria=[
                "路由命名符合 API_SOT.md",
                "使用依赖注入获取当前用户",
                "权限检查符合 AUTH_SPEC.md",
            ],
        ))

        # 测试任务
        tasks.append(Task(
            id=f"{base_id}_test",
            description=f"编写 {requirement} 的单元测试",
            category="test",
            priority=4,
            acceptance_criteria=[
                "覆盖正常和异常场景",
                "使用 pytest fixture",
                "Mock 外部依赖",
            ],
        ))

    if scope in ["frontend", "fullstack"]:
        # Types 任务
        tasks.append(Task(
            id=f"{base_id}_types",
            description=f"创建 {requirement} 的 TypeScript 类型",
            category="frontend",
            priority=1,
            acceptance_criteria=[
                "类型与后端 Schema 一致",
                "使用严格模式",
            ],
        ))

        # API Service 任务
        tasks.append(Task(
            id=f"{base_id}_api",
            description=f"实现 {requirement} 的前端 API 调用",
            category="frontend",
            priority=2,
            acceptance_criteria=[
                "使用 apiFetch 封装",
                "处理错误响应",
            ],
        ))

        # Hooks 任务
        tasks.append(Task(
            id=f"{base_id}_hooks",
            description=f"实现 {requirement} 的 TanStack Query Hooks",
            category="frontend",
            priority=3,
            acceptance_criteria=[
                "使用 useQuery/useMutation",
                "配置正确的 queryKey",
                "处理 loading/error 状态",
            ],
        ))

        # Component 任务
        tasks.append(Task(
            id=f"{base_id}_component",
            description=f"实现 {requirement} 的 UI 组件",
            category="frontend",
            priority=4,
            acceptance_criteria=[
                "使用 shadcn/ui 组件",
                "响应式设计",
                "符合项目风格",
            ],
        ))

    return tasks
