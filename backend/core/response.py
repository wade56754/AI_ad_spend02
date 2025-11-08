from datetime import datetime
from typing import Any, Dict, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _timestamp_meta(meta: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = meta or {}
    if "timestamp" not in base:
        base["timestamp"] = datetime.utcnow().isoformat()
    return base


def ok(data: Any = None, status_code: int = 200, meta: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": jsonable_encoder(data),
            "error": None,
            "meta": _timestamp_meta(meta),
        },
    )


def fail(code: str, message: str, status_code: int = 400, meta: Optional[Dict[str, Any]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "error": {"code": code, "message": message},
            "meta": _timestamp_meta(meta),
        },
    )


