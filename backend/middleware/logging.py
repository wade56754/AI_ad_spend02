"""
日志中间件
统一处理请求日志记录
"""
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    def __init__(self, app, logger_name: str = "api"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)
        # 排除不需要记录日志的路径
        self.exclude_paths = {"/health", "/healthz", "/ready", "/readyz", "/metrics"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 获取用户信息（如果已认证）
        user_id = None
        user_email = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
            user_email = request.state.user.email

        # 跳过健康检查等路径的日志
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 记录请求开始
        self.logger.info(
            "Request started",
            extra={
                "event": "request_start",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id,
                "user_email": user_email,
            }
        )

        # 执行请求
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录请求异常
            self.logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "event": "request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True
            )
            raise

        # 计算响应时间
        process_time = time.time() - start_time

        # 记录请求完成
        log_level = logging.INFO
        if response.status_code >= 400:
            log_level = logging.WARNING
        if response.status_code >= 500:
            log_level = logging.ERROR

        self.logger.log(
            log_level,
            "Request completed",
            extra={
                "event": "request_end",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "client_ip": client_ip,
                "user_id": user_id,
                "user_email": user_email,
            }
        )

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 返回直接连接的IP
        return request.client.host


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件
    记录敏感操作的审计日志
    """

    def __init__(self, app):
        super().__init__(app)
        # 需要审计的操作
        self.audit_methods = {"POST", "PUT", "PATCH", "DELETE"}
        self.audit_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/users",
            "/api/v1/projects",
            "/api/v1/ad-accounts",
            "/api/v1/topups",
            "/api/v1/reconciliations",
            "/api/v1/daily-reports",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取请求前的状态
        request_body = None
        if request.method in self.audit_methods:
            # 读取请求体（注意：这会消耗请求体，需要重新设置）
            request_body = await request.body()

        # 执行请求
        response = await call_next(request)

        # 判断是否需要审计
        if self._should_audit(request):
            # 记录审计日志
            await self._log_audit(request, response, request_body)

        return response

    def _should_audit(self, request: Request) -> bool:
        """判断是否需要审计"""
        # 检查请求方法
        if request.method not in self.audit_methods:
            return False

        # 检查路径
        for path in self.audit_paths:
            if request.url.path.startswith(path):
                return True

        return False

    async def _log_audit(self, request: Request, response: Response, request_body: bytes):
        """记录审计日志"""
        try:
            # 获取用户信息
            user_id = None
            user_email = None
            if hasattr(request.state, "user"):
                user_id = request.state.user.id
                user_email = request.state.user.email

            # 获取IP地址
            client_ip = request.headers.get("x-forwarded-for", request.client.host)

            # 解析请求体
            body_data = None
            if request_body:
                import json
                try:
                    body_data = json.loads(request_body.decode())
                    # 脱敏处理：移除密码等敏感字段
                    if isinstance(body_data, dict):
                        body_data = self._sanitize_body(body_data)
                except:
                    pass

            # 构建审计日志
            audit_log = {
                "event": "api_call",
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "user_id": user_id,
                "user_email": user_email,
                "client_ip": client_ip,
                "request_body": body_data,
                "timestamp": time.time(),
            }

            # 记录到专门的审计日志
            audit_logger = logging.getLogger("audit")
            audit_logger.info("API audit", extra=audit_log)

        except Exception as e:
            # 审计日志记录失败不应影响主流程
            logger.error(f"Failed to log audit: {e}")

    def _sanitize_body(self, body: dict) -> dict:
        """脱敏处理请求体"""
        sensitive_fields = {"password", "token", "secret", "key", "authorization"}
        sanitized = {}

        for key, value in body.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_body(value)
            else:
                sanitized[key] = value

        return sanitized


def setup_logging(config: dict = None):
    """配置日志系统

    Args:
        config: 日志配置字典
    """
    import os
    from logging.config import dictConfig

    # 默认配置
    default_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/audit.log",
                "maxBytes": 52428800,  # 50MB
                "backupCount": 30,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # root logger
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
            },
            "api": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "audit": {
                "level": "INFO",
                "handlers": ["audit_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    # 合并用户配置
    if config:
        # 深度合并配置
        merged_config = default_config
        for key, value in config.items():
            if key in merged_config and isinstance(merged_config[key], dict):
                merged_config[key].update(value)
            else:
                merged_config[key] = value
    else:
        merged_config = default_config

    # 创建日志目录
    os.makedirs("logs", exist_ok=True)

    # 应用配置
    dictConfig(merged_config)

    logger.info("Logging system initialized")