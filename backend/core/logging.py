"""
统一日志管理模块
提供统一的日志记录功能，包含请求追踪和结构化日志
"""

import logging
import time
import uuid
from typing import Callable, Any
from functools import wraps

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 配置标准库日志处理器
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)

# 为标准库日志添加 structlog 处理器
formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.dev.ConsoleRenderer(),
    foreign_pre_chain=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ],
)

# 配置根日志处理器
root_handler = logging.StreamHandler()
root_handler.setFormatter(formatter)
logging.root.handlers = [root_handler]
logging.root.setLevel(logging.INFO)

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件，为每个请求生成唯一标识符"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 将请求ID添加到结构化日志上下文
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # 记录请求开始
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host if request.client else None,
        )

        # 记录请求处理时间
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录请求完成
        logger.info(
            "Request completed",
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id

        return response


def log_requests(request_id_param: str = "request_id"):
    """
    路由日志记录装饰器
    自动记录请求参数、用户信息和处理结果
    支持同步和异步函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = None

            # 如果还没有request_id，生成一个
            if not request_id:
                request_id = str(uuid.uuid4())
                structlog.contextvars.bind_contextvars(request_id=request_id)

            # 记录请求开始
            logger.info(
                f"{func.__name__} started",
                request_id=request_id,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                # 提取用户信息
                user_info = {}
                current_user = kwargs.get("current_user")
                if current_user:
                    user_info = {
                        "user_id": getattr(current_user, "id", None),
                        "user_email": getattr(current_user, "email", None),
                        "user_role": getattr(current_user, "role", None),
                    }

                logger.info(
                    f"{func.__name__} processing",
                    request_id=request_id,
                    **user_info
                )

                # 执行同步函数
                result = func(*args, **kwargs)

                # 记录成功结果
                process_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed successfully",
                    request_id=request_id,
                    process_time=f"{process_time:.3f}s",
                    **user_info
                )

                return result

            except Exception as e:
                # 记录错误
                process_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    request_id=request_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time=f"{process_time:.3f}s",
                    exc_info=True,
                    **user_info
                )

                # 重新抛出异常
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = None

            # 尝试从kwargs或request中获取request_id
            if "request" in kwargs:
                request = kwargs["request"]
                request_id = getattr(request.state, "request_id", None)

            # 如果没有request_id，从参数中获取
            if not request_id and request_id_param in kwargs:
                request_id = kwargs[request_id_param]

            # 如果还没有request_id，生成一个
            if not request_id:
                request_id = str(uuid.uuid4())
                structlog.contextvars.bind_contextvars(request_id=request_id)

            # 记录请求开始
            logger.info(
                f"{func.__name__} started",
                request_id=request_id,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                # 提取用户信息
                user_info = {}
                current_user = kwargs.get("current_user")
                if current_user:
                    user_info = {
                        "user_id": getattr(current_user, "id", None),
                        "user_email": getattr(current_user, "email", None),
                        "user_role": getattr(current_user, "role", None),
                    }

                logger.info(
                    f"{func.__name__} processing",
                    request_id=request_id,
                    **user_info
                )

                # 执行异步函数
                result = await func(*args, **kwargs)

                # 记录成功结果
                process_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed successfully",
                    request_id=request_id,
                    process_time=f"{process_time:.3f}s",
                    **user_info
                )

                return result

            except Exception as e:
                # 记录错误
                process_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    request_id=request_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time=f"{process_time:.3f}s",
                    exc_info=True,
                    **user_info
                )

                # 重新抛出异常
                raise

        # 检查函数是否是异步的，返回相应的wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_service_calls(service_name: str):
    """
    服务层日志记录装饰器
    记录服务方法的调用和执行结果
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()

            logger.info(
                f"{service_name}.{method.__name__} started",
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                # 执行服务方法
                result = method(self, *args, **kwargs)

                # 记录成功结果
                process_time = time.time() - start_time
                logger.info(
                    f"{service_name}.{method.__name__} completed successfully",
                    process_time=f"{process_time:.3f}s",
                )

                return result

            except Exception as e:
                # 记录错误
                process_time = time.time() - start_time
                logger.error(
                    f"{service_name}.{method.__name__} failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time=f"{process_time:.3f}s",
                    exc_info=True,
                )

                # 重新抛出异常
                raise

        return wrapper
    return decorator


def log_function_calls(func_name: str = None):
    """
    通用函数日志记录装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            logger.debug(
                f"{name} started",
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                # 执行函数
                result = func(*args, **kwargs)

                # 记录成功结果
                process_time = time.time() - start_time
                logger.debug(
                    f"{name} completed successfully",
                    process_time=f"{process_time:.3f}s",
                )

                return result

            except Exception as e:
                # 记录错误
                process_time = time.time() - start_time
                logger.error(
                    f"{name} failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time=f"{process_time:.3f}s",
                    exc_info=True,
                )

                # 重新抛出异常
                raise

        return wrapper
    return decorator


class LoggingMixin:
    """日志混入类，为服务类提供统一的日志方法"""

    @property
    def _logger(self):
        """获取当前类的日志记录器"""
        return structlog.get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        self._logger.info(message, **kwargs)

    def log_warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._logger.warning(message, **kwargs)

    def log_error(self, message: str, **kwargs):
        """记录错误日志"""
        self._logger.error(message, **kwargs)

    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._logger.debug(message, **kwargs)

    def log_exception(self, message: str, exception: Exception, **kwargs):
        """记录异常日志，包含完整的异常信息"""
        self._logger.error(
            message,
            exc_info=True,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            **kwargs
        )


def setup_user_context(request: Request, user=None):
    """设置用户相关的日志上下文"""
    context_data = {"request_path": request.url.path}

    if user:
        context_data.update({
            "user_id": getattr(user, "id", None),
            "user_email": getattr(user, "email", None),
            "user_role": getattr(user, "role", None),
        })

    structlog.contextvars.bind_user_context(**context_data)


def create_request_logger(request: Request, endpoint: str):
    """创建请求专用的日志记录器"""
    return logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        endpoint=endpoint,
        method=request.method,
        path=request.url.path,
    )