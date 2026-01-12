"""
wshobson/agents 技能加载器

从 wshobson/agents 项目加载技能定义，适配到项目需求

版本: v1.0
基准: wshobson/agents + AI 广告代投系统需求
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import Skill, SkillMetadata
from .loader import SkillLoader
from .path_utils import get_project_root, get_wshobson_agents_path
from .cache import SkillCache
from .config import get_config

logger = logging.getLogger(__name__)


class WshobsonSkillLoader:
    """加载 wshobson/agents 的技能"""
    
    def __init__(self, wshobson_repo_path: Optional[Path] = None):
        """
        初始化加载器
        
        Args:
            wshobson_repo_path: wshobson/agents 仓库路径
        """
        config = get_config()
        
        if wshobson_repo_path:
            self.repo_path = Path(wshobson_repo_path)
        else:
            # P1-1 fix: 使用统一的路径工具函数
            self.repo_path = config.wshobson_agents_path
        
        # 加载映射配置
        mapping_file = Path(__file__).parent / "skill_mapping.yaml"
        self.mapping = self._load_mapping(mapping_file) if mapping_file.exists() else {}
        
        # 技能定义路径
        self.skills_dir = self.repo_path / ".claude-plugin" / "plugins"
        if not self.skills_dir.exists():
            self.skills_dir = self.repo_path / "plugins"
        
        # P1-1: 初始化缓存
        self.cache = SkillCache(max_size=config.cache_size) if config.cache_enabled else None
    
    def _load_mapping(self, mapping_file: Path) -> Dict[str, Dict]:
        """加载映射配置"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                mappings = {}
                for mapping in data.get('mappings', []):
                    source = mapping.get('source')
                    if source:
                        mappings[source] = mapping
                return mappings
        except Exception as e:
            # P1-2 fix: 使用 logging 而不是 print
            logger.warning(f"Failed to load mapping file {mapping_file}: {e}")
            return {}
    
    def load_skill(self, skill_id: str) -> Optional[Skill]:
        """
        加载指定技能
        
        Args:
            skill_id: 技能 ID
            
        Returns:
            适配后的技能，如果不存在则返回 None
        """
        # 1. 检查映射配置
        if skill_id in self.mapping:
            mapping = self.mapping[skill_id]
            source_id = mapping.get('source', skill_id)
        else:
            source_id = skill_id
        
        # 2. 从 wshobson/agents 加载技能定义
        skill_path = self._find_skill_path(source_id)
        if not skill_path:
            return None
        
        # 3. 使用基础 SkillLoader 加载技能
        try:
            skill = Skill(skill_path)
            
            # P1-3 fix: 应用映射规则 - 创建新的元数据而不是直接修改
            if skill_id in self.mapping:
                mapping = self.mapping[skill_id]
                # 更新元数据（SkillMetadata 是可变的，可以直接修改）
                if skill.metadata:
                    # 更新类别
                    if 'category' in mapping:
                        skill.metadata.category = mapping['category']
                    # 添加 model_tier 到元数据的 sot_references（如果不存在 model_tier 属性）
                    # 注意：SkillMetadata 没有 model_tier 字段，我们将其添加到 sot_references
                    if 'model_tier' in mapping:
                        model_tier_ref = f"model_tier:{mapping['model_tier']}"
                        if model_tier_ref not in skill.metadata.sot_references:
                            skill.metadata.sot_references.append(model_tier_ref)
            
            # P1-1: 存入缓存
            if self.cache:
                self.cache.set(skill_id, skill)
            
            return skill
        except Exception as e:
            # P1-2 fix: 使用 logging 而不是 print
            logger.warning(f"Failed to load skill {skill_id}: {e}", exc_info=True)
            return None
    
    def _find_skill_path(self, skill_id: str) -> Optional[Path]:
        """
        查找技能文件路径
        
        Args:
            skill_id: 技能 ID
            
        Returns:
            技能目录路径
        """
        # 尝试多种可能的路径
        possible_paths = [
            self.skills_dir / skill_id,
            self.skills_dir / skill_id / "skills",
            self.repo_path / "plugins" / skill_id / "skills",
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # 查找 skill.yaml 或 skill.md
                for skill_file in ['skill.yaml', 'skill.md', 'SKILL.md', 'SKILL.yaml']:
                    skill_file_path = path / skill_file
                    if skill_file_path.exists():
                        return path
        
        return None
    
    def load_all_skills(self) -> Dict[str, Skill]:
        """
        加载所有可用技能
        
        Returns:
            技能字典，key 为技能 ID
        """
        skills = {}
        
        # 从映射配置加载
        for skill_id in self.mapping.keys():
            skill = self.load_skill(skill_id)
            if skill:
                skills[skill.metadata.id if skill.metadata else skill_id] = skill
        
        return skills

