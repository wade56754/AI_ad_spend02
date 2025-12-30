"""
Preprompts 系统 v5.0 - 借鉴 gpt-engineer

提供可配置的提示词模板系统，支持:
- 系统人格定义
- 需求澄清
- 代码生成
- 代码改进
- 代码审查
- 项目模板

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .loader import PromptLoader


class PrepromptType(str, Enum):
    """Preprompt 类型"""
    SYSTEM = "system"
    CLARIFY = "clarify"
    GENERATE = "generate"
    IMPROVE = "improve"
    REVIEW = "review"
    SECURITY = "security"
    BEHAVIOR = "behavior"


class ProjectTemplate(str, Enum):
    """项目模板类型"""
    FASTAPI = "fastapi"
    NEXTJS = "nextjs"
    FULLSTACK = "fullstack"


@dataclass
class PrepromptContext:
    """Preprompt 上下文"""
    preprompt_type: PrepromptType
    content: str
    source: str  # "builtin" | "project"
    variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class PrepromptSet:
    """Preprompt 集合 - 一个完整的提示词配置"""
    system: str
    clarify: str
    generate: str
    improve: str
    review: str
    security: str
    behavior: str
    project_template: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "system": self.system,
            "clarify": self.clarify,
            "generate": self.generate,
            "improve": self.improve,
            "review": self.review,
            "security": self.security,
            "behavior": self.behavior,
            "project_template": self.project_template or "",
        }


class Preprompts:
    """
    Preprompts 系统 - 借鉴 gpt-engineer 设计
    
    提供可配置的提示词模板系统，支持:
    - 内置模板
    - 项目级覆盖
    - 动态变量替换
    
    使用方式:
    ```python
    from agents.skills.code_factory.prompts import Preprompts
    
    # 创建实例
    preprompts = Preprompts(project_dir=Path("./my_project"))
    
    # 加载单个 preprompt
    system_prompt = preprompts.load(PrepromptType.SYSTEM)
    
    # 加载完整集合
    prompt_set = preprompts.load_all()
    
    # 加载项目模板
    fastapi_template = preprompts.load_project_template(ProjectTemplate.FASTAPI)
    ```
    """
    
    VERSION = "5.0"
    
    def __init__(
        self, 
        project_dir: Path,
        loader: Optional["PromptLoader"] = None,
    ):
        """初始化 Preprompts
        
        Args:
            project_dir: 项目根目录
            loader: 可选的 PromptLoader 实例
        """
        self.project_dir = Path(project_dir)
        
        # 使用传入的 loader 或创建新的
        if loader:
            self._loader = loader
        else:
            from .loader import PromptLoader
            self._loader = PromptLoader(project_dir)
        
        # 缓存
        self._cache: Dict[str, PrepromptContext] = {}
    
    def load(
        self, 
        preprompt_type: PrepromptType,
        variables: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> str:
        """加载单个 Preprompt
        
        Args:
            preprompt_type: Preprompt 类型
            variables: 变量替换字典
            use_cache: 是否使用缓存
            
        Returns:
            Preprompt 内容
        """
        cache_key = preprompt_type.value
        
        # 检查缓存
        if use_cache and cache_key in self._cache:
            content = self._cache[cache_key].content
        else:
            # 加载内容
            content = self._loader.load(preprompt_type.value)
            
            # 缓存
            if use_cache:
                self._cache[cache_key] = PrepromptContext(
                    preprompt_type=preprompt_type,
                    content=content,
                    source="builtin",
                )
        
        # 变量替换
        if variables:
            content = self._replace_variables(content, variables)
        
        return content
    
    def load_all(
        self, 
        project_template: Optional[ProjectTemplate] = None,
    ) -> PrepromptSet:
        """加载完整的 Preprompt 集合
        
        Args:
            project_template: 项目模板类型
            
        Returns:
            PrepromptSet 实例
        """
        return PrepromptSet(
            system=self.load(PrepromptType.SYSTEM),
            clarify=self.load(PrepromptType.CLARIFY),
            generate=self.load(PrepromptType.GENERATE),
            improve=self.load(PrepromptType.IMPROVE),
            review=self.load(PrepromptType.REVIEW),
            security=self.load(PrepromptType.SECURITY),
            behavior=self.load(PrepromptType.BEHAVIOR),
            project_template=self.load_project_template(project_template) if project_template else None,
        )
    
    def load_project_template(
        self, 
        template: ProjectTemplate,
    ) -> str:
        """加载项目模板
        
        Args:
            template: 项目模板类型
            
        Returns:
            项目模板内容
        """
        template_path = f"project_templates/{template.value}"
        return self._loader.load(template_path)
    
    def load_task_template(
        self, 
        task_type: str,
    ) -> str:
        """加载任务模板
        
        Args:
            task_type: 任务类型 (refactor, feature, bugfix, research)
            
        Returns:
            任务模板内容
        """
        template_path = f"task/{task_type}"
        return self._loader.load(template_path)
    
    def _replace_variables(
        self, 
        content: str, 
        variables: Dict[str, str],
    ) -> str:
        """替换变量
        
        支持格式: {variable_name} 或 ${VARIABLE_NAME}
        """
        for key, value in variables.items():
            # 支持两种格式
            content = content.replace(f"{{{key}}}", value)
            content = content.replace(f"${{{key.upper()}}}", value)
        return content
    
    def get_available_templates(self) -> Dict[str, List[str]]:
        """获取所有可用模板
        
        Returns:
            模板分类字典
        """
        all_templates = self._loader.list_templates()
        
        result = {
            "preprompts": [],
            "project_templates": [],
            "task_templates": [],
            "other": [],
        }
        
        for template in all_templates:
            if template.startswith("project_templates/"):
                result["project_templates"].append(template)
            elif template.startswith("task/"):
                result["task_templates"].append(template)
            elif template in [t.value for t in PrepromptType]:
                result["preprompts"].append(template)
            else:
                result["other"].append(template)
        
        return result
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def reload(self, preprompt_type: PrepromptType) -> str:
        """重新加载 Preprompt (忽略缓存)"""
        if preprompt_type.value in self._cache:
            del self._cache[preprompt_type.value]
        return self.load(preprompt_type, use_cache=True)
    
    # =========================================================================
    # 便捷方法
    # =========================================================================
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.load(PrepromptType.SYSTEM)
    
    def get_clarify_prompt(self) -> str:
        """获取需求澄清提示词"""
        return self.load(PrepromptType.CLARIFY)
    
    def get_generate_prompt(
        self, 
        template: Optional[ProjectTemplate] = None,
    ) -> str:
        """获取代码生成提示词
        
        Args:
            template: 项目模板
            
        Returns:
            生成提示词 (可能包含项目模板)
        """
        generate = self.load(PrepromptType.GENERATE)
        
        if template:
            project_template = self.load_project_template(template)
            return f"{generate}\n\n---\n\n{project_template}"
        
        return generate
    
    def get_improve_prompt(self) -> str:
        """获取代码改进提示词"""
        return self.load(PrepromptType.IMPROVE)
    
    def get_review_prompt(self) -> str:
        """获取代码审查提示词"""
        return self.load(PrepromptType.REVIEW)
    
    def get_constraints(self) -> str:
        """获取约束提示词 (安全 + 行为)"""
        security = self.load(PrepromptType.SECURITY)
        behavior = self.load(PrepromptType.BEHAVIOR)
        return f"{security}\n\n---\n\n{behavior}"


# ============================================================
# 便捷函数
# ============================================================

def create_preprompts(
    project_dir: str | Path,
    sot_loader = None,
) -> Preprompts:
    """创建 Preprompts 实例
    
    Args:
        project_dir: 项目根目录
        sot_loader: 可选的 SoT 加载器
        
    Returns:
        Preprompts 实例
    """
    from .loader import PromptLoader
    
    loader = PromptLoader(
        project_dir=Path(project_dir),
        sot_loader=sot_loader,
    )
    return Preprompts(project_dir=Path(project_dir), loader=loader)


def load_preprompt(
    preprompt_type: str | PrepromptType,
    project_dir: str | Path = ".",
) -> str:
    """快速加载单个 Preprompt
    
    Args:
        preprompt_type: Preprompt 类型
        project_dir: 项目根目录
        
    Returns:
        Preprompt 内容
    """
    if isinstance(preprompt_type, str):
        preprompt_type = PrepromptType(preprompt_type)
    
    preprompts = Preprompts(project_dir=Path(project_dir))
    return preprompts.load(preprompt_type)


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    import sys
    
    # 获取项目根目录
    project_dir = Path(__file__).parent.parent.parent.parent.parent
    
    print("=" * 60)
    print(f"Preprompts 系统 v{Preprompts.VERSION}")
    print(f"项目目录: {project_dir}")
    print("=" * 60)
    
    # 创建实例
    preprompts = Preprompts(project_dir=project_dir)
    
    # 列出可用模板
    templates = preprompts.get_available_templates()
    print("\n可用模板:")
    for category, items in templates.items():
        if items:
            print(f"\n  {category}:")
            for item in items:
                print(f"    - {item}")
    
    # 加载示例
    print("\n" + "=" * 60)
    print("系统提示词预览 (前 500 字符):")
    print("=" * 60)
    system_prompt = preprompts.get_system_prompt()
    print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)

