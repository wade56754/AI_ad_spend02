"""
配置管理

支持环境变量和配置文件

版本: v1.0
基准: Python dotenv + 配置优先级
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .path_utils import get_project_root

logger = logging.getLogger(__name__)


class Config:
    """配置管理 - 统一管理所有配置"""
    
    def __init__(self):
        """
        初始化配置
        
        优先级: 环境变量 > 配置文件 > 默认值
        """
        # 项目路径
        self.project_root = self._get_project_root()
        
        # wshobson/agents 路径
        self.wshobson_agents_path = self._get_wshobson_agents_path()
        
        # 缓存配置
        self.cache_enabled = self._get_bool_env("CACHE_ENABLED", True)
        self.cache_size = self._get_int_env("CACHE_SIZE", 100)
        
        # API 配置
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # 性能配置
        self.max_concurrent_agents = self._get_int_env("MAX_CONCURRENT_AGENTS", 5)
        self.request_timeout = self._get_int_env("REQUEST_TIMEOUT", 60)
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        project_root_env = os.getenv("PROJECT_ROOT")
        if project_root_env:
            return Path(project_root_env).resolve()
        return get_project_root()
    
    def _get_wshobson_agents_path(self) -> Path:
        """获取 wshobson/agents 路径"""
        wshobson_path_env = os.getenv("WSHOBSON_AGENTS_PATH")
        if wshobson_path_env:
            return Path(wshobson_path_env).resolve()
        return self.project_root / "external" / "wshobson-agents"
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """获取布尔环境变量"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def _get_int_env(self, key: str, default: int) -> int:
        """获取整数环境变量"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default {default}")
            return default
    
    def validate(self) -> bool:
        """
        验证配置
        
        Returns:
            配置是否有效
        """
        errors = []
        
        # 验证项目根目录
        if not self.project_root.exists():
            errors.append(f"Project root does not exist: {self.project_root}")
        
        # 验证 wshobson/agents 路径（可选）
        if not self.wshobson_agents_path.exists():
            logger.warning(f"wshobson/agents path does not exist: {self.wshobson_agents_path}")
        
        # 验证缓存大小
        if self.cache_size <= 0:
            errors.append(f"Invalid cache size: {self.cache_size}")
        
        # 验证并发数
        if self.max_concurrent_agents <= 0:
            errors.append(f"Invalid max concurrent agents: {self.max_concurrent_agents}")
        
        if errors:
            for error in errors:
                logger.error(f"Config validation error: {error}")
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """转换为字典（隐藏敏感信息）"""
        return {
            "project_root": str(self.project_root),
            "wshobson_agents_path": str(self.wshobson_agents_path),
            "cache_enabled": self.cache_enabled,
            "cache_size": self.cache_size,
            "log_level": self.log_level,
            "max_concurrent_agents": self.max_concurrent_agents,
            "request_timeout": self.request_timeout,
            "anthropic_api_key_set": bool(self.anthropic_api_key),
        }


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例（单例模式）
    
    Returns:
        配置对象
    """
    global _config
    if _config is None:
        _config = Config()
        if not _config.validate():
            logger.warning("Config validation failed, but continuing with defaults")
    return _config

