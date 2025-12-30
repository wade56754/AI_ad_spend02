"""
APM (Application Performance Monitoring) 模块

Phase 3 性能优化 - TASK-PERF-003
提供 Sentry 错误追踪和 Prometheus 指标收集

SoT Ref: docs/sot/MASTER.md §7 (AI 防幻觉原则)
- 仅提示和记录，不阻断业务
"""

import time
from typing import Callable, Optional
from functools import wraps

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 延迟导入，避免未安装依赖时报错
_sentry_sdk = None
_prometheus_client = None
_instrumentator = None


def _lazy_import_sentry():
    """延迟导入 Sentry SDK"""
    global _sentry_sdk
    if _sentry_sdk is None:
        try:
            import sentry_sdk

            _sentry_sdk = sentry_sdk
        except ImportError:
            _sentry_sdk = False
    return _sentry_sdk if _sentry_sdk else None


def _lazy_import_prometheus():
    """延迟导入 Prometheus 客户端"""
    global _prometheus_client
    if _prometheus_client is None:
        try:
            import prometheus_client

            _prometheus_client = prometheus_client
        except ImportError:
            _prometheus_client = False
    return _prometheus_client if _prometheus_client else None


def _lazy_import_instrumentator():
    """延迟导入 Prometheus FastAPI 集成"""
    global _instrumentator
    if _instrumentator is None:
        try:
            from prometheus_fastapi_instrumentator import Instrumentator

            _instrumentator = Instrumentator
        except ImportError:
            _instrumentator = False
    return _instrumentator if _instrumentator else None


class APMConfig:
    """APM 配置类"""

    def __init__(
        self,
        # Sentry 配置
        sentry_dsn: Optional[str] = None,
        sentry_enabled: bool = False,
        sentry_environment: str = "development",
        sentry_traces_sample_rate: float = 0.1,
        sentry_profiles_sample_rate: float = 0.1,
        # Prometheus 配置
        prometheus_enabled: bool = False,
        prometheus_metrics_path: str = "/metrics",
        # 通用配置
        app_name: str = "ai-ad-spend",
        app_version: str = "1.0.0",
    ):
        self.sentry_dsn = sentry_dsn
        self.sentry_enabled = sentry_enabled and bool(sentry_dsn)
        self.sentry_environment = sentry_environment
        self.sentry_traces_sample_rate = sentry_traces_sample_rate
        self.sentry_profiles_sample_rate = sentry_profiles_sample_rate
        self.prometheus_enabled = prometheus_enabled
        self.prometheus_metrics_path = prometheus_metrics_path
        self.app_name = app_name
        self.app_version = app_version


