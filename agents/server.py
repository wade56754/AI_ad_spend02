"""
Agents HTTP Server - FastAPI 接口

# Fix: P1-05 - 添加 HTTP 速率限制

提供 HTTP 接口调用 Agent 系统，支持：
- GET /agents - 列出可用 Agent
- POST /agents/{agent_key}/handle - 调用指定 Agent
- GET /health - 健康检查

启动方式：
    uvicorn agents.server:app --reload --port 8001

或者使用 CLI：
    python -m agents.server
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .agents_config import (
    create_agent,
    list_agents,
    check_llm_available,
    AgentInfo,
)

# === 日志配置 ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# === Fix: P1-05 - 速率限制配置 ===
class RateLimiter:
    """
    简单的内存速率限制器。

    # Fix: P1-05 - 生产环境建议使用 Redis 或专用中间件

    配置：
    - 默认限制：每个 IP 每分钟 60 次请求
    - Agent 调用限制：每个 IP 每分钟 10 次（LLM 调用较慢）
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_ip: str) -> bool:
        """检查请求是否在限制内"""
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # 清理过期记录
            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip] if ts > cutoff
            ]

            # 检查是否超限
            if len(self._requests[client_ip]) >= self.max_requests:
                return False

            # 记录本次请求
            self._requests[client_ip].append(now)
            return True

    def get_remaining(self, client_ip: str) -> int:
        """获取剩余请求次数"""
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            current = [ts for ts in self._requests[client_ip] if ts > cutoff]
            return max(0, self.max_requests - len(current))


# Fix: P1-05 - 速率限制实例
# - 通用限制：60 次/分钟
# - Agent 调用限制：10 次/分钟（LLM 调用开销大）
_general_limiter = RateLimiter(max_requests=60, window_seconds=60)
_agent_limiter = RateLimiter(max_requests=10, window_seconds=60)


# === FastAPI App ===
app = FastAPI(
    title="AI_ad_spend02 Agents API",
    description="HTTP 接口调用 Agent 系统",
    version="1.0.0",
)

# CORS 配置（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Fix: P1-05 - 速率限制中间件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    HTTP 速率限制中间件。

    # Fix: P1-05 - 防止 API 滥用

    限制策略：
    - /agents/{key}/handle: 10 次/分钟（Agent 调用）
    - 其他端点: 60 次/分钟（通用限制）
    """
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # 选择限制器
    if "/handle" in path:
        limiter = _agent_limiter
        limit_name = "agent"
    else:
        limiter = _general_limiter
        limit_name = "general"

    if not limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded: {client_ip} ({limit_name})")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": f"Rate limit exceeded. Please wait before making more requests.",
                "retry_after": limiter.window_seconds,
            },
            headers={
                "Retry-After": str(limiter.window_seconds),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)

    # 添加速率限制头
    response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(client_ip))
    response.headers["X-RateLimit-Limit"] = str(limiter.max_requests)

    return response


# === 请求/响应模型 ===

class AgentRequest(BaseModel):
    """Agent 请求体"""
    action: Optional[str] = None
    task: Optional[str] = None
    target_files: Optional[list] = None
    changes: Optional[Dict[str, str]] = None
    context: Optional[str] = None
    # 其他可选参数
    extra: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent 响应体"""
    success: bool
    agent: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    llm_backend: str
    llm_available: bool
    agents_count: int


# === 路由 ===

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    llm_status = check_llm_available()
    agents = list_agents()

    return HealthResponse(
        status="ok",
        llm_backend=llm_status["backend"],
        llm_available=llm_status["available"],
        agents_count=len(agents),
    )


@app.get("/agents", response_model=Dict[str, AgentInfo])
async def get_agents():
    """列出所有可用 Agent"""
    return list_agents()


@app.post("/agents/{agent_key}/handle", response_model=AgentResponse)
async def handle_agent_request(agent_key: str, request: AgentRequest):
    """
    调用指定 Agent 处理请求。

    Args:
        agent_key: Agent 标识符（fe, be, test, orch, doc, review）
        request: Agent 请求体

    Returns:
        Agent 处理结果
    """
    logger.info(f"Agent request: {agent_key}, action={request.action}")

    try:
        # 创建 Agent 实例
        agent = create_agent(agent_key)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 构建请求字典
    req_dict: Dict[str, Any] = {}
    if request.action:
        req_dict["action"] = request.action
    if request.task:
        req_dict["task"] = request.task
    if request.target_files:
        req_dict["target_files"] = request.target_files
    if request.changes:
        req_dict["changes"] = request.changes
    if request.context:
        req_dict["context"] = request.context
    if request.extra:
        req_dict.update(request.extra)

    try:
        # 调用 Agent
        result = agent.handle_request(req_dict)

        # 统一响应格式
        return AgentResponse(
            success=result.get("success", True),
            agent=agent_key,
            data=result,
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return AgentResponse(
            success=False,
            agent=agent_key,
            data=None,
            error=str(e),
        )


# === CLI 入口 ===

def main():
    """CLI 启动入口"""
    import uvicorn

    print("=" * 50)
    print("AI_ad_spend02 Agents HTTP Server")
    print("=" * 50)

    llm_status = check_llm_available()
    print(f"LLM Backend: {llm_status['backend']}")
    print(f"LLM Available: {llm_status['available']}")
    print(f"Agents: {', '.join(list_agents().keys())}")
    print("=" * 50)

    uvicorn.run(
        "agents.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    main()
