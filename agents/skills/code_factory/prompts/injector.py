"""
提示词注入器 v5.0

功能:
- 根据任务类型自动选择模板组合
- 注入三层约束 (Security/Behavior/Task)
- 返回 InjectedContext 供 GenerationContext 使用

这是 factory.py 依赖的核心模块！

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from .loader import PromptLoader


class TaskType(Enum):
    """任务类型"""
    REFACTOR = "refactor"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    MIGRATION = "migration"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REVIEW = "review"
    RESEARCH = "research"
    UNKNOWN = "unknown"


# 任务类型关键词映射
TASK_TYPE_KEYWORDS: Dict[TaskType, List[str]] = {
    TaskType.REFACTOR: ["重构", "refactor", "改造", "优化结构", "restructure"],
    TaskType.FEATURE: ["新增", "添加", "实现", "开发", "功能", "feature", "implement"],
    TaskType.BUGFIX: ["修复", "fix", "bug", "问题", "错误", "异常", "repair"],
    TaskType.MIGRATION: ["迁移", "migrate", "升级", "upgrade", "版本", "migration"],
    TaskType.DOCUMENTATION: ["文档", "doc", "说明", "readme", "document"],
    TaskType.TESTING: ["测试", "test", "覆盖率", "单元测试", "coverage"],
    TaskType.REVIEW: ["审查", "review", "检查", "分析", "评估", "analyze"],
    TaskType.RESEARCH: ["研究", "调研", "research", "探索", "学习", "了解"],
}


@dataclass
class InjectedContext:
    """注入的提示词上下文
    
    这是 factory.py GenerationContext.prompt_context 的类型
    """
    # Layer 1 + Layer 2: 安全约束 + 行为约束
    system_constraints: str = ""
    
    # Layer 3: 任务约束 (根据任务类型)
    task_guidance: str = ""
    
    # 补充说明 (模块相关上下文)
    supporting_context: str = ""
    
    # 使用的模板列表 (用于追溯)
    prompts_used: List[str] = field(default_factory=list)
    
    # 任务类型
    task_type: TaskType = TaskType.UNKNOWN
    
    def to_prompt_section(self) -> str:
        """转换为可插入 Prompt 的文本段"""
        sections = []
        
        if self.system_constraints:
            sections.append(self.system_constraints)
        
        if self.task_guidance:
            sections.append(self.task_guidance)
        
        if self.supporting_context:
            sections.append(self.supporting_context)
        
        return "\n\n".join(sections)


class PromptInjector:
    """提示词注入器
    
    根据需求自动匹配并注入合适的提示词模板。
    这是 factory.py _get_prompt_injector() 尝试加载的类。
    """
    
    def __init__(self, loader: PromptLoader):
        """初始化注入器
        
        Args:
            loader: 提示词模板加载器
        """
        self.loader = loader
    
    def inject(
        self,
        requirement: str,
        module_id: Optional[str] = None,
        include_system: bool = True,
        max_supporting: int = 3,
    ) -> InjectedContext:
        """注入提示词到代码生成上下文
        
        Args:
            requirement: 需求描述
            module_id: 模块 ID (pitcher/finance/ad_account/project)
            include_system: 是否包含系统约束
            max_supporting: 最大补充说明数量
            
        Returns:
            InjectedContext 实例
        """
        prompts_used = []
        
        # 1. 分析任务类型
        task_type = self._analyze_task_type(requirement)
        
        # 2. 加载系统约束 (Layer 1: Security + Layer 2: Behavior)
        system_constraints = ""
        if include_system:
            security = self.loader.load("security")
            behavior = self.loader.load("behavior")
            
            if security:
                system_constraints += security
                prompts_used.append("security")
            
            if behavior:
                if system_constraints:
                    system_constraints += "\n\n"
                system_constraints += behavior
                prompts_used.append("behavior")
        
        # 3. 加载任务约束 (Layer 3: Task)
        task_guidance = ""
        task_template_name = f"task/{task_type.value}"
        task_template = self.loader.load(task_template_name)
        if task_template:
            task_guidance = task_template
            prompts_used.append(task_template_name)
        else:
            # 回退到默认任务约束
            default_task = self.loader.load("task/default")
            if default_task:
                task_guidance = default_task
                prompts_used.append("task/default")
        
        # 4. 构建补充说明 (模块相关)
        supporting = self._build_supporting_context(module_id, max_supporting)
        
        return InjectedContext(
            system_constraints=system_constraints,
            task_guidance=task_guidance,
            supporting_context=supporting,
            prompts_used=prompts_used,
            task_type=task_type,
        )
    
    def _analyze_task_type(self, requirement: str) -> TaskType:
        """分析需求文本，识别任务类型
        
        Args:
            requirement: 需求描述
            
        Returns:
            识别的任务类型
        """
        req_lower = requirement.lower()
        
        for task_type, keywords in TASK_TYPE_KEYWORDS.items():
            if any(kw.lower() in req_lower for kw in keywords):
                return task_type
        
        return TaskType.UNKNOWN
    
    def _build_supporting_context(
        self, 
        module_id: Optional[str], 
        max_items: int
    ) -> str:
        """构建补充说明上下文
        
        Args:
            module_id: 模块 ID
            max_items: 最大条目数
            
        Returns:
            补充说明文本
        """
        if not module_id:
            return ""
        
        # 模块边界定义 (来自 STATE_MACHINE.md v2.8)
        module_boundaries = {
            "pitcher": {
                "可写表": ["daily_reports", "pitchers(仅自己)"],
                "只读表": ["account_ownership_history", "ad_accounts", "projects"],
                "禁止表": ["ledger", "period_locks", "recon_*"],
            },
            "finance": {
                "可写表": ["ledger(仅INSERT)", "period_locks", "recon_*"],
                "只读表": ["daily_reports", "ad_accounts", "agencies"],
                "禁止表": ["pitchers(写)"],
            },
            "ad_account": {
                "可写表": ["ad_accounts", "agencies", "account_ownership_history", "attribution_*", "spend_*"],
                "只读表": ["pitchers", "projects"],
                "禁止表": ["ledger", "daily_reports(写)", "period_locks"],
            },
            "project": {
                "可写表": ["projects", "clients"],
                "只读表": ["pitchers", "ad_accounts"],
                "禁止表": ["ledger", "daily_reports(写)", "account_ownership_history(写)"],
            },
        }
        
        if module_id not in module_boundaries:
            return ""
        
        boundary = module_boundaries[module_id]
        lines = [f"## 模块边界约束 ({module_id})"]
        
        if boundary.get("可写表"):
            lines.append(f"- 可写表: {', '.join(boundary['可写表'][:max_items])}")
        if boundary.get("只读表"):
            lines.append(f"- 只读表: {', '.join(boundary['只读表'][:max_items])}")
        if boundary.get("禁止表"):
            lines.append(f"- 禁止表: {', '.join(boundary['禁止表'][:max_items])}")
        
        return "\n".join(lines)
    
    def get_task_type(self, requirement: str) -> TaskType:
        """获取任务类型 (公开方法)"""
        return self._analyze_task_type(requirement)
    
    def list_available_templates(self) -> List[str]:
        """列出所有可用的提示词模板"""
        return self.loader.list_templates()

