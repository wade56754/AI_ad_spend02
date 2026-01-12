"""
技能基类 (Skill Base)

实现渐进式披露架构：
- Layer 1: 元数据 (始终加载, ~50 tokens)
- Layer 2: 核心指令 (激活时加载, ~200 tokens)
- Layer 3: 完整资源 (按需加载, ~500+ tokens)

借鉴: wshobson/agents 的技能系统设计
版本: v1.0
"""

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 配置常量
# ============================================================================

# 支持的资源文件扩展名
SUPPORTED_RESOURCE_EXTENSIONS = frozenset({".md", ".yaml", ".yml", ".json", ".py", ".txt"})

# Token 估算系数 (字符数 / 系数 = Token 数)
TOKEN_ESTIMATION_FACTOR = 4

# 元数据 Token 估算值 (固定值)
METADATA_TOKEN_ESTIMATE = 50


@dataclass
class SkillMetadata:
    """
    Layer 1: 技能元数据 (始终加载)
    
    Token 消耗: ~50 tokens
    用途: 快速匹配和激活判断
    """
    id: str
    name: str
    version: str
    triggers: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    sot_references: List[str] = field(default_factory=list)
    category: str = "general"
    
    def __post_init__(self):
        """验证字段值"""
        # 验证 id
        if not self.id or not self.id.strip():
            raise ValueError("技能 ID 不能为空")
        self.id = self.id.strip()
        
        # 验证 id 格式 (只允许字母、数字、下划线、连字符)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', self.id):
            raise ValueError(f"技能 ID 格式无效: '{self.id}' (应以字母开头，只能包含字母、数字、下划线、连字符)")
        
        # 验证 name
        if not self.name or not self.name.strip():
            raise ValueError("技能名称不能为空")
        self.name = self.name.strip()
        
        # 验证 version 格式 (简单验证，允许 x.y.z 或 x.y 格式)
        if not re.match(r'^\d+(\.\d+){0,2}$', self.version):
            raise ValueError(f"版本格式无效: '{self.version}' (应为 x.y 或 x.y.z 格式)")
        
        # 验证 category
        if not self.category or not self.category.strip():
            self.category = "general"
        self.category = self.category.strip()
    
    def matches(self, query: str) -> bool:
        """检查查询是否匹配此技能"""
        query_lower = query.lower()
        
        # P1-1 fix: 使用词边界匹配替代子串匹配
        for trigger in self.triggers:
            pattern = r'\b' + re.escape(trigger.lower()) + r'\b'
            if re.search(pattern, query_lower):
                return True
        
        for keyword in self.keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "triggers": self.triggers,
            "keywords": self.keywords,
            "sot_references": self.sot_references,
            "category": self.category,
        }


