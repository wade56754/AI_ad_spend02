"""
Agents HTTP Server - FastAPI 接口

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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