# 自定义业务指标
class BusinessMetrics:
    """业务指标收集器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        prometheus = _lazy_import_prometheus()
        if not prometheus:
            self._initialized = True
            return

        # API 请求指标
        self.http_requests_total = prometheus.Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
        )

        self.http_request_duration_seconds = prometheus.Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )

        # 业务指标
        self.daily_reports_created = prometheus.Counter(
            "daily_reports_created_total",
            "Total daily reports created",
            ["project_id", "status"],
        )

        self.daily_reports_state_transitions = prometheus.Counter(
            "daily_reports_state_transitions_total",
            "Daily report state transitions",
            ["from_state", "to_state"],
        )

        self.topups_processed = prometheus.Counter(
            "topups_processed_total", "Total topups processed", ["status"]
        )

        self.reconciliations_completed = prometheus.Counter(
            "reconciliations_completed_total",
            "Total reconciliations completed",
            ["result"],
        )

        # 缓存指标
        self.cache_hits = prometheus.Counter(
            "cache_hits_total", "Total cache hits", ["cache_type"]
        )

        self.cache_misses = prometheus.Counter(
            "cache_misses_total", "Total cache misses", ["cache_type"]
        )

        # 数据库指标
        self.db_query_duration_seconds = prometheus.Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
        )

        self._initialized = True

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """记录 HTTP 请求指标"""
        if not _lazy_import_prometheus():
            return

        # 简化端点路径（移除 ID 参数）
        normalized_endpoint = self._normalize_endpoint(endpoint)

        self.http_requests_total.labels(
            method=method, endpoint=normalized_endpoint, status_code=str(status_code)
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method, endpoint=normalized_endpoint
        ).observe(duration)

    def record_daily_report_created(self, project_id: str, status: str):
        """记录日报创建"""
        if not _lazy_import_prometheus():
            return
        self.daily_reports_created.labels(project_id=project_id, status=status).inc()

    def record_state_transition(self, from_state: str, to_state: str):
        """记录状态流转"""
        if not _lazy_import_prometheus():
            return
        self.daily_reports_state_transitions.labels(
            from_state=from_state, to_state=to_state
        ).inc()

    def record_topup(self, status: str):
        """记录充值处理"""
        if not _lazy_import_prometheus():
            return
        self.topups_processed.labels(status=status).inc()

    def record_reconciliation(self, result: str):
        """记录对账完成"""
        if not _lazy_import_prometheus():
            return
        self.reconciliations_completed.labels(result=result).inc()

    def record_cache_hit(self, cache_type: str = "redis"):
        """记录缓存命中"""
        if not _lazy_import_prometheus():
            return
        self.cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str = "redis"):
        """记录缓存未命中"""
        if not _lazy_import_prometheus():
            return
        self.cache_misses.labels(cache_type=cache_type).inc()

    def record_db_query(self, operation: str, duration: float):
        """记录数据库查询耗时"""
        if not _lazy_import_prometheus():
            return
        self.db_query_duration_seconds.labels(operation=operation).observe(duration)

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        """
        规范化端点路径，将动态参数替换为占位符

        例如: /api/v1/projects/123 -> /api/v1/projects/{id}
        """
        import re

        # UUID 模式
        endpoint = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            endpoint,
        )
        # 纯数字 ID
        endpoint = re.sub(r"/\d+", "/{id}", endpoint)

        return endpoint


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus 指标收集中间件"""

    def __init__(self, app, metrics: BusinessMetrics, exclude_paths: set = None):
        super().__init__(app)
        self.metrics = metrics
        self.exclude_paths = exclude_paths or {
            "/metrics",
            "/health",
            "/healthz",
            "/readyz",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过排除的路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # 记录指标
        self.metrics.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )

        return response


def init_sentry(config: APMConfig) -> bool:
    """
    初始化 Sentry SDK

    返回: 是否成功初始化
    """
    if not config.sentry_enabled:
        print("INFO: Sentry 未启用 (sentry_enabled=False 或 sentry_dsn 未配置)")
        return False

    sentry_sdk = _lazy_import_sentry()
    if not sentry_sdk:
        print("WARNING: sentry-sdk 未安装，跳过 Sentry 初始化")
        return False

    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=config.sentry_dsn,
            environment=config.sentry_environment,
            traces_sample_rate=config.sentry_traces_sample_rate,
            profiles_sample_rate=config.sentry_profiles_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=None,  # 不自动捕获日志
                    event_level=40,  # 只捕获 ERROR 级别
                ),
            ],
            release=f"{config.app_name}@{config.app_version}",
            # 敏感数据过滤
            before_send=_sentry_before_send,
            send_default_pii=False,
        )

        print(f"SUCCESS: Sentry 初始化成功 (环境: {config.sentry_environment})")
        return True

    except Exception as e:
        print(f"ERROR: Sentry 初始化失败: {e}")
        return False


def _sentry_before_send(event, hint):
    """
    Sentry 事件发送前的过滤器

    用于过滤敏感信息和不需要上报的错误
    """
    # 过滤敏感字段
    if "request" in event:
        request_data = event["request"]

        # 过滤请求头中的敏感信息
        if "headers" in request_data:
            sensitive_headers = {"authorization", "cookie", "x-api-key"}
            request_data["headers"] = {
                k: "[FILTERED]" if k.lower() in sensitive_headers else v
                for k, v in request_data["headers"].items()
            }

        # 过滤请求体中的敏感信息
        if "data" in request_data and isinstance(request_data["data"], dict):
            sensitive_fields = {"password", "token", "secret", "key", "api_key"}
            request_data["data"] = {
                k: "[FILTERED]" if k.lower() in sensitive_fields else v
                for k, v in request_data["data"].items()
            }

    # 过滤用户信息
    if "user" in event and event["user"]:
        # 保留 id 和 email，移除其他敏感信息
        allowed_fields = {"id", "email", "username"}
        event["user"] = {k: v for k, v in event["user"].items() if k in allowed_fields}

    return event


