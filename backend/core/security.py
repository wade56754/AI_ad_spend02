from __future__ import annotations

import base64
import hmac
import json
from dataclasses import dataclass
from hashlib import sha256
from time import time
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.db import get_db
from backend.models.users import User


def _base64url_decode(data: str) -> bytes:
    padding = (-len(data)) % 4
    return base64.urlsafe_b64decode(data + ("=" * padding))


def _decode_segment(segment: str) -> Dict[str, Any]:
    try:
        decoded = _base64url_decode(segment)
        return json.loads(decoded.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 解析失败"},
        ) from exc


def _verify_signature(token: str, secret: str) -> Dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 结构不合法"},
        ) from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()

    actual_signature = _base64url_decode(signature_segment)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 校验失败"},
        )

    header = _decode_segment(header_segment)
    if header.get("alg") != "HS256":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "不支持的签名算法"},
        )

    payload = _decode_segment(payload_segment)

    exp = payload.get("exp")
    if exp is not None and exp < int(time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_EXPIRED", "message": "Token 已过期"},
        )

    return payload


@dataclass
class AuthenticatedUser:
    id: str
    role: Optional[str]
    email: Optional[str]
    raw_claims: Dict[str, Any]


def _extract_user(payload: Dict[str, Any]) -> AuthenticatedUser:
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 缺少用户标识"},
        )

    role = payload.get("role") or payload.get("app_metadata", {}).get("role")
    email = payload.get("email") or payload.get("user_metadata", {}).get("email")

    return AuthenticatedUser(id=str(user_id), role=role, email=email, raw_claims=payload)


def _resolve_role(db: Session, user_id: str, fallback: Optional[str]) -> Optional[str]:
    try:
        user_uuid = UUID(str(user_id))
    except (TypeError, ValueError):
        return fallback
    db_user = db.query(User).filter(User.id == user_uuid).first()
    if db_user:
        return db_user.role
    return fallback


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_MISSING_TOKEN", "message": "缺少 Authorization 头"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Authorization 头格式错误"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID_TOKEN", "message": "Token 为空"},
        )

    settings = get_settings()
    secret = getattr(settings, "jwt_secret", None)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "AUTH_CONFIG_ERROR", "message": "JWT_SECRET 未配置"},
        )

    payload = _verify_signature(token, secret)
    user = _extract_user(payload)
    user.role = _resolve_role(db, user.id, user.role)
    return user


def authenticated_user_dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    return user


