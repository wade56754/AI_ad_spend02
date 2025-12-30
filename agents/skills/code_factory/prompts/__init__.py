"""
提示词子系统 v5.0

整合能力:
- prompt-optimizer: 7 必需标签、质量评分
- ai-ad-prompt-structurer: 三层约束、MCP 工具、子代理
- prompt_structurer.py: Python 实现
- gpt-engineer: Preprompts 系统

核心组件:
- PromptLoader: 模板加载 (内置 + 项目覆盖)
- PromptInjector: 提示词注入 (返回 InjectedContext)
- PromptOptimizer: 7 标签生成、质量评估
- PromptStructurer: 结构化提示词
- PromptValidator: 格式验证
- Preprompts: gpt-engineer 风格的模板系统

基准文档: MASTER.md v4.6
版本: v5.0
"""

from .loader import PromptLoader
from .injector import PromptInjector, InjectedContext, TaskType
from .optimizer import (
    PromptOptimizer, 
    RequiredTags, 
    QualityScore,
    validate_prompt,
    evaluate_prompt,
)
from .structurer import (
    PromptStructurer,
    StructuredPrompt,
    BehavioralMode,
    SubAgentType,
    structure_prompt,
)
from .validator import (
    PromptValidator,
    ValidationResult,
    quick_validate,
)
from .preprompts import (
    Preprompts,
    PrepromptType,
    PrepromptSet,
    ProjectTemplate,
    create_preprompts,
    load_preprompt,
)

__version__ = "5.0.0"

__all__ = [
    # 核心加载器
    "PromptLoader",
    
    # 注入器
    "PromptInjector",
    "InjectedContext",
    "TaskType",
    
    # 优化器
    "PromptOptimizer",
    "RequiredTags",
    "QualityScore",
    "validate_prompt",
    "evaluate_prompt",
    
    # 结构化器
    "PromptStructurer",
    "StructuredPrompt",
    "BehavioralMode",
    "SubAgentType",
    "structure_prompt",
    
    # 验证器
    "PromptValidator",
    "ValidationResult",
    "quick_validate",
    
    # Preprompts (gpt-engineer 风格)
    "Preprompts",
    "PrepromptType",
    "PrepromptSet",
    "ProjectTemplate",
    "create_preprompts",
    "load_preprompt",
]