class Skill:
    """
    技能基类 - 渐进式披露架构
    
    三层加载策略:
    1. 元数据 (metadata): 始终加载，用于匹配和激活
    2. 指令 (instructions): 激活时加载，核心使用指南
    3. 资源 (resources): 按需加载，详细示例和边缘案例
    """
    
    def __init__(self, skill_path: Path):
        """
        初始化技能
        
        Args:
            skill_path: 技能目录路径
        """
        self.skill_path = skill_path
        self._metadata: Optional[SkillMetadata] = None
        self._instructions: Optional[str] = None
        self._resources: Optional[Dict[str, str]] = None
        self._loaded_layers: Set[int] = set()
    
    # ========================================================================
    # Layer 1: 元数据 (始终加载)
    # ========================================================================
    
    @property
    def metadata(self) -> SkillMetadata:
        """获取技能元数据 (Layer 1)"""
        if self._metadata is None:
            self._load_metadata()
            self._loaded_layers.add(1)
        return self._metadata
    
    def _load_metadata(self) -> None:
        """加载元数据"""
        skill_file = self.skill_path / "skill.yaml"
        if not skill_file.exists():
            raise FileNotFoundError(f"技能定义文件不存在: {skill_file}")
        
        with open(skill_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # P0-1 fix: 空 YAML 文件检查
        if data is None:
            raise ValueError(f"技能定义文件为空或格式无效: {skill_file}")
        
        self._metadata = SkillMetadata(
            id=data.get("id", self.skill_path.name),
            name=data.get("name", self.skill_path.name),
            version=data.get("version", "1.0"),
            triggers=data.get("triggers", []),
            keywords=data.get("keywords", []),
            sot_references=data.get("sot_references", []),
            category=data.get("category", "general"),
        )
        
        logger.debug(f"已加载技能元数据: {self._metadata.id}")
    
    # ========================================================================
    # Layer 2: 核心指令 (激活时加载)
    # ========================================================================
    
    @property
    def instructions(self) -> str:
        """获取核心指令 (Layer 2)"""
        if self._instructions is None:
            self._load_instructions()
            self._loaded_layers.add(2)
        return self._instructions
    
    def _load_instructions(self) -> None:
        """加载核心指令"""
        instructions_file = self.skill_path / "instructions.md"
        if not instructions_file.exists():
            self._instructions = ""
            logger.warning(f"技能指令文件不存在: {instructions_file}")
            return
        
        with open(instructions_file, "r", encoding="utf-8") as f:
            self._instructions = f.read()
        
        logger.debug(f"已加载技能指令: {self.metadata.id} ({len(self._instructions)} chars)")
    
    # ========================================================================
    # Layer 3: 完整资源 (按需加载)
    # ========================================================================
    
    @property
    def resources(self) -> Dict[str, str]:
        """获取完整资源 (Layer 3)"""
        if self._resources is None:
            self._load_resources()
            self._loaded_layers.add(3)
        return self._resources
    
    def _load_resources(self) -> None:
        """加载完整资源"""
        resources_dir = self.skill_path / "resources"
        self._resources = {}
        
        if not resources_dir.exists():
            logger.debug(f"技能资源目录不存在: {resources_dir}")
            return
        
        # P1-3 fix: 支持多种资源文件类型
        for resource_file in resources_dir.iterdir():
            if resource_file.is_file() and resource_file.suffix.lower() in SUPPORTED_RESOURCE_EXTENSIONS:
                try:
                    with open(resource_file, "r", encoding="utf-8") as f:
                        self._resources[resource_file.stem] = f.read()
                except UnicodeDecodeError:
                    logger.warning(f"无法读取资源文件 (编码问题): {resource_file}")
        
        logger.debug(f"已加载技能资源: {self.metadata.id} ({len(self._resources)} files)")
    
    def get_resource(self, name: str) -> Optional[str]:
        """获取特定资源"""
        return self.resources.get(name)
    
    def set_category(self, category: str) -> None:
        """
        设置技能类别 (P1-2 fix)
        
        Args:
            category: 新的类别名称
        """
        if self._metadata is None:
            _ = self.metadata  # 触发加载
        self._metadata.category = category
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def get_loaded_layers(self) -> Set[int]:
        """获取已加载的层"""
        return self._loaded_layers.copy()
    
    def get_token_estimate(self) -> Dict[str, int]:
        """估算 Token 消耗"""
        estimates = {
            "layer1_metadata": METADATA_TOKEN_ESTIMATE,
            "layer2_instructions": 0,
            "layer3_resources": 0,
        }
        
        if self._instructions:
            estimates["layer2_instructions"] = len(self._instructions) // TOKEN_ESTIMATION_FACTOR
        
        if self._resources:
            total_chars = sum(len(content) for content in self._resources.values())
            estimates["layer3_resources"] = total_chars // TOKEN_ESTIMATION_FACTOR
        
        return estimates
    
    def __repr__(self) -> str:
        # P1-5 fix: 避免在 __repr__ 中触发 I/O
        skill_id = self._metadata.id if self._metadata else self.skill_path.name
        return f"Skill(id={skill_id}, layers={self._loaded_layers})"


class SkillRegistry:
    """
    技能注册表 (线程安全)
    
    管理所有已注册技能，支持:
    - 按 ID 查找
    - 按关键词匹配
    - 按类别筛选
    
    注意: 此类是线程安全的，可在多线程环境中使用
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._by_category: Dict[str, List[str]] = {}
        self._lock = threading.RLock()  # 可重入锁，支持嵌套调用
    
    def register(self, skill: Skill) -> None:
        """注册技能 (线程安全)"""
        skill_id = skill.metadata.id
        category = skill.metadata.category
        
        with self._lock:
            self._skills[skill_id] = skill
            
            if category not in self._by_category:
                self._by_category[category] = []
            self._by_category[category].append(skill_id)
        
        logger.info(f"已注册技能: {skill_id} (category={category})")
    
    def unregister(self, skill_id: str) -> bool:
        """
        注销技能 (线程安全)
        
        Args:
            skill_id: 技能 ID
            
        Returns:
            是否成功注销
        """
        with self._lock:
            if skill_id not in self._skills:
                return False
            
            skill = self._skills.pop(skill_id)
            category = skill.metadata.category
            
            if category in self._by_category and skill_id in self._by_category[category]:
                self._by_category[category].remove(skill_id)
            
            logger.info(f"已注销技能: {skill_id}")
            return True
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """按 ID 获取技能 (线程安全)"""
        with self._lock:
            return self._skills.get(skill_id)
    
    def find_by_query(self, query: str) -> List[Skill]:
        """按查询匹配技能 (线程安全)"""
        with self._lock:
            matched = []
            for skill in self._skills.values():
                if skill.metadata.matches(query):
                    matched.append(skill)
            return matched
    
    def find_by_category(self, category: str) -> List[Skill]:
        """按类别获取技能 (线程安全)"""
        with self._lock:
            skill_ids = self._by_category.get(category, [])
            return [self._skills[sid] for sid in skill_ids if sid in self._skills]
    
    def list_all(self) -> List[Skill]:
        """列出所有技能 (线程安全)"""
        with self._lock:
            return list(self._skills.values())
    
    def list_categories(self) -> List[str]:
        """列出所有类别 (线程安全)"""
        with self._lock:
            return list(self._by_category.keys())
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._skills)
    
    def __contains__(self, skill_id: str) -> bool:
        with self._lock:
            return skill_id in self._skills
