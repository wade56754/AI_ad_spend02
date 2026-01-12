"""
性能监控

收集性能指标和错误统计

版本: v1.0
基准: 标准性能监控模式
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_count: int = 0
    total_tokens: int = 0
    total_time: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    agent_executions: Dict[str, int] = field(default_factory=dict)
    model_usage: Dict[str, int] = field(default_factory=dict)


class PerformanceMonitor:
    """性能监控器 - 收集和报告性能指标"""
    
    def __init__(self):
        """初始化监控器"""
        self.metrics = PerformanceMetrics()
        self._lock = Lock()
        self._start_time = time.time()
    
    def record_execution(
        self,
        agent_id: str,
        model: str,
        tokens: int,
        time_taken: float,
        success: bool
    ):
        """
        记录执行
        
        Args:
            agent_id: 代理 ID
            model: 使用的模型
            tokens: Token 使用量
            time_taken: 执行时间（秒）
            success: 是否成功
        """
        with self._lock:
            self.metrics.execution_count += 1
            self.metrics.total_tokens += tokens
            self.metrics.total_time += time_taken
            
            if not success:
                self.metrics.error_count += 1
            
            # 记录代理执行次数
            self.metrics.agent_executions[agent_id] = (
                self.metrics.agent_executions.get(agent_id, 0) + 1
            )
            
            # 记录模型使用
            self.metrics.model_usage[model] = (
                self.metrics.model_usage.get(model, 0) + tokens
            )
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self._lock:
            self.metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self._lock:
            self.metrics.cache_misses += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            指标字典
        """
        with self._lock:
            execution_count = self.metrics.execution_count
            cache_total = self.metrics.cache_hits + self.metrics.cache_misses
            
            return {
                "execution_count": execution_count,
                "total_tokens": self.metrics.total_tokens,
                "avg_tokens": (
                    self.metrics.total_tokens / execution_count
                    if execution_count > 0 else 0
                ),
                "total_time": self.metrics.total_time,
                "avg_time": (
                    self.metrics.total_time / execution_count
                    if execution_count > 0 else 0
                ),
                "error_count": self.metrics.error_count,
                "error_rate": (
                    self.metrics.error_count / execution_count
                    if execution_count > 0 else 0
                ),
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_rate": (
                    self.metrics.cache_hits / cache_total
                    if cache_total > 0 else 0
                ),
                "agent_executions": dict(self.metrics.agent_executions),
                "model_usage": dict(self.metrics.model_usage),
                "uptime": time.time() - self._start_time,
            }
    
    def reset(self):
        """重置指标"""
        with self._lock:
            self.metrics = PerformanceMetrics()
            self._start_time = time.time()
        logger.info("Performance metrics reset")
    
    def log_summary(self):
        """记录性能摘要"""
        metrics = self.get_metrics()
        logger.info("Performance Summary:")
        logger.info(f"  Executions: {metrics['execution_count']}")
        logger.info(f"  Avg Time: {metrics['avg_time']:.2f}s")
        logger.info(f"  Avg Tokens: {metrics['avg_tokens']:.0f}")
        logger.info(f"  Error Rate: {metrics['error_rate']:.2%}")
        logger.info(f"  Cache Hit Rate: {metrics['cache_hit_rate']:.2%}")


# 全局监控实例
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """
    获取全局监控实例（单例模式）
    
    Returns:
        监控器对象
    """
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor

