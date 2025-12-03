基于探索结果，我来设计 Agent 平台模块化方案。

  1. 建议的 /agent_platform/ 目录结构

  AI_ad_spend02/
  ├── agent_platform/                    # 🆕 可独立拆分的通用 Agent 平台
  │   ├── pyproject.toml                 # 独立的包定义
  │   ├── README.md                      # 平台文档
  │   ├── __init__.py                    # 版本号、公开 API
  │   │
  │   ├── core/                          # 核心抽象层（与业务无关）
  │   │   ├── __init__.py
  │   │   ├── protocol.py                # AgentProtocol 抽象基类
  │   │   ├── registry.py                # 插件注册中心
  │   │   ├── orchestrator.py            # 通用 Orchestrator 抽象
  │   │   ├── run.py                     # AgentRun / AgentRunStep 模型
  │   │   └── exceptions.py              # 平台级异常定义
  │   │
  │   ├── llm/                           # LLM 客户端抽象
  │   │   ├── __init__.py
  │   │   ├── base.py                    # LLMClient 抽象基类
  │   │   ├── anthropic_client.py        # Anthropic API 实现
  │   │   ├── claude_code_adapter.py     # Claude Code CLI 适配器
  │   │   ├── factory.py                 # get_llm_client() 工厂
  │   │   └── types.py                   # LLM 相关类型
  │   │
  │   ├── tools/                         # 通用工具（与业务无关）
  │   │   ├── __init__.py
  │   │   ├── fs_tool.py                 # 文件系统工具
  │   │   ├── validation.py              # 通用校验
  │   │   └── types.py                   # AgentResponse, SkillResult 等
  │   │
  │   ├── server/                        # HTTP 服务层
  │   │   ├── __init__.py
  │   │   ├── app.py                     # FastAPI 应用
  │   │   ├── routes.py                  # 路由定义
  │   │   └── middleware.py              # 中间件（限流、CORS）
  │   │
  │   ├── cli/                           # 命令行接口
  │   │   ├── __init__.py
  │   │   └── main.py                    # CLI 入口
  │   │
  │   └── contrib/                       # 🆕 官方插件示例（可选）
  │       └── __init__.py
  │
  ├── agents/                            # 🔄 重构为 AI_ad_spend 专属插件
  │   ├── __init__.py                    # 注册入口
  │   ├── plugin.py                      # 🆕 插件注册逻辑
  │   ├── config.py                      # 🔄 项目级配置（SOT_FILES 等）
  │   │
  │   ├── ai_ad_spend/                   # 🆕 业务 Agent 插件包
  │   │   ├── __init__.py
  │   │   ├── fe_agent.py                # FE Agent（移入）
  │   │   ├── be_agent.py                # BE Agent（移入）
  │   │   ├── test_agent.py              # Test Agent（移入）
  │   │   ├── doc_agent.py               # Doc Agent（移入）
  │   │   ├── code_review_agent.py       # Code Review Agent（移入）
  │   │   └── orchestrator.py            # 🔄 业务 Orchestrator（继承平台抽象）
  │   │
  │   ├── skills/                        # 业务 Skills（保留）
  │   │   ├── __init__.py
  │   │   ├── be_dev_skill.py
  │   │   ├── fe_dev_skill.py
  │   │   ├── db_test_skill.py
  │   │   ├── backend_test_skill.py
  │   │   └── sot_guard_skill.py
  │   │
  │   └── tests/                         # 业务 Agent 测试
  │       └── ...
  │
  └── ...（其他项目文件）

  2. 核心抽象接口设计

  2.1 AgentProtocol（核心协议）

  # agent_platform/core/protocol.py
  from abc import ABC, abstractmethod
  from typing import Any, Dict, Optional
  from dataclasses import dataclass, field
  from datetime import datetime
  import uuid

  @dataclass
  class AgentContext:
      """Agent 执行上下文"""
      run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
      parent_run_id: Optional[str] = None
      user_id: Optional[str] = None
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: datetime = field(default_factory=datetime.utcnow)


  class AgentProtocol(ABC):
      """
      所有 Agent 必须实现的协议。

      设计原则：
      - 无状态：每次调用独立，不依赖实例变量存储状态
      - 可追溯：通过 AgentContext 传递 run_id 用于日志关联
      - 可插拔：通过 registry 动态注册/发现
      """

      @property
      @abstractmethod
      def name(self) -> str:
          """Agent 唯一标识符（用于注册）"""
          ...

      @property
      def description(self) -> str:
          """Agent 描述（用于文档/发现）"""
          return ""

      @property
      def version(self) -> str:
          """Agent 版本号"""
          return "1.0.0"

      @abstractmethod
      def handle_request(
          self,
          request: Dict[str, Any],
          context: Optional[AgentContext] = None
      ) -> Dict[str, Any]:
          """
          处理请求的主入口。

          Args:
              request: 请求参数，结构由具体 Agent 定义
              context: 执行上下文（可选，用于追溯）

          Returns:
              标准响应：{"success": bool, "data": Any, "error": Optional[str]}
          """
          ...

      def validate_request(self, request: Dict[str, Any]) -> Optional[str]:
          """
          请求校验（可选重写）。

          Returns:
              None 表示校验通过，否则返回错误信息
          """
          return None

  2.2 AgentRun / AgentRunStep（执行记录模型）

  # agent_platform/core/run.py
  from dataclasses import dataclass, field
  from datetime import datetime
  from typing import Any, Dict, List, Optional
  from enum import Enum
  import uuid


  class RunStatus(str, Enum):
      PENDING = "pending"
      RUNNING = "running"
      COMPLETED = "completed"
      FAILED = "failed"
      CANCELLED = "cancelled"


  @dataclass
  class AgentRunStep:
      """单步执行记录"""
      step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
      agent_name: str = ""
      action: str = ""
      status: RunStatus = RunStatus.PENDING
      input_data: Dict[str, Any] = field(default_factory=dict)
      output_data: Dict[str, Any] = field(default_factory=dict)
      error: Optional[str] = None
      started_at: Optional[datetime] = None
      completed_at: Optional[datetime] = None
      duration_ms: Optional[int] = None

      def start(self):
          self.status = RunStatus.RUNNING
          self.started_at = datetime.utcnow()

      def complete(self, output: Dict[str, Any]):
          self.status = RunStatus.COMPLETED
          self.output_data = output
          self.completed_at = datetime.utcnow()
          if self.started_at:
              self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

      def fail(self, error: str):
          self.status = RunStatus.FAILED
          self.error = error
          self.completed_at = datetime.utcnow()


  @dataclass
  class AgentRun:
      """
      完整的 Agent 执行记录。

      用途：
      - 追溯：记录完整的执行链路
      - 调试：保存输入输出用于问题排查
      - 监控：统计执行时间、成功率
      - 恢复：失败后可基于记录重试
      """
      run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
      agent_name: str = ""
      flow_type: str = ""  # 例如 "full_pipeline", "backend_only"
      status: RunStatus = RunStatus.PENDING

      # 执行链路
      steps: List[AgentRunStep] = field(default_factory=list)

      # 输入输出
      input_request: Dict[str, Any] = field(default_factory=dict)
      final_output: Dict[str, Any] = field(default_factory=dict)

      # 时间戳
      created_at: datetime = field(default_factory=datetime.utcnow)
      started_at: Optional[datetime] = None
      completed_at: Optional[datetime] = None

      # 元数据
      metadata: Dict[str, Any] = field(default_factory=dict)

      def add_step(self, agent_name: str, action: str) -> AgentRunStep:
          step = AgentRunStep(agent_name=agent_name, action=action)
          self.steps.append(step)
          return step

      def to_dict(self) -> Dict[str, Any]:
          """序列化为字典（用于存储/传输）"""
          return {
              "run_id": self.run_id,
              "agent_name": self.agent_name,
              "flow_type": self.flow_type,
              "status": self.status.value,
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
              "created_at": self.created_at.isoformat(),
              "completed_at": self.completed_at.isoformat() if self.completed_at else None,
          }

  2.3 Registry（插件注册中心）

  # agent_platform/core/registry.py
  from typing import Callable, Dict, List, Optional, Type
  from dataclasses import dataclass
  import logging

  from .protocol import AgentProtocol

  logger = logging.getLogger(__name__)


  @dataclass
  class AgentMeta:
      """Agent 元信息"""
      name: str
      factory: Callable[..., AgentProtocol]
      description: str = ""
      version: str = "1.0.0"
      tags: List[str] = None  # 例如 ["frontend", "codegen"]

      def __post_init__(self):
          if self.tags is None:
              self.tags = []


  class AgentRegistry:
      """
      Agent 插件注册中心（单例模式）。

      使用方式：
      ```python
      # 注册 Agent
      registry = AgentRegistry.instance()
      registry.register("fe", FEAgent, description="Frontend Agent")

      # 发现 Agent
      agent = registry.create("fe", config={"model": "claude-3"})

      # 列出所有 Agent
      for meta in registry.list_agents():
          print(f"{meta.name}: {meta.description}")
      ```
      """

      _instance: Optional["AgentRegistry"] = None

      def __init__(self):
          self._agents: Dict[str, AgentMeta] = {}

      @classmethod
      def instance(cls) -> "AgentRegistry":
          if cls._instance is None:
              cls._instance = cls()
          return cls._instance

      @classmethod
      def reset(cls):
          """重置注册表（用于测试）"""
          cls._instance = None

      def register(
          self,
          name: str,
          factory: Callable[..., AgentProtocol],
          *,
          description: str = "",
          version: str = "1.0.0",
          tags: List[str] = None,
          override: bool = False,
      ) -> None:
          """
          注册 Agent。

          Args:
              name: 唯一标识符
              factory: Agent 工厂函数或类
              description: 描述
              version: 版本号
              tags: 标签（用于分类筛选）
              override: 是否允许覆盖已注册的同名 Agent
          """
          if name in self._agents and not override:
              raise ValueError(f"Agent '{name}' already registered. Use override=True to replace.")

          self._agents[name] = AgentMeta(
              name=name,
              factory=factory,
              description=description,
              version=version,
              tags=tags or [],
          )
          logger.info(f"Registered agent: {name} (v{version})")

      def unregister(self, name: str) -> bool:
          """注销 Agent"""
          if name in self._agents:
              del self._agents[name]
              logger.info(f"Unregistered agent: {name}")
              return True
          return False

      def get(self, name: str) -> Optional[AgentMeta]:
          """获取 Agent 元信息"""
          return self._agents.get(name)

      def create(self, name: str, **kwargs) -> AgentProtocol:
          """
          创建 Agent 实例。

          Args:
              name: Agent 名称
              **kwargs: 传递给工厂函数的参数

          Returns:
              Agent 实例

          Raises:
              KeyError: Agent 未注册
          """
          meta = self._agents.get(name)
          if meta is None:
              available = ", ".join(self._agents.keys())
              raise KeyError(f"Agent '{name}' not found. Available: {available}")

          return meta.factory(**kwargs)

      def list_agents(self, tag: Optional[str] = None) -> List[AgentMeta]:
          """
          列出已注册的 Agent。

          Args:
              tag: 按标签筛选（可选）
          """
          agents = list(self._agents.values())
          if tag:
              agents = [a for a in agents if tag in a.tags]
          return agents

      def has(self, name: str) -> bool:
          """检查 Agent 是否已注册"""
          return name in self._agents


  # 便捷函数
  def get_registry() -> AgentRegistry:
      return AgentRegistry.instance()


  def register_agent(
      name: str,
      factory: Callable[..., AgentProtocol],
      **kwargs
  ) -> None:
      get_registry().register(name, factory, **kwargs)


  def create_agent(name: str, **kwargs) -> AgentProtocol:
      return get_registry().create(name, **kwargs)

  2.4 Orchestrator 抽象基类

  # agent_platform/core/orchestrator.py
  from abc import abstractmethod
  from typing import Any, Callable, Dict, List, Optional
  import logging

  from .protocol import AgentProtocol, AgentContext
  from .run import AgentRun, AgentRunStep, RunStatus
  from .registry import get_registry

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
      """

      def __init__(self):
          self._flows: Dict[str, Callable] = {}
          self._register_flows()

      @property
      def name(self) -> str:
          return "orchestrator"

      @abstractmethod
      def _register_flows(self) -> None:
          """
          注册支持的流程。

          子类实现示例：
          ```python
          def _register_flows(self):
              self._flows = {
                  "full_pipeline": self._run_full_pipeline,
                  "backend_only": self._run_backend_only,
              }
          ```
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
          """
          flow_type = request.get("flow", "full_pipeline")

          if flow_type not in self._flows:
              return {
                  "success": False,
                  "error": f"Unknown flow: {flow_type}. Available: {list(self._flows.keys())}",
              }

          # 创建执行记录
          context = context or AgentContext()
          run = AgentRun(
              run_id=context.run_id,
              agent_name=self.name,
              flow_type=flow_type,
              input_request=request,
              metadata=context.metadata,
          )
          run.status = RunStatus.RUNNING
          run.started_at = run.created_at

          try:
              # 执行流程
              handler = self._flows[flow_type]
              result = handler(request, run, context)

              run.status = RunStatus.COMPLETED
              run.final_output = result

              return {
                  "success": True,
                  "data": {
                      "flow": flow_type,
                      "run_id": run.run_id,
                      "steps": run.to_dict()["steps"],
                      "result": result,
                  },
              }

          except Exception as e:
              logger.exception(f"Flow {flow_type} failed")
              run.status = RunStatus.FAILED
              return {
                  "success": False,
                  "error": str(e),
                  "data": {"run_id": run.run_id},
              }

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
          """
          step = run.add_step(agent_name, request.get("action", "handle"))
          step.input_data = request
          step.start()

          try:
              agent = get_registry().create(agent_name)
              child_context = AgentContext(
                  parent_run_id=context.run_id,
                  user_id=context.user_id,
                  metadata=context.metadata,
              )
              result = agent.handle_request(request, child_context)

              if result.get("success"):
                  step.complete(result)
              else:
                  step.fail(result.get("error", "Unknown error"))

              return result

          except Exception as e:
              step.fail(str(e))
              raise

      @property
      def available_flows(self) -> List[str]:
          """列出可用的流程类型"""
          return list(self._flows.keys())

  3. 迁移方案

  3.1 迁移步骤

  Phase 1: 创建 agent_platform 骨架（不影响现有代码）
  ├── 创建目录结构
  ├── 实现 core/protocol.py, registry.py, run.py
  ├── 迁移 tools/llm_client.py → agent_platform/llm/
  └── 添加 agent_platform/pyproject.toml

  Phase 2: 适配现有 Agent（渐进式）
  ├── agents/plugin.py 中注册所有 Agent 到新 registry
  ├── 现有 Agent 继承 AgentProtocol（已兼容）
  ├── agents_config.py 改为调用 agent_platform.registry
  └── 保持 CLI/Server 入口不变

  Phase 3: 重构 Orchestrator
  ├── 创建 agent_platform/core/orchestrator.py 抽象基类
  ├── agents/ai_ad_spend/orchestrator.py 继承抽象基类
  └── 迁移流程实现代码

  Phase 4: 清理与文档
  ├── 删除冗余代码
  ├── 更新 import 路径
  └── 编写迁移文档

  3.2 关键文件变更清单

  | 现有文件                                | 迁移目标                                      | 变更类型       |
  |-------------------------------------|-------------------------------------------|------------|
  | agents/tools/llm_client.py          | agent_platform/llm/factory.py             | 移动         |
  | agents/tools/claude_code_adapter.py | agent_platform/llm/claude_code_adapter.py | 移动         |
  | agents/tools/types.py               | agent_platform/tools/types.py             | 移动         |
  | agents/tools/fs_tool.py             | agent_platform/tools/fs_tool.py           | 移动         |
  | agents/tools/validation.py          | agent_platform/tools/validation.py        | 移动         |
  | agents/agents_config.py             | agents/config.py                          | 重构（保留业务配置） |
  | agents/agent_core/*.py              | agents/ai_ad_spend/*.py                   | 移动         |
  | agents/cli.py                       | agent_platform/cli/main.py                | 移动 + 适配    |
  | agents/server.py                    | agent_platform/server/app.py              | 移动 + 适配    |
  | agents/skills/*.py                  | agents/skills/*.py                        | 保留（业务相关）   |

  3.3 插件注册入口

  # agents/plugin.py
  """
  AI_ad_spend02 专属 Agent 插件包。

  在应用启动时调用 register_all() 注册所有业务 Agent。
  """
  from agent_platform.core.registry import register_agent

  def register_all():
      """注册所有 AI_ad_spend Agent 到平台"""

      # 延迟导入避免循环依赖
      from .ai_ad_spend.fe_agent import FEAgent
      from .ai_ad_spend.be_agent import BEAgent
      from .ai_ad_spend.test_agent import TestAgent
      from .ai_ad_spend.doc_agent import DocAgent
      from .ai_ad_spend.code_review_agent import CodeReviewAgent
      from .ai_ad_spend.orchestrator import AIAdSpendOrchestrator

      register_agent(
          "fe",
          FEAgent,
          description="Frontend TSX/React code generation",
          tags=["codegen", "frontend"],
      )

      register_agent(
          "be",
          BEAgent,
          description="Backend FastAPI code generation",
          tags=["codegen", "backend"],
      )

      register_agent(
          "test",
          TestAgent,
          description="Test prompt generation (DB/Backend)",
          tags=["testing"],
      )

      register_agent(
          "doc",
          DocAgent,
          description="Documentation generation",
          tags=["documentation"],
      )

      register_agent(
          "review",
          CodeReviewAgent,
          description="Code review with SoT compliance",
          tags=["review", "sot"],
      )

      register_agent(
          "orch",
          AIAdSpendOrchestrator,
          description="AI Ad Spend orchestrator (BE→FE→Test pipeline)",
          tags=["orchestrator"],
      )


  # 自动注册（导入时执行）
  register_all()

  3.4 业务 Orchestrator 示例

  # agents/ai_ad_spend/orchestrator.py
  from agent_platform.core.orchestrator import OrchestratorBase
  from agent_platform.core.run import AgentRun
  from agent_platform.core.protocol import AgentContext
  from typing import Any, Dict

  from ..config import SOT_FILES, FRONTEND_RESTRUCTURE_FILES


  class AIAdSpendOrchestrator(OrchestratorBase):
      """
      AI_ad_spend02 专属 Orchestrator。

      支持的流程：
      - full_pipeline: BE → FE → Test 完整流水线
      - backend_only: 仅后端生成
      - frontend_only: 仅前端生成
      - frontend_restructure: 7 步前端重构
      - auto_fix: 生成 → 测试 → 修复循环
      """

      @property
      def name(self) -> str:
          return "ai_ad_spend_orchestrator"

      @property
      def description(self) -> str:
          return "AI Ad Spend project orchestrator with SoT-aligned pipelines"

      def _register_flows(self) -> None:
          self._flows = {
              "full_pipeline": self._run_full_pipeline,
              "backend_only": self._run_backend_only,
              "frontend_only": self._run_frontend_only,
              "frontend_restructure": self._run_frontend_restructure,
              "auto_fix": self._run_auto_fix,
          }

      def _run_full_pipeline(
          self,
          request: Dict[str, Any],
          run: AgentRun,
          context: AgentContext,
      ) -> Dict[str, Any]:
          """BE → FE → Test 完整流水线"""
          results = {}

          # Step 1: Backend
          be_result = self._invoke_agent("be", {
              "action": request.get("task"),
              "files": request.get("files", []),
          }, run, context)
          results["backend"] = be_result

          if not be_result.get("success"):
              return {"partial": True, "results": results}

          # Step 2: Frontend
          fe_result = self._invoke_agent("fe", {
              "action": request.get("task"),
              "files": request.get("files", []),
          }, run, context)
          results["frontend"] = fe_result

          # Step 3: Test (prompt only)
          test_result = self._invoke_agent("test", {
              "mode": "backend",
              "context": request.get("task"),
          }, run, context)
          results["test"] = test_result

          return {"results": results}

      def _run_backend_only(self, request, run, context):
          return self._invoke_agent("be", request, run, context)

      def _run_frontend_only(self, request, run, context):
          return self._invoke_agent("fe", request, run, context)

      def _run_frontend_restructure(self, request, run, context):
          """7 步前端重构流程"""
          # 实现 SC-ORCH 7 步流程...
          pass

      def _run_auto_fix(self, request, run, context):
          """生成 → 测试 → 修复循环 (P1-01)"""
          # 实现 auto-fix 循环...
          pass

  4. 拆仓库影响评估

  4.1 拆分后的仓库结构

  # 仓库 A: agent-platform (独立 PyPI 包)
  agent-platform/
  ├── pyproject.toml              # name = "agent-platform"
  ├── agent_platform/
  │   ├── core/
  │   ├── llm/
  │   ├── tools/
  │   ├── server/
  │   └── cli/
  └── tests/

  # 仓库 B: AI_ad_spend02 (业务项目)
  AI_ad_spend02/
  ├── pyproject.toml              # dependencies = ["agent-platform>=1.0"]
  ├── agents/
  │   ├── plugin.py               # 注册到 agent-platform
  │   ├── config.py               # SOT_FILES 等业务配置
  │   ├── ai_ad_spend/            # 业务 Agent
  │   └── skills/                 # 业务 Skills
  ├── backend/
  ├── frontend/
  └── docs/

  4.2 需要修改的地方

  | 修改类别      | 修改内容                                                   | 工作量 |
  |-----------|--------------------------------------------------------|-----|
  | Import 路径 | from agents.tools.llm_client → from agent_platform.llm | 低   |
  | 依赖声明      | pyproject.toml 添加 agent-platform 依赖                    | 低   |
  | 入口调整      | CLI/Server 改为调用 agent-platform 提供的入口                   | 中   |
  | 配置分离      | SOT_FILES 等业务配置留在 agents/config.py                     | 低   |
  | 测试拆分      | 平台测试 vs 业务测试分开                                         | 中   |
  | 文档更新      | 更新 README 和使用指南                                        | 低   |

  4.3 拆分检查清单

  ## 拆仓库前检查清单

  ### 代码边界
  - [ ] agent_platform 不依赖任何 agents/ 下的代码
  - [ ] agent_platform 不依赖 backend/, frontend/, docs/
  - [ ] agents/ 只通过公开 API 使用 agent_platform

  ### 配置分离
  - [ ] SOT_FILES 在 agents/config.py 中定义
  - [ ] LLM_CONFIG 可在 agent_platform 外部覆盖
  - [ ] 环境变量名无冲突

  ### 测试覆盖
  - [ ] agent_platform 有独立的单元测试
  - [ ] 集成测试可在两个仓库各自运行

  ### 版本兼容
  - [ ] agent_platform 版本号遵循 SemVer
  - [ ] 定义好 API 稳定性承诺（哪些是公开 API）

  5. 依赖关系图

  ┌─────────────────────────────────────────────────────────────────┐
  │                        AI_ad_spend02                            │
  │  ┌───────────────────────────────────────────────────────────┐  │
  │  │                    agents/ (插件层)                        │  │
  │  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
  │  │  │ ai_ad_spend/│  │   skills/    │  │     config.py    │  │  │
  │  │  │  FEAgent    │  │ sot_guard    │  │  - SOT_FILES     │  │  │
  │  │  │  BEAgent    │  │ be_dev_skill │  │  - PROJECT_ROOT  │  │  │
  │  │  │  TestAgent  │  │ fe_dev_skill │  │  - LLM overrides │  │  │
  │  │  │  DocAgent   │  │ db_test_skill│  │                  │  │  │
  │  │  │  Orchestr.  │  │              │  │                  │  │  │
  │  │  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │  │
  │  │         │                │                    │            │  │
  │  │         │     plugin.py (注册到平台)          │            │  │
  │  │         └────────────────┼────────────────────┘            │  │
  │  └──────────────────────────┼────────────────────────────────┘  │
  │                             │                                    │
  │                             ▼                                    │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │              agent_platform/ (可独立拆分)                 │   │
  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │
  │  │  │  core/   │  │   llm/   │  │  tools/  │  │ server/  │  │   │
  │  │  │ protocol │  │ factory  │  │ fs_tool  │  │ FastAPI  │  │   │
  │  │  │ registry │  │ anthropic│  │ types    │  │ routes   │  │   │
  │  │  │orchestr. │  │ claude   │  │ validate │  │          │  │   │
  │  │  │   run    │  │          │  │          │  │          │  │   │
  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │   │
  │  └──────────────────────────────────────────────────────────┘   │
  │                             │                                    │
  │                             ▼                                    │
  │                    ┌─────────────────┐                          │
  │                    │ External Deps   │                          │
  │                    │ - anthropic     │                          │
  │                    │ - fastapi       │                          │
  │                    │ - pydantic      │                          │
  │                    └─────────────────┘                          │
  └─────────────────────────────────────────────────────────────────┘

  ---
  总结

  | 维度     | 设计决策                                         |
  |--------|----------------------------------------------|
  | 边界原则   | agent_platform 只包含通用、可复用的基础设施；业务逻辑留在 agents/ |
  | 注册机制   | 插件式注册（agents/plugin.py），平台对业务 Agent 零依赖      |
  | LLM 抽象 | 保持现有双后端策略，移入 agent_platform/llm/             |
  | 执行追溯   | 新增 AgentRun/AgentRunStep 模型，支持全链路追踪          |
  | 拆分成本   | 低（主要是 import 路径变更），约 1-2 天工作量                |
