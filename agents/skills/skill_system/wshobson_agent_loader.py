"""
wshobson/agents 代理加载器

从 wshobson/agents 项目加载代理定义，适配到项目需求

版本: v1.0
基准: wshobson/agents + AI 广告代投系统需求
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .base import SkillMetadata
from .path_utils import get_project_root, get_wshobson_agents_path
from .cache import AgentCache
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """代理定义"""
    id: str
    name: str
    source: str = "wshobson/agents"
    model_tier: str = "tier2"
    category: str = "general"
    description: str = ""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "model_tier": self.model_tier,
            "category": self.category,
            "description": self.description,
            "skills": self.skills,
            "tools": self.tools,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
        }


class WshobsonAgentLoader:
    """加载 wshobson/agents 的代理"""
    
    def __init__(self, wshobson_repo_path: Optional[Path] = None):
        """
        初始化加载器
        
        Args:
            wshobson_repo_path: wshobson/agents 仓库路径
                               如果为 None，则使用默认路径 external/wshobson-agents
        """
        config = get_config()
        
        if wshobson_repo_path:
            self.repo_path = Path(wshobson_repo_path)
        else:
            # P1-1 fix: 使用统一的路径工具函数
            self.repo_path = config.wshobson_agents_path
        
        # 加载映射配置
        mapping_file = Path(__file__).parent / "agent_mapping.yaml"
        self.mapping = self._load_mapping(mapping_file) if mapping_file.exists() else {}
        
        # 代理定义路径
        self.agents_dir = self.repo_path / ".claude-plugin" / "plugins"
        if not self.agents_dir.exists():
            # 尝试其他可能的路径
            self.agents_dir = self.repo_path / "plugins"
        
        # P1-1: 初始化缓存
        self.cache = AgentCache(max_size=config.cache_size) if config.cache_enabled else None
    
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
    
    def _get_default_path(self) -> Path:
        """获取默认路径"""
        # P1-1 fix: 使用统一的路径工具函数
        return get_wshobson_agents_path()
    
    def load_agent(self, agent_id: str) -> Optional[Agent]:
        """
        加载指定代理
        
        Args:
            agent_id: 代理 ID
            
        Returns:
            适配后的代理，如果不存在则返回 None
        """
        # P1-1: 检查缓存
        if self.cache:
            cached_agent = self.cache.get(agent_id)
            if cached_agent:
                try:
                    from ...code_factory.core.monitoring import get_monitor
                    get_monitor().record_cache_hit()
                except ImportError:
                    # 如果监控模块不可用，跳过
                    pass
                return cached_agent
            try:
                from ...code_factory.core.monitoring import get_monitor
                get_monitor().record_cache_miss()
            except ImportError:
                # 如果监控模块不可用，跳过
                pass
        
        # 1. 检查映射配置
        if agent_id in self.mapping:
            mapping = self.mapping[agent_id]
            source_id = mapping.get('source', agent_id)
        else:
            source_id = agent_id
        
        # 2. 从 wshobson/agents 加载代理定义
        agent_def = self._load_agent_definition(source_id)
        if not agent_def:
            return None
        
        # 3. 应用映射规则
        if agent_id in self.mapping:
            mapping = self.mapping[agent_id]
            agent_def.update({
                'id': mapping.get('target', agent_id),
                'model_tier': mapping.get('model_tier', 'tier2'),
                'category': mapping.get('category', 'general'),
                'description': mapping.get('description', agent_def.get('description', '')),
            })
        
        # 4. 适配项目 SoT 规范（通过适配器）
        # 这里返回基础代理，具体适配在 AgentAdapter 中完成
        
        agent = Agent(**agent_def)
        
        # P1-1: 存入缓存
        if self.cache:
            self.cache.set(agent_id, agent)
        
        return agent
    
    def _load_agent_definition(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        从 wshobson/agents 加载代理定义
        
        Args:
            agent_id: 代理 ID
            
        Returns:
            代理定义字典
        """
        # 尝试多种可能的路径和格式
        possible_paths = [
            self.agents_dir / agent_id / f"{agent_id}.md",
            self.agents_dir / agent_id / "agent.md",
            self.agents_dir / agent_id / "agent.yaml",
            self.repo_path / "plugins" / agent_id / f"{agent_id}.md",
        ]
        
        for path in possible_paths:
            if path.exists():
                return self._parse_agent_file(path)
        
        # P0-3 fix: 如果找不到，返回包含所有必需字段的默认定义
        # 尝试从映射配置获取默认值
        default_model_tier = "tier2"
        default_category = "general"
        default_source = "wshobson/agents"
        
        if agent_id in self.mapping:
            mapping = self.mapping[agent_id]
            default_model_tier = mapping.get('model_tier', default_model_tier)
            default_category = mapping.get('category', default_category)
        
        return {
            'id': agent_id,
            'name': agent_id.replace('-', ' ').title(),
            'source': default_source,
            'model_tier': default_model_tier,
            'category': default_category,
            'description': f"Agent: {agent_id}",
            'skills': [],
            'tools': [],
            'capabilities': [],
        }
    
    def _parse_agent_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析代理文件（支持 Markdown 和 YAML）
        
        Args:
            file_path: 文件路径
            
        Returns:
            代理定义字典
        """
        try:
            if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # Markdown 文件，解析 frontmatter
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单的 frontmatter 解析
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            return frontmatter or {}
        except Exception as e:
            # P1-2 fix: 使用 logging 而不是 print
            logger.warning(f"Failed to parse agent file {file_path}: {e}")
        
        return {}
    
    def load_all_agents(self) -> Dict[str, Agent]:
        """
        加载所有可用代理
        
        Returns:
            代理字典，key 为代理 ID
        """
        agents = {}
        
        # 从映射配置加载
        for agent_id in self.mapping.keys():
            agent = self.load_agent(agent_id)
            if agent:
                agents[agent.id] = agent
        
        # 如果 agents_dir 存在，扫描所有代理
        if self.agents_dir.exists():
            for agent_dir in self.agents_dir.iterdir():
                if agent_dir.is_dir():
                    agent_id = agent_dir.name
                    if agent_id not in agents:
                        agent = self.load_agent(agent_id)
                        if agent:
                            agents[agent.id] = agent
        
        return agents
    
    def get_agents_by_tier(self, tier: str) -> List[Agent]:
        """
        按模型层级获取代理
        
        Args:
            tier: 模型层级 ("tier1" 或 "tier2")
            
        Returns:
            代理列表
        """
        all_agents = self.load_all_agents()
        return [agent for agent in all_agents.values() if agent.model_tier == tier]

