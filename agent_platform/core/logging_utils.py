"""
Agent Platform Observability - Unified Logging Utilities

提供结构化日志和错误分类，用于 Agent 执行链路追踪。

基准对齐：
- Agent Layer Freeze v1.0 (AGENT_ORCHESTRATION_PIPELINE.md)
- MASTER.md v3.5

使用示例：
    from agent_platform.core.logging_utils import log_event, ErrorKind

    # 在 Agent 中记录事件
    log_event(
        run_id=context.run_id,
        agent_name="be",
        flow="be_then_test",
        stage="start",
        success=True,
        error_kind=ErrorKind.OK,
        message="Starting backend code generation"
    )
"""

import logging
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

# 配置模块级 logger
logger = logging.getLogger("agent_platform.observability")


class ErrorKind(str, Enum):
    """
    错误分类枚举。

    用于标识 Agent 执行失败的根因类别，便于：
    - 自动告警分级
    - 重试策略选择
    - 根因分析统计

    Categories:
        OK: 执行成功，无错误
        VALIDATION_ERROR: 输入验证失败（参数缺失、格式错误）
        SOT_VIOLATION: 违反 SoT 规则（状态机、业务规则、错误码）
        LLM_ERROR: LLM 调用失败（API 超时、Token 限制、内容过滤）
        INFRA_ERROR: 基础设施错误（数据库、网络、文件系统）
        AGENT_ERROR: Agent 内部错误（流程编排、子 Agent 调用失败）
        UNKNOWN: 未分类错误
    """
    OK = "OK"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SOT_VIOLATION = "SOT_VIOLATION"
    LLM_ERROR = "LLM_ERROR"
    INFRA_ERROR = "INFRA_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    UNKNOWN = "UNKNOWN"


def log_event(
    run_id: str,
    agent_name: str,
    flow: str,
    stage: str,
    success: bool,
    error_kind: ErrorKind = ErrorKind.OK,
    message: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    记录结构化的 Agent 执行事件。

    生成统一格式的日志条目，支持：
    - 分布式追踪（通过 run_id）
    - 执行阶段标记（start/end/error）
    - 错误根因分类
    - 扩展元数据

    Args:
        run_id: 执行链路唯一标识（UUID 格式）
        agent_name: Agent 名称（如 "be", "fe", "test", "orch"）
        flow: 执行流程名称（如 "be_then_test", "backend_only"）
        stage: 执行阶段（如 "start", "end", "error", "step:backend", "step:test"）
        success: 当前阶段是否成功
        error_kind: 错误分类（默认 OK）
        message: 人类可读的事件描述
        extra: 额外的结构化数据（可选）

    Returns:
        生成的日志条目字典，包含所有字段和时间戳

    Example:
        >>> entry = log_event(
        ...     run_id="abc-123",
        ...     agent_name="orch",
        ...     flow="be_then_test",
        ...     stage="start",
        ...     success=True,
        ...     error_kind=ErrorKind.OK,
        ...     message="Starting orchestration"
        ... )
        >>> print(entry["agent_name"])
        orch
    """
    # 构建日志条目
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "agent_name": agent_name,
        "flow": flow,
        "stage": stage,
        "success": success,
        "error_kind": error_kind.value if isinstance(error_kind, ErrorKind) else error_kind,
        "message": message,
    }

    # 添加扩展数据
    if extra:
        entry["extra"] = extra

    # 根据 success 和 stage 选择日志级别
    if not success or stage == "error":
        log_level = logging.ERROR
    elif stage.startswith("warn"):
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    # 输出结构化日志
    logger.log(
        log_level,
        json.dumps(entry, ensure_ascii=False, default=str),
    )

    return entry


def derive_error_kind(error: Exception) -> ErrorKind:
    """
    从异常类型推断 ErrorKind。

    用于自动分类捕获的异常，减少手动指定 error_kind 的需要。

    Args:
        error: 捕获的异常对象

    Returns:
        推断的 ErrorKind 枚举值

    Example:
        >>> from agent_platform.core.exceptions import AgentExecutionError
        >>> kind = derive_error_kind(AgentExecutionError("test", "failed"))
        >>> print(kind)
        ErrorKind.AGENT_ERROR
    """
    # 延迟导入避免循环依赖
    from .exceptions import (
        AgentPlatformError,
        AgentExecutionError,
        LLMClientError,
    )

    error_type = type(error).__name__
    error_msg = str(error).lower()

    # LLM 相关错误
    if isinstance(error, LLMClientError):
        return ErrorKind.LLM_ERROR

    # Agent 执行错误
    if isinstance(error, AgentExecutionError):
        return ErrorKind.AGENT_ERROR

    # 平台级错误
    if isinstance(error, AgentPlatformError):
        return ErrorKind.INFRA_ERROR

    # 验证错误
    if any(kw in error_type.lower() for kw in ["validation", "value", "type"]):
        return ErrorKind.VALIDATION_ERROR
    if any(kw in error_msg for kw in ["required", "missing", "invalid"]):
        return ErrorKind.VALIDATION_ERROR

    # SoT 违规
    if any(kw in error_msg for kw in ["sot", "state machine", "business rule"]):
        return ErrorKind.SOT_VIOLATION

    # 基础设施错误
    # Use specific error type names to avoid false positives (e.g., "io" in "exception")
    infra_error_types = ["connectionerror", "timeouterror", "ioerror", "oserror", "networkerror"]
    if error_type.lower() in infra_error_types or any(
        error_type.lower().endswith(suffix) for suffix in ["connectionerror", "timeouterror"]
    ):
        return ErrorKind.INFRA_ERROR

    return ErrorKind.UNKNOWN


def create_error_response(
    error: Exception,
    run_id: str,
    agent_name: str,
    flow: str = "unknown",
) -> Dict[str, Any]:
    """
    创建标准化的错误响应。

    结合 derive_error_kind 和 log_event，生成完整的错误响应结构。

    Args:
        error: 捕获的异常
        run_id: 执行链路 ID
        agent_name: Agent 名称
        flow: 执行流程名称

    Returns:
        符合 AgentResponse 结构的错误响应字典
    """
    error_kind = derive_error_kind(error)

    # 记录错误事件
    log_event(
        run_id=run_id,
        agent_name=agent_name,
        flow=flow,
        stage="error",
        success=False,
        error_kind=error_kind,
        message=str(error),
        extra={"error_type": type(error).__name__},
    )

    return {
        "success": False,
        "data": None,
        "error": str(error),
        "error_kind": error_kind.value,
    }


__all__ = [
    "ErrorKind",
    "log_event",
    "derive_error_kind",
    "create_error_response",
]
