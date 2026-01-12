"""
代理执行器

负责实际调用代理执行任务，集成 Claude API

版本: v1.0
基准: wshobson/agents + AI 代码工厂
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from ...skill_system.wshobson_agent_loader import Agent
from ...skill_system.model_strategy import ModelStrategy

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    agent_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    execution_time: Optional[float] = None
    model_used: Optional[str] = None


class AgentExecutor:
    """代理执行器 - 实际调用代理执行任务"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化执行器
        
        Args:
            api_key: Anthropic API 密钥，如果为 None 则从环境变量读取
        """
        if not ANTHROPIC_AVAILABLE:
            logger.warning("anthropic package not available, AgentExecutor will use mock mode")
            self.client = None
        else:
            self.api_key = api_key or self._get_api_key()
            if self.api_key:
                try:
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                except Exception as e:
                    logger.error(f"Failed to initialize Anthropic client: {e}")
                    self.client = None
            else:
                logger.warning("ANTHROPIC_API_KEY not set, AgentExecutor will use mock mode")
                self.client = None
        
        self.model_strategy = ModelStrategy()
    
    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取 API 密钥"""
        return os.getenv("ANTHROPIC_API_KEY")
    
    def execute_agent(
        self,
        agent: Agent,
        requirement: str,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """
        执行代理任务
        
        Args:
            agent: 代理对象
            requirement: 需求描述
            context: 执行上下文（包含之前代理的输出等）
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        # 1. 获取模型
        model = self.model_strategy.get_model_for_agent(agent.id)
        
        # 2. 构建提示词
        prompt = self._build_prompt(agent, requirement, context)
        
        # 3. 如果没有 API 客户端，返回模拟结果
        if not self.client:
            logger.warning(f"Using mock execution for agent {agent.id} (no API client)")
            return ExecutionResult(
                agent_id=agent.id,
                success=True,
                output=f"[Mock] Agent {agent.name} executed for: {requirement[:50]}...",
                model_used=model,
                execution_time=time.time() - start_time,
                tokens_used=0
            )
        
        # 4. 调用 Claude API
        try:
            logger.info(f"Executing agent {agent.id} with model {model}")
            
            response = self.client.messages.create(
                model=self._map_model_name(model),
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            execution_time = time.time() - start_time
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            logger.info(
                f"Agent {agent.id} completed in {execution_time:.2f}s, "
                f"tokens: {tokens_used}"
            )
            
            return ExecutionResult(
                agent_id=agent.id,
                success=True,
                output=response.content[0].text if response.content else "",
                model_used=model,
                execution_time=execution_time,
                tokens_used=tokens_used
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {agent.id} execution failed: {e}", exc_info=True)
            
            return ExecutionResult(
                agent_id=agent.id,
                success=False,
                error=str(e),
                model_used=model,
                execution_time=execution_time
            )
    
    def _map_model_name(self, model: str) -> str:
        """
        映射模型名称到 Anthropic API 格式
        
        Args:
            model: 内部模型名称 (opus-4.5, sonnet-4.5)
            
        Returns:
            Anthropic API 模型名称
        """
        # 映射到实际的 Anthropic 模型名称
        # 注意：这里使用占位符，实际需要根据 Anthropic 的模型命名更新
        model_mapping = {
            "opus-4.5": "claude-3-5-sonnet-20241022",  # 临时使用 sonnet，等待 opus 发布
            "sonnet-4.5": "claude-3-5-sonnet-20241022",
        }
        return model_mapping.get(model, "claude-3-5-sonnet-20241022")
    
    def _build_prompt(self, agent: Agent, requirement: str, context: Dict[str, Any]) -> str:
        """
        构建提示词
        
        Args:
            agent: 代理对象
            requirement: 需求描述
            context: 执行上下文
            
        Returns:
            完整的提示词
        """
        prompt_parts = []
        
        # 1. 代理角色和描述
        prompt_parts.append(f"# {agent.name}")
        prompt_parts.append("")
        if agent.description:
            prompt_parts.append(agent.description)
            prompt_parts.append("")
        
        # 2. 代理能力
        if agent.capabilities:
            prompt_parts.append("## 能力")
            for capability in agent.capabilities:
                prompt_parts.append(f"- {capability}")
            prompt_parts.append("")
        
        # 3. 上下文信息（之前代理的输出）
        if context.get("previous_outputs"):
            prompt_parts.append("## 上下文信息")
            for prev_agent_id, prev_output in context["previous_outputs"].items():
                prompt_parts.append(f"### {prev_agent_id} 的输出")
                prompt_parts.append(prev_output[:500])  # 限制长度
                prompt_parts.append("")
        
        # 4. 当前需求
        prompt_parts.append("## 任务需求")
        prompt_parts.append(requirement)
        prompt_parts.append("")
        
        # 5. 项目约束（从 context 获取）
        if context.get("project_constraints"):
            prompt_parts.append("## 项目约束")
            prompt_parts.append(context["project_constraints"])
            prompt_parts.append("")
        
        # 6. 输出要求
        prompt_parts.append("## 输出要求")
        prompt_parts.append("请根据以上信息，完成你的任务。")
        prompt_parts.append("输出应该清晰、完整、符合项目规范。")
        
        return "\n".join(prompt_parts)

