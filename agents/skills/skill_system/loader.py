"""
技能加载器 (Skill Loader)

自动发现和加载技能目录中的技能

版本: v1.0
"""

from pathlib import Path
from typing import List, Optional
import logging

from .base import Skill, SkillRegistry

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    技能加载器
    
    自动扫描技能目录，发现并加载技能
    """
    
    def __init__(self, skills_root: Optional[Path] = None):
        """
        初始化加载器
        
        Args:
            skills_root: 技能根目录，默认为 agents/skills/
        """
        if skills_root is None:
            # 默认使用相对于此文件的路径
            skills_root = Path(__file__).parent.parent
        
        self.skills_root = skills_root
        self.registry = SkillRegistry()
    
    def load_all(self) -> SkillRegistry:
        """加载所有技能"""
        logger.info(f"开始加载技能，根目录: {self.skills_root}")
        
        # 加载领域技能
        domain_skills_path = self.skills_root / "domain_skills"
        if domain_skills_path.exists():
            self._load_skills_from_directory(domain_skills_path, "domain")
        
        # 加载语言技能
        language_skills_path = self.skills_root / "language_skills"
        if language_skills_path.exists():
            self._load_skills_from_directory(language_skills_path, "language")
        
        # v7.0: 加载方法论技能
        methodology_skills_path = self.skills_root / "methodology_skills"
        if methodology_skills_path.exists():
            self._load_skills_from_directory(methodology_skills_path, "methodology")
        
        # 加载代码块
        code_blocks_path = self.skills_root / "code_blocks"
        if code_blocks_path.exists():
            self._load_skills_from_directory(code_blocks_path, "code_block")
        
        logger.info(f"技能加载完成，共 {len(self.registry)} 个技能")
        return self.registry
    
    def _load_skills_from_directory(self, directory: Path, default_category: str) -> None:
        """从目录加载技能"""
        if not directory.exists():
            logger.warning(f"技能目录不存在: {directory}")
            return
        
        for skill_dir in directory.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "skill.yaml"
            if not skill_file.exists():
                logger.debug(f"跳过非技能目录: {skill_dir}")
                continue
            
            try:
                skill = Skill(skill_dir)
                # 触发元数据加载
                _ = skill.metadata
                
                # P1-2 fix: 使用公开方法替代私有属性访问
                if skill.metadata.category == "general":
                    skill.set_category(default_category)
                
                self.registry.register(skill)
            except Exception as e:
                logger.error(f"加载技能失败 {skill_dir}: {e}")
    
    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """加载单个技能"""
        try:
            skill = Skill(skill_path)
            _ = skill.metadata  # 触发元数据加载
            self.registry.register(skill)
            return skill
        except Exception as e:
            logger.error(f"加载技能失败 {skill_path}: {e}")
            return None
    
    def find_skill(self, query: str) -> List[Skill]:
        """根据查询查找技能"""
        return self.registry.find_by_query(query)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """根据 ID 获取技能"""
        return self.registry.get(skill_id)
