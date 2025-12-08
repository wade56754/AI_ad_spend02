"""
Orchestrator Base Class - 编排器抽象基类

提供多 Agent 协调和流程管理的通用框架。
"""

from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional
import logging

from .protocol import AgentProtocol, AgentContext
from .run import AgentRun, AgentRunStep, RunStatus
from .registry import get_registry
from .exceptions import AgentExecutionError

logger = logging.getLogger(__name__)


class OrchestratorBase(AgentProtocol):
    """
    Orchestrator 抽象基类。

    职责：
    - 定义流程路由（flow routing）
    - 协调多个 Agent 的执行顺序
    - 管理 AgentRun 生命周期
    - 提供钩子点用于扩展

    子类需要实现：
    - _register_flows(): 注册支持的流程
    - 各流程的具体实现方法

    使用示例：
    ```python
    class MyOrchestrator(OrchestratorBase):
        @property
        def name(self) -> str:
            return "my_orchestrator"

        def _register_flows(self) -> None:
            self._flows = {
                "full_pipeline": self._run_full_pipeline,
                "quick_check": self._run_quick_check,
            }

        def _run_full_pipeline(self, request, run, context):
            # 调用多个 Agent
            be_result = self._invoke_agent("be", {...}, run, context)
            fe_result = self._invoke_agent("fe", {...}, run, context)
            return {"backend": be_result, "frontend": fe_result}
    ```
    """

    def __init__(self):
        self._flows: Dict[str, Callable] = {}
        self._register_flows()

    @property
    def name(self) -> str:
        """默认名称，子类应覆盖"""
        return "orchestrator"

    @property
    def description(self) -> str:
        return "Base orchestrator for multi-agent coordination"

    @abstractmethod
    def _register_flows(self) -> None:
        """
        注册支持的流程。

        子类必须实现此方法，注册可用的流程到 self._flows 字典。

        Example:
            def _register_flows(self):
                self._flows = {
                    "full_pipeline": self._run_full_pipeline,
                    "backend_only": self._run_backend_only,
                }
        """
        ...

    def handle_request(
        self,
        request: Dict[str, Any],
        context: Optional[AgentContext] = None,
    ) -> Dict[str, Any]:
        """
        处理编排请求。

        Request 结构：
        {
            "flow": str,           # 流程类型（必需）
            "task": str,           # 任务描述
            "files": List[str],    # 相关文件
            "options": Dict,       # 流程特定选项
        }

        Returns:
            {
                "success": bool,
                "data": {
                    "flow": str,
                    "run_id": str,
                    "steps": List[Dict],
                    "result": Any,
                },
                "error": Optional[str],
            }
        """
        flow_type = request.get("flow", self._default_flow)

        if flow_type not in self._flows:
            return {
                "success": False,
                "error": f"Unknown flow: {flow_type}. Available: {list(self._flows.keys())}",
                "data": None,
            }

        # 创建执行上下文
        context = context or AgentContext()

        # 创建执行记录
        run = AgentRun(
            run_id=context.run_id,
            agent_name=self.name,
            flow_type=flow_type,
            input_request=request,
            metadata=context.metadata,
        )
        run.start()

        try:
            # 执行流程
            handler = self._flows[flow_type]
            result = handler(request, run, context)

            run.complete(result)

            return {
                "success": True,
                "data": {
                    "flow": flow_type,
                    "run_id": run.run_id,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "agent_name": s.agent_name,
                            "action": s.action,
                            "status": s.status.value,
                            "duration_ms": s.duration_ms,
                            "error": s.error,
                        }
                        for s in run.steps
                    ],
                    "result": result,
                },
                "error": None,
            }

        except Exception as e:
            logger.exception(f"Flow {flow_type} failed: {e}")
            run.fail(str(e))
            return {
                "success": False,
                "error": str(e),
                "data": {"run_id": run.run_id, "flow": flow_type},
            }

    @property
    def _default_flow(self) -> str:
        """默认流程名称（子类可覆盖）"""
        flows = list(self._flows.keys())
        return flows[0] if flows else "default"

    def _invoke_agent(
        self,
        agent_name: str,
        request: Dict[str, Any],
        run: AgentRun,
        context: AgentContext,
    ) -> Dict[str, Any]:
        """
        调用子 Agent 并记录步骤。

        子类流程实现中使用此方法调用其他 Agent。

        Args:
            agent_name: 要调用的 Agent 名称
            request: 传递给 Agent 的请求
            run: 当前 AgentRun 记录
            context: 执行上下文

        Returns:
            Agent 返回的响应

        Raises:
            AgentExecutionError: Agent 执行失败
        """
        action = request.get("action", "handle")
        step = run.add_step(agent_name, action)
        step.input_data = request
        step.start()

        try:
            # 从 Registry 获取 Agent
            agent = get_registry().create(agent_name)

            # 创建子上下文
            child_context = AgentContext(
                parent_run_id=context.run_id,
                user_id=context.user_id,
                metadata=context.metadata,
            )

            # 调用 Agent
            result = agent.handle_request(request, child_context)

            if result.get("success"):
                step.complete(result)
            else:
                step.fail(result.get("error", "Unknown error"))

            return result

        except Exception as e:
            error_msg = str(e)
            step.fail(error_msg)
            logger.error(f"Agent {agent_name} failed: {error_msg}")
            raise AgentExecutionError(agent_name, error_msg, run.run_id) from e

    @property
    def available_flows(self) -> List[str]:
        """列出可用的流程类型"""
        return list(self._flows.keys())

    def validate_request(self, request: Dict[str, Any]) -> Optional[str]:
        """校验请求"""
        flow = request.get("flow", self._default_flow)
        if flow not in self._flows:
            return f"Unknown flow: {flow}. Available: {self.available_flows}"
        return None
