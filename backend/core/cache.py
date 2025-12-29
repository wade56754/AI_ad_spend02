"""
Redis 缓存工具模块

Phase 3 性能优化 (TASK-PERF-001)

功能:
- 统一的缓存接口
- 自动序列化/反序列化
- 缓存键命名规范
- 优雅降级 (Redis 不可用时回退到无缓存)

使用示例:
```python
from backend.core.cache import cache_manager

# 简单缓存
await cache_manager.set("key", {"data": "value"}, ttl=60)
data = await cache_manager.get("key")

# 装饰器模式
@cache_manager.cached(prefix="dashboard", ttl=60)
async def get_dashboard_data(user_id: str):
    return expensive_query()
```
"""

import json
import hashlib
import logging
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheManager:
    """
    Redis 缓存管理器

    特性:
    - 连接池管理
    - 自动重连
    - JSON 序列化
    - 优雅降级
    """

    def __init__(self):
        self._client: Optional[Any] = None
        self._enabled: bool = False
        self._connected: bool = False
        self._default_ttl: int = 300

    async def initialize(self, redis_url: str, enabled: bool = True, default_ttl: int = 300):
        """
        初始化 Redis 连接

        Args:
            redis_url: Redis 连接 URL
            enabled: 是否启用缓存
            default_ttl: 默认过期时间（秒）
        """
        self._enabled = enabled
        self._default_ttl = default_ttl

        if not enabled:
            logger.info("Redis 缓存已禁用")
            return

        try:
            import redis.asyncio as redis
            self._client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # 测试连接
            await self._client.ping()
            self._connected = True
            logger.info(f"Redis 连接成功: {redis_url.split('@')[-1]}")
        except ImportError:
            logger.warning("redis 包未安装，缓存功能禁用")
            self._enabled = False
        except Exception as e:
            logger.warning(f"Redis 连接失败，降级为无缓存模式: {e}")
            self._connected = False

    async def close(self):
        """关闭 Redis 连接"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis 连接已关闭")

    @property
    def is_available(self) -> bool:
        """检查缓存是否可用"""
        return self._enabled and self._connected and self._client is not None

    def _serialize(self, value: Any) -> str:
        """序列化值为 JSON 字符串"""
        return json.dumps(value, ensure_ascii=False, default=str)

    def _deserialize(self, value: str) -> Any:
        """反序列化 JSON 字符串"""
        return json.loads(value)

    @staticmethod
    def make_key(*parts: str) -> str:
        """
        生成缓存键

        命名规范: ai_ads:{module}:{entity}:{id}
        例如: ai_ads:dashboard:overview:user_123
        """
        return "ai_ads:" + ":".join(str(p) for p in parts)

    @staticmethod
    def hash_params(**kwargs) -> str:
        """将参数哈希为短字符串，用于缓存键"""
        if not kwargs:
            return "default"
        sorted_items = sorted(kwargs.items())
        param_str = json.dumps(sorted_items, sort_keys=True, default=str)
        return hashlib.md5(param_str.encode()).hexdigest()[:12]

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或失败返回 None
        """
        if not self.is_available:
            return None

        try:
            value = await self._client.get(key)
            if value is not None:
                logger.debug(f"缓存命中: {key}")
                return self._deserialize(value)
            logger.debug(f"缓存未命中: {key}")
            return None
        except Exception as e:
            logger.warning(f"缓存读取失败: {key}, 错误: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值

        Returns:
            是否成功
        """
        if not self.is_available:
            return False

        try:
            ttl = ttl or self._default_ttl
            serialized = self._serialize(value)
            await self._client.setex(key, ttl, serialized)
            logger.debug(f"缓存写入: {key}, TTL={ttl}s")
            return True
        except Exception as e:
            logger.warning(f"缓存写入失败: {key}, 错误: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available:
            return False

        try:
            await self._client.delete(key)
            logger.debug(f"缓存删除: {key}")
            return True
        except Exception as e:
            logger.warning(f"缓存删除失败: {key}, 错误: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        批量删除匹配模式的缓存

        Args:
            pattern: 键模式，如 "ai_ads:dashboard:*"

        Returns:
            删除的键数量
        """
        if not self.is_available:
            return 0

        try:
            count = 0
            async for key in self._client.scan_iter(match=pattern, count=100):
                await self._client.delete(key)
                count += 1
            logger.info(f"批量删除缓存: {pattern}, 删除 {count} 个键")
            return count
        except Exception as e:
            logger.warning(f"批量删除缓存失败: {pattern}, 错误: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: Optional[int] = None
    ) -> T:
        """
        获取缓存值，不存在则通过 factory 生成并缓存

        Args:
            key: 缓存键
            factory: 值生成函数
            ttl: 过期时间

        Returns:
            缓存值或新生成的值
        """
        # 尝试从缓存获取
        cached = await self.get(key)
        if cached is not None:
            return cached

        # 生成新值
        if callable(factory):
            import asyncio
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory

        # 写入缓存
        await self.set(key, value, ttl)
        return value

    def cached(
        self,
        prefix: str,
        ttl: Optional[int] = None,
        key_builder: Optional[Callable[..., str]] = None
    ):
        """
        缓存装饰器

        Args:
            prefix: 缓存键前缀
            ttl: 过期时间
            key_builder: 自定义键生成函数

        Example:
            @cache_manager.cached(prefix="dashboard", ttl=60)
            async def get_overview(user_id: str):
                return await expensive_query()
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # 生成缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # 默认键: prefix:func_name:params_hash
                    params_hash = self.hash_params(**kwargs)
                    cache_key = self.make_key(prefix, func.__name__, params_hash)

                # 尝试获取缓存
                cached = await self.get(cache_key)
                if cached is not None:
                    return cached

                # 执行原函数
                result = await func(*args, **kwargs)

                # 写入缓存
                await self.set(cache_key, result, ttl)

                return result
            return wrapper
        return decorator

    async def invalidate_dashboard(self, user_id: Optional[str] = None):
        """
        失效 Dashboard 缓存

        Args:
            user_id: 指定用户 ID，None 则失效所有
        """
        if user_id:
            pattern = f"ai_ads:dashboard:*:{user_id}*"
        else:
            pattern = "ai_ads:dashboard:*"
        await self.delete_pattern(pattern)

    async def invalidate_list(self, entity: str):
        """
        失效列表缓存

        Args:
            entity: 实体类型 (projects, accounts, etc.)
        """
        pattern = f"ai_ads:{entity}:list:*"
        await self.delete_pattern(pattern)


# 全局缓存管理器实例
cache_manager = CacheManager()


async def init_cache():
    """初始化缓存（应用启动时调用）"""
    from backend.core.config import get_settings
    settings = get_settings()
    await cache_manager.initialize(
        redis_url=settings.redis_url,
        enabled=settings.redis_enabled,
        default_ttl=settings.cache_ttl_default
    )


async def close_cache():
    """关闭缓存（应用关闭时调用）"""
    await cache_manager.close()
