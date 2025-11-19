"""
健康检查路由
Version: 1.0
Author: Claude Code
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.core.response import success_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    API 健康检查端点

    返回服务状态和时间戳
    """
    return success_response(
        data={
            "status": "ok",
            "service": "ai-ad-spend-backend",
            "version": "v2.1",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        },
        message="Health check passed"
    )
