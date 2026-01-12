"""
代码工厂主编排器

整合所有组件：插件、代理、技能、工具、工作流

版本: v1.0
基准: wshobson/agents 架构 + AI 代码工厂
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from ...skill_system.plugin_loader import PluginLoader, Plugin
from ...skill_system.wshobson_agent_loader import WshobsonAgentLoader, Agent
from ...skill_system.wshobson_skill_loader import WshobsonSkillLoader
from ...skill_system.model_strategy import ModelStrategy
from ...skill_system.path_utils import get_project_root
from ..workflow.presets import WorkflowPresets
from .agent_executor import AgentExecutor, ExecutionResult
from .task_queue import TaskQueue
from .monitoring import get_monitor


@dataclass
class OrchestrationContext:
    """编排上下文"""
    requirement: str
    workflow_type: Optional[str] = None
    selected_agents: List[str] = field(default_factory=list)
    selected_skills: List[str] = field(default_factory=list)
    model_assignments: Dict[str, str] = field(default_factory=dict)


class CodeFactoryOrchestrator:
    """代码工厂主编排器 - 整合所有组件"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化编排器
        
        Args:
            project_root: 项目根目录
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # P1-1 fix: 使用统一的路径工具函数
            self.project_root = get_project_root()
        
        # 初始化组件
        self.plugin_loader = PluginLoader(project_root=self.project_root)
        self.agent_loader = WshobsonAgentLoader()
        self.skill_loader = WshobsonSkillLoader()
        self.model_strategy = ModelStrategy()
        
        # P0-1: 初始化执行引擎
        self.executor = AgentExecutor()
        self.task_queue = TaskQueue(self.executor)
        self.monitor = get_monitor()
    
    def execute(self, requirement: str, workflow_type: str = "full_stack_development") -> Dict[str, Any]:
        """
        执行完整工作流
        
        Args:
            requirement: 需求描述
            workflow_type: 工作流类型
            
        Returns:
            执行结果
        """
        # 1. 加载相关插件
        plugins = self._load_relevant_plugins(requirement)
        
        # 2. 选择代理
        agents = self._select_agents(requirement, workflow_type)
        
        # 3. 分配模型
        model_assignments = self._assign_models(agents)
        
        # 4. 执行工作流
        result = self._execute_workflow(requirement, agents, model_assignments, workflow_type)
        
        return result
    
    def _load_relevant_plugins(self, requirement: str) -> List[Plugin]:
        """
        加载相关插件
        
        Args:
            requirement: 需求描述
            
        Returns:
            插件列表
        """
        all_plugins = self.plugin_loader.load_all_plugins()
        relevant = []
        
        # P1-5 fix: 改进插件匹配逻辑
        requirement_lower = requirement.lower()
        requirement_words = set(requirement_lower.split())
        
        for plugin in all_plugins.values():
            score = 0
            
            # 1. 类别匹配（权重：2）
            category_words = set(plugin.category.lower().split("-"))
            if category_words & requirement_words:
                score += 2
            
            # 2. 名称匹配（权重：3）
            name_words = set(plugin.name.lower().split())
            if name_words & requirement_words:
                score += 3
            
            # 3. 描述匹配（权重：1）
            if plugin.description:
                desc_words = set(plugin.description.lower().split())
                if desc_words & requirement_words:
                    score += 1
            
            # 4. 代理能力匹配（权重：2）
            for agent_def in plugin.agents:
                agent_id = agent_def.get("id", "").lower()
                if agent_id in requirement_lower:
                    score += 2
                    break
            
            # 5. 技能匹配（权重：1）
            for skill_def in plugin.skills:
                skill_id = skill_def.get("id", "").lower()
                if skill_id in requirement_lower:
                    score += 1
                    break
            
            # 只添加得分 >= 2 的插件
            if score >= 2:
                relevant.append((plugin, score))
        
        # 按得分排序，返回插件列表
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [plugin for plugin, score in relevant]
    
    def _select_agents(self, requirement: str, workflow_type: str) -> List[Agent]:
        """
        选择代理
        
        Args:
            requirement: 需求描述
            workflow_type: 工作流类型
            
        Returns:
            代理列表
        """
        # 使用工作流预设选择代理
        if workflow_type:
            try:
                workflow = WorkflowPresets.get_workflow(workflow_type)
                agent_ids = [a["id"] for a in workflow["agents"]]
            except ValueError:
                # 如果工作流不存在，根据需求推断
                agent_ids = self._infer_agents_from_requirement(requirement)
        else:
            agent_ids = self._infer_agents_from_requirement(requirement)
        
        # 加载代理
        agents = []
        for agent_id in agent_ids:
            agent = self.agent_loader.load_agent(agent_id)
            if agent:
                agents.append(agent)
        
        return agents
    
    def _infer_agents_from_requirement(self, requirement: str) -> List[str]:
        """
        从需求推断需要的代理
        
        Args:
            requirement: 需求描述
            
        Returns:
            代理 ID 列表
        """
        requirement_lower = requirement.lower()
        agents = []
        
        # 关键词匹配
        if any(kw in requirement_lower for kw in ["架构", "architecture", "系统设计"]):
            agents.append("system-architect")
        
        if any(kw in requirement_lower for kw in ["后端", "backend", "api", "服务"]):
            agents.append("backend-architect")
        
        if any(kw in requirement_lower for kw in ["前端", "frontend", "页面", "组件"]):
            agents.append("frontend-developer")
        
        if any(kw in requirement_lower for kw in ["审查", "review", "检查"]):
            agents.append("code-reviewer")
        
        if any(kw in requirement_lower for kw in ["bug", "错误", "修复", "调试"]):
            agents.append("debugging-specialist")
        
        if any(kw in requirement_lower for kw in ["性能", "performance", "优化"]):
            agents.append("performance-engineer")
        
        # 默认代理
        if not agents:
            agents = ["backend-architect", "frontend-developer"]
        
        return agents
    
    def _assign_models(self, agents: List[Agent]) -> Dict[str, str]:
        """
        分配模型
        
        Args:
            agents: 代理列表
            
        Returns:
            模型分配字典 {agent_id: model}
        """
        assignments = {}
        for agent in agents:
            model = self.model_strategy.get_model_for_agent(agent.id)
            assignments[agent.id] = model
        return assignments
    
    def _execute_workflow(
        self,
        requirement: str,
        agents: List[Agent],
        model_assignments: Dict[str, str],
        workflow_type: str
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            requirement: 需求描述
            agents: 代理列表
            model_assignments: 模型分配
            workflow_type: 工作流类型
            
        Returns:
            执行结果
        """
        # 获取工作流定义
        try:
            workflow = WorkflowPresets.get_workflow(workflow_type)
        except ValueError:
            # 使用默认工作流
            workflow = WorkflowPresets.full_stack_development()
        
        # P0-1: 实际执行工作流
        pattern = workflow.get("pattern", "sequential")
        context = {
            "project_constraints": self._get_project_constraints(),
            "previous_outputs": {},
        }
        
        # 执行任务队列
        execution_results = self.task_queue.execute_workflow(
            workflow_type=workflow_type,
            agents=agents,
            requirement=requirement,
            context=context
        )
        
        # 记录性能指标
        for result in execution_results:
            if result.success:
                self.monitor.record_execution(
                    agent_id=result.agent_id,
                    model=result.model_used or model_assignments.get(result.agent_id, "unknown"),
                    tokens=result.tokens_used or 0,
                    time_taken=result.execution_time or 0.0,
                    success=True
                )
            else:
                self.monitor.record_execution(
                    agent_id=result.agent_id,
                    model=result.model_used or model_assignments.get(result.agent_id, "unknown"),
                    tokens=0,
                    time_taken=result.execution_time or 0.0,
                    success=False
                )
        
        # 构建执行结果
        all_success = all(r.success for r in execution_results)
        result = {
            "requirement": requirement,
            "workflow_type": workflow_type,
            "workflow": workflow,
            "agents": [agent.to_dict() for agent in agents],
            "model_assignments": model_assignments,
            "status": "completed" if all_success else "partial_failure",
            "execution_results": [
                {
                    "agent_id": r.agent_id,
                    "success": r.success,
                    "output": r.output[:500] if r.output else None,  # 限制输出长度
                    "error": r.error,
                    "tokens_used": r.tokens_used,
                    "execution_time": r.execution_time,
                }
                for r in execution_results
            ],
            "performance_metrics": self.monitor.get_metrics(),
        }
        
        return result
    
    def _get_project_constraints(self) -> str:
        """获取项目约束说明"""
        return """
## 项目技术栈

### 后端
- Framework: FastAPI
- ORM: SQLAlchemy 2.x
- Validation: Pydantic v2
- Database: PostgreSQL (Supabase)
- Auth: Supabase Auth + JWT

### 前端
- Framework: Next.js 16
- Language: TypeScript 5.x (strict mode)
- UI: shadcn/ui + Tailwind CSS
- State: TanStack Query v5
- Form: react-hook-form + zod

## SoT 规范

所有代码必须符合以下 SoT 规范：
- MASTER.md - 系统宪法
- STATE_MACHINE.md - 状态机定义（8 状态）
- DATA_SCHEMA.md - 数据模型
- API_SOT.md - API 契约
- ERROR_CODES_SOT.md - 错误码

## 代码规范

- Python: PEP8, 类型提示
- TypeScript: strict mode, 无 any 类型
- API 响应: 使用 Envelope 格式
- 错误处理: 使用 BusinessError 和标准错误码
"""

