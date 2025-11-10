"""
认证路由模块
处理用户登录、登出、令牌刷新等认证相关功能
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.security import (
    AuthenticatedUser,
    jwt_manager,
    token_blacklist,
    get_current_active_user
)
from backend.core.response import ok, fail

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    用户登录
    支持用户名/邮箱 + 密码登录
    """
    try:
        # 这里应该实现实际的用户验证逻辑
        # 示例实现，实际应该查询数据库验证用户

        # 模拟用户验证（实际实现需要查询用户表）
        if form_data.username == "admin" and form_data.password == "admin123":
            user_data = {
                "sub": "admin-user-id",
                "role": "admin",
                "email": "admin@example.com",
                "permissions": ["read", "write", "delete", "manage_users"]
            }
        elif form_data.username == "user" and form_data.password == "user123":
            user_data = {
                "sub": "user-id",
                "role": "user",
                "email": "user@example.com",
                "permissions": ["read", "write"]
            }
        else:
            return fail(
                code="AUTH_INVALID_CREDENTIALS",
                message="用户名或密码错误",
                status_code=401
            )

        # 创建令牌对
        token_info = jwt_manager.create_token_pair(user_data)

        return ok({
            "user": {
                "id": user_data["sub"],
                "role": user_data["role"],
                "email": user_data["email"],
                "permissions": user_data["permissions"]
            },
            "token": {
                "access_token": token_info.access_token,
                "refresh_token": token_info.refresh_token,
                "token_type": token_info.token_type,
                "expires_in": token_info.expires_in,
                "expires_at": token_info.expires_at.isoformat() if token_info.expires_at else None
            }
        })

    except Exception as e:
        return fail(
            code="AUTH_LOGIN_ERROR",
            message="登录失败，请稍后重试",
            status_code=500
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    刷新访问令牌
    """
    try:
        # 验证刷新令牌
        payload = jwt_manager.verify_token(refresh_token, "refresh")

        # 检查令牌是否在黑名单中
        jti = payload.get("jti")
        if jti and token_blacklist.is_blacklisted(jti):
            return fail(
                code="AUTH_TOKEN_REVOKED",
                message="刷新令牌已被撤销",
                status_code=401
            )

        # 生成新的访问令牌
        user_data = {
            "sub": payload.get("sub"),
            "role": payload.get("role"),
            "email": payload.get("email"),
            "permissions": payload.get("permissions", [])
        }

        new_access_token = jwt_manager.create_access_token(user_data)

        return ok({
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": jwt_manager.access_token_expire_minutes * 60
        })

    except HTTPException:
        raise
    except Exception as e:
        return fail(
            code="AUTH_REFRESH_ERROR",
            message="令牌刷新失败",
            status_code=500
        )


@router.post("/logout")
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    用户登出
    将用户的令牌添加到黑名单
    """
    try:
        # 获取当前令牌的JTI并添加到黑名单
        jti = current_user.raw_claims.get("jti")
        if jti:
            token_blacklist.add_to_blacklist(jti)

        return ok({
            "message": "登出成功",
            "logged_out_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return fail(
            code="AUTH_LOGOUT_ERROR",
            message="登出失败",
            status_code=500
        )


@router.post("/logout-all")
async def logout_all(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    登出所有设备
    撤销用户的所有令牌
    """
    try:
        # 这里应该实现撤销用户所有令牌的逻辑
        # 实际项目中可以在数据库中记录用户的令牌版本号
        # 或者维护用户的所有活跃令牌列表

        return ok({
            "message": "已从所有设备登出",
            "logged_out_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return fail(
            code="AUTH_LOGOUT_ALL_ERROR",
            message="全设备登出失败",
            status_code=500
        )


@router.get("/me")
async def get_current_user_info(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取当前用户信息
    """
    return ok({
        "user": {
            "id": current_user.id,
            "role": current_user.role,
            "email": current_user.email,
            "permissions": current_user.permissions,
            "is_active": current_user.is_active,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
    })


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    修改密码
    """
    try:
        # 这里应该实现实际的密码修改逻辑
        # 1. 验证旧密码
        # 2. 检查新密码强度
        # 3. 更新数据库中的密码
        # 4. 撤销所有现有令牌，强制重新登录

        if len(new_password) < 8:
            return fail(
                code="AUTH_WEAK_PASSWORD",
                message="新密码长度至少8位",
                status_code=400
            )

        # 模拟密码修改成功
        return ok({
            "message": "密码修改成功，请重新登录",
            "changed_at": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return fail(
            code="AUTH_CHANGE_PASSWORD_ERROR",
            message="密码修改失败",
            status_code=500
        )


@router.get("/verify-token")
async def verify_token(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    验证令牌有效性
    """
    return ok({
        "valid": True,
        "user_id": current_user.id,
        "role": current_user.role,
        "expires_at": current_user.raw_claims.get("exp")
    })


# 错误处理
@router.exception_handler(HTTPException)
async def auth_exception_handler(request, exc: HTTPException):
    """认证异常统一处理"""
    return fail(
        code=exc.detail.get("code", "AUTH_ERROR") if isinstance(exc.detail, dict) else "AUTH_ERROR",
        message=exc.detail.get("message", "认证失败") if isinstance(exc.detail, dict) else str(exc.detail),
        status_code=exc.status_code
    )