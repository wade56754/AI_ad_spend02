"""
统一日志模块

提供 AI 代码工厂的标准化日志配置和工具。

特性:
- 结构化日志格式
- 上下文追踪
- 阶段标记
- 性能计时

版本: v7.0
"""

import logging
import time
import functools
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

# 日志格式
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class LogContext:
    """日志上下文"""
    session_id: str = ""
    task_id: str = ""
    phase: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


# 全局上下文
_current_context: Optional[LogContext] = None


def get_logger(name: str) -> logging.Logger:
    """
    获取标准化 logger
    
    Args:
        name: logger 名称
        
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def set_context(
    session_id: str = "",
    task_id: str = "",
    phase: str = "",
    **extra: Any,
) -> None:
    """设置日志上下文"""
    global _current_context
    _current_context = LogContext(
        session_id=session_id,
        task_id=task_id,
        phase=phase,
        extra=extra,
    )


def get_context() -> Optional[LogContext]:
    """获取当前日志上下文"""
    return _current_context


@contextmanager
def log_context(
    session_id: str = "",
    task_id: str = "",
    phase: str = "",
    **extra: Any,
):
    """
    临时设置日志上下文
    
    使用示例:
        with log_context(phase="CLARIFY", task_id="task-001"):
            logger.info("开始澄清阶段")
    """
    global _current_context
    old_context = _current_context
    
    _current_context = LogContext(
        session_id=session_id or (old_context.session_id if old_context else ""),
        task_id=task_id or (old_context.task_id if old_context else ""),
        phase=phase,
        extra=extra,
    )
    
    try:
        yield _current_context
    finally:
        _current_context = old_context


def log_phase(phase_name: str):
    """
    阶段日志装饰器
    
    使用示例:
        @log_phase("IMPLEMENT")
        def implement_feature(spec):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            start_time = time.time()
            logger.info(f"[{phase_name}] 阶段开始")
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"[{phase_name}] 阶段完成 | 耗时: {elapsed:.2f}s")
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[{phase_name}] 阶段失败 | 耗时: {elapsed:.2f}s | 错误: {e}")
                raise
        
        return wrapper
    return decorator


def log_timing(operation_name: str):
    """
    计时日志装饰器
    
    使用示例:
        @log_timing("加载技能")
        def load_skills():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{operation_name} | 耗时: {elapsed:.3f}s")
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(f"{operation_name} 失败 | 耗时: {elapsed:.3f}s | 错误: {e}")
                raise
        
        return wrapper
    return decorator


class PhaseLogger:
    """
    阶段日志器
    
    用于记录流水线阶段的详细日志。
    
    使用示例:
        logger = PhaseLogger("CLARIFY")
        logger.start("分析需求")
        logger.progress("解析完成", items_processed=10)
        logger.end("需求分析完成")
    """
    
    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self._logger = get_logger(f"code_factory.{phase_name}")
        self._start_time: Optional[float] = None
        self._step_count = 0
    
    def start(self, message: str = "开始") -> None:
        """记录阶段开始"""
        self._start_time = time.time()
        self._step_count = 0
        self._logger.info(f"[{self.phase_name}] ▶ {message}")
    
    def progress(self, message: str, **metrics: Any) -> None:
        """记录进度"""
        self._step_count += 1
        metrics_str = " | ".join(f"{k}={v}" for k, v in metrics.items())
        
        if metrics_str:
            self._logger.info(f"[{self.phase_name}] ● Step {self._step_count}: {message} | {metrics_str}")
        else:
            self._logger.info(f"[{self.phase_name}] ● Step {self._step_count}: {message}")
    
    def warning(self, message: str) -> None:
        """记录警告"""
        self._logger.warning(f"[{self.phase_name}] ⚠ {message}")
    
    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """记录错误"""
        if error:
            self._logger.error(f"[{self.phase_name}] ✖ {message} | {error}")
        else:
            self._logger.error(f"[{self.phase_name}] ✖ {message}")
    
    def end(self, message: str = "完成", success: bool = True) -> float:
        """
        记录阶段结束
        
        Returns:
            阶段耗时 (秒)
        """
        elapsed = time.time() - (self._start_time or time.time())
        
        if success:
            self._logger.info(
                f"[{self.phase_name}] ■ {message} | 耗时: {elapsed:.2f}s | 步骤: {self._step_count}"
            )
        else:
            self._logger.error(
                f"[{self.phase_name}] ✖ {message} | 耗时: {elapsed:.2f}s | 步骤: {self._step_count}"
            )
        
        return elapsed


__all__ = [
    "get_logger",
    "set_context",
    "get_context",
    "log_context",
    "log_phase",
    "log_timing",
    "PhaseLogger",
    "LogContext",
]
