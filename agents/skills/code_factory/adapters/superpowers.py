"""
Superpowers 适配器

集成 obra/superpowers 技能库到 AI 代码工厂。

支持的技能:
- test-driven-development: TDD 红绿重构
- systematic-debugging: 4 阶段根因分析
- brainstorming: 设计讨论和细化
- writing-plans: 创建详细实施计划
- executing-plans: 批量执行计划
- subagent-driven-development: 子代理驱动开发

版本: v7.0
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SuperpowersSkill:
    """Superpowers 技能"""
    name: str
    description: str
    content: str
    path: Path
    triggers: List[str] = field(default_factory=list)


class SuperpowersAdapter:
    """
    Superpowers 适配器
    
    加载和使用 .superpowers/skills/ 中的技能
    """
    
    # 核心技能映射
    CORE_SKILLS = {
        "tdd": "test-driven-development",
        "debugging": "systematic-debugging",
        "brainstorm": "brainstorming",
        "plan": "writing-plans",
        "execute": "executing-plans",
        "subagent": "subagent-driven-development",
        "review": "requesting-code-review",
        "finish": "finishing-a-development-branch",
    }
    
    # 触发关键词
    TRIGGERS = {
        "test-driven-development": [
            "实现", "开发", "功能", "修复", "测试",
            "implement", "develop", "feature", "fix", "test",
        ],
        "systematic-debugging": [
            "调试", "debug", "错误", "bug", "问题",
            "不工作", "失败", "异常",
        ],
        "brainstorming": [
            "设计", "架构", "方案", "讨论",
            "design", "architecture", "approach",
        ],
        "writing-plans": [
            "计划", "规划", "步骤", "任务",
            "plan", "steps", "tasks",
        ],
    }
    
    def __init__(self, superpowers_dir: Optional[Path] = None):
        """
        初始化适配器
        
        Args:
            superpowers_dir: Superpowers 技能目录
        """
        if superpowers_dir is None:
            # 默认路径
            superpowers_dir = Path(__file__).parents[4] / ".superpowers" / "skills"
        
        self.superpowers_dir = superpowers_dir
        self._cache: Dict[str, SuperpowersSkill] = {}
    
    def is_available(self) -> bool:
        """检查 Superpowers 是否可用"""
        return self.superpowers_dir.exists()
    
    def load_skill(self, skill_name: str) -> Optional[SuperpowersSkill]:
        """
        加载技能
        
        Args:
            skill_name: 技能名称 (短名或完整名)
            
        Returns:
            SuperpowersSkill 或 None
        """
        # 解析短名
        full_name = self.CORE_SKILLS.get(skill_name, skill_name)
        
        # 检查缓存
        if full_name in self._cache:
            return self._cache[full_name]
        
        # 加载技能文件
        skill_dir = self.superpowers_dir / full_name
        skill_file = skill_dir / "SKILL.md"
        
        if not skill_file.exists():
            logger.warning(f"技能文件不存在: {skill_file}")
            return None
        
        try:
            content = skill_file.read_text(encoding="utf-8")
            
            # 解析 frontmatter
            description = self._extract_description(content)
            
            skill = SuperpowersSkill(
                name=full_name,
                description=description,
                content=content,
                path=skill_file,
                triggers=self.TRIGGERS.get(full_name, []),
            )
            
            self._cache[full_name] = skill
            return skill
            
        except Exception as e:
            logger.error(f"加载技能失败 {full_name}: {e}")
            return None
    
    def find_skill_for_task(self, task_description: str) -> Optional[SuperpowersSkill]:
        """
        根据任务描述查找适合的技能
        
        Args:
            task_description: 任务描述
            
        Returns:
            最匹配的技能或 None
        """
        task_lower = task_description.lower()
        
        for skill_name, triggers in self.TRIGGERS.items():
            for trigger in triggers:
                if trigger in task_lower:
                    return self.load_skill(skill_name)
        
        return None
    
    def get_tdd_principles(self) -> str:
        """
        获取 TDD 原则
        
        用于注入到实现阶段
        """
        skill = self.load_skill("tdd")
        if not skill:
            return self._default_tdd_principles()
        
        return skill.content
    
    def get_review_checklist(self) -> str:
        """
        获取审查清单
        
        用于注入到审查阶段
        """
        skill = self.load_skill("review")
        if not skill:
            return self._default_review_checklist()
        
        return skill.content
    
    def _extract_description(self, content: str) -> str:
        """从 frontmatter 提取描述"""
        lines = content.split("\n")
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == "---":
                if in_frontmatter:
                    break
                in_frontmatter = True
                continue
            
            if in_frontmatter and line.startswith("description:"):
                return line.split(":", 1)[1].strip().strip('"')
        
        return ""
    
    def _default_tdd_principles(self) -> str:
        """默认 TDD 原则"""
        return """
# TDD 铁律

NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST

## Red-Green-Refactor

1. RED: 写一个失败的测试
2. 验证测试失败
3. GREEN: 写最小代码使测试通过
4. 验证测试通过
5. REFACTOR: 清理代码

## 规则

- 写代码前先写测试? 删掉代码，重新开始
- 测试必须先失败，证明它真的在测试某些东西
- 只写使测试通过的最小代码
"""
    
    def _default_review_checklist(self) -> str:
        """默认审查清单"""
        return """
# 代码审查清单

## 规格合规
- [ ] 所有需求点都已实现
- [ ] 没有多余功能 (YAGNI)
- [ ] 符合验收标准

## 代码质量
- [ ] 命名清晰
- [ ] 函数短小
- [ ] 错误处理完整
- [ ] 测试覆盖充分
"""
    
    def list_available_skills(self) -> List[str]:
        """列出所有可用技能"""
        if not self.is_available():
            return []
        
        skills = []
        for item in self.superpowers_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        
        return sorted(skills)


# =============================================================================
# 便捷函数
# =============================================================================

def load_superpowers_skill(
    skill_name: str,
    superpowers_dir: Optional[Path] = None,
) -> Optional[SuperpowersSkill]:
    """
    加载 Superpowers 技能
    
    Args:
        skill_name: 技能名称
        superpowers_dir: 技能目录 (可选)
        
    Returns:
        SuperpowersSkill 或 None
    """
    adapter = SuperpowersAdapter(superpowers_dir)
    return adapter.load_skill(skill_name)


def get_tdd_skill() -> Optional[SuperpowersSkill]:
    """获取 TDD 技能"""
    return load_superpowers_skill("tdd")


def get_debugging_skill() -> Optional[SuperpowersSkill]:
    """获取调试技能"""
    return load_superpowers_skill("debugging")


__all__ = [
    "SuperpowersAdapter",
    "SuperpowersSkill",
    "load_superpowers_skill",
    "get_tdd_skill",
    "get_debugging_skill",
]
