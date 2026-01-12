"""
工作流模式定义

借鉴 wshobson/agents 的工作流模式

版本: v1.0
"""

from enum import Enum
from typing import Dict, List, Any, Callable, Optional


class WorkflowPattern(str, Enum):
    """工作流模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    CONDITIONAL = "conditional" # 条件分支
    LOOP = "loop"              # 循环执行


class WorkflowExecutor:
    """工作流执行器"""
    
    @staticmethod
    def execute_sequential(
        agents: List[Dict[str, Any]],
        context: Dict[str, Any],
        executor_func: Callable
    ) -> Dict[str, Any]:
        """
        顺序执行工作流
        
        Args:
            agents: 代理列表
            context: 上下文
            executor_func: 执行函数
            
        Returns:
            执行结果
        """
        results = []
        current_context = context.copy()
        
        for agent in agents:
            result = executor_func(agent, current_context)
            results.append(result)
            # 更新上下文
            if "output" in result:
                current_context.update(result["output"])
        
        return {
            "pattern": "sequential",
            "results": results,
            "final_context": current_context,
        }
    
    @staticmethod
    def execute_parallel(
        agents: List[Dict[str, Any]],
        context: Dict[str, Any],
        executor_func: Callable
    ) -> Dict[str, Any]:
        """
        并行执行工作流
        
        Args:
            agents: 代理列表
            context: 上下文
            executor_func: 执行函数
            
        Returns:
            执行结果
        """
        # 注意：实际并行执行需要异步支持
        results = []
        for agent in agents:
            result = executor_func(agent, context)
            results.append(result)
        
        return {
            "pattern": "parallel",
            "results": results,
            "context": context,
        }
    
    @staticmethod
    def execute_conditional(
        condition: Callable[[Dict], bool],
        branches: Dict[str, List[Dict[str, Any]]],
        context: Dict[str, Any],
        executor_func: Callable
    ) -> Dict[str, Any]:
        """
        条件分支工作流
        
        Args:
            condition: 条件函数
            branches: 分支定义 {"true": [...], "false": [...]}
            context: 上下文
            executor_func: 执行函数
            
        Returns:
            执行结果
        """
        if condition(context):
            agents = branches.get("true", [])
        else:
            agents = branches.get("false", [])
        
        return WorkflowExecutor.execute_sequential(agents, context, executor_func)
    
    @staticmethod
    def execute_loop(
        agents: List[Dict[str, Any]],
        context: Dict[str, Any],
        executor_func: Callable,
        max_iterations: int = 10,
        stop_condition: Optional[Callable[[Dict], bool]] = None
    ) -> Dict[str, Any]:
        """
        循环执行工作流
        
        Args:
            agents: 代理列表
            context: 上下文
            executor_func: 执行函数
            max_iterations: 最大迭代次数
            stop_condition: 停止条件
            
        Returns:
            执行结果
        """
        results = []
        current_context = context.copy()
        
        for iteration in range(max_iterations):
            iteration_results = []
            for agent in agents:
                result = executor_func(agent, current_context)
                iteration_results.append(result)
                if "output" in result:
                    current_context.update(result["output"])
            
            results.append({
                "iteration": iteration + 1,
                "results": iteration_results,
            })
            
            # 检查停止条件
            if stop_condition and stop_condition(current_context):
                break
        
        return {
            "pattern": "loop",
            "iterations": len(results),
            "results": results,
            "final_context": current_context,
        }