def init_prometheus(app: FastAPI, config: APMConfig) -> bool:
    """
    初始化 Prometheus 指标收集

    返回: 是否成功初始化
    """
    if not config.prometheus_enabled:
        print("INFO: Prometheus 未启用 (prometheus_enabled=False)")
        return False

    prometheus = _lazy_import_prometheus()
    if not prometheus:
        print("WARNING: prometheus-client 未安装，跳过 Prometheus 初始化")
        return False

    Instrumentator = _lazy_import_instrumentator()
    if not Instrumentator:
        print("WARNING: prometheus-fastapi-instrumentator 未安装，使用自定义中间件")
        # 使用自定义中间件
        metrics = BusinessMetrics()
        app.add_middleware(MetricsMiddleware, metrics=metrics)

        # 添加 /metrics 端点
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response as FastAPIResponse

        @app.get(config.prometheus_metrics_path, include_in_schema=False)
        async def metrics_endpoint():
            return FastAPIResponse(
                content=generate_latest(), media_type=CONTENT_TYPE_LATEST
            )

        print(f"SUCCESS: Prometheus 自定义中间件初始化成功 (端点: {config.prometheus_metrics_path})")
        return True

    try:
        # 使用 prometheus-fastapi-instrumentator
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/healthz", "/readyz"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )

        # 添加默认指标
        instrumentator.add(instrumentator.metrics.default()).add(
            instrumentator.metrics.requests()
        ).add(instrumentator.metrics.latency())

        # 注入到应用
        instrumentator.instrument(app).expose(
            app, endpoint=config.prometheus_metrics_path, include_in_schema=False
        )

        print(
            f"SUCCESS: Prometheus Instrumentator 初始化成功 (端点: {config.prometheus_metrics_path})"
        )
        return True

    except Exception as e:
        print(f"ERROR: Prometheus 初始化失败: {e}")
        return False


def setup_apm(app: FastAPI, config: APMConfig) -> dict:
    """
    设置 APM 监控

    Args:
        app: FastAPI 应用实例
        config: APM 配置

    Returns:
        初始化状态字典
    """
    status = {
        "sentry": False,
        "prometheus": False,
    }

    # 初始化 Sentry
    status["sentry"] = init_sentry(config)

    # 初始化 Prometheus
    status["prometheus"] = init_prometheus(app, config)

    return status


# 导出业务指标实例
metrics = BusinessMetrics()


# 装饰器：追踪函数执行
def trace_function(operation_name: str = None):
    """
    函数追踪装饰器

    自动记录函数执行到 Sentry 和 Prometheus
    """

    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            sentry_sdk = _lazy_import_sentry()
            if sentry_sdk:
                with sentry_sdk.start_span(op="function", description=name):
                    try:
                        result = await func(*args, **kwargs)
                        duration = time.time() - start_time
                        metrics.record_db_query(name, duration)
                        return result
                    except Exception as e:
                        sentry_sdk.capture_exception(e)
                        raise
            else:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_db_query(name, duration)
                return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            sentry_sdk = _lazy_import_sentry()
            if sentry_sdk:
                with sentry_sdk.start_span(op="function", description=name):
                    try:
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time
                        metrics.record_db_query(name, duration)
                        return result
                    except Exception as e:
                        sentry_sdk.capture_exception(e)
                        raise
            else:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_db_query(name, duration)
                return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def capture_exception(exception: Exception, **extra):
    """
    手动捕获异常到 Sentry

    Args:
        exception: 异常对象
        **extra: 额外上下文信息
    """
    sentry_sdk = _lazy_import_sentry()
    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **extra):
    """
    手动发送消息到 Sentry

    Args:
        message: 消息内容
        level: 日志级别 (info, warning, error)
        **extra: 额外上下文信息
    """
    sentry_sdk = _lazy_import_sentry()
    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str = None, email: str = None, role: str = None):
    """
    设置用户上下文

    Args:
        user_id: 用户 ID
        email: 用户邮箱
        role: 用户角色
    """
    sentry_sdk = _lazy_import_sentry()
    if sentry_sdk:
        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": email,
                "role": role,
            }
        )
