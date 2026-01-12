"""
缓存机制

LRU 缓存代理和技能定义，提升性能

版本: v1.0
基准: Python functools.lru_cache + 自定义 LRU
"""

import logging
from typing import Dict, Optional, Any, TypeVar
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)

# 使用类型变量避免循环导入
T = TypeVar('T')


class LRUCache:
    """LRU 缓存实现"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化 LRU 缓存
        
        Args:
            max_size: 最大缓存大小
        """
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回 None
        """
        with self._lock:
            if key in self._cache:
                # 移动到末尾（最近使用）
                self._cache.move_to_end(key)
                return self._cache[key]
            return None
    
    def set(self, key: str, value: Any):
        """
        设置缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        with self._lock:
            if key in self._cache:
                # 更新现有项
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                # 添加新项
                if len(self._cache) >= self.max_size:
                    # 删除最旧的项
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"Cache evicted: {oldest_key}")
                
                self._cache[key] = value
                logger.debug(f"Cache set: {key}")
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "usage": len(self._cache) / self.max_size if self.max_size > 0 else 0
            }


class AgentCache:
    """代理缓存"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化代理缓存
        
        Args:
            max_size: 最大缓存大小
        """
        self._cache = LRUCache(max_size=max_size)
        self._hits = 0
        self._misses = 0
        self._lock = Lock()
    
    def get(self, agent_id: str) -> Optional[Any]:
        """
        获取代理
        
        Args:
            agent_id: 代理 ID
            
        Returns:
            代理对象，如果不存在则返回 None
        """
        agent = self._cache.get(agent_id)
        with self._lock:
            if agent:
                self._hits += 1
            else:
                self._misses += 1
        return agent
    
    def set(self, agent_id: str, agent: Any):
        """
        设置代理
        
        Args:
            agent_id: 代理 ID
            agent: 代理对象
        """
        self._cache.set(agent_id, agent)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        with self._lock:
            self._hits = 0
            self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        cache_stats = self._cache.stats()
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
        
        return {
            **cache_stats,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }


class SkillCache:
    """技能缓存"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化技能缓存
        
        Args:
            max_size: 最大缓存大小
        """
        self._cache = LRUCache(max_size=max_size)
        self._hits = 0
        self._misses = 0
        self._lock = Lock()
    
    def get(self, skill_id: str) -> Optional[Any]:
        """
        获取技能
        
        Args:
            skill_id: 技能 ID
            
        Returns:
            技能对象，如果不存在则返回 None
        """
        skill = self._cache.get(skill_id)
        with self._lock:
            if skill:
                self._hits += 1
            else:
                self._misses += 1
        return skill
    
    def set(self, skill_id: str, skill: Any):
        """
        设置技能
        
        Args:
            skill_id: 技能 ID
            skill: 技能对象
        """
        self._cache.set(skill_id, skill)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        with self._lock:
            self._hits = 0
            self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        cache_stats = self._cache.stats()
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
        
        return {
            **cache_stats,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate
        }

