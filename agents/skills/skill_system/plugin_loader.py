"""
插件加载器

支持 wshobson/agents 和自定义插件的统一加载

版本: v1.0
基准: wshobson/agents 插件系统
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .wshobson_agent_loader import WshobsonAgentLoader, Agent
from .wshobson_skill_loader import WshobsonSkillLoader
from .base import Skill
from .path_utils import get_project_root
from .config import get_config

logger = logging.getLogger(__name__)


class Plugin:
    """插件定义"""
    
    def __init__(self, plugin_id: str, definition: Dict[str, Any]):
        """
        初始化插件
        
        Args:
            plugin_id: 插件 ID
            definition: 插件定义
        """
        self.id = plugin_id
        self.name = definition.get("name", plugin_id)
        self.version = definition.get("version", "1.0")
        self.source = definition.get("source", "custom")
        self.description = definition.get("description", "")
        self.category = definition.get("category", "general")
        self.agents = definition.get("agents", [])
        self.skills = definition.get("skills", [])
        self.tools = definition.get("tools", [])
        self.dependencies = definition.get("dependencies", [])
        self._definition = definition
        # P1-4 fix: 在类定义中明确声明这些属性
        self._loaded_agents: List[Agent] = []
        self._loaded_skills: List[Skill] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "description": self.description,
            "category": self.category,
            "agents": self.agents,
            "skills": self.skills,
            "tools": self.tools,
            "dependencies": self.dependencies,
        }


class PluginLoader:
    """插件加载器 - 支持 wshobson/agents 和自定义插件"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化插件加载器
        
        Args:
            project_root: 项目根目录
        """
        config = get_config()
        
        if project_root:
            self.project_root = Path(project_root)
        else:
            # P1-1 fix: 使用统一的路径工具函数
            self.project_root = config.project_root
        
        # 初始化加载器
        self.wshobson_agent_loader = WshobsonAgentLoader()
        self.wshobson_skill_loader = WshobsonSkillLoader()
        
        # 插件市场路径
        self.marketplace_path = self.project_root / ".claude-plugin" / "marketplace.json"
        
        # 加载插件市场
        self.marketplace = self._load_marketplace()
    
    def _load_marketplace(self) -> Dict[str, Dict]:
        """
        加载插件市场
        
        Returns:
            插件市场字典
        """
        if not self.marketplace_path.exists():
            return {}
        
        try:
            with open(self.marketplace_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                plugins = {}
                for plugin_def in data.get("plugins", []):
                    plugin_id = plugin_def.get("id")
                    if plugin_id:
                        plugins[plugin_id] = plugin_def
                return plugins
        except Exception as e:
            # P1-2 fix: 使用 logging 而不是 print
            logger.warning(f"Failed to load marketplace {self.marketplace_path}: {e}")
            return {}
    
    def load_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        加载插件（支持多种来源）
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            插件对象，如果不存在则返回 None
        """
        plugin_def = self._get_plugin_definition(plugin_id)
        if not plugin_def:
            return None
        
        source = plugin_def.get("source", "custom")
        
        if source == "wshobson/agents":
            # 从 wshobson/agents 加载
            return self._load_from_wshobson(plugin_def)
        elif source == "custom":
            # 从自定义目录加载
            return self._load_from_custom(plugin_def)
        else:
            raise ValueError(f"Unknown plugin source: {source}")
    
    def _get_plugin_definition(self, plugin_id: str) -> Optional[Dict]:
        """
        获取插件定义
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            插件定义字典
        """
        return self.marketplace.get(plugin_id)
    
    def _load_from_wshobson(self, plugin_def: Dict) -> Plugin:
        """
        从 wshobson/agents 加载插件
        
        Args:
            plugin_def: 插件定义
            
        Returns:
            插件对象
        """
        # 加载代理
        agents = []
        for agent_def in plugin_def.get("agents", []):
            agent_id = agent_def.get("id")
            if agent_id:
                agent = self.wshobson_agent_loader.load_agent(agent_id)
                if agent:
                    agents.append(agent)
        
        # 加载技能
        skills = []
        for skill_def in plugin_def.get("skills", []):
            skill_id = skill_def.get("id")
            if skill_id:
                skill = self.wshobson_skill_loader.load_skill(skill_id)
                if skill:
                    skills.append(skill)
        
        # P1-4 fix: 创建插件对象（属性已在 __init__ 中定义）
        plugin = Plugin(plugin_def["id"], plugin_def)
        
        # 将加载的代理和技能附加到插件
        plugin._loaded_agents = agents
        plugin._loaded_skills = skills
        
        return plugin
    
    def _load_from_custom(self, plugin_def: Dict) -> Plugin:
        """
        从自定义目录加载插件
        
        Args:
            plugin_def: 插件定义
            
        Returns:
            插件对象
        """
        # 自定义插件从 .claude/skills/ 目录加载
        plugin = Plugin(plugin_def["id"], plugin_def)
        return plugin
    
    def load_all_plugins(self) -> Dict[str, Plugin]:
        """
        加载所有可用插件
        
        Returns:
            插件字典
        """
        plugins = {}
        for plugin_id in self.marketplace.keys():
            plugin = self.load_plugin(plugin_id)
            if plugin:
                plugins[plugin_id] = plugin
        return plugins
    
    def get_plugins_by_category(self, category: str) -> List[Plugin]:
        """
        按类别获取插件
        
        Args:
            category: 插件类别
            
        Returns:
            插件列表
        """
        all_plugins = self.load_all_plugins()
        return [plugin for plugin in all_plugins.values() if plugin.category == category]
    
    def get_plugins_by_source(self, source: str) -> List[Plugin]:
        """
        按来源获取插件
        
        Args:
            source: 插件来源 ("wshobson/agents" 或 "custom")
            
        Returns:
            插件列表
        """
        all_plugins = self.load_all_plugins()
        return [plugin for plugin in all_plugins.values() if plugin.source == source]

