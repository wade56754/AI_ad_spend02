"""
任务队列

管理任务执行队列，支持顺序和并行执行

版本: v1.0
基准: wshobson/agents 工作流模式
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .agent_executor import AgentExecutor, ExecutionResult
from ...skill_system.wshobson_agent_loader import Agent
from ..workflow.presets import WorkflowPresets

logger = logging.getLogger(__name__)


class ExecutionPattern(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    CONDITIONAL = "conditional" # 条件分支


class TaskQueue:
    """任务队列 - 管理代理执行"""
    
    def __init__(self, executor: AgentExecutor):
        """
        初始化任务队列
        
        Args:
            executor: 代理执行器
        """
        self.executor = executor
        self.results: List[ExecutionResult] = []
    
    def execute_sequential(
        self,
        agents: List[Agent],
        requirement: str,
        context: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """
        顺序执行代理任务
        
        Args:
            agents: 代理列表
            requirement: 需求描述
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        results = []
        current_context = context.copy()
        current_context.setdefault("previous_outputs", {})
        
        for agent in agents:
            logger.info(f"Executing agent {agent.id} sequentially")
            
            # 执行代理
            result = self.executor.execute_agent(agent, requirement, current_context)
            results.append(result)
            
            # 更新上下文
            if result.success and result.output:
                current_context["previous_outputs"][agent.id] = result.output
            else:
                logger.warning(f"Agent {agent.id} failed: {result.error}")
                # 继续执行，但记录错误
        
        self.results = results
        return results
    
    def execute_parallel(
        self,
        agents: List[Agent],
        requirement: str,
        context: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """
        并行执行代理任务
        
        Args:
            agents: 代理列表
            requirement: 需求描述
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        # 注意：当前实现是同步的，真正的并行需要异步支持
        # 这里先实现同步版本，后续可以升级为异步
        
        results = []
        for agent in agents:
            logger.info(f"Executing agent {agent.id} in parallel")
            # 并行执行时，每个代理使用独立的上下文副本
            agent_context = context.copy()
            agent_context.setdefault("previous_outputs", {})
            
            result = self.executor.execute_agent(agent, requirement, agent_context)
            results.append(result)
        
        self.results = results
        return results
    
    async def execute_parallel_async(
        self,
        agents: List[Agent],
        requirement: str,
        context: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """
        异步并行执行代理任务
        
        Args:
            agents: 代理列表
            requirement: 需求描述
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        async def execute_single_agent(agent: Agent) -> ExecutionResult:
            """执行单个代理（异步包装）"""
            agent_context = context.copy()
            agent_context.setdefault("previous_outputs", {})
            # 在异步环境中运行同步执行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.executor.execute_agent,
                agent,
                requirement,
                agent_context
            )
        
        # 并行执行所有代理
        tasks = [execute_single_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        execution_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agents[i].id} execution exception: {result}")
                execution_results.append(ExecutionResult(
                    agent_id=agents[i].id,
                    success=False,
                    error=str(result)
                ))
            else:
                execution_results.append(result)
        
        self.results = execution_results
        return execution_results
    
    def execute_workflow(
        self,
        workflow_type: str,
        agents: List[Agent],
        requirement: str,
        context: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """
        根据工作流类型执行任务
        
        Args:
            workflow_type: 工作流类型
            agents: 代理列表
            requirement: 需求描述
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        try:
            workflow = WorkflowPresets.get_workflow(workflow_type)
            pattern = workflow.get("pattern", "sequential")
        except ValueError:
            logger.warning(f"Unknown workflow {workflow_type}, using sequential")
            pattern = "sequential"
        
        if pattern == ExecutionPattern.PARALLEL:
            return self.execute_parallel(agents, requirement, context)
        else:
            return self.execute_sequential(agents, requirement, context)

