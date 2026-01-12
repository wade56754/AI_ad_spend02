"""
工作流引擎

整合 wshobson/agents 工作流模式

版本: v1.0
"""

from .presets import WorkflowPresets
from .patterns import WorkflowPattern, WorkflowExecutor

__all__ = ["WorkflowPresets", "WorkflowPattern", "WorkflowExecutor"]
