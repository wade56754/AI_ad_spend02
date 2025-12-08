"""
Agent Run Models - Agent 执行记录

提供 AgentRun 和 AgentRunStep 用于记录和追溯 Agent 执行过程。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class RunStatus(str, Enum):
    """执行状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStep(BaseModel):
    """
    单步执行记录。

    记录 Agent 调用链中每一步的输入、输出、状态和耗时。
    """

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    action: str = ""
    status: RunStatus = RunStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    model_config = {"frozen": False}

    def start(self) -> None:
        """标记步骤开始"""
        self.status = RunStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, output: Dict[str, Any]) -> None:
        """标记步骤完成"""
        self.status = RunStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.utcnow()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def fail(self, error: str) -> None:
        """标记步骤失败"""
        self.status = RunStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


class AgentRun(BaseModel):
    """
    完整的 Agent 执行记录。

    用途：
    - 追溯：记录完整的执行链路
    - 调试：保存输入输出用于问题排查
    - 监控：统计执行时间、成功率
    - 恢复：失败后可基于记录重试
    """

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    flow_type: str = ""  # 例如 "full_pipeline", "backend_only"
    status: RunStatus = RunStatus.PENDING

    # 执行链路
    steps: List[AgentRunStep] = Field(default_factory=list)

    # 输入输出
    input_request: Dict[str, Any] = Field(default_factory=dict)
    final_output: Dict[str, Any] = Field(default_factory=dict)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}

    def add_step(self, agent_name: str, action: str) -> AgentRunStep:
        """添加一个执行步骤"""
        step = AgentRunStep(agent_name=agent_name, action=action)
        self.steps.append(step)
        return step

    def start(self) -> None:
        """标记运行开始"""
        self.status = RunStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, output: Dict[str, Any]) -> None:
        """标记运行完成"""
        self.status = RunStatus.COMPLETED
        self.final_output = output
        self.completed_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        """标记运行失败"""
        self.status = RunStatus.FAILED
        self.final_output = {"error": error}
        self.completed_at = datetime.utcnow()

    @property
    def duration_ms(self) -> Optional[int]:
        """计算总耗时（毫秒）"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    def to_summary(self) -> Dict[str, Any]:
        """生成执行摘要（用于日志/API 响应）"""
        return {
            "run_id": self.run_id,
            "agent_name": self.agent_name,
            "flow_type": self.flow_type,
            "status": self.status.value,
            "steps_count": len(self.steps),
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def to_detail(self) -> Dict[str, Any]:
        """生成完整详情（包含所有步骤）"""
        return {
            **self.to_summary(),
            "steps": [
                {
                    "step_id": s.step_id,
                    "agent_name": s.agent_name,
                    "action": s.action,
                    "status": s.status.value,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "input_request": self.input_request,
            "final_output": self.final_output,
        }
