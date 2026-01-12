"""
两层模型策略

根据任务类型和代理配置，智能选择 Opus 4.5 或 Sonnet 4.5

版本: v1.0
基准: wshobson/agents 三层模型策略（简化为两层）
"""

from typing import Dict, Set, Optional
from enum import Enum


class ModelTier(str, Enum):
    """模型层级"""
    TIER_1_OPUS = "tier1"      # Opus 4.5
    TIER_2_SONNET = "tier2"    # Sonnet 4.5


class ModelStrategy:
    """两层模型策略"""
    
    # Tier 1 任务类型（使用 Opus 4.5）
    TIER_1_TASKS: Set[str] = {
        "system-architecture",      # 系统架构
        "code-generation",          # 代码生成
        "code-review",              # 代码审查
        "bug-fixing",               # Bug 修复
        "performance-optimization", # 性能优化
    }
    
    # Tier 1 代理类别（使用 Opus 4.5）
    TIER_1_CATEGORIES: Set[str] = {
        "architecture",             # 架构类
        "development",               # 开发类（代码生成相关）
        "quality",                   # 质量类（代码审查、性能优化）
        "security",                  # 安全类
    }
    
    def __init__(self, agent_registry: Optional[object] = None):
        """
        初始化模型策略
        
        Args:
            agent_registry: 代理注册表（可选）
        """
        self.agent_registry = agent_registry
    
    def get_model_for_task(self, task_type: str) -> str:
        """
        根据任务类型获取模型
        
        Args:
            task_type: 任务类型
            
        Returns:
            模型名称: "opus-4.5" 或 "sonnet-4.5"
        """
        if task_type in self.TIER_1_TASKS:
            return "opus-4.5"
        return "sonnet-4.5"
    
    def get_model_for_agent(self, agent_id: str) -> str:
        """
        根据代理 ID 获取模型
        
        Args:
            agent_id: 代理 ID
            
        Returns:
            模型名称: "opus-4.5" 或 "sonnet-4.5"
        """
        # P0-2 fix: 如果没有注册表，直接根据 ID 推断
        if not self.agent_registry:
            return self._infer_model_from_agent_id(agent_id)
        
        # P0-2 fix: 检查 agent_registry 是否有 get_agent 方法
        if not hasattr(self.agent_registry, 'get_agent'):
            return self._infer_model_from_agent_id(agent_id)
        
        try:
            agent = self.agent_registry.get_agent(agent_id)
            
            # P0-2 fix: 检查 agent 是否为 None
            if agent is None:
                return self._infer_model_from_agent_id(agent_id)
            
            # 根据 model_tier 判断
            if hasattr(agent, 'model_tier'):
                if agent.model_tier == ModelTier.TIER_1_OPUS or agent.model_tier == "tier1":
                    return "opus-4.5"
                elif agent.model_tier == ModelTier.TIER_2_SONNET or agent.model_tier == "tier2":
                    return "sonnet-4.5"
            
            # 根据代理类别推断
            if hasattr(agent, 'category') and agent.category:
                if agent.category in self.TIER_1_CATEGORIES:
                    return "opus-4.5"
        except AttributeError:
            # P0-2 fix: 明确处理 AttributeError（方法不存在）
            return self._infer_model_from_agent_id(agent_id)
        except Exception as e:
            # P0-2 fix: 记录其他异常但不中断执行
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get model for agent {agent_id}: {e}, using inference")
            return self._infer_model_from_agent_id(agent_id)
        
        return "sonnet-4.5"
    
    def _infer_model_from_agent_id(self, agent_id: str) -> str:
        """
        根据代理 ID 推断模型
        
        Args:
            agent_id: 代理 ID
            
        Returns:
            模型名称
        """
        # Tier 1 代理关键词
        tier1_keywords = {
            "architect", "reviewer", "auditor", "engineer",
            "specialist", "developer"  # 代码生成相关的 developer
        }
        
        # Tier 2 代理关键词
        tier2_keywords = {
            "writer", "automator", "tester", "formatter"
        }
        
        agent_id_lower = agent_id.lower()
        
        # 检查 Tier 1 关键词
        for keyword in tier1_keywords:
            if keyword in agent_id_lower:
                # 排除 Tier 2 的情况
                if not any(t2_kw in agent_id_lower for t2_kw in tier2_keywords):
                    return "opus-4.5"
        
        return "sonnet-4.5"
    
    def get_model_for_category(self, category: str) -> str:
        """
        根据代理类别获取模型
        
        Args:
            category: 代理类别
            
        Returns:
            模型名称
        """
        if category in self.TIER_1_CATEGORIES:
            return "opus-4.5"
        return "sonnet-4.5"
    
    def is_tier1_task(self, task_type: str) -> bool:
        """
        判断任务是否为 Tier 1 任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            是否为 Tier 1 任务
        """
        return task_type in self.TIER_1_TASKS

